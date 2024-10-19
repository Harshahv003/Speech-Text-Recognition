import streamlit as st
import moviepy.editor as mp
import tempfile
import io
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech

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

        # Text-to-Speech
        st.write("Generating audio from text...")
        tts_client = texttospeech.TextToSpeechClient()

        input_text = st.text_area("Enter text to convert to speech:", value=full_transcription)

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
