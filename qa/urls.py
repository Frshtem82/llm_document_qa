from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet, SearchView

router = DefaultRouter()
router.register('questions', QuestionViewSet, basename='question')

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('', include(router.urls)),
]