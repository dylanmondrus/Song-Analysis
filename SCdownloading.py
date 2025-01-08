import sclib
import json
import os
import boto3
from botocore.exceptions import ClientError


def url_collection(playlist_urls, output_file):
    """
    Collect data from SoundCloud playlists and store permanent track URLs in a JSON file.

    Args:
        playlist_urls (list): List of SoundCloud playlist URLs.
        output_file (str): Path to the output JSON file.
    """
    # Initialize SoundCloud API
    client = sclib.SoundcloudAPI()

    # Ensure the file exists
    if not os.path.exists(output_file):
        with open(output_file, "w") as f:
            json.dump([], f)

    # Load existing data
    with open(output_file, "r") as f:
        all_tracks = json.load(f)

    # Process each playlist URL
    for playlist_index, playlist_url in enumerate(playlist_urls, start=1):
        try:
            playlist = client.resolve(playlist_url)
            print(f"\nProcessing playlist {playlist_index}/{len(playlist_urls)}: {playlist.title} by {playlist.user['username']}")
            print(f"Tracks in playlist: {len(playlist.tracks)}")

            # Collect new track data
            for track_index, track in enumerate(playlist.tracks, start=1):
                print(f"  Processing track {track_index}/{len(playlist.tracks)}: {getattr(track, 'title', 'Unknown')}")

                try:
                    resolved_track = client.resolve(track.permalink_url)
                    track_url = resolved_track.permalink_url
                    new_track = {
                        "title": resolved_track.title,
                        "artist": resolved_track.user["username"],
                        "track_url": track_url,  # Store permanent track URL
                        "duration": resolved_track.duration,
                        "genre": resolved_track.genre,
                    }

                    # Avoid duplicate entries
                    if new_track not in all_tracks:
                        all_tracks.append(new_track)
                        print(f"    Fetched: {resolved_track.title}")
                        print(f"    Track URL: {track_url}")

                except Exception as e:
                    print(f"    Error resolving track {getattr(track, 'title', 'Unknown')}: {e}")

            # Save progress after each playlist
            with open(output_file, "w") as f:
                json.dump(all_tracks, f, indent=4)
            print(f"Progress saved after playlist: {playlist.title}")

        except Exception as e:
            print(f"Error fetching playlist {playlist_url}: {e}")

    print(f"\nFinal database saved to {output_file}")


def upload_to_s3(bucket_name, file_name):
    """
    Upload a file to AWS S3.

    Args:
        bucket_name (str): S3 bucket name.
        file_name (str): Path to the local file.
    """
    # Initialize S3 client with AWS credentials

    # Upload file to S3
    try:
        s3.upload_file(file_name, bucket_name, file_name)
        print(f"{file_name} successfully uploaded to S3 bucket {bucket_name}")
    except ClientError as e:
        print(f"Error uploading to S3: {e}")


if __name__ == "__main__":
    # List of playlist URLs
    playlist_urls = [
        "https://soundcloud.com/electronicfuture/sets/deep-house-chillout-2024",
        "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-new-edm-hits",
        "https://soundcloud.com/luk_music/sets/ibiza-techno-afro-house-remixes-2024-summer-mix",
        "https://soundcloud.com/electronic-dance-dj-party/sets/vocal-chill-deep-house-top-pop-electronic-dance-music-edm-club-remix-party-dj-mix-set-2019-2020",
        "https://soundcloud.com/vocaltrance4ever/sets/best-vocal-trance-songs",
        "https://soundcloud.com/namir-wattar/sets/remix-of-popular-songs-edm",
        "https://soundcloud.com/david-murphy-26/sets/club-mix-2023-dance-music",
        "https://soundcloud.com/martin-heinrich-566502433/sets/club-mix-2024-dance-music",
        "https://soundcloud.com/luk_music/sets/ibiza-techno-afro-house-remixes-2024-summer-mix",
        "https://soundcloud.com/soundcloud-the-peak/sets/level-up-edm-next",
        "https://soundcloud.com/namir-wattar/sets/remix-of-popular-songs-edm"
    ]

    # File to save local JSON data
    output_file = "all_songs.json"

    url_collection(playlist_urls, output_file)


