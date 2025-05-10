from django.db import models

import uuid

from .choices import StatusChoices, SenderTypeChoices
from .managers import (
    AvatarManager,
    ChatHistoryManager,
    GeneratedAudioManager,
    MoodManager,
)
from .utils import avatar_video_upload_path
# Create your models here.


class GeneratedAudio(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    conversation_id = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    audio = models.FileField(upload_to="audio/")
    sender_type = models.CharField(max_length=10, choices=SenderTypeChoices)
    status = models.CharField(
        max_length=10, choices=StatusChoices, default=StatusChoices.ACTIVE
    )

    objects = GeneratedAudioManager()

    def __str__(self):
        audio_str = str(self.audio)
        audio_file_name = audio_str.split("/")[1].strip()
        audio_title = audio_file_name.split(".")[0].strip()

        return audio_title

    @property
    def audio_length(self) -> float:
        from mutagen.mp3 import MP3

        try:
            audio = MP3("media/" + str(self.audio))
            return f"{round(audio.info.length, 2)} seconds"
        except Exception:
            return -1


class ChatHistory(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    conversation_id = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, unique=True)
    chat = (
        models.TextField()
    )  # NOTE: should be a json with key value pair of sender type and message
    # sender_type = models.CharField(max_length=10, choices=SenderTypeChoices)
    status = models.CharField(
        max_length=10, choices=StatusChoices, default=StatusChoices.ACTIVE
    )

    objects = ChatHistoryManager()

    def __str__(self):
        return self.title


class Avatar(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    side = models.CharField(max_length=10, choices=SenderTypeChoices)
    avatar_name = models.CharField(max_length=255)
    voice_name = models.CharField(max_length=255)
    elevenlabs_voice_id = models.CharField(max_length=100)
    video = models.FileField(upload_to=avatar_video_upload_path)
    status = models.CharField(
        max_length=10, choices=StatusChoices, default=StatusChoices.ACTIVE
    )

    objects = AvatarManager()

    def __str__(self):
        return f"Avatar: {self.avatar_name} - Voice: {self.voice_name}"


class Mood(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mood_name = models.CharField(max_length=255)
    mood_prompt = models.TextField()
    status = models.CharField(
        max_length=10, choices=StatusChoices, default=StatusChoices.ACTIVE
    )
    
    objects = MoodManager()
    
    def save(self, *args, **kwargs):
        self.mood_name = self.mood_name.lower()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.mood_name
