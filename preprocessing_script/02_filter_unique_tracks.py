import json
from datetime import datetime

# Load the JSON data from the file
with open('mpd.slice.0-999_albums_edited.json', 'r') as file:
    data = json.load(file)

# Initialize a set to store unique track URIs and a list to store unique track details
unique_track_uris = set()
unique_tracks = []

# Function to clean album details by excluding specific fields
def clean_album(album):
    fields_to_remove = ['available_markets', 'tracks', 'copyrights', 'images']
    for field in fields_to_remove:
        if field in album:
            del album[field]
    return album

# Function to clean track details by excluding specific fields
def clean_track(track):
    if 'pos' in track:
        del track['pos']
    track['album'] = clean_album(track.get('album', {}))
    return track

# Loop through each playlist and its tracks
for playlist in data.get('playlists', []):
    for track in playlist.get('tracks', []):
        # Extract the necessary track details
        track_uri = track.get('track_uri')
        album = track.get('album', {})
        release_date = album.get('release_date')
        
        # Filter tracks based on the release date
        if release_date:
            try:
                release_year = datetime.strptime(release_date, '%Y-%m-%d').year
                if 2015 <= release_year <= 2019:
                    # Check if the track URI is already added
                    if track_uri not in unique_track_uris:
                        unique_track_uris.add(track_uri)
                        # Clean the track details
                        unique_tracks.append(clean_track(track))
            except ValueError:
                # Handle cases where the release_date is not in the expected format
                continue

# Prepare the output JSON data
output_data = {
    "tracks": unique_tracks
}

with open('unique_tracks_2015_2019.json', 'w') as output_file:
    json.dump(output_data, output_file, indent=4)

print("Unique tracks from 2015 to 2019 have been written to unique_tracks_2015_2019.json")