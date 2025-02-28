import unittest
from cryptvault import generate_nonce, generate_uuid_v7, generate_salt

class TestGenerators(unittest.TestCase):
    def test_generate_nonce(self):
        nonce = generate_nonce()
        self.assertEqual(len(nonce), 12)

    def test_generate_uuid_v7(self):
        uuid = generate_uuid_v7()
        self.assertTrue(isinstance(uuid, str))

    def test_generate_salt(self):
        salt = generate_salt()
        self.assertEqual(len(salt), 16)

if __name__ == '__main__':
    unittest.main()