import os
import json
import re
import time
import uuid

import google.generativeai as genai
import requests
from dotenv import load_dotenv

# from .models import Avatar

load_dotenv()


def avatar_video_upload_path(instance, filename):
    # Determine folder based on side
    folder = "user" if instance.side == "USER" else "ai"
    # Optional: include avatar name or UUID to avoid filename collisions
    return os.path.join(f"video/{folder}", filename)


def generate_elevenlabs_audio(text, voice_id, filename):
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7},
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        with open(filename, "wb") as f:
            f.write(res.content)
    else:
        raise Exception("ElevenLabs error")


def clean_text(text):
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002700-\U000027bf"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub(r"", text)
    return re.sub(r"[^\x00-\x7F]+", "", text)


# def get_voice_id(voice_name):
#     voice_name_from_db = Avatar.objects.filter(voice_name=voice_name).first()
#     voice_id = voice_name_from_db.elevenlabs_voice_id
#     return ""
