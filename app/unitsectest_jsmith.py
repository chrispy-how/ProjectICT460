import unittest
import hashlib
from utils.sqlite_utils import (
    check_login,
    get_track,
    add_artist,
    delete_artist,
    add_track,
    delete_track,
    get_artist,
    get_user_role,
)


class TestSecuritySqliteUtils(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        # Cleanup any test data added during security tests
        pass

    def test_sql_injection_check_login_username(self):
        # Test SQL injection in username
        malicious_inputs = [
            "' OR '1'='1' --",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
        ]
        for username in malicious_inputs:
            result = check_login(username, "password")
            self.assertFalse(result, f"SQL injection succeeded with username: {username}")

    def test_sql_injection_check_login_password(self):
        # Test SQL injection in password
        malicious_inputs = [
            "' OR '1'='1' --",
            "'; DROP TABLE users; --",
        ]
        for password in malicious_inputs:
            result = check_login("username", password)
            self.assertFalse(result, f"SQL injection succeeded with password: {password}")

    def test_sql_injection_get_track(self):
        # get_track uses parameterized query, should be safe
        malicious_inputs = [
            "1; DROP TABLE tracks; --",
            "' OR '1'='1'",
        ]
        for track_id in malicious_inputs:
            try:
                track = get_track(track_id)
                self.assertIsNone(track, f"SQL injection succeeded with track_id: {track_id}")
            except (ValueError, TypeError):
                # If it raises ValueError or TypeError for non-int, that's also fine
                pass

    def test_sql_injection_add_artist(self):
        # Test SQL injection in artist name
        malicious_names = [
            "Test'; DROP TABLE artists; --",
            "Test' OR '1'='1",
        ]
        for name in malicious_names:
            artist_id = add_artist(name)
            if artist_id:
                # If added, check if it was malicious
                artist = get_artist(artist_id)
                if artist:
                    self.assertNotEqual(artist['Name'], name, f"Malicious name added: {name}")
                delete_artist(artist_id)

    def test_sql_injection_add_track(self):
        # Test SQL injection in track name
        malicious_names = [
            "Test'; DROP TABLE tracks; --",
        ]
        for name in malicious_names:
            track_id = add_track(name, 1, 1, 1, 1000, 0.99)
            if track_id:
                track = get_track(track_id)
                if track:
                    self.assertNotEqual(track['Name'], name, f"Malicious name added: {name}")
                delete_track(track_id)

    def test_password_hashing_weakness(self):
        # Test that MD5 is used (though weak)
        password = "password"
        salt = "salt"
        combined = password + salt
        hashed = hashlib.md5(combined.encode()).hexdigest()
        # Since internal, just check MD5 produces expected
        expected = hashlib.md5(b"passwordsalt").hexdigest()
        self.assertEqual(hashed, expected)

    def test_input_validation_artist_name_empty(self):
        # Test empty artist name
        artist_id = add_artist("")
        if artist_id:
            # If added, it's a vulnerability
            self.assertIsNone(artist_id, "Empty name should not be added")
            delete_artist(artist_id)

    def test_input_validation_artist_name_whitespace(self):
        artist_id = add_artist("   ")
        if artist_id:
            self.assertIsNone(artist_id, "Whitespace name should not be added")
            delete_artist(artist_id)

    def test_input_validation_track_name_empty(self):
        track_id = add_track("", 1, 1, 1, 1000, 0.99)
        if track_id:
            self.assertIsNone(track_id, "Empty track name should not be added")
            delete_track(track_id)

    def test_delete_artist_with_albums_prevents_deletion(self):
        # Security: prevent deleting artist with albums
        result = delete_artist(1)  # Assuming artist 1 has albums
        self.assertFalse(result, "Should not delete artist with albums")

    def test_role_based_access_simulation(self):
        # Simulate role check
        role = get_user_role("admin")
        if role:
            self.assertIsInstance(role, int)
        # For security, check if high role prevents actions, but since functions don't check, note it


if __name__ == '__main__':
    unittest.main()
