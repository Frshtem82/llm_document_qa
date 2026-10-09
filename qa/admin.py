from django.contrib import admin, messages
from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'document_title', 'status', 'created_at')
    list_filter = ('status', 'document', 'created_at')
    search_fields = ('text', 'answer')
    
    readonly_fields = ('created_at', 'answer', 'status', 'sources')
    
    actions = ['ask_questions']
    
    fieldsets = (
        ('پرسش', {
            'fields': ('text', 'document'),
            'description': 'اگه می‌خوای جستجو فقط توی یه سند خاص انجام بشه، سند رو انتخاب کن. '
                           'اگه خالی بمونه، توی همه اسناد جستجو می‌شه.'
        }),
        ('پاسخ (خودکار)', {
            'fields': ('answer', 'sources', 'status'),
            'description': 'این فیلدها بعد از اجرای action «پرسیدن سوال» به صورت خودکار پر می‌شن.'
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )

    def short_text(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    short_text.short_description = "پرسش"

    def document_title(self, obj):
        return obj.document.title if obj.document else "— همه اسناد —"
    document_title.short_description = "سند"

    @admin.action(description="پرسیدن سوال‌های انتخاب‌شده از LLM")
    def ask_questions(self, request, queryset):
        success = 0
        failed = 0
        for q in queryset:
            try:
                q.ask()
                success += 1
            except Exception as e:
                failed += 1
                self.message_user(
                    request,
                    f"خطا در «{q.text[:40]}»: {e}",
                    level=messages.ERROR
                )
        if success:
            self.message_user(
                request,
                f"{success} سوال با موفقیت پاسخ داده شد.",
                level=messages.SUCCESS
            )
        if failed:
            self.message_user(
                request,
                f"{failed} سوال با خطا مواجه شد.",
                level=messages.WARNING
            )