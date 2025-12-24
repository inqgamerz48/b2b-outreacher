import hashlib
import os

def get_password_hash(password: str) -> str:
    """
    Returns a SHA-256 hash of the password + fixed salt (simple secure for this use case).
    In prod, use bcrypt/argon2.
    """
    salt = "b2b_outreach_secure_salt_2025" # Simple static salt for MVP
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password
