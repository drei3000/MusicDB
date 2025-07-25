import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
from dotenv import load_dotenv
import os

class SpotifyHandler:

    # Creates a connection to my spotify client on initialization
    def __init__(self):

        
        load_dotenv()

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri='http://127.0.0.1:8888/callback',
            scope='playlist-modify-public'
        ))

        # Spotify user 
        user = self.sp.current_user()
        self.user_id = user['id']

    # Query spotify api to find best match for an album in my sql database using the album's name. Not always accurate because some albums may not be in spotify api
    def get_album_id(self, album_name):
        results = self.sp.search(q=f"album:{album_name}", type='album', limit=1)
        albums = results['albums']['items']
        if albums: 
            return albums[0]['id'] # Return the first album in the list of results
        return None
    
    # Get the tracks from album (returns 3 for adding to a playlist)
    def get_songs_from_album(self, album_name):
        album_id = self.get_album_id(album_name)
        if not album_id:
            return []

        track_data = self.sp.album_tracks(album_id)
        all_songs = track_data.get('items', [])
        
        # If there are fewer than 3 songs, return all; otherwise, pick 3 randomly
        return [track['uri'] for track in random.sample(all_songs, min(3, len(all_songs)))]