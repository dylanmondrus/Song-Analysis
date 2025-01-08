from sclib import SoundcloudAPI
import requests
import librosa
import io


def test_soundcloud_url(track_url):
    """
    Test a SoundCloud track URL by resolving it and validating the streaming URL.
    """
    api = SoundcloudAPI()
    try:
        # Resolve the track
        track = api.resolve(track_url)
        print(f"Resolved Track: {track.title} by {track.user['username']}")
        print(f"Duration: {track.duration} ms")
        print(f"Genre: {track.genre}")

        # Get the streaming URL
        stream_url = track.get_stream_url()
        print(f"Stream URL: {stream_url}")

        # Validate the streaming URL
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(stream_url, headers=headers)

        if response.status_code == 200:
            print("Stream URL is valid and accessible.")
            return stream_url
        else:
            print(f"Stream URL is not accessible. Status Code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Failed to resolve or validate the track URL: {e}")
        return None


def analyze_song_bpm_and_key(stream_url):
    """
    Analyze a song's audio to extract BPM and key.

    Args:
        stream_url (str): The streaming URL of the song.

    Returns:
        tuple: (BPM, Key) if successful, or (None, None) on failure.
    """
    try:
        # Fetch the audio data
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(stream_url, headers=headers, stream=True)

        if response.status_code != 200:
            print(f"Failed to fetch audio from {stream_url}. Status Code: {response.status_code}")
            return None, None

        # Load the audio data into librosa
        y, sr = librosa.load(io.BytesIO(response.content), sr=None)

        # Analyze BPM (tempo)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        # Analyze key using chroma features
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_index = chroma.mean(axis=1).argmax()

        # Map the key index to musical notes
        key_mapping = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]
        key = key_mapping[key_index]

        return tempo, key
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return None, None


if __name__ == "__main__":
    # Test SoundCloud URL
    track_url = "https://soundcloud.com/meme_suprememe/lost-forever"  # Replace with a valid SoundCloud track URL
    stream_url = test_soundcloud_url(track_url)

    if stream_url:
        # Analyze the song if the streaming URL is valid
        bpm, key = analyze_song_bpm_and_key(stream_url)

        if bpm and key:
            print(f"Estimated BPM: {bpm}")
            print(f"Estimated Key: {key}")
        else:
            print("Failed to analyze the song.")
