import mysql.connector
import random
import hashlib

class SQLHandler:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()

    def generate_random_id(self):
        return random.randint(10000000, 99999999)

    def generate_album_id(self, band_id, album_title):
        base = f"{band_id}_{album_title}"
        return int(hashlib.sha256(base.encode()).hexdigest(), 16) % (10 ** 8)

    def insert_band(self, band_id, name, subgenre):
        self.cursor.execute("INSERT INTO Bands (id, name, subgenre) VALUES (%s, %s, %s)", (band_id, name, subgenre))
        self.conn.commit()

    def insert_album(self, album_id, name, year, band_id):
        self.cursor.execute("INSERT INTO Albums (id, name, release_year, band_id) VALUES (%s, %s, %s, %s)", (album_id, name, year, band_id))
        self.conn.commit()

    def band_name_exists(self, band_name):
        self.cursor.execute("SELECT 1 FROM Bands WHERE name = %s LIMIT 1", (band_name,))
        return self.cursor.fetchone() is not None

    def album_id_exists(self, album_id):
        self.cursor.execute("SELECT 1 FROM Albums WHERE id = %s LIMIT 1", (album_id,))
        return self.cursor.fetchone() is not None

    def reset_database(self, sql_file="Metal_db.sql"):
        with open(sql_file, "r") as f:
            sql = f.read()
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                self.cursor.execute(stmt)
        self.conn.commit()

    def get_random_album(self):
        self.cursor.execute("""
            SELECT Albums.id, Albums.name, Bands.name
            FROM Albums
            JOIN Bands ON Albums.band_id = Bands.id
            ORDER BY RAND() LIMIT 1
        """)
        result = self.cursor.fetchone()
        if result:
            album_id, album_name, band_name = result
            print(album_id, album_name, "by: "f"{band_name}")
            return (album_id, album_name, f"{band_name}")
        else:
            return None
        
    def get_band_id_by_name(self, band_name):
        self.cursor.execute("SELECT id FROM Bands WHERE name = %s", (band_name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def get_albums_by_band(self, band_name):
        band_id = self.get_band_id_by_name(band_name)
        self.cursor.execute("SELECT id, name, release_year FROM Albums WHERE band_id = %s ORDER BY release_year", (band_id,))
        albums = self.cursor.fetchall()
        return [(album[0], album[1], album[2]) for album in albums]
    
    def get_2_albums_by_band(self, band_name):
        band_id = self.get_band_id_by_name(band_name)
        self.cursor.execute("SELECT name FROM Albums WHERE band_id = %s ORDER BY RAND() LIMIT 2", (band_id,))
        albums = self.cursor.fetchall()
        return [(album[0]) for album in albums]

    def list_all_artists(self):
        self.cursor.execute("SELECT name, subgenre FROM Bands ORDER BY name")
        artists = self.cursor.fetchall()
        return [(artist[0], artist[1]) for artist in artists]

    def close(self):
        self.cursor.close()
        self.conn.close()

    def get_10_artists_from_subgenre(self, subgenre):
        self.cursor.execute("SELECT name FROM Bands WHERE subgenre = %s ORDER BY RAND() LIMIT 10", (subgenre,))
        result = self.cursor.fetchall()
        return [row[0] for row in result]
