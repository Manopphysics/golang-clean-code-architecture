"""
Password hashing and verification utilities.

Uses bcrypt with cost factor 10, matching the Go original.
"""
import bcrypt

# Cost factor 10 — matches Go's bcrypt.GenerateFromPassword(..., 10)
BCRYPT_ROUNDS = 10


def hash_password(plain: str) -> str:
    """
    Bcrypt-hash a plain-text password.
    Mirrors Go's BcryptHashing() in UserRegisterRequest.
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    Mirrors Go's bcrypt.CompareHashAndPassword().
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())
