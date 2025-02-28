import unittest
from cryptvault import hmac_sha256

class TestHMAC(unittest.TestCase):
    def test_hmac_sha256(self):
        key = b'secret_key'
        message = b'mensagem'
        hmac = hmac_sha256(key, message)
        self.assertIsInstance(hmac, bytes)

if __name__ == '__main__':
    unittest.main()