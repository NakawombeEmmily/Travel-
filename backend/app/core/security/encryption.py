import base64
import secrets

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    def __init__(self, key: str):
        if key.startswith("base64:"):
            raw = key[7:]
            self._key = self._b64decode(raw)
        else:
            decoded = self._b64decode(key)
            self._key = decoded if len(decoded) == 32 else key.encode("utf-8")
        if len(self._key) != 32:
            raise ValueError("ENCRYPTION_KEY must be 32 bytes")
        self._aesgcm = AESGCM(self._key)

    @staticmethod
    def _b64decode(value: str) -> bytes:
        try:
            return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        except Exception:
            return b""

    def encrypt(self, plaintext: str) -> bytes:
        nonce = secrets.token_bytes(12)
        data = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return nonce + data

    def decrypt(self, encrypted: bytes) -> str:
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        return self._aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    def encrypt_bytes(self, data: bytes) -> bytes:
        nonce = secrets.token_bytes(12)
        return nonce + self._aesgcm.encrypt(nonce, data, None)

    def decrypt_bytes(self, encrypted: bytes) -> bytes:
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        return self._aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def hash_plaintext(plaintext: str) -> str:
        h = hashes.Hash(hashes.SHA256())
        h.update(plaintext.encode("utf-8"))
        return h.finalize().hex()
