import pandas as pd
import requests
import base64

# Replace these with your client ID and secret
client_id = 'Your_Client_ID'
client_secret = 'Your_Client_Secret'

def get_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
    }
    data = {
        'grant_type': 'client_credentials'
    }

    response = requests.post(auth_url, headers=headers, data=data)
    response_data = response.json()
    return response_data['access_token']

def search_track(track_name, artist_name, token):
    search_url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    query = f'track:{track_name} artist:{artist_name}'
    params = {
        'q': query,
        'type': 'track',
        'limit': 1
    }

    response = requests.get(search_url, headers=headers, params=params)
    response_data = response.json()
    print(response_data)
    tracks = response_data.get('tracks', {}).get('items', [])
    if tracks:
        return tracks[0]['id']
    return None

def get_audio_features(track_id, token):
    audio_features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(audio_features_url, headers=headers)
    return response.json()

# Get access token
token = get_token(client_id, client_secret)

# Load the CSV file
csv_file_path = 'Spotify 2016 - 2019 Top 100.csv'
df = pd.read_csv(csv_file_path)

# Remove outliners with release date earlier then 1990 (Given the dataset, there's only one outliner)
# To use IQR for other dataset
df = df[df['year released'] > 1990]

# Extract the track names and artist names
track_names = df['title']
artist_names = df['artist']

# Initialize lists to store audio features
nrgy, dnce, dB, live, val, dur, acous, spch, pop = [], [], [], [], [], [], [], [], []

# Get track ID and audio features for each track name and artist name
for track_name, artist_name in zip(track_names, artist_names):
    track_id = search_track(track_name, artist_name, token)
    if track_id:
        audio_features = get_audio_features(track_id, token)
        nrgy.append(audio_features.get('energy'))
        dnce.append(audio_features.get('danceability'))
        dB.append(audio_features.get('loudness'))
        live.append(audio_features.get('liveness'))
        val.append(audio_features.get('valence'))
        dur.append(audio_features.get('duration_ms'))
        acous.append(audio_features.get('acousticness'))
        spch.append(audio_features.get('speechiness'))
    else:
        # If track ID is not found, append None for each feature
        nrgy.append(None)
        dnce.append(None)
        dB.append(None)
        live.append(None)
        val.append(None)
        dur.append(None)
        acous.append(None)
        spch.append(None)

# Update the DataFrame with the new audio features
df['nrgy'] = nrgy
df['dnce'] = dnce
df['dB'] = dB
df['live'] = live
df['val'] = val
df['dur'] = dur
df['acous'] = acous
df['spch'] = spch

# Save the updated DataFrame to a new CSV file
updated_csv_file_path = 'Updated_Spotify_Top_100.csv'
df.to_csv(updated_csv_file_path, index=False)

print(f"Updated CSV file saved to {updated_csv_file_path}")