
import os
import wave
import io

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()

router = APIRouter(prefix="/api/voice", tags=["METHU Voice"])


class VoiceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)


@router.post("/speak")
def speak(request: VoiceRequest):
    try:
        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

        result = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=(
                "Speak the following text naturally. "
                "Use a warm, friendly Sri Lankan female voice. "
                "Speak Sinhala clearly. Do not add any words.\n\n"
                + request.text
            ),
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore"
                        )
                    )
                ),
            ),
        )

        pcm = result.candidates[0].content.parts[0].inline_data.data

        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(pcm)

        return Response(
            content=buffer.getvalue(),
            media_type="audio/wav"
        )

    except Exception as error:
        print("METHU Voice Error:", error)
        raise HTTPException(
            status_code=502,
            detail="Voice generation failed"
        )
