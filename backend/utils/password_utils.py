# backend/utils/password_utils.py
import hashlib
import os
import base64

def hash_password(password):
    """Hash a password using SHA-256 with salt"""
    salt = os.urandom(32)  # 32 bytes salt
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Number of iterations
    )
    # Store salt and key together
    salt_key = salt + key
    return base64.b64encode(salt_key).decode('utf-8')

def verify_password(stored_password, provided_password):
    """Verify a password against its hash"""
    try:
        salt_key = base64.b64decode(stored_password.encode('utf-8'))
        salt = salt_key[:32]  # First 32 bytes are salt
        key = salt_key[32:]   # Rest is the key
        
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return new_key == key
    except Exception:
        return False