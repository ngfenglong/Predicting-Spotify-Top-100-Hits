from flask import Flask, render_template, request
import joblib
import requests
import base64
import numpy as np
import pandas as pd

# Load the saved components
top_100_train_genres = joblib.load('model/top_100_genres.pkl')
scaler_loudness = joblib.load('model/scaler_loudness.pkl')
scaler_genres = joblib.load('model/scaler_genres.pkl')
pca = joblib.load('model/pca.pkl')
model = joblib.load('model/model.pkl')

CLIENT_ID = 'YOUR_CLIENT_ID'  # Replace with your actual Spotify client ID
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'  # Replace with your actual Spotify client secret

selected_features = ['album_release_date', 'artist_popularity', 'pca_genre_1', 'pca_genre_3', 'pca_genre_4', 'pca_genre_5', 'pca_genre_6', 'pca_genre_7']

app = Flask(__name__)

# Function to clean genres
def clean_genres(genre_str):
    if isinstance(genre_str, str):
        return [genre.strip().lower() for genre in genre_str.split(',')]
    return []

# Function to encode genres based on the top 100
def encode_top_genres(cleaned_genres, top_genres):
    genre_set = set(cleaned_genres)
    encoded = {genre: (1 if genre in genre_set else 0) for genre in top_genres}
    encoded['other'] = 1 if not genre_set.isdisjoint(set(top_genres)) else 0
    return encoded

# Function to get Spotify API token
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
        headers['Authorization'] = "Bearer " + get_spotify_token(client_id, client_secret)
        response = requests.get(url, headers=headers, params=params)
    return response

# Function to search for a track by name (with optional artist name)
def search_track(query, token):
    search_url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'q': query,
        'type': 'track',
        'limit': 1
    }

    response = requests.get(search_url, headers=headers, params=params)
    response_data = response.json()
    tracks = response_data.get('tracks', {}).get('items', [])
    if tracks:
        return tracks[0]['id']
    return None

# Preprocess a single data point
def preprocess_single_data_point(data_point):
    data_point = data_point.copy()
    data_point['cleaned_genres'] = clean_genres(data_point['artist_genres'])
    genre_encoding = encode_top_genres(data_point['cleaned_genres'], top_100_train_genres)
    
    for genre in top_100_train_genres:
        data_point[genre] = genre_encoding.get(genre, 0)

    data_point['artist_popularity'] = np.log1p(data_point['artist_popularity'])
    data_point['audio_features_loudness_scaled'] = scaler_loudness.transform([[data_point['audio_features_loudness']]])[0][0]

    duration_ms = data_point['duration_ms']
    Q1, Q3 = 0, 0  # Replace with actual values from training data
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    if duration_ms < lower_bound or duration_ms > upper_bound:
        duration_ms = 0  # Replace with mean of non-outliers from your training data
    data_point['duration_ms'] = np.log1p(duration_ms)

    genres_features = np.array([[data_point[genre] for genre in top_100_train_genres]])
    genres_pca = pca.transform(scaler_genres.transform(genres_features))
    for i in range(genres_pca.shape[1]):
        data_point[f'pca_genre_{i+1}'] = genres_pca[0][i]

    data_point['tempo_danceability_interaction'] = data_point['audio_features_tempo'] * data_point['audio_features_danceability']
    preprocessed_data = data_point[selected_features]

    return np.array(preprocessed_data).reshape(1, -1)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    query = request.form.get('track-content')

    # Get Spotify API token
    token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)

    # Check if the input is a track ID (assume track IDs are alphanumeric strings of length 22)
    if len(query) == 22 and query.isalnum():
        trackId = query
    else:
        # Otherwise, treat the input as a search query for track name or track name with artist name
        trackId = search_track(query, token)

    if not trackId:
        return render_template("index.html", prediction="Track not found")

    # Get track details
    track_url = f"https://api.spotify.com/v1/tracks/{trackId}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    track_response = make_api_request(track_url, headers, {}, CLIENT_ID, CLIENT_SECRET)

    if track_response.status_code == 200:
        track_data = track_response.json()
        track_name = track_data.get('name', 'Unknown')
        artist_id = track_data['artists'][0]['id']
        album_release_date = track_data['album'].get('release_date', '1970-01-01')
        duration_ms = track_data.get('duration_ms', 0)
        image_url = track_data['album']['images'][0]['url'] if track_data['album'].get('images') else ''
    else:
        return render_template("index.html", prediction="Track details could not be retrieved")

    # Get artist details
    artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
    artist_response = make_api_request(artist_url, headers, {}, CLIENT_ID, CLIENT_SECRET)

    if artist_response.status_code == 200:
        artist_data = artist_response.json()
        artist_name = artist_data.get('name', 'Unknown')
        artist_popularity = artist_data.get('popularity', 0)
        artist_genres = ','.join(artist_data.get('genres', []))
    else:
        artist_name = 'Unknown'
        artist_popularity = 0
        artist_genres = ''

    # Get audio features
    audio_features_url = f"https://api.spotify.com/v1/audio-features/{trackId}"
    audio_features_response = make_api_request(audio_features_url, headers, {}, CLIENT_ID, CLIENT_SECRET)

    if audio_features_response.status_code == 200:
        audio_features = audio_features_response.json()
        audio_features_tempo = audio_features.get('tempo', 0)
        audio_features_loudness = audio_features.get('loudness', 0)
        audio_features_danceability = audio_features.get('danceability', 0)
    else:
        return render_template("index.html", prediction="Audio features could not be retrieved")

    # Create a single data point for prediction
    single_data_point = {
        'album_release_date': pd.Timestamp(album_release_date),
        'audio_features_tempo': audio_features_tempo,
        'audio_features_energy': audio_features.get('energy', 0),
        'audio_features_danceability': audio_features_danceability,
        'audio_features_loudness': audio_features_loudness,
        'audio_features_liveness': audio_features.get('liveness', 0),
        'audio_features_valence': audio_features.get('valence', 0),
        'duration_ms': duration_ms,
        'audio_features_acousticness': audio_features.get('acousticness', 0),
        'audio_features_speechiness': audio_features.get('speechiness', 0),
        'artist_popularity': artist_popularity,
        'artist_genres': artist_genres,
    }

    # Preprocess the data
    single_data_point_df = pd.DataFrame([single_data_point])
    single_data_point_df['album_release_date'] = (single_data_point_df['album_release_date'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1D')
    preprocessed_data = preprocess_single_data_point(single_data_point_df.iloc[0])

    # Make prediction
    prediction = model.predict(preprocessed_data)
    prediction_text = "Top 100 Track" if prediction == 1 else "Not in Top 100 Track"

    return render_template("index.html", prediction=prediction_text, trackId=trackId,
                           track_name=track_name,
                           artist_name=artist_name,
                           album_name=track_data['album']['name'], release_date=album_release_date,
                           image_url=image_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)