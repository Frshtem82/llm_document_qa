from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Document, DocumentChunk
from .serializers import (
    DocumentSerializer,
    DocumentDetailSerializer,
    DocumentChunkSerializer,
)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    مدیریت اسناد:
    - list: لیست اسناد
    - create: ساخت سند جدید (با فایل docx یا متن)
    - retrieve: جزئیات سند + chunkها
    - update/partial_update: ویرایش
    - destroy: حذف
    - process: پردازش سند (chunking + embedding)
    """
    
    queryset = Document.objects.all().order_by('-created_at')
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentSerializer
    
    @action(detail=True, methods=['post'], url_path='process')
    def process(self, request, pk=None):
        """پردازش یک سند: chunking + embedding + ذخیره در Qdrant."""
        document = self.get_object()
        try:
            n = document.process()
            return Response({
                'detail': f'{n} تکه ساخته شد.',
                'chunk_count': n,
                'is_processed': document.is_processed,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': f'خطا در پردازش: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهده تکه‌های سند (فقط خواندنی).
    """
    queryset = DocumentChunk.objects.select_related('document').all()
    serializer_class = DocumentChunkSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        document_id = self.request.query_params.get('document_id')
        if document_id:
            qs = qs.filter(document_id=document_id)
        return qs