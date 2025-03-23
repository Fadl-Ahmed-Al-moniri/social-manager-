from django.urls import path,include
from .views import InteractionsView
from platform_media.view.instgram_view import InstagramView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'engage', InteractionsView, basename='engage')

urlpatterns = [
    path('', include(router.urls)),
]
