from django.db import models
from documents.models import Document, DocumentChunk
from typing import Optional


class Question(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('answered', 'پاسخ داده شده'),
        ('failed', 'خطا'),
    ]
    
    text = models.TextField(verbose_name="متن پرسش")
    
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name="سند (اختیاری)",
        help_text="اگه انتخاب بشه، فقط توی همین سند جستجو می‌شه. "
                  "اگه خالی بمونه، توی همه اسناد جستجو می‌شه."
    )
    
    answer = models.TextField(blank=True, verbose_name="پاسخ")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت"
    )
    sources = models.ManyToManyField(
        DocumentChunk,
        blank=True,
        related_name='questions',
        verbose_name="منابع"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "پرسش"
        verbose_name_plural = "پرسش‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:50]

    def ask(self, k: int = 4):
        """
        این سوال رو از سرویس RAG می‌پرسه و پاسخ رو ذخیره می‌کنه.
        اگه self.document ست شده باشه، فقط توی همون سند جستجو می‌شه.
        """
        from .services import answer_question
        from documents.models import DocumentChunk
        
        self.status = 'pending'
        self.save(update_fields=['status'])
        
        try:
            # اگه سند انتخاب شده، فقط توی همون سند جستجو کن
            document_id = self.document_id if self.document_id else None
            
            result = answer_question(self.text, k=k, document_id=document_id)
            self.answer = result['answer']
            self.status = 'answered'
            self.save(update_fields=['answer', 'status'])
            
            chunk_ids = [s['chunk_id'] for s in result['sources'] if s.get('chunk_id')]
            if chunk_ids:
                chunks = DocumentChunk.objects.filter(id__in=chunk_ids)
                self.sources.set(chunks)
            
            return result
        except Exception as e:
            self.status = 'failed'
            self.answer = f"خطا: {e}"
            self.save(update_fields=['answer', 'status'])
            raise