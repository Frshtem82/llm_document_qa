from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'document', 'content', 'chunk_index', 'created_at']
        read_only_fields = ['id', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file', 'full_text',
            'is_processed', 'chunk_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'is_processed', 'created_at', 'updated_at']
    
    def get_chunk_count(self, obj):
        return obj.chunks.count()


class DocumentDetailSerializer(DocumentSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)
    
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ['chunks']