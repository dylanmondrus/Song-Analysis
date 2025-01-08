from sclib import SoundcloudAPI
import requests
import librosa
import numpy as np
import io
import matplotlib.pyplot as plt
import time


# Initialize the SoundCloud API
api = SoundcloudAPI()

# Search for a song by URL
track_url = "https://soundcloud.com/meme_suprememe/lost-forever"
track = api.resolve(track_url)

# Print song details
print(f"Title: {track.title}")
print(f"Duration: {track.duration} ms")
print(f"Genre: {track.genre}")
print(f"Playback Count: {track.playback_count}")
print(f"Stream URL: {track.get_stream_url()}")





# Stream the audio data from the URL
stream_url = track.get_stream_url() # Replace with actual stream URL
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(stream_url, headers=headers, stream=True)

# Load the audio directly from the stream
y, sr = librosa.load(io.BytesIO(response.content), sr=None)

# Analyze the audio
tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
print(f"Estimated BPM: {tempo}")
print(f"Duration: {librosa.get_duration(y=y, sr=sr)} seconds")

# Waveform visualization
plt.figure(figsize=(10, 4))
librosa.display.waveshow(y, sr=sr)
plt.title("Waveform")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.show()


