from django.db import models
from django.db import transaction


class Document(models.Model):
    
    title = models.CharField(max_length=255, verbose_name="عنوان")
    file = models.FileField(
        upload_to='documents/',
        blank=True,
        null=True,
        verbose_name="فایل (docx)"
    )
    full_text = models.TextField(blank=True, verbose_name="متن کامل")
    is_processed = models.BooleanField(default=False, verbose_name="پردازش شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ ویرایش")

    class Meta:
        verbose_name = "سند"
        verbose_name_plural = "اسناد"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        اول سند رو ذخیره کن (تا فایل روی دیسک نوشته بشه).
        بعد:
        - اگه فایل جدید آپلود شده، متن رو دوباره استخراج کن
        - اگه فایل حذف شده، متن رو پاک کن
        - اگه فایل عوض شده، is_processed رو ریست کن (چون chunkها دیگه معتبر نیستن)
        """
        # قبل از ذخیره، وضعیت فایل قبلی رو بگیر
        old_file_name = None
        if self.pk:
            try:
                old = Document.objects.get(pk=self.pk)
                old_file_name = old.file.name if old.file else None
            except Document.DoesNotExist:
                old_file_name = None
        
        # ذخیره سند (فایل روی دیسک نوشته می‌شه)
        super().save(*args, **kwargs)
        
        new_file_name = self.file.name if self.file else None
        file_changed = (old_file_name != new_file_name)
        
        # حالت ۱: فایل حذف شده → متن رو پاک کن
        if old_file_name and not new_file_name:
            if self.full_text:
                self.full_text = ''
                self.is_processed = False
                super().save(update_fields=['full_text', 'is_processed'])
                print(f"🗑️ متن سند '{self.title}' پاک شد (فایل حذف شد).")
            return
        
        # حالت ۲: فایل جدید آپلود شده → متن رو دوباره استخراج کن
        if new_file_name and (file_changed or not self.full_text):
            from .utils import extract_text_from_file
            try:
                text = extract_text_from_file(self.file)
                if text:
                    self.full_text = text
                    update_fields = ['full_text']
                    
                    # اگه فایل عوض شد، is_processed رو ریست کن
                    if file_changed and self.is_processed:
                        self.is_processed = False
                        update_fields.append('is_processed')
                        print(f"⚠️ سند '{self.title}' نیاز به پردازش مجدد داره (فایل عوض شد).")
                    
                    super().save(update_fields=update_fields)
                    print(f"✅ متن استخراج شد: {len(text)} کاراکتر از {self.file.name}")
            except Exception as e:
                print(f"❌ خطا در استخراج: {e}")

    def process(self):
        """
        chunking + embedding + Qdrant.
        is_processed فقط بعد از موفقیت کامل (DB + Qdrant) True می‌شه.
        اگه هر مرحله fail بده، is_processed=False می‌مونه.
        """
        from .utils import split_text_into_chunks
        from .embeddings import add_chunks_to_index, delete_document_from_index
        
        # قدم ۰: چک متن خالی
        if not self.full_text or not self.full_text.strip():
            print(f"⚠️ سند '{self.title}' متن خالی داره.")
            self.is_processed = False
            self.save(update_fields=['is_processed'])
            raise ValueError(f"سند '{self.title}' متن خالی داره. اول متن رو استخراج کن.")
        
        # قدم ۱: is_processed رو False کن (تا اگه خطا داد، False بمونه)
        self.is_processed = False
        self.save(update_fields=['is_processed'])
        
        # قدم ۲: پاک کردن از Qdrant (اگه قبلاً index شده)
        # خطای این مرحله کشنده نیست (شاید اصلاً چیزی نباشه که پاک بشه)
        try:
            delete_document_from_index(self.id)
        except Exception as e:
            print(f"⚠️ خطا در پاک کردن از Qdrant (ادامه می‌دیم): {e}")
        
        # قدم ۳: پاک کردن chunkهای قبلی از DB
        self.chunks.all().delete()
        
        # قدم ۴: chunking
        chunks = split_text_into_chunks(self.full_text)
        if not chunks:
            self.is_processed = False
            self.save(update_fields=['is_processed'])
            raise ValueError(f"سند '{self.title}' هیچ chunk ای تولید نکرد.")
        
        # قدم ۵: ساخت chunkها توی DB
        chunk_objects = [
            DocumentChunk(document=self, content=c, chunk_index=i)
            for i, c in enumerate(chunks)
        ]
        
        with transaction.atomic():
            DocumentChunk.objects.bulk_create(chunk_objects)
        
        # خوندن مجدد برای گرفتن idها
        created = list(DocumentChunk.objects.filter(document=self))
        
        # قدم ۶: اضافه کردن به Qdrant
        # اگه این fail بده، is_processed=False می‌مونه
        try:
            n = add_chunks_to_index(created)
            print(f"✅ {n} chunk به Qdrant اضافه شد.")
        except Exception as e:
            print(f"❌ خطا در Qdrant: {e}")
            # raise می‌کنیم تا admin هم ببینه
            raise RuntimeError(
                f"پردازش سند '{self.title}' ناموفق بود: "
                f"خطا در ارتباط با Qdrant. جزئیات: {e}"
            )
        
        # قدم ۷: حالا که همه چیز موفق بود، is_processed=True
        self.is_processed = True
        self.save(update_fields=['is_processed'])
        print(f"✅ سند '{self.title}' با {len(created)} chunk پردازش شد.")
        
        return len(created)

    def delete(self, *args, **kwargs):
        """قبل از حذف سند، chunkهاش رو از Qdrant پاک کن."""
        from .embeddings import delete_document_from_index
        try:
            delete_document_from_index(self.id)
        except Exception as e:
            print(f"خطا در پاک کردن از Qdrant: {e}")
        super().delete(*args, **kwargs)


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='chunks', verbose_name="سند"
    )
    content = models.TextField(verbose_name="محتوا")
    chunk_index = models.IntegerField(verbose_name="شماره تکه")
    embedding = models.JSONField(null=True, blank=True, verbose_name="بردار معنایی")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تکه سند"
        verbose_name_plural = "تکه‌های سند"
        ordering = ['document', 'chunk_index']
        unique_together = ('document', 'chunk_index')

    def __str__(self):
        return f"{self.document.title} - chunk {self.chunk_index}"