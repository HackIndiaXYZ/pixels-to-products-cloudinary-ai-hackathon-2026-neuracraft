"""Pytest configuration and fixtures"""
import pytest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "test_password_123"
    }


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "name": "Test Analysis",
        "description": "A test analysis for unit testing"
    }
