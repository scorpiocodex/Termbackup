"""
Top-level crypto module owning all security-critical operations.
Argon2id KDF, AES-256-GCM encryption/decryption, Ed25519 signatures, Recovery Phrase generation.
"""
import hashlib
import hmac
import os
from typing import Tuple

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mnemonic import Mnemonic

from .errors import DecryptionError, EncryptionError, KeyDerivationError, SignatureError

SALT_LEN = 32
NONCE_LEN = 12
KEY_LEN = 32

def compute_sha256(data: bytes) -> str:
    """Compute the SHA-256 hash of raw bytes."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()

def generate_salt() -> bytes:
    """Generate 32 bytes of secure random salt."""
    return os.urandom(SALT_LEN)

def generate_nonce() -> bytes:
    """Generate 12 bytes of secure random nonce for AES-GCM."""
    return os.urandom(NONCE_LEN)

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte key using Argon2id.
    Parameters: 64 MiB memory, 3 iterations, 4 lanes.
    """
    try:
        key = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=65536,  # 64 MiB
            parallelism=4,
            hash_len=KEY_LEN,
            type=Type.ID
        )
        return key
    except Exception as e:
        raise KeyDerivationError(f"Failed to derive key: {e}") from e

def generate_recovery_phrase() -> str:
    """Generate a high-entropy 24-word recovery phrase."""
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=256)

def derive_recovery_key(phrase: str, salt: bytes) -> bytes:
    """Derives a key from the 24-word recovery phrase using Argon2id."""
    return derive_key(phrase, salt)

def encrypt(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data using AES-256-GCM.
    Returns: nonce (12 bytes) + ciphertext + tag (16 bytes implicitly via AESGCM)
    """
    if len(key) != KEY_LEN:
        raise EncryptionError("Invalid key length for AES-256-GCM.")
    try:
        aesgcm = AESGCM(key)
        nonce = generate_nonce()
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e

def decrypt(payload: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES-256-GCM.
    Payload expected format: nonce (12 bytes) + ciphertext (includes tag)
    """
    if len(payload) < NONCE_LEN + 16:  # Minimum length: nonce + tag
        raise DecryptionError("Payload too short.")
    if len(key) != KEY_LEN:
        raise DecryptionError("Invalid key length.")
    
    nonce = payload[:NONCE_LEN]
    ciphertext = payload[NONCE_LEN:]
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext
    except Exception as e:
        raise DecryptionError("Decryption failed. Invalid key or corrupted data.") from e

def generate_signing_keypair() -> Tuple[bytes, bytes]:
    """
    Generate an Ed25519 keypair.
    Returns (private_key_bytes, public_key_bytes).
    """
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    
    priv_bytes = priv_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return priv_bytes, pub_bytes

def sign(data: bytes, private_key_raw: bytes) -> bytes:
    """Sign data using an Ed25519 private key (raw bytes)."""
    try:
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_raw)
        return priv_key.sign(data)
    except Exception as e:
        raise SignatureError(f"Signing failed: {e}") from e

def verify(data: bytes, signature: bytes, public_key_raw: bytes) -> bool:
    """Verify an Ed25519 signature."""
    try:
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_raw)
        pub_key.verify(signature, data)
        return True
    except Exception:
        return False

def secure_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(a, b)
