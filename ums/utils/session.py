"""
Session management utilities for the User Management Services

This module provides functions for session token generation, validation,
and management across anonymous and returning users.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid


def generate_session_id() -> str:
    """
    Generate a unique session identifier

    Returns:
        Unique session ID string
    """
    return str(uuid.uuid4())


def generate_session_token() -> str:
    """
    Generate a secure session token

    Returns:
        Cryptographically secure session token
    """
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """
    Hash a session token for storage

    Args:
        token: Raw session token

    Returns:
        Hashed token for secure storage
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def validate_session(session_token: str, stored_hash: str) -> bool:
    """
    Validate a session token against stored hash

    Args:
        session_token: Token to validate
        stored_hash: Stored hash to compare against

    Returns:
        True if token is valid, False otherwise
    """
    token_hash = hash_session_token(session_token)
    return secrets.compare_digest(token_hash, stored_hash)


def calculate_session_expiry(duration_hours: int = 24) -> datetime:
    """
    Calculate session expiry time

    Args:
        duration_hours: Session duration in hours (default: 24)

    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(hours=duration_hours)


def is_session_expired(expires_at: Optional[datetime]) -> bool:
    """
    Check if a session has expired

    Args:
        expires_at: Session expiry time

    Returns:
        True if session is expired, False otherwise
    """
    if expires_at is None:
        return False

    return datetime.utcnow() > expires_at


def calculate_session_duration(started_at: datetime, ended_at: Optional[datetime] = None) -> int:
    """
    Calculate session duration in seconds

    Args:
        started_at: Session start time
        ended_at: Session end time (default: now)

    Returns:
        Session duration in seconds
    """
    if ended_at is None:
        ended_at = datetime.utcnow()

    delta = ended_at - started_at
    return int(delta.total_seconds())


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Parse user agent string to extract browser and OS information

    Args:
        user_agent: Browser user agent string

    Returns:
        Dictionary with browser and OS information
    """
    info = {
        'browser': 'Unknown',
        'browser_version': 'Unknown',
        'os': 'Unknown',
        'device_type': 'Unknown'
    }

    if not user_agent:
        return info

    user_agent = user_agent.lower()

    # Browser detection
    if 'chrome' in user_agent and 'edg' not in user_agent:
        info['browser'] = 'Chrome'
    elif 'firefox' in user_agent:
        info['browser'] = 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        info['browser'] = 'Safari'
    elif 'edg' in user_agent:
        info['browser'] = 'Edge'
    elif 'opera' in user_agent:
        info['browser'] = 'Opera'

    # OS detection
    if 'windows' in user_agent:
        info['os'] = 'Windows'
    elif 'macintosh' in user_agent or 'mac os' in user_agent:
        info['os'] = 'macOS'
    elif 'linux' in user_agent and 'android' not in user_agent:
        info['os'] = 'Linux'
    elif 'android' in user_agent:
        info['os'] = 'Android'
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        info['os'] = 'iOS'

    # Device type detection
    if 'mobile' in user_agent or 'android' in user_agent:
        info['device_type'] = 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        info['device_type'] = 'tablet'
    else:
        info['device_type'] = 'desktop'

    return info


def extract_ip_info(ip_address: str) -> Dict[str, str]:
    """
    Extract basic information from IP address

    Args:
        ip_address: Client IP address

    Returns:
        Dictionary with IP information
    """
    info = {
        'ip': ip_address,
        'type': 'Unknown',
        'is_private': False
    }

    if not ip_address:
        return info

    # Check for private IP ranges
    if (ip_address.startswith('192.168.') or
        ip_address.startswith('10.') or
        ip_address.startswith('172.') or
        ip_address == '127.0.0.1' or
        ip_address == 'localhost'):
        info['is_private'] = True
        info['type'] = 'Private'
    else:
        info['type'] = 'Public'

    # Check for IPv6
    if ':' in ip_address:
        info['version'] = 'IPv6'
    else:
        info['version'] = 'IPv4'

    return info


def generate_device_signature(user_agent: str, ip_address: str, additional_data: Optional[Dict] = None) -> str:
    """
    Generate a device signature for session validation

    Args:
        user_agent: Browser user agent string
        ip_address: Client IP address
        additional_data: Additional data for signature generation

    Returns:
        Device signature hash
    """
    signature_data = {
        'user_agent': user_agent,
        'ip_network': '.'.join(ip_address.split('.')[:3]) + '.0' if ip_address else '',  # IP subnet for stability
    }

    if additional_data:
        signature_data.update(additional_data)

    # Create signature string
    signature_string = '|'.join(f"{k}:{v}" for k, v in sorted(signature_data.items()))

    # Generate hash
    return hashlib.sha256(signature_string.encode('utf-8')).hexdigest()


def validate_device_signature(current_signature: str, stored_signature: str, tolerance: float = 0.8) -> bool:
    """
    Validate device signature with tolerance for minor changes

    Args:
        current_signature: Current device signature
        stored_signature: Stored device signature
        tolerance: Tolerance level (0.0-1.0, higher = more tolerant)

    Returns:
        True if signatures match within tolerance, False otherwise
    """
    if current_signature == stored_signature:
        return True

    # For now, we use exact matching
    # In the future, we could implement fuzzy matching for more sophisticated validation
    return False


def cleanup_expired_sessions(session_expiry_hours: int = 24) -> Dict[str, Any]:
    """
    Helper function to identify criteria for cleaning up expired sessions

    Args:
        session_expiry_hours: Hours after which sessions expire

    Returns:
        Dictionary with cleanup criteria
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=session_expiry_hours)

    return {
        'cutoff_time': cutoff_time,
        'conditions': {
            'last_activity_before': cutoff_time,
            'is_active': False
        }
    }