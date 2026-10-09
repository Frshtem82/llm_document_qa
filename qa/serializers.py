from rest_framework import serializers
from .models import Question
from documents.serializers import DocumentChunkSerializer


class QuestionSerializer(serializers.ModelSerializer):
    sources = DocumentChunkSerializer(many=True, read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'document', 'document_title',
            'answer', 'status', 'sources', 'created_at'
        ]
        read_only_fields = ['id', 'answer', 'status', 'sources', 'created_at']


class AskQuestionSerializer(serializers.Serializer):
    
    text = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
        help_text="متن پرسش"
    )
    k = serializers.IntegerField(
        required=False,
        default=4,
        min_value=1,
        max_value=10,
        help_text="تعداد تکه‌های بازیابی‌شده (پیش‌فرض 4)"
    )
    document_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="اگر داده شود، فقط در همان سند جستجو می‌شود"
    )
    save = serializers.BooleanField(
        required=False,
        default=True,
        help_text="آیا پرسش و پاسخ در تاریخچه ذخیره شود؟"
    )