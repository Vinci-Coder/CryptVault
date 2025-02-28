import unittest
from cryptvault import encrypt_aes_gcm, decrypt_aes_gcm

class TestCrypto(unittest.TestCase):
    def test_encrypt_decrypt_aes(self):
        key = b'01234567890123456789012345678901'
        plaintext = b'teste de criptografia'
        ciphertext = encrypt_aes_gcm(plaintext, key)
        decrypted = decrypt_aes_gcm(ciphertext, key)
        self.assertEqual(plaintext, decrypted)

if __name__ == '__main__':
    unittest.main()