import uuid
# from django.shortcuts import render

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


from rest_framework_simplejwt.tokens import RefreshToken

from .choices import SenderTypeChoices, StatusChoices
from .models import Avatar, ChatHistory, GeneratedAudio
from .serializers import (
    AvatarSerializer,
    ChatHistorySerializer,
    GeneratedAudioSerializer,
    LoginUserSerializer,
    UserSerializer,
)
from .utils import clean_text, generate_elevenlabs_audio

import google.generativeai as genai

# Create your views here.


class LoginUserView(generics.GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(username=username, password=password)

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


class RetrieveUpdateMeUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# class GenerateAudioView(APIView):
class GenerateAudioView(generics.GenericAPIView):
    serializer_class = GeneratedAudioSerializer
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GeneratedAudioSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            # data = request.data
            # user_text = data.get("text")
            # mode = data.get("mode", "friendly")
            # convo_id = data.get("conversation_id", str(uuid.uuid4()))
            user_text = validated_data.get("text")
            mode = validated_data.get("mode", "friendly")
            convo_id = request.data.get("conversation_id", str(uuid.uuid4()))
            # user_voice = data.get("user_voice", "Boy 1")
            # ai_voice = data.get("ai_voice", "Girl 1")
            user_voice_name = validated_data.get("user_voice_name")
            ai_voice_name = validated_data.get("ai_voice_name")
            reply_as = validated_data.get("reply_as", "AI")
            user_voice = Avatar.objects.get(
                voice_name=user_voice_name, side=SenderTypeChoices.USER
            )
            ai_voice = Avatar.objects.get(
                voice_name=ai_voice_name, side=SenderTypeChoices.AI
            )

            user_voice_id = user_voice.elevenlabs_voice_id
            ai_voice_id = ai_voice.elevenlabs_voice_id
            prompt = ""
            if mode == "friendly":
                prompt = f"Respond like a friendly person would in a casual conversation. Keep it short and to the point.\nUser: {user_text}\nAI:"
            elif mode == "funny":
                prompt = f"Respond in a funny and lighthearted way. Keep it short and humorous.\nUser: {user_text}\nAI:"
            elif mode == "flirty":
                prompt = f"Respond in a playful, flirty way but keep it respectful. Keep it short and sweet.\nUser: {user_text}\nAI:"
            elif mode == "wise":
                prompt = f"Respond like a wise person with a calm and thoughtful tone. Keep it brief but insightful.\nUser: {user_text}\nAI:"
            elif mode == "formal":
                prompt = f"Respond in a professional and respectful manner. Keep it concise and clear.\nUser: {user_text}\nAI:"
            elif mode == "angry":
                prompt = f"Respond with frustration but be short and direct.\nUser: {user_text}\nAI:"
            elif mode == "sad":
                prompt = f"Respond with a sad or somber tone, but keep it brief and respectful.\nUser: {user_text}\nAI:"

            if reply_as == "AI":
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                ai_reply = clean_text(response.text.strip())
            else:
                # reply_text = validated_data.get("reply_text", None)
                reply_text = request.data.get("reply_text", None)
                if not reply_text:
                    raise serializers.ValidationError("User must provide a reply text")
                ai_reply = clean_text(reply_text)
            audio_id = uuid.uuid4().hex
            user_audio = f"media/audio/user_{audio_id}.mp3"
            ai_audio = f"media/audio/ai_{audio_id}.mp3"
            # print(user_audio.split("media/"))
            try:
                gen_user_audio = generate_elevenlabs_audio(
                    user_text, user_voice_id, user_audio
                )
                gen_ai_audio = generate_elevenlabs_audio(
                    ai_reply, ai_voice_id, ai_audio
                )
                # gen_user = GeneratedAudio.objects.create(audio=gen_user_audio, sender_type=SenderTypeChoices.USER)
                # gen_ai = GeneratedAudio.objects.create(audio=gen_ai_audio, sender_type=SenderTypeChoices.AI)
                # print("Print gen_user and gen_ai", gen_user, gen_ai)
            except:
                from gtts import gTTS

                gen_user_audio = gTTS(user_text).save(user_audio)
                gen_ai_audio = gTTS(ai_reply).save(ai_audio)
                # gen_user = GeneratedAudio.objects.create(audio=gen_user_audio, sender_type=SenderTypeChoices.USER)
                # gen_ai = GeneratedAudio.objects.create(audio=gen_ai_audio, sender_type=SenderTypeChoices.AI)
                # print("Print gen_user and gen_ai", gen_user, gen_ai)

            # gen_user = GeneratedAudio.objects.create(audio=gen_user_audio, sender_type=SenderTypeChoices.USER)
            # gen_ai = GeneratedAudio.objects.create(audio=gen_ai_audio, sender_type=SenderTypeChoices.AI)
            gen_user = GeneratedAudio.objects.create(
                text=user_text,
                audio=user_audio.split("media/")[1],
                sender_type=SenderTypeChoices.USER,
                conversation_id=convo_id,
            )
            gen_ai = GeneratedAudio.objects.create(
                text=ai_reply,
                audio=ai_audio.split("media/")[1],
                sender_type=SenderTypeChoices.AI,
                conversation_id=convo_id,
            )
            validated_data.pop("text")
            # serializer.save()

            return Response(
                {
                    "reply": ai_reply,
                    "user_audio": user_audio.split("media/")[1],
                    "ai_audio": ai_audio.split("media/")[1],
                    "conversation_id": convo_id,
                },
                # serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListCreateAvatarAPIView(generics.ListCreateAPIView):
    queryset = Avatar.objects.IS_ACTIVE()
    serializer_class = AvatarSerializer
    # permission_classes = [IsAuthenticated]


class RetrieveUpdatedDestroyAvatarAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AvatarSerializer
    lookup_field = "uid"
    permission_classes = [IsAuthenticated]

    def get_object(self):
        avatar = Avatar.objects.get(
            uid=self.kwargs["uid"],
            status__in=[StatusChoices.ACTIVE, StatusChoices.INACTIVE],
        )
        return avatar

    def perform_destroy(self, instance):
        instance.status = StatusChoices.REMOVED
        instance.save()


class ListCreateChatHistorySerializer(generics.ListCreateAPIView):
    queryset = ChatHistory.objects.IS_ACTIVE()
    serializer_class = ChatHistorySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class RetrieveUpdatedDestroyChatHistoryAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatHistorySerializer
    lookup_field = "uid"
    permission_classes = [IsAuthenticated]
    # queryset = ChatHistory.objects.filter(status__in=[StatusChoices.ACTIVE, StatusChoices.INACTIVE])

    def retrieve(self, request, *args, **kwargs):
        # chat_history = self.get_object()
        chat_history = ChatHistory.objects.IS_ACTIVE().get(uid=self.kwargs["uid"])

        chat_dict = []
        audio_dict = []

        chats = GeneratedAudio.objects.filter(
            conversation_id=chat_history.conversation_id, status=StatusChoices.ACTIVE
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
        
        GeneratedAudio.objects.filter(conversation_id=instance.conversation_id).update(status=StatusChoices.REMOVED)


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
            status=StatusChoices.ACTIVE
        )

        if not generated_audios.exists():
            return Response(
                {"error": "No data found for this conversation_id."},
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
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            # Debug: Print the full response from Gemini
            # print(f"Full Response from Gemini: {response}")

            # Ensure the response is in the expected format
            if response and response.candidates:
                candidates = response.candidates
                # Extract the analysis text from the response
                analysis = candidates[0].content.parts[0].text.strip()
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
                status=status.HTTP_500_INTERNAL,
            )
