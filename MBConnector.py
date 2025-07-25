from spotify_handler import SpotifyHandler
import SQLHandler
import requests
import time
import sys
import random
from dotenv import load_dotenv
import os

# Connection to the SQL database
db = SQLHandler.SQLHandler(
    host="localhost",
    user="root",
    password="Yukithedog23!",
    database="metal_songs_db"
)

load_dotenv()

# Query music from MusicBrainz API and insertion into the database
def collect_music():
    per_subgenre_limit = get_per_subgenere_limit()
    subgenres = get_subgenres_from_user()  # Get subgenres from user input  

    total_bands = 0                                         # Limit of bands to be inserted 
    expected_total = len(subgenres) * per_subgenre_limit    # For progress bar
    progress = 0

    def print_progress(progress, total):
        bar_len = 40
        filled_len = int(round(bar_len * progress / float(total)))
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write(f'\rFinding music [{bar}]')
        sys.stdout.flush()
        if progress == total:
            print()  

    # For each subgenre, query MusicBrainz for bands tagged with that subgenre
    for subgenre in subgenres:                                         
        band_count = 0                                                 
        url = f"https://musicbrainz.org/ws/2/artist?query=tag:{subgenre} AND type:group&inc=tags&fmt=json" 
        headers = {'User-Agent': f"MyMetalApp/1.0 ({os.getenv('CONTACT_EMAIL')})"}
        response = requests.get(url, headers=headers, timeout=10) # Query MusicBrainz
        time.sleep(1)
        if response and response.status_code == 200:
            data = response.json()
            # For all artists in the response
            for artist in data.get("artists", []):         
                tags = [t['name'].lower() for t in artist.get('tags', [])] # Lowercase tags for matching
                if subgenre in tags: # Add if tagged with the subgenre
                    band_name = artist["name"]                        
                    band_id = db.generate_random_id()                  
                    if db.band_name_exists(band_name): # Skip if already in DB (can happen if in a previous subgenre)
                        continue
                    db.insert_band(band_id, band_name, subgenre)                
                    total_bands += 1                                  
                    progress += 1                                      
                    print_progress(progress, expected_total)           
                    mbid = artist.get("id") # Get artists MusicBrainz ID to query albums
                    if not mbid:                                      
                        continue
                    albums_url = f"https://musicbrainz.org/ws/2/release-group?artist={mbid}&type=album&fmt=json" # Albums API URL
                    album_response = requests.get(albums_url, headers=headers, timeout=10) # Query for albums
                    if album_response is None:
                        print(f"  Skipping albums for band {band_name} due to repeated request failures.")
                        continue
                    time.sleep(2)
                    album_res = album_response.json() # Get album data
                    for album in album_res.get("release-groups", []): # "release-groups" is the key for albums
                        title = album["title"] # Get title field                       
                        year = album.get("first-release-date", "0000")[:4] # Get release year
                        try:
                            year = int(year)
                        except:
                            year = 0 # If year is null
                        album_id = db.generate_album_id(band_id, title) # Generate album id
                        if db.album_id_exists(album_id):                # Skip if already in DB
                            continue
                        db.insert_album(album_id, title, year, band_id) # Insert album into DB
                    band_count += 1                                     # Increment band count for subgenre
                    if band_count >= per_subgenre_limit:                # Stop if limit reached
                        break
    print(f"Found and inserted {total_bands} bands across {len(subgenres)} subgenres into your database.")

# --- Helpers for menu options ---
def get_albums_by_band():
    band_name = input("Enter the name of the band: ").strip()
    if not band_name:
        print("No band name entered. Exiting.")
        return
    albums = db.get_albums_by_band(band_name)
    print()
    print(f"Albums by {band_name}:")
    for album in albums:
        print(f"{album[1]} ({album[2]})")

def list_all_artists():
    artists = db.list_all_artists()
    print("\nList of all artists:")
    for artist in artists:
        print(artist)

def make_spotify_playlist():
    
    # Spotify handler object 
    sp_handler = SpotifyHandler()
    
    # Create an empty playlist
    playlist_name = input("Enter a name for your playlist: ")
    playlist = sp_handler.sp.user_playlist_create(user=sp_handler.user_id, name=playlist_name, public=True)
    playlist_id = playlist['id']

    # A playlist of 5 songs per album, 2 albums per artist, max 5 artists
    subgenres = get_subgenres_from_user()
    artists = []
    albums = []

    # Get a list of artists 
    for subgenre in subgenres:
        artists += db.get_10_artists_from_subgenre(subgenre)
        
    # Get albums from the arists
    for artist in artists:
        albums += db.get_2_albums_by_band(artist)
        
    # Song list
    all_songs = []

    # Get songs
    for album in albums:
        songs = sp_handler.get_songs_from_album(album)
        all_songs.extend(songs)

    # Randomize order
    random.shuffle(all_songs) 

    # Add songs to the empty playlist
    for i in range(0, len(all_songs), 100):
        sp_handler.sp.playlist_add_items(playlist_id, all_songs[i:i+100])

    print(f"Playlist created with {len(all_songs)} tracks.")

def get_subgenres_from_user():
    print()
    print("Enter subgenres to search (comma separated, e.g. death metal, black metal):")
    user_input = input().strip()
    subgenres = [s.strip() for s in user_input.split(",") if s.strip()]
    if not subgenres:
        print("No subgenres entered. Exiting.")
        exit(0)
    return subgenres

def invalid_choice():
        print("Invalid choice. Please try again.")

def get_per_subgenere_limit():
    print("Enter the maximum number of bands to insert per subgenre (default is 10):")
    user_input = input().strip()
    if user_input.isdigit():
        return int(user_input)
    else:
        print("Invalid input, using default limit of 10.")
        return 10      
# --------------------------------


def spotify_menu():
    menu_options = {
        "1": make_spotify_playlist
    }

    while True:
        print("\n--- Spotify Menu ---")
        print("1. Create a playlist from your database")
        print("0. Back to main menu")
        choice = input("> ")

        if choice == "0":
            return  

        action = menu_options.get(choice, invalid_choice)
        action()

def main():
    # Mapping of menu options to functions
    menu_options = {
        "1": collect_music,
        "2": db.get_random_album,
        "3": list_all_artists,  
        "4": get_albums_by_band,
        "5": db.reset_database,
        "6": spotify_menu,  
        "7": exit
        
    }

    while True:
        print("\n--- MY FIRST PROJECT - WONDERFUL MUSIC DATABASE!!! ---")
        print()
        print("1. Collect music from MusicBrainz")
        print("2. Get a random album")
        print("3. List all artists")
        print("4. Get albums by a specific band")
        print("5. Reset the database")
        print("6. Spotify menu")
        print("7. Exit")
        choice = input("> ")

        action = menu_options.get(choice, invalid_choice)
        action()

       

    db.close()
    print("Done!")

   

if __name__ == "__main__":
    main()
    print("Done!")
    db.close()

