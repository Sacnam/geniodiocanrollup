"""
Utility functions for generating share tokens.
"""
import secrets
import string


def generate_share_token(length: int = 32) -> str:
    """Generate a cryptographically secure share token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
