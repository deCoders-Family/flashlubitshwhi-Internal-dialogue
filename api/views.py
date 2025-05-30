import os
import uuid

from django.contrib.auth import authenticate
from django.db.models import Q
# from django.views.decorators.cache import cache_page
# from django.utils.decorators import method_decorator

from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView


from rest_framework_simplejwt.tokens import RefreshToken

from dotenv import load_dotenv

from .choices import SenderTypeChoices, StatusChoices
from .models import Avatar, ChatHistory, GeneratedAudio, Mood, User
from .serializers import (
    AvatarSerializer,
    ChatHistorySerializer,
    GeneratedAudioSerializer,
    LoginUserSerializer,
    MoodSerializer,
    UserSerializer,
)
from .utils import clean_text, generate_elevenlabs_audio

import google.generativeai as genai
from openai import OpenAI

# Create your views here.

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ListCreateUserAPIView(generics.ListCreateAPIView):
    queryset = User.objects.IS_ACTIVE().order_by("id")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAdminUser]

        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]


class RetrieveUpdateDestroyMeUserAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.status = StatusChoices.REMOVED
        instance.save()


class LoginUserView(generics.GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = authenticate(username=email, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refreshToken": str(refresh),
                "accessToken": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


# class RetrieveUpdateMeUserView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         return self.request.user


# class GenerateAudioView(APIView):
class GenerateAudioAPIView(generics.GenericAPIView):
    serializer_class = GeneratedAudioSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = self.request.user
        serializer = GeneratedAudioSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            user_text = validated_data.get("text")
            mode = request.data.get("mode", "friendly")
            convo_id = request.data.get("conversation_id", str(uuid.uuid4()))
            user_voice_name = validated_data.get("user_voice_name")
            ai_voice_name = validated_data.get("ai_voice_name")
            reply_as = validated_data.get("reply_as", "AI")
            # reply_as = request.data.get("reply_as", "AI")
            sender_type = request.data.get("sender_type")

            user_voice = Avatar.objects.filter(
                voice_name=user_voice_name, side=SenderTypeChoices.USER
            ).latest("created_at")
            ai_voice = Avatar.objects.filter(
                voice_name=ai_voice_name, side=SenderTypeChoices.AI
            ).latest("created_at")

            user_voice_id = user_voice.elevenlabs_voice_id
            ai_voice_id = ai_voice.elevenlabs_voice_id

            mood_obj = Mood.objects.filter(
                mood_name=mode.lower(), status=StatusChoices.ACTIVE
            ).latest("created_at")
            prompt = f"{mood_obj.mood_prompt}\nUser: {user_text}\nAI:"

            if reply_as == SenderTypeChoices.AI:
                # --- OpenAI integration ---

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are not an AI character. You will act like another person and reply in a conversation.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                    )
                    ai_reply = clean_text(response.choices[0].message.content.strip())

                except Exception as e:
                    return Response(
                        {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                audio_id = uuid.uuid4().hex
                user_audio = f"media/audio/user_{audio_id}.mp3"
                ai_audio = f"media/audio/ai_{audio_id}.mp3"

                try:
                    generate_elevenlabs_audio(user_text, user_voice_id, user_audio)
                    generate_elevenlabs_audio(ai_reply, ai_voice_id, ai_audio)
                except Exception:
                    from gtts import gTTS

                    gTTS(user_text).save(user_audio)
                    gTTS(ai_reply).save(ai_audio)

                gen_user = GeneratedAudio.objects.create(
                    text=user_text,
                    audio=user_audio.split("media/")[1],
                    sender_type=SenderTypeChoices.USER,
                    conversation_id=convo_id,
                    user=user,
                )
                gen_ai = GeneratedAudio.objects.create(
                    text=ai_reply,
                    audio=ai_audio.split("media/")[1],
                    sender_type=SenderTypeChoices.AI,
                    conversation_id=convo_id,
                    user=user,
                )

                validated_data.pop("text")

                return Response(
                    {
                        "reply": ai_reply,
                        # "reply_as": reply_as,
                        "user_audio": user_audio.split("media/")[1],
                        "ai_audio": ai_audio.split("media/")[1],
                        "conversation_id": convo_id,
                        # "user_audio_response": GeneratedAudioSerializer(gen_user).data,
                        # "ai_audio_response": GeneratedAudioSerializer(gen_ai).data
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                reply_text = request.data.get("reply_text", None)
                if not reply_text:
                    raise serializers.ValidationError("User must provide a reply text")
                ai_reply = clean_text(reply_text)

                audio_id = uuid.uuid4().hex
                if sender_type == SenderTypeChoices.USER:
                    user_audio = f"media/audio/user_{audio_id}.mp3"
                    # ai_audio = f"media/audio/ai_{audio_id}.mp3"

                    try:
                        generate_elevenlabs_audio(user_text, user_voice_id, user_audio)
                        # generate_elevenlabs_audio(ai_reply, ai_voice_id, ai_audio)
                    except Exception:
                        from gtts import gTTS

                        gTTS(user_text).save(user_audio)
                        # gTTS(ai_reply).save(ai_audio)

                    gen_user = GeneratedAudio.objects.create(
                        text=user_text,
                        audio=user_audio.split("media/")[1],
                        sender_type=SenderTypeChoices.USER,
                        conversation_id=convo_id,
                        user=user,
                    )
                    # gen_ai = GeneratedAudio.objects.create(
                    #     text=ai_reply,
                    #     audio=ai_audio.split("media/")[1],
                    #     sender_type=SenderTypeChoices.AI,
                    #     conversation_id=convo_id,
                    #     user=user,
                    # )

                    validated_data.pop("text")

                    return Response(
                        {
                            "reply": ai_reply,
                            # "reply_as": reply_as,
                            "user_audio": user_audio.split("media/")[1],
                            # "ai_audio": ai_audio.split("media/")[1],
                            "conversation_id": convo_id,
                            # "user_audio_response": GeneratedAudioSerializer(gen_user).data,
                            # "ai_audio_response": GeneratedAudioSerializer(gen_ai).data
                        },
                        status=status.HTTP_201_CREATED,
                    )

                elif sender_type == SenderTypeChoices.AI:
                    # user_audio = f"media/audio/user_{audio_id}.mp3"
                    ai_audio = f"media/audio/ai_{audio_id}.mp3"

                    try:
                        # generate_elevenlabs_audio(user_text, user_voice_id, user_audio)
                        generate_elevenlabs_audio(ai_reply, ai_voice_id, ai_audio)
                    except Exception:
                        from gtts import gTTS

                        # gTTS(user_text).save(user_audio)
                        gTTS(ai_reply).save(ai_audio)

                    # gen_user = GeneratedAudio.objects.create(
                    #     text=user_text,
                    #     audio=user_audio.split("media/")[1],
                    #     sender_type=SenderTypeChoices.USER,
                    #     conversation_id=convo_id,
                    #     user=user,
                    # )
                    gen_ai = GeneratedAudio.objects.create(
                        text=ai_reply,
                        audio=ai_audio.split("media/")[1],
                        sender_type=SenderTypeChoices.AI,
                        conversation_id=convo_id,
                        user=user,
                    )

                    validated_data.pop("text")

                    return Response(
                        {
                            "reply": ai_reply,
                            # "reply_as": reply_as,
                            # "user_audio": user_audio.split("media/")[1],
                            "ai_audio": ai_audio.split("media/")[1],
                            "conversation_id": convo_id,
                            # "user_audio_response": GeneratedAudioSerializer(gen_user).data,
                            # "ai_audio_response": GeneratedAudioSerializer(gen_ai).data
                        },
                        status=status.HTTP_201_CREATED,
                    )

            # audio_id = uuid.uuid4().hex
            # user_audio = f"media/audio/user_{audio_id}.mp3"
            # ai_audio = f"media/audio/ai_{audio_id}.mp3"

            # try:
            #     generate_elevenlabs_audio(user_text, user_voice_id, user_audio)
            #     generate_elevenlabs_audio(ai_reply, ai_voice_id, ai_audio)
            # except Exception:
            #     from gtts import gTTS

            #     gTTS(user_text).save(user_audio)
            #     gTTS(ai_reply).save(ai_audio)

            # gen_user = GeneratedAudio.objects.create(
            #     text=user_text,
            #     audio=user_audio.split("media/")[1],
            #     sender_type=SenderTypeChoices.USER,
            #     conversation_id=convo_id,
            #     user=user,
            # )
            # gen_ai = GeneratedAudio.objects.create(
            #     text=ai_reply,
            #     audio=ai_audio.split("media/")[1],
            #     sender_type=SenderTypeChoices.AI,
            #     conversation_id=convo_id,
            #     user=user,
            # )

            # validated_data.pop("text")

            # return Response(
            #     {
            #         "reply": ai_reply,
            #         # "reply_as": reply_as,
            #         "user_audio": user_audio.split("media/")[1],
            #         "ai_audio": ai_audio.split("media/")[1],
            #         "conversation_id": convo_id,
            #         # "user_audio_response": GeneratedAudioSerializer(gen_user).data,
            #         # "ai_audio_response": GeneratedAudioSerializer(gen_ai).data
            #     },
            #     status=status.HTTP_201_CREATED,
            # )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveDestroyGenericAudioAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = GeneratedAudioSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"

    def get_object(self):
        return GeneratedAudio.objects.IS_ACTIVE().get(uid=self.kwargs["uid"])

    def perform_destroy(self, instance):
        instance.status = StatusChoices.REMOVED
        instance.save()


class ListCreateAvatarAPIView(generics.ListCreateAPIView):
    # queryset = Avatar.objects.IS_ACTIVE()
    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Avatar.objects.IS_ACTIVE()
            .filter(Q(user=self.request.user) | Q(user__isnull=True))
            .order_by("id")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # @method_decorator(cache_page(60 * 15, key_prefix="avatar_list_cache"))
    # def list(self, request, *args, **kwargs):
    #     return super().list(request, *args, **kwargs)


class RetrieveUpdatedDestroyAvatarAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AvatarSerializer
    lookup_field = "uid"
    permission_classes = [IsAuthenticated]

    def get_object(self):
        avatar = Avatar.objects.get(
            user=self.request.user,
            uid=self.kwargs["uid"],
            status__in=[StatusChoices.ACTIVE, StatusChoices.INACTIVE],
        )
        return avatar

    # @method_decorator(cache_page(60 * 15, key_prefix="avatar_list_cache"))
    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.status = StatusChoices.REMOVED
        instance.save()


class ListCreateChatHistorySerializer(generics.ListCreateAPIView):
    # queryset = ChatHistory.objects.IS_ACTIVE()
    serializer_class = ChatHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            ChatHistory.objects.IS_ACTIVE()
            .filter(user=self.request.user)
            .order_by("id")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetrieveUpdatedDestroyChatHistoryAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatHistorySerializer
    lookup_field = "uid"
    permission_classes = [IsAuthenticated]
    # queryset = ChatHistory.objects.filter(status__in=[StatusChoices.ACTIVE, StatusChoices.INACTIVE])

    # @method_decorator(cache_page(60 * 2, key_prefix="chatHistory_list_cache"))
    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # chat_history = self.get_object()
        chat_history = ChatHistory.objects.IS_ACTIVE().get(
            uid=self.kwargs["uid"], user=self.request.user
        )

        chat_dict = []
        audio_dict = []

        chats = GeneratedAudio.objects.filter(
            conversation_id=chat_history.conversation_id,
            status=StatusChoices.ACTIVE,
            user=self.request.user,
        )

        for chat in chats:
            chat_dict.append({chat.sender_type.lower(): chat.text})
            audio_dict.append(
                {chat.sender_type.lower(): chat.audio.url.split("/media/")[1]}
            )

        return Response(
            {
                "chat_history": self.get_serializer(chat_history).data,
                "title": chat_history.title,
                "conversation_id": chat_history.conversation_id,
                "chat_dict": chat_dict,
                "audio_dict": audio_dict,
            },
            status=status.HTTP_200_OK,
        )

    def perform_destroy(self, instance):
        instance.status = StatusChoices.REMOVED
        instance.save()

        GeneratedAudio.objects.filter(conversation_id=instance.conversation_id).update(
            status=StatusChoices.REMOVED
        )


class ReplayDialogeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        if not conversation_id:
            return Response(
                {"error": "conversation_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch all chats and audios for this conversation
        generated_audios = GeneratedAudio.objects.filter(
            conversation_id=conversation_id,
            status=StatusChoices.ACTIVE,
            user=self.request.user,
        )

        if not generated_audios.exists():
            return Response(
                {"error": "No data found for this conversation id or User."},
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_list = []
        audio_list = []

        for item in generated_audios:
            chat_list.append({item.sender_type.lower(): item.text})
            audio_list.append(
                {item.sender_type.lower(): item.audio.url.split("/media/")[1]}
            )

        return Response(
            {
                "conversation_id": conversation_id,
                "chat_list": chat_list,
                "audio_list": audio_list,
            },
            status=status.HTTP_200_OK,
        )


class AnalyzeTextView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text")
        if not text:
            return Response(
                {"error": "text is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        # prompt = f"Analyze the following conversation and give a short summary or insight in 4-5 sentences:\n\nText: {text}"
        prompt = (
            f"Analyze the emotional tone and mood of the following text or conversation. "
            f"Describe how the speaker(s) might be feeling, and provide a short summary of the overall emotional context "
            f"in 2-3 sentences:\n\nText: {text}"
        )
        try:
            # model = genai.GenerativeModel("gemini-2.0-flash")
            # response = model.generate_content(prompt)

            # # Ensure the response is in the expected format
            # if response and response.candidates:
            #     candidates = response.candidates
            #     # Extract the analysis text from the response
            #     analysis = candidates[0].content.parts[0].text.strip()
            #     if analysis:
            #         summary = clean_text(analysis)
            #         return Response({"summary": summary}, status=status.HTTP_200_OK)

            response = client.chat.completions.create(
                model="gpt-4o",  # or "gpt-4" if needed
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes content.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            analysis = response.choices[0].message.content.strip()
            if analysis:
                summary = clean_text(analysis)
                return Response({"summary": summary}, status=status.HTTP_200_OK)

            return Response(
                {
                    "error": "Unable to generate a valid emotion analysis. Please try again."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception:
            return Response(
                {"error": "Failed to analyze the text."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListCreateMoodAPIView(generics.ListCreateAPIView):
    # queryset = Mood.objects.IS_ACTIVE()
    serializer_class = MoodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Mood.objects.IS_ACTIVE()
            .filter(Q(user=self.request.user) | Q(user__isnull=True))
            .order_by("id")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # @method_decorator(cache_page(60 * 15, key_prefix="mood_list_cache"))
    # def list(self, request, *args, **kwargs):
    #     return super().list(request, *args, **kwargs)


class RetrieveUpdateDestroyMoodAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MoodSerializer
    lookup_field = "uid"
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Mood.objects.get(
            user=self.request.user,
            uid=self.kwargs["uid"],
            status__in=[StatusChoices.ACTIVE, StatusChoices.INACTIVE],
        )

    # @method_decorator(cache_page(60 * 15, key_prefix="mood_list_cache"))
    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)
