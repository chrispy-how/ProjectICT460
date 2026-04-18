import unittest
from utils.sqlite_utils import (
    get_db_connection,
    check_login,
    get_filter_options,
    get_filtered_tracks,
    get_track,
    add_track,
    update_track,
    delete_track,
    get_all_artists,
    get_artist,
    get_artist_albums,
    add_artist,
    update_artist,
    delete_artist,
    get_user_role,
)


class TestSqliteUtils(unittest.TestCase):

    def setUp(self):
        # Setup if needed, but using existing db
        pass

    def tearDown(self):
        # Cleanup test data
        pass

    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        if conn:
            conn.close()

    def test_check_login_invalid(self):
        result = check_login("invalid", "invalid")
        self.assertFalse(result)

    def test_get_filter_options(self):
        options = get_filter_options()
        self.assertIsInstance(options, dict)
        self.assertIn('genres', options)
        self.assertIn('artists', options)
        self.assertIn('media_types', options)
        self.assertIn('albums', options)

    def test_get_filtered_tracks(self):
        tracks = get_filtered_tracks()
        self.assertIsInstance(tracks, list)

    def test_get_track_existing(self):
        track = get_track(1)
        self.assertIsNotNone(track)

    def test_get_track_nonexisting(self):
        track = get_track(999999)
        self.assertIsNone(track)

    def test_get_all_artists(self):
        artists = get_all_artists()
        self.assertIsInstance(artists, list)
        self.assertGreater(len(artists), 0)

    def test_get_artist_existing(self):
        artist = get_artist(1)
        self.assertIsNotNone(artist)

    def test_get_artist_nonexisting(self):
        artist = get_artist(999999)
        self.assertIsNone(artist)

    def test_get_artist_albums(self):
        albums = get_artist_albums(1)
        self.assertIsInstance(albums, list)

    def test_add_and_delete_artist(self):
        artist_id = add_artist("Test Artist")
        self.assertIsNotNone(artist_id)
        if artist_id:
            artist = get_artist(artist_id)
            self.assertIsNotNone(artist)
            self.assertEqual(artist['Name'], "Test Artist")
            result = delete_artist(artist_id)
            self.assertTrue(result)

    def test_update_artist(self):
        artist_id = add_artist("Test Artist Update")
        self.assertIsNotNone(artist_id)
        if artist_id:
            result = update_artist(artist_id, "Updated Test Artist")
            self.assertTrue(result)
            artist = get_artist(artist_id)
            self.assertEqual(artist['Name'], "Updated Test Artist")
            delete_artist(artist_id)

    def test_add_and_delete_track(self):
        track_id = add_track("Test Track", 1, 1, 1, 1000, 0.99)
        self.assertIsNotNone(track_id)
        if track_id:
            track = get_track(track_id)
            self.assertIsNotNone(track)
            self.assertEqual(track['Name'], "Test Track")
            result = delete_track(track_id)
            self.assertTrue(result)

    def test_update_track(self):
        track_id = add_track("Test Track Update", 1, 1, 1, 1000, 0.99)
        self.assertIsNotNone(track_id)
        if track_id:
            result = update_track(track_id, "Updated Test Track", 1, 1, 1, 2000, 1.99)
            self.assertTrue(result)
            track = get_track(track_id)
            self.assertEqual(track['Name'], "Updated Test Track")
            delete_track(track_id)

    def test_get_user_role(self):
        role = get_user_role("testuser")
        self.assertTrue(role is None or isinstance(role, int))


if __name__ == '__main__':
    unittest.main()
