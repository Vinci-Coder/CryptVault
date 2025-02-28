import unittest
from cryptvault import base64_encode, base64_decode

class TestEncoders(unittest.TestCase):
    def test_base64(self):
        data = b'mensagem'
        encoded = base64_encode(data)
        decoded = base64_decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == '__main__':
    unittest.main()