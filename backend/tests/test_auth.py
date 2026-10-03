"""Tests for authentication"""
import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing():
    """Test password hashing and verification"""
    password = "test_password_123"
    hashed = hash_password(password)
    
    # Hash should not equal plain password
    assert hashed != password
    
    # Verification should succeed
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_creation_and_decoding():
    """Test JWT token creation and decoding"""
    user_id = 123
    # sub must be a string per JWT spec (python-jose enforces this)
    token = create_access_token(data={"sub": str(user_id)})
    
    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode token
    payload = decode_access_token(token)
    
    # Should contain user ID as a string
    assert payload is not None
    assert payload.get("sub") == str(user_id)  # sub is always a string in JWT
    assert "exp" in payload


def test_invalid_token_decoding():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    payload = decode_access_token(invalid_token)
    
    # Should return None for invalid token
    assert payload is None


def test_different_passwords_produce_different_hashes():
    """Test that different passwords produce different hashes"""
    password1 = "password1"
    password2 = "password2"
    
    hash1 = hash_password(password1)
    hash2 = hash_password(password2)
    
    assert hash1 != hash2


def test_same_password_produces_different_hashes():
    """Test that hashing the same password twice produces different hashes (salt)"""
    password = "test_password"
    
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Hashes should be different due to salt
    assert hash1 != hash2
    
    # Both should verify successfully
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
