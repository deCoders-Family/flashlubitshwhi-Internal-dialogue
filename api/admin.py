from django.contrib import admin

from .models import GeneratedAudio, ChatHistory, Avatar, Mood

# Register your models here.


@admin.register(GeneratedAudio)
class GeneratedAudioAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = [
        "id",
        "uid",
        "conversation_id",
        "short_text",
        "audio",
        "audio_length",
        "sender_type",
        "created_at",
        "updated_at",
        "status",
    ]

    def short_text(self, obj):
        return (obj.text[:30] + "...") if len(obj.text) > 30 else obj.text

    short_text.short_description = "Text Preview"


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = [
        "id",
        "uid",
        "title",
        "conversation_id",
        "short_chat",
        "created_at",
        "updated_at",
        "status",
    ]

    def short_chat(self, obj):
        return (obj.chat[:30] + "...") if len(obj.chat) > 30 else obj.chat

    short_chat.short_description = "Chat Preview"


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = [
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

@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    ordering = ["id"]
    list_display = [
        "id",
        "uid",
        "mood_name",
        "mood_prompt",
        "created_at",
        "updated_at",
        "status",
    ]
