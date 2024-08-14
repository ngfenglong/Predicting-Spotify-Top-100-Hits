import json
import requests
import base64
import time

# Spotify API credentials
CLIENT_ID = 'your_client_id'  # Replace with your actual Spotify client ID
CLIENT_SECRET = 'your_client_secret'  # Replace with your actual Spotify client secret

# Function to get the Spotify API token
def get_spotify_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode((client_id + ":" + client_secret).encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")

# Function to make API request with token refresh
def make_api_request(url, headers, params, client_id, client_secret):
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 401:  # Token expired
        print("Access token expired. Refreshing token...")
        headers['Authorization'] = "Bearer " + get_spotify_token(client_id, client_secret)
        response = requests.get(url, headers=headers, params=params)
    return response

# Get the Spotify API token
token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)

# Load the JSON file containing the playlist data
file_path = '1000playlist.json'
with open(file_path, 'r') as file:
    data = json.load(file)

# Extract all unique URIs
track_uris = []
album_uris = []
artist_uris = []

for playlist in data['playlists']:
    for track in playlist['tracks']:
        track_uris.append(track['track_uri'])
        album_uris.append(track['album_uri'])
        artist_uris.append(track['artist_uri'])

# Remove duplicates
unique_track_uris = list(set(track_uris))
unique_album_uris = list(set(album_uris))
unique_artist_uris = list(set(artist_uris))

# Clean the URIs
cleaned_track_uris = [uri.split(':')[-1] for uri in unique_track_uris]
cleaned_album_uris = [uri.split(':')[-1] for uri in unique_album_uris]
cleaned_artist_uris = [uri.split(':')[-1] for uri in unique_artist_uris]

# Spotify API URLs
album_url = "https://api.spotify.com/v1/albums"
audio_features_url = "https://api.spotify.com/v1/audio-features"
artist_url = "https://api.spotify.com/v1/artists"

headers = {
    "Authorization": f"Bearer {token}"
}

# Function to split list into chunks of 20 or 50
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Function to fetch data from Spotify
def fetch_spotify_data(url, uris, client_id, client_secret, chunk_size):
    results = {}
    for uri_chunk in chunks(uris, chunk_size):
        params = {
            "ids": ",".join(uri_chunk)
        }
        response = make_api_request(url, headers, params, client_id, client_secret)
        if response.status_code == 200:
            data_list = response.json().get(url.split('/')[-1], [])
            for item in data_list:
                results[item['id']] = item
        else:
            print(f"Error: {response.status_code} - {response.text}")
        time.sleep(30)  # To avoid rate limits
    return results

# Fetch data for albums, audio features, and artists
print("Fetching Album Data...")
album_data = fetch_spotify_data(album_url, cleaned_album_uris, CLIENT_ID, CLIENT_SECRET, 20)

print("Fetching Audio Features Data...")
audio_features_data = fetch_spotify_data(audio_features_url, cleaned_track_uris, CLIENT_ID, CLIENT_SECRET, 50)

print("Fetching Artist Data...")
artist_data = fetch_spotify_data(artist_url, cleaned_artist_uris, CLIENT_ID, CLIENT_SECRET, 50)

# Update the original JSON data with all retrieved information
for playlist in data['playlists']:
    for track in playlist['tracks']:
        track_id = track['track_uri'].split(':')[-1]
        album_id = track['album_uri'].split(':')[-1]
        artist_id = track['artist_uri'].split(':')[-1]

        # Add album data
        if album_id in album_data:
            track['album'] = album_data[album_id]

        # Add audio features data
        if track_id in audio_features_data:
            track['audio_features'] = audio_features_data[track_id]

        # Add artist data
        if artist_id in artist_data:
            track['artist'] = artist_data[artist_id]

# Save the combined data to a new JSON file
output_file_path = '1000playlist_combined.json'
with open(output_file_path, 'w') as outfile:
    json.dump(data, outfile, indent=4)

print(f"Combined playlist data has been saved to {output_file_path}")