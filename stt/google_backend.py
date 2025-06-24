# stt/google_backend.py
"""
Helper methods for building Google STT config and streaming objects.
"""

from google.cloud import speech

def build_google_config(language="en-US", punctuation=True, model="default"):
    return speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # Mic default; system can override if needed
        language_code=language,
        enable_automatic_punctuation=punctuation,
        model=model
    )

def build_streaming_config(config):
    return speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )
