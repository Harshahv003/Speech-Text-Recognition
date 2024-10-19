import streamlit as st
import moviepy.editor as mp
import tempfile
import io
import requests
import json
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech

# Azure OpenAI connection details
AZURE_OPENAI_KEY = "22ec84421ec24230a3638d1b51e3a7dc"  # Your Azure OpenAI key
AZURE_OPENAI_ENDPOINT = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

# Function to correct text using Azure OpenAI
def correct_text_with_azure(transcription):
    """Send transcription to Azure OpenAI GPT-4o for correction."""
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    
    data = {
        "messages": [
            {"role": "user", "content": f"Correct the following text: {transcription}"}
        ],
        "max_tokens": 100  # Adjust as needed
    }

    response = requests.post(AZURE_OPENAI_ENDPOINT, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    else:
        st.error(f"Error correcting text: {response.status_code} - {response.text}")
        return transcription  # Return original transcription in case of error

def main():
    # Custom CSS for background color
    st.markdown("""
        <style>
        .reportview-container {
            background-color: #f0f2f5;  /* Light gray background */
        }
        .sidebar .sidebar-content {
            background-color: #ffffff;  /* White sidebar background */
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("🎤 Video Audio Processing App")

    # Streamlit file uploader
    video_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])

    if video_file is not None:
        # Create a temporary file to store the uploaded video content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_file.read())
            temp_filename = temp_file.name

        # Load the video from the temporary file using MoviePy
        video_clip = mp.VideoFileClip(temp_filename)

        # Check if the video has audio
        if video_clip.audio is None:
            st.error("No audio found in the uploaded video.")
        else:
            # Extract audio from video and save it temporarily
            audio_filename = temp_filename.replace('.mp4', '.wav')
            video_clip.audio.write_audiofile(audio_filename, codec='pcm_s16le')

            # Speech-to-Text
            st.write("Transcribing audio...")
            client = speech.SpeechClient()

            with io.open(audio_filename, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
            )

            response = client.recognize(config=config, audio=audio)

            # Collect the transcriptions
            transcriptions = []
            for result in response.results:
                transcriptions.append(result.alternatives[0].transcript)

            # Join the transcriptions
            full_transcription = " ".join(transcriptions)
            st.write("Transcription:")
            st.write(full_transcription)

            # Correct the transcription using Azure OpenAI
            corrected_transcription = correct_text_with_azure(full_transcription)
            st.write("Corrected Transcription:")
            st.write(corrected_transcription)

            # Text-to-Speech
            st.write("Generating audio from text...")
            tts_client = texttospeech.TextToSpeechClient()

            input_text = st.text_area("Enter text to convert to speech:", value=corrected_transcription)

            if st.button("Convert Text to Speech"):
                synthesis_input = texttospeech.SynthesisInput(text=input_text)

                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
                )

                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                )

                response = tts_client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )

                # Save the generated audio to a file
                output_audio_filename = "output_audio.mp3"
                with open(output_audio_filename, "wb") as out:
                    out.write(response.audio_content)

                # Provide a link to download the audio file
                st.success("Audio generated successfully!")
                st.audio(output_audio_filename)  # Stream the audio file in the app

if __name__ == "__main__":
    main()


