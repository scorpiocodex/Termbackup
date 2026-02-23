import pytest
from hypothesis import given, settings, strategies as st
from termbackup.crypto import (
    generate_salt,
    derive_key,
    encrypt,
    decrypt,
    generate_recovery_phrase,
    derive_recovery_key,
    generate_signing_keypair,
    sign,
    verify,
    DecryptionError,
    SignatureError
)

@settings(max_examples=50, deadline=None)
@given(
    password=st.text(min_size=8, max_size=64),
    data=st.binary(min_size=1, max_size=1024)
)
def test_crypto_roundtrip(password: str, data: bytes):
    salt = generate_salt()
    key = derive_key(password, salt)
    
    encrypted = encrypt(data, key)
    assert encrypted != data
    
    decrypted = decrypt(encrypted, key)
    assert decrypted == data

def test_wrong_password_fails():
    salt = generate_salt()
    key1 = derive_key("correct_password", salt)
    key2 = derive_key("wrong_password", salt)
    
    data = b"secret_message"
    encrypted = encrypt(data, key1)
    
    with pytest.raises(DecryptionError):
        decrypt(encrypted, key2)

def test_recovery_phrase_generation():
    phrase = generate_recovery_phrase()
    words = phrase.split()
    assert len(words) == 24

def test_signing_verification():
    priv, pub = generate_signing_keypair()
    data = b"important_metadata"
    
    signature = sign(data, priv)
    assert verify(data, signature, pub) is True
    
    # Tampered data
    assert verify(b"tampered_data", signature, pub) is False
    
    # Tampered signature
    bad_sig = bytearray(signature)
    bad_sig[0] ^= 0xFF
    assert verify(data, bytes(bad_sig), pub) is False
