import json
import librosa
import numpy as np
import requests
import io
import time
from sclib import SoundcloudAPI


def extract_energy_by_section(y, sr, segment_times, frame_length=2048, hop_length=512):
    """
    Extract the average energy of each section.

    Args:
        y (np.ndarray): Audio time-series.
        sr (int): Sample rate.
        segment_times (list): List of section start times in seconds.
        frame_length (int): Frame length for RMS calculation.
        hop_length (int): Hop length for RMS calculation.

    Returns:
        list: List of tuples (section_start_time, average_energy).
    """
    # Calculate RMS energy for all frames
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

    # Map frame indices to time
    frame_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)

    # Calculate average energy for each section
    energy_by_section = []
    for i, start_time in enumerate(segment_times):
        # Determine the end of the section
        end_time = segment_times[i + 1] if i < len(segment_times) - 1 else frame_times[-1]

        # Get RMS values for frames within this section
        section_indices = (frame_times >= start_time) & (frame_times < end_time)
        section_energy = rms[section_indices]

        # Compute average energy for the section
        average_energy = float(np.mean(section_energy)) if len(section_energy) > 0 else 0.0
        energy_by_section.append((float(start_time), average_energy))

    return energy_by_section



def extract_rhythm(y, sr):
    """
    Extract rhythm features such as tempo and beat positions.

    Args:
        y (np.ndarray): Audio time-series.
        sr (int): Sample rate.

    Returns:
        dict: Tempo and beat times.
    """
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    return {
        "tempo": float(tempo),  # Convert to native Python float
        "beat_times": beat_times.tolist()
    }


def extract_structure(y, sr, num_sections=4):
    """
    Analyze the structure of a song, identifying sections and bars.

    Args:
        y (np.ndarray): Audio time-series.
        sr (int): Sample rate.
        num_sections (int): Number of desired sections.

    Returns:
        dict: Section times and bar positions.
    """
    # Estimate structural boundaries using spectral features
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    boundaries = librosa.segment.agglomerative(mfcc.T, k=num_sections)
    segment_times = librosa.frames_to_time(boundaries, sr=sr)

    # Estimate bar positions
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bar_length = 4  # Assuming 4 beats per bar
    bars = [beat_frames[i:i + bar_length] for i in range(0, len(beat_frames), bar_length)]
    bar_times = [librosa.frames_to_time(bar, sr=sr).tolist() for bar in bars]

    return {
        "sections": segment_times.tolist(),  # Convert NumPy array to list
        "bars": bar_times
    }


def analyze_song_deep(y, sr):
    """
    Perform deep analysis on a song, extracting energy, rhythm, and structure.

    Args:
        y (np.ndarray): Audio time-series.
        sr (int): Sample rate.

    Returns:
        dict: Deep analysis data.
    """
    structure = extract_structure(y, sr)
    rhythm = extract_rhythm(y, sr)
    energy = extract_energy_by_section(y, sr, structure["sections"])
    return {
        "energy": energy,
        "rhythm": rhythm,
        "structure": structure
    }


def get_stream_url(track_url):
    """
    Resolve a track URL to get a fresh stream URL.

    Args:
        track_url (str): Permanent track URL.

    Returns:
        str: Fresh stream URL or None if resolution fails.
    """
    api = SoundcloudAPI()
    try:
        track = api.resolve(track_url)
        return track.get_stream_url()
    except Exception as e:
        print(f"Failed to resolve track URL {track_url}: {e}")
        return None


def analyze_songs(input_file, output_file):
    """
    Analyze all songs in the cleaned_songs.json file and add deep analysis data.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to save the updated JSON file.
    """
    try:
        # Load songs from the input JSON file
        with open(input_file, "r") as f:
            songs = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_file}.")
        return

    for idx, song in enumerate(songs):
        print(f"\nProcessing song {idx + 1}/{len(songs)}: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}")
        track_url = song.get("track_url")
        if not track_url:
            print("  Skipping: No track URL available.")
            continue

        # Get fresh stream URL
        stream_url = get_stream_url(track_url)
        if not stream_url:
            print("  Skipping: Unable to resolve stream URL.")
            continue

        try:
            # Fetch audio data from stream URL
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(stream_url, headers=headers, stream=True)
            if response.status_code != 200:
                print(f"  Skipping: Failed to fetch audio. Status Code: {response.status_code}")
                continue

            # Load audio data with librosa
            y, sr = librosa.load(io.BytesIO(response.content), sr=None)

            # Perform deep analysis
            deep_analysis = analyze_song_deep(y, sr)
            song["features"] = deep_analysis
            print("  Analysis complete. Added features.")

        except Exception as e:
            print(f"  Error analyzing song: {e}")
            continue

        # Save progress incrementally
        with open(output_file, "w") as f:
            json.dump(songs, f, indent=4)
        print(f"  Progress saved to {output_file}.")

        # Add a small delay to avoid overwhelming the system
        time.sleep(1)


if __name__ == "__main__":
    input_file = "cleaned_songs.json"
    output_file = "deep_analyzed_songs.json"
    analyze_songs(input_file, output_file)
