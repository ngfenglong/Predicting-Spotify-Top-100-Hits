import pandas as pd
import json

# Load the CSV file
csv_file_path = 'Spotify 2016 - 2019 Top 100.csv'
csv_data = pd.read_csv(csv_file_path)

# Load the JSON file
json_file_path = 'unique_tracks_2015_2019.json'
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# Extract necessary columns from CSV
csv_titles = csv_data[['title', 'artist']]

# Function to check if a track should be removed
def should_remove(track, csv_titles):
    for index, row in csv_titles.iterrows():
        if track['track_name'] == row['title'] and track['artist_name'] == row['artist']:
            print(f"Removing track: {track['track_name']} by {track['artist_name']}")
            return True
    return False

# Function to flatten nested JSON
def flatten_json(track):
    flat_track = {
        'artist_name': track.get('artist_name', ''),
        'track_name': track.get('track_name', ''),
        'duration_ms': track.get('duration_ms', 0),
        'album_name': track.get('album_name', ''),
        'artist_genres': ', '.join(track.get('artist', {}).get('genres', [])),
        'artist_popularity': track.get('artist', {}).get('popularity', None),
        'artist_followers': track.get('artist', {}).get('followers', None),
        'album_type': track.get('album', {}).get('album_type', ''),
        'album_release_date': track.get('album', {}).get('release_date', ''),
        'audio_features_danceability': track.get('audio_features', {}).get('danceability', 0.0),
        'audio_features_energy': track.get('audio_features', {}).get('energy', 0.0),
        'audio_features_key': track.get('audio_features', {}).get('key', 0),
        'audio_features_loudness': track.get('audio_features', {}).get('loudness', 0.0),
        'audio_features_mode': track.get('audio_features', {}).get('mode', 0),
        'audio_features_speechiness': track.get('audio_features', {}).get('speechiness', 0.0),
        'audio_features_acousticness': track.get('audio_features', {}).get('acousticness', 0.0),
        'audio_features_instrumentalness': track.get('audio_features', {}).get('instrumentalness', 0.0),
        'audio_features_liveness': track.get('audio_features', {}).get('liveness', 0.0),
        'audio_features_valence': track.get('audio_features', {}).get('valence', 0.0),
        'audio_features_tempo': track.get('audio_features', {}).get('tempo', 0.0),
        'audio_features_time_signature': track.get('audio_features', {}).get('time_signature', 0),
    }
    return flat_track

# Filter and flatten the tracks
cleaned_tracks = [flatten_json(track) for track in json_data['tracks'] if not should_remove(track, csv_titles)]

# Convert the cleaned and flattened data to a DataFrame
df = pd.DataFrame(cleaned_tracks)

# Save the DataFrame to a CSV file
cleaned_csv_file_path = 'cleaned_unique_tracks_2015_2019_flattened.csv'
df.to_csv(cleaned_csv_file_path, index=False)

print(f"Cleaned and flattened data saved to {cleaned_csv_file_path}")