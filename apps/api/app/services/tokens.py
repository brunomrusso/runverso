import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    secret = get_settings().token_encryption_secret.encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_token(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_token(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
