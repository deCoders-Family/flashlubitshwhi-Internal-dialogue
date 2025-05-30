from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    AnalyzeTextView,
    GenerateAudioAPIView,
    ListCreateAvatarAPIView,
    ListCreateChatHistorySerializer,
    ListCreateMoodAPIView,
    ListCreateUserAPIView,
    LoginUserView,
    RetrieveDestroyGenericAudioAPIView,
    RetrieveUpdatedDestroyAvatarAPIView,
    RetrieveUpdatedDestroyChatHistoryAPIView,
    RetrieveUpdateDestroyMeUserAPIView,
    RetrieveUpdateDestroyMoodAPIView,
    ReplayDialogeAPIView,
)


urlpatterns = [
    path("users", ListCreateUserAPIView.as_view()),
    path("login", LoginUserView.as_view()),
    path("me", RetrieveUpdateDestroyMeUserAPIView.as_view()),
    path("speak", GenerateAudioAPIView.as_view()),
    path("speak/<uuid:uid>", RetrieveDestroyGenericAudioAPIView.as_view()),
    path("avatar", ListCreateAvatarAPIView.as_view()),
    path("avatar/<uuid:uid>", RetrieveUpdatedDestroyAvatarAPIView.as_view()),
    path("chat-history", ListCreateChatHistorySerializer.as_view()),
    path("chat-history/<uuid:uid>", RetrieveUpdatedDestroyChatHistoryAPIView.as_view()),
    path("replay-dialogue", ReplayDialogeAPIView.as_view()),
    path("analyze", AnalyzeTextView.as_view()),
    path("moods", ListCreateMoodAPIView.as_view()),
    path("mood/<uuid:uid>", RetrieveUpdateDestroyMoodAPIView.as_view()),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
