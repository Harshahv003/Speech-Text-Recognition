import streamlit as st
import moviepy.editor as mp
import tempfile
import io
import requests
import json
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from google.oauth2 import service_account

# Load Google Cloud credentials
# Replace 'path/to/your/service_account.json' with your actual path
credentials = service_account.Credentials.from_service_account_file('path/to/your/service_account.json')

def transcribe_audio(video_file):
    """Transcribe audio from the video file using Google Speech-to-Text API."""
    # Load the video file and extract audio
    video_clip = mp.VideoFileClip(video_file.name)
    audio_clip = video_clip.audio
    with tempfile.NamedTemporaryFile(delete=True) as temp_audio_file:
        audio_filename = f"{temp_audio_file.name}.wav"
        audio_clip.write_audiofile(audio_filename, codec='pcm_s16le')
    
    # Initialize the Speech client
    client = speech.SpeechClient(credentials=credentials)
    
    # Configure audio and recognition parameters
    with open(audio_filename, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    
    # Transcribe the audio
    response = client.recognize(config=config, audio=audio)
    transcript = " ".join([result.alternatives[0].transcript for result in response.results])
    return transcript

def generate_speech(text):
    """Generate speech from text using Google Text-to-Speech API."""
    client = texttospeech.TextToSpeechClient(credentials=credentials)
    
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config,
    )

    # Save the generated audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=True) as temp_audio_file:
        temp_audio_file.write(response.audio_content)
        temp_audio_file.flush()
        return temp_audio_file.name

def main():
    st.title("🎤 Video Audio Processing App")
    st.markdown("""
        This app allows you to upload a video file, transcribe its audio to text, and convert that text back to speech.
    """)

    video_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])

    if video_file is not None:
        st.video(video_file)  # Display the uploaded video
        with st.spinner("Transcribing audio..."):
            transcript = transcribe_audio(video_file)
            st.success("Transcription complete!")
            st.text_area("Transcription Output:", transcript, height=200)

        # Convert transcript to speech
        if st.button("Convert Text to Speech"):
            audio_filename = generate_speech(transcript)
            st.audio(audio_filename, format="audio/mp3")
            st.success("Text-to-Speech conversion complete!")

if __name__ == "__main__":
    main()


