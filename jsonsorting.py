import json
import sclib
import librosa
import requests
import io
from collections import defaultdict
import time


def sort_songs_by_genre(songs):
    """
    Sort songs by genre.

    Args:
        songs (list): List of songs.

    Returns:
        dict: Songs sorted by genre.
    """
    sorted_songs = defaultdict(list)
    for song in songs:
        genre = song.get("genre", "Unknown")
        sorted_songs[genre].append(song)
    return sorted_songs


def get_stream_url(track_url, api):
    """
    Resolve a track URL to get a fresh stream URL.

    Args:
        track_url (str): Permanent track URL.

    Returns:
        str: Fresh stream URL or None if resolution fails.
    """
    try:
        track = api.resolve(track_url)
        return track.get_stream_url()
    except Exception as e:
        print(f"Failed to resolve track URL {track_url}: {e}")
        return None


def analyze_song(stream_url):
    """
    Analyze a song using librosa to extract BPM and key.

    Args:
        stream_url (str): Stream URL of the song.

    Returns:
        tuple: (BPM, Key) or (None, None) on failure.
    """
    try:
        # Fetch the audio data
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(stream_url, headers=headers, stream=True)

        if response.status_code != 200:
            print(f"Failed to fetch audio from {stream_url}. Status Code: {response.status_code}")
            return None, None

        # Load the audio into librosa
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

        return float(tempo), key  # Ensure BPM is a float and key is a string
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return None, None


def process_songs(input_file, output_file):
    """
    Sort songs by genre, analyze each song for BPM and key, and save the updated data.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output JSON file.
    """
    api = sclib.SoundcloudAPI()

    # Load songs from the input JSON file
    try:
        with open(input_file, "r") as f:
            songs = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_file}.")
        return

    # Sort songs by genre
    sorted_songs = sort_songs_by_genre(songs)

    # Analyze each song
    for genre, genre_songs in sorted_songs.items():
        print(f"\nProcessing genre: {genre} with {len(genre_songs)} songs.")

        for song in genre_songs:
            track_url = song.get("track_url")
            if not track_url:
                print(f"Skipping song '{song.get('title', 'Unknown')}' (no track URL).")
                continue

            print(f"  Analyzing: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}")

            # Get a fresh stream URL
            stream_url = get_stream_url(track_url, api)
            if not stream_url:
                print(f"  Skipping song: Unable to resolve stream URL.")
                continue

            # Analyze the song
            bpm, key = analyze_song(stream_url)
            if bpm and key:
                song["bpm"] = bpm  # Store BPM as a float
                song["key"] = key  # Store key as a string
                print(f"    Extracted BPM: {bpm}, Key: {key}")
            else:
                print(f"    Failed to analyze the song.")

            # Save progress incrementally
            with open(output_file, "w") as f:
                json.dump(songs, f, indent=4)
            print(f"    Progress saved to {output_file}.")

            # Add a small delay to avoid overwhelming the system or API
            time.sleep(1)


def clean_analyzed_songs(input_file, output_file):
    """
    Remove songs without BPM or key from the analyzed songs JSON file.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to save the cleaned JSON file.
    """
    try:
        # Load the JSON file
        with open(input_file, "r") as f:
            songs = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_file}.")
        return

    # Filter songs with both BPM and key
    cleaned_songs = [song for song in songs if "bpm" in song and "key" in song]

    # Save the cleaned data
    try:
        with open(output_file, "w") as f:
            json.dump(cleaned_songs, f, indent=4)
        print(f"Cleaned data saved to {output_file}. Removed {len(songs) - len(cleaned_songs)} incomplete songs.")
    except Exception as e:
        print(f"Error saving cleaned JSON file: {e}")


if __name__ == "__main__":
    # Input and output file paths
    input_file = "analyzed_songs.json"  # Replace with your input JSON file
    output_file = "cleaned_songs.json"  # Replace with your desired output file

    # Clean the analyzed songs
    clean_analyzed_songs(input_file, output_file)

