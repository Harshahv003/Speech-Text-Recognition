import streamlit as st
import requests
import moviepy.editor as mp
import os

# Set the environment variables for Azure OpenAI
API_KEY = "22ec84421ec24230a3638d1b51e3a7dc"
ENDPOINT = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

# Function to extract audio from video
def extract_audio_from_video(video_file):
    # Save the uploaded video to a temporary file
    video_file_path = "temp_video.mp4"
    with open(video_file_path, "wb") as f:
        f.write(video_file.getbuffer())

    # Extract audio using moviepy
    video = mp.VideoFileClip(video_file_path)
    audio_file_path = "extracted_audio.wav"
    video.audio.write_audiofile(audio_file_path)
    return audio_file_path

# Function to transcribe audio using Azure OpenAI
import base64

import requests
import base64

def transcribe_audio(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        audio_data = audio_file.read()

    # Encode audio data to base64
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "gpt-4o",  # Specify the model if required
        "messages": [
            {"role": "user", "content": "Please transcribe this audio."}
        ],
        "audio": audio_base64  # Send the base64 encoded audio
    }

    response = requests.post(ENDPOINT, headers=headers, json=data)
    
    # Debugging: Print the raw response for troubleshooting
    print("Response status code:", response.status_code)
    print("Response content:", response.content)

    if response.status_code == 200:
        try:
            json_response = response.json()
            if "choices" in json_response and len(json_response["choices"]) > 0:
                return json_response["choices"][0]["message"]["content"]
            else:
                print("Unexpected response structure from the API.")
                return "Error in transcription."
        except Exception as e:
            print(f"Error parsing response: {e}")
            return "Error in transcription."
    else:
        print(f"API request failed with status {response.status_code}: {response.text}")
        return "Error in transcription."


# Streamlit UI
def main():
    st.title("Video to Text Transcription")
    
    video_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
    
    if video_file is not None:
        # Step 1: Extract audio from video
        audio_file_path = extract_audio_from_video(video_file)
        st.success("Audio extracted successfully.")

        # Step 2: Transcribe the extracted audio
        transcription = transcribe_audio(audio_file_path)
        
        # Display transcription
        st.subheader("Transcription:")
        st.write(transcription)
        
        # Clean up temporary files
        os.remove(audio_file_path)
        os.remove("temp_video.mp4")

if __name__ == "__main__":
    main()
