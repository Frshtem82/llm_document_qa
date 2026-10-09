from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .models import Question
from .serializers import QuestionSerializer, AskQuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    """
    مدیریت پرسش‌ها:
    - list: تاریخچه پرسش‌ها
    - retrieve: جزئیات یک پرسش
    - destroy: حذف پرسش
    - ask: پرسیدن یک پرسش جدید (تولید پاسخ با LLM)
    """
    
    queryset = Question.objects.all().order_by('-created_at')
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        document_id = self.request.query_params.get('document_id')
        if document_id:
            qs = qs.filter(document_id=document_id)
        return qs
    
    @action(detail=False, methods=['post'], url_path='ask')
    def ask(self, request):
        """
        یک پرسش جدید ثبت کن و پاسخ رو با LLM تولید کن.
        
        ورودی:
            - text (اجباری): متن پرسش
            - k (اختیاری): تعداد chunkهای بازیابی (پیش‌فرض 4)
            - document_id (اختیاری): محدود کردن جستجو به یک سند
            - save (اختیاری): ذخیره در تاریخچه (پیش‌فرض true)
        """
        serializer = AskQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # ساخت آبجکت Question
        question = Question(
            text=data['text'],
            document_id=data.get('document_id')
        )
        
        if data.get('save', True):
            question.save()
        
        try:
            question.ask(k=data.get('k', 4))
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            if data.get('save', True):
                question.status = 'failed'
                question.answer = f"خطا: {e}"
                question.save(update_fields=['status', 'answer'])
            
            return Response(
                {
                    'detail': f'خطا در تولید پاسخ: {e}',
                    'question_id': question.id if question.id else None,
                    'status': 'failed',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_data = {
            'question_id': question.id if question.id else None,
            'text': question.text,
            'document_id': question.document_id,
            'document_title': question.document.title if question.document else None,
            'answer': question.answer,
            'status': question.status,
            'sources': [
                {
                    'chunk_id': s.id,
                    'document_id': s.document_id,
                    'document_title': s.document.title,
                    'chunk_index': s.chunk_index,
                    'content': s.content,
                }
                for s in question.sources.all()
            ],
        }
        return Response(response_data, status=status.HTTP_200_OK)


class SearchView(APIView):
    """
    جستجوی معنایی مستقیم در اسناد (بدون LLM).
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'detail': 'پارامتر q (متن جستجو) اجباری است.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            k = int(request.query_params.get('k', 4))
        except ValueError:
            k = 4
        
        document_id = request.query_params.get('document_id')
        if document_id:
            try:
                document_id = int(document_id)
            except ValueError:
                document_id = None
        
        from documents.embeddings import search_similar_chunks
        results = search_similar_chunks(query, k=k, document_id=document_id)
        
        return Response({
            'query': query,
            'count': len(results),
            'results': results,
        })