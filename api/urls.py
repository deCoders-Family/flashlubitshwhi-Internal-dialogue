from django.urls import path

from .views import (
    AnalyzeTextView,
    GenerateAudioView,
    ListCreateAvatarAPIView,
    ListCreateChatHistorySerializer,
    RetrieveUpdatedDestroyAvatarAPIView,
    RetrieveUpdatedDestroyChatHistoryAPIView,
    ReplayDialogeAPIView,
)


urlpatterns = [
    path("speak", GenerateAudioView.as_view()),
    path("avatar", ListCreateAvatarAPIView.as_view()),
    path("avatar/<uuid:uid>", RetrieveUpdatedDestroyAvatarAPIView.as_view()),
    path("chat-history", ListCreateChatHistorySerializer.as_view()),
    path("chat-history/<uuid:uid>", RetrieveUpdatedDestroyChatHistoryAPIView.as_view()),
    path("replay-dialogue", ReplayDialogeAPIView.as_view()),
    path("analyze", AnalyzeTextView.as_view()),
]
