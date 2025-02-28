import unittest
from cryptvault import hash_sha256, hash_password, verify_password

class TestHash(unittest.TestCase):
    def test_hash_sha256(self):
        data = b'conteudo'
        hashed = hash_sha256(data)
        self.assertIsInstance(hashed, bytes)

    def test_hash_password(self):
        password = "senha_super_segura"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))

if __name__ == '__main__':
    unittest.main()