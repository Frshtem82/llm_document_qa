from django.contrib import admin, messages
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_processed', 'chunk_count', 'created_at', 'updated_at')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('title', 'full_text')
    readonly_fields = ('created_at', 'updated_at', 'is_processed')
    actions = ['process_documents', 'extract_text_action', 'rebuild_index_action']
    
    fieldsets = (
        ('اطلاعات اصلی', {'fields': ('title', 'file', 'full_text')}),
        ('وضعیت', {
            'fields': ('is_processed', 'created_at', 'updated_at'),
            'description': 'change file -> is_processed = false'
        }),
    )

    def chunk_count(self, obj):
        return obj.chunks.count()
    chunk_count.short_description = "تعداد تکه"

    @admin.action(description="پردازش اسناد انتخاب‌شده")
    def process_documents(self, request, queryset):
        success = 0
        failed = 0
        for doc in queryset:
            try:
                n = doc.process()
                success += 1
                self.message_user(
                    request,
                    f"✅ '{doc.title}': {n} تکه ساخته شد.",
                    level=messages.SUCCESS
                )
            except Exception as e:
                failed += 1
                self.message_user(
                    request,
                    f"❌ خطا در '{doc.title}': {e}",
                    level=messages.ERROR
                )
        if failed:
            self.message_user(
                request,
                f"{failed} سند با خطا مواجه شد. is_processed برای این اسناد False مونده.",
                level=messages.WARNING
            )

    @admin.action(description="استخراج مجدد متن از فایل")
    def extract_text_action(self, request, queryset):
        from .utils import extract_text_from_file
        count = 0
        for doc in queryset:
            if doc.file:
                try:
                    doc.full_text = extract_text_from_file(doc.file)
                    doc.save(update_fields=['full_text'])
                    count += 1
                    self.message_user(
                        request,
                        f"'{doc.title}': متن استخراج شد.",
                        level=messages.SUCCESS
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f"خطا در '{doc.title}': {e}",
                        level=messages.ERROR
                    )
        if count:
            self.message_user(
                request,
                f"{count} سند استخراج شد. برای اعمال، دوباره پردازش کن.",
                level=messages.INFO
            )

    @admin.action(description="بازسازی کل index جستجو (Qdrant)")
    def rebuild_index_action(self, request, queryset):
        from .embeddings import rebuild_index
        try:
            n = rebuild_index()
            self.message_user(
                request,
                f"index با {n} تکه بازسازی شد.",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"خطا در بازسازی index: {e}",
                level=messages.ERROR
            )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'short_content')
    list_filter = ('document',)
    search_fields = ('content',)

    def short_content(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    short_content.short_description = "محتوا"