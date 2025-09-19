"""
Enhanced fingerprinting utilities that work with existing schema

These utilities enhance the existing browser_fingerprint field in UserDB
with better algorithms while maintaining backwards compatibility.
"""

import hashlib
import json
from typing import Dict, Any, Optional


def normalize_fingerprint_data(raw_fingerprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize fingerprint data for consistent hashing

    Compatible with existing browser_fingerprint field structure
    """
    normalized = {}

    # Browser information
    if 'userAgent' in raw_fingerprint:
        normalized['user_agent'] = raw_fingerprint['userAgent']

    if 'language' in raw_fingerprint:
        normalized['language'] = raw_fingerprint['language']

    if 'languages' in raw_fingerprint:
        normalized['languages'] = sorted(raw_fingerprint['languages'])

    # Screen information (rounded for privacy)
    if 'screenResolution' in raw_fingerprint:
        width, height = raw_fingerprint['screenResolution']
        # Round to nearest 100 for privacy
        normalized['screen_width'] = round(width / 100) * 100
        normalized['screen_height'] = round(height / 100) * 100

    if 'colorDepth' in raw_fingerprint:
        normalized['color_depth'] = raw_fingerprint['colorDepth']

    if 'pixelRatio' in raw_fingerprint:
        # Round to 1 decimal place
        normalized['pixel_ratio'] = round(raw_fingerprint['pixelRatio'], 1)

    # Timezone
    if 'timezone' in raw_fingerprint:
        normalized['timezone'] = raw_fingerprint['timezone']

    # Platform information
    if 'platform' in raw_fingerprint:
        normalized['platform'] = raw_fingerprint['platform']

    # Hardware information (if available)
    if 'hardwareConcurrency' in raw_fingerprint:
        normalized['cpu_cores'] = raw_fingerprint['hardwareConcurrency']

    if 'deviceMemory' in raw_fingerprint:
        normalized['device_memory'] = raw_fingerprint['deviceMemory']

    # Canvas fingerprint (if available)
    if 'canvas' in raw_fingerprint:
        normalized['canvas'] = raw_fingerprint['canvas']

    # WebGL information (if available)
    if 'webgl' in raw_fingerprint:
        webgl = raw_fingerprint['webgl']
        if isinstance(webgl, dict):
            normalized['webgl_vendor'] = webgl.get('vendor', '')
            normalized['webgl_renderer'] = webgl.get('renderer', '')

    return normalized


def generate_enhanced_fingerprint(raw_fingerprint: Dict[str, Any]) -> str:
    """
    Generate enhanced browser fingerprint hash

    Works with existing browser_fingerprint field in UserDB
    """
    normalized = normalize_fingerprint_data(raw_fingerprint)

    # Convert to JSON string with sorted keys for consistent hashing
    fingerprint_string = json.dumps(normalized, sort_keys=True, separators=(',', ':'))

    # Generate SHA256 hash (compatible with existing field)
    fingerprint_hash = hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()

    return fingerprint_hash


def calculate_fingerprint_confidence(raw_fingerprint: Dict[str, Any]) -> int:
    """
    Calculate fingerprint confidence score (0-100)

    Higher score = more unique and reliable for user recognition
    """
    score = 0

    # Basic browser info (10 points)
    if 'userAgent' in raw_fingerprint:
        score += 10

    # Language info (5 points)
    if 'language' in raw_fingerprint:
        score += 5

    # Screen resolution (15 points - highly identifying)
    if 'screenResolution' in raw_fingerprint:
        score += 15

    # Timezone (10 points - fairly identifying)
    if 'timezone' in raw_fingerprint:
        score += 10

    # Hardware info (10 points each)
    if 'hardwareConcurrency' in raw_fingerprint:
        score += 10

    if 'deviceMemory' in raw_fingerprint:
        score += 10

    # Canvas fingerprint (20 points - very identifying)
    if 'canvas' in raw_fingerprint:
        score += 20

    # WebGL info (15 points - fairly identifying)
    if 'webgl' in raw_fingerprint:
        score += 15

    # Fonts (up to 10 points based on count)
    if 'fonts' in raw_fingerprint:
        font_count = len(raw_fingerprint['fonts'])
        score += min(font_count // 10, 10)

    return min(score, 100)


def extract_device_info_from_fingerprint(raw_fingerprint: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract device information from fingerprint data

    Returns structured device info for analytics
    """
    device_info = {}

    user_agent = raw_fingerprint.get('userAgent', '')

    # Extract browser name
    if 'Chrome' in user_agent and 'Edge' not in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        device_info['browser'] = 'Safari'
    elif 'Edge' in user_agent:
        device_info['browser'] = 'Edge'
    else:
        device_info['browser'] = 'Unknown'

    # Extract OS
    if 'Windows' in user_agent:
        device_info['os'] = 'Windows'
    elif 'Mac OS' in user_agent or 'macOS' in user_agent:
        device_info['os'] = 'macOS'
    elif 'Linux' in user_agent and 'Android' not in user_agent:
        device_info['os'] = 'Linux'
    elif 'Android' in user_agent:
        device_info['os'] = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        device_info['os'] = 'iOS'
    else:
        device_info['os'] = 'Unknown'

    # Determine device type
    if 'Mobile' in user_agent or 'Android' in user_agent:
        device_info['device_type'] = 'mobile'
    elif 'Tablet' in user_agent or 'iPad' in user_agent:
        device_info['device_type'] = 'tablet'
    else:
        device_info['device_type'] = 'desktop'

    # Extract screen resolution
    if 'screenResolution' in raw_fingerprint:
        width, height = raw_fingerprint['screenResolution']
        device_info['screen_resolution'] = f"{width}x{height}"

    # Extract timezone
    if 'timezone' in raw_fingerprint:
        device_info['timezone'] = raw_fingerprint['timezone']

    # Extract language
    if 'language' in raw_fingerprint:
        device_info['language'] = raw_fingerprint['language']

    return device_info


def is_fingerprint_match(fingerprint1: str, fingerprint2: str) -> bool:
    """
    Check if two fingerprints match

    Args:
        fingerprint1: First fingerprint hash
        fingerprint2: Second fingerprint hash

    Returns:
        True if fingerprints match, False otherwise
    """
    if not fingerprint1 or not fingerprint2:
        return False

    return fingerprint1 == fingerprint2


def should_recognize_user(fingerprint_confidence: int, min_confidence: int = 60) -> bool:
    """
    Determine if fingerprint is reliable enough for user recognition

    Args:
        fingerprint_confidence: Confidence score (0-100)
        min_confidence: Minimum confidence threshold

    Returns:
        True if fingerprint is reliable enough for recognition
    """
    return fingerprint_confidence >= min_confidence