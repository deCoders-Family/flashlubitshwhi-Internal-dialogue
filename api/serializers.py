from django.contrib.auth.models import User

import json
from rest_framework import serializers
from .models import GeneratedAudio, ChatHistory, Avatar



# class UserSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'email')


class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)


class GeneratedAudioSerializer(serializers.ModelSerializer):
    # text = serializers.CharField(write_only=True)
    # reply_text = serializers.CharField(write_only=True)
    user_voice_name = serializers.CharField(write_only=True)
    ai_voice_name = serializers.CharField(write_only=True)
    reply_as = serializers.CharField(write_only=True)

    class Meta:
        model = GeneratedAudio
        fields = [
            "id",
            "uid",
            "text",
            # "reply_text",
            "user_voice_name",
            "ai_voice_name",
            "reply_as",
            "audio",
            "audio_length",
            "sender_type",
            "created_at",
            "updated_at",
            "status",
        ]
        read_only_fields = [
            "id",
            "uid",
            "audio",
            "audio_length",
            "created_at",
            "updated_at",
        ]


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = [
            "id",
            "uid",
            "title",
            "conversation_id",
            "chat",
            "created_at",
            "updated_at",
            "status",
        ]

        read_only_fields = [
            "id",
            "uid",
            "chat",
            "created_at",
            "updated_at",
        ]

    # def validate_chat(self, value):
    #     """
    #     Validate that the 'chat' field contains valid JSON in the format:
    #     {"user": "message", "ai": "reply"} where keys are 'user' or 'ai' and values are strings.
    #     """
    #     try:
    #         # Parse the TextField content as JSON
    #         chat_data = json.loads(value)
    #     except json.JSONDecodeError:
    #         raise serializers.ValidationError("The 'chat' field must be valid JSON.")

    #     # Check if the parsed data is a dictionary
    #     if not isinstance(chat_data, dict):
    #         raise serializers.ValidationError("The 'chat' field must be a JSON object.")

    #     # Validate keys and values
    #     valid_keys = {"user", "ai"}
    #     for key, val in chat_data.items():
    #         # Check if key is valid
    #         if key not in valid_keys:
    #             raise serializers.ValidationError(
    #                 f"Invalid key '{key}' in 'chat'. Allowed keys are 'user' and 'ai'."
    #             )
    #         # Check if value is a string
    #         if not isinstance(val, str):
    #             raise serializers.ValidationError(
    #                 f"Value for '{key}' must be a string, got {type(val).__name__}."
    #             )

    #     return value

    def create(self, validated_data):
        convo_id = validated_data.get("conversation_id")
        gen_audios = GeneratedAudio.objects.IS_ACTIVE().filter(conversation_id=convo_id)
        # chat=""
        # for gen_audio in gen_audios:
        #     sender_type = gen_audio.sender_type
        #     chat_prefix = ""
        #     if sender_type == "USER":
        #         chat_prefix = "user:"
        #     else:
        #         chat_prefix = "ai:"
        #     chat = chat + (f"{chat_prefix}"+f"{gen_audio.text}"+", ")

        # return ChatHistory.objects.create(chat=chat, **validated_data)

        chat_data = []
        for gen_audio in gen_audios:
            sender_type = gen_audio.sender_type
            if sender_type == "USER":
                chat_data.append({"user": gen_audio.text})
            else:
                chat_data.append({"ai": gen_audio.text})

        chat_str = json.dumps(chat_data, ensure_ascii=False)
        return ChatHistory.objects.create(chat=chat_str, **validated_data)


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = [
            "id",
            "uid",
            "side",
            "avatar_name",
            "voice_name",
            "elevenlabs_voice_id",
            "video",
            "created_at",
            "updated_at",
            "status",
        ]
        read_only_fields = [
            "id",
            "uid",
            "created_at",
            "updated_at",
        ]
