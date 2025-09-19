"""
Browser fingerprinting utilities for user recognition

This module provides functions to generate and normalize browser fingerprints
for identifying returning anonymous users.
"""

import hashlib
import json
from typing import Dict, Any, Optional


def normalize_fingerprint(raw_fingerprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and clean fingerprint data to improve matching accuracy

    Args:
        raw_fingerprint: Raw fingerprint data from browser

    Returns:
        Normalized fingerprint data
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

    # Fonts (if available)
    if 'fonts' in raw_fingerprint:
        # Sort fonts for consistent hashing
        normalized['fonts'] = sorted(raw_fingerprint['fonts'])

    # Plugins (if available)
    if 'plugins' in raw_fingerprint:
        # Sort plugins for consistent hashing
        normalized['plugins'] = sorted(raw_fingerprint['plugins'])

    return normalized


def generate_fingerprint(raw_fingerprint: Dict[str, Any]) -> str:
    """
    Generate a stable hash from normalized fingerprint data

    Args:
        raw_fingerprint: Raw fingerprint data from browser

    Returns:
        SHA256 hash of the normalized fingerprint
    """
    normalized = normalize_fingerprint(raw_fingerprint)

    # Convert to JSON string with sorted keys for consistent hashing
    fingerprint_string = json.dumps(normalized, sort_keys=True, separators=(',', ':'))

    # Generate SHA256 hash
    fingerprint_hash = hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()

    return fingerprint_hash


def calculate_fingerprint_strength(raw_fingerprint: Dict[str, Any]) -> int:
    """
    Calculate the strength/uniqueness of a fingerprint

    Args:
        raw_fingerprint: Raw fingerprint data from browser

    Returns:
        Strength score from 0-100 (higher = more unique)
    """
    score = 0
    components = 0

    # Basic browser info (10 points)
    if 'userAgent' in raw_fingerprint:
        score += 10
        components += 1

    # Language info (5 points)
    if 'language' in raw_fingerprint:
        score += 5
        components += 1

    # Screen resolution (15 points - highly identifying)
    if 'screenResolution' in raw_fingerprint:
        score += 15
        components += 1

    # Timezone (10 points - fairly identifying)
    if 'timezone' in raw_fingerprint:
        score += 10
        components += 1

    # Hardware info (10 points each)
    if 'hardwareConcurrency' in raw_fingerprint:
        score += 10
        components += 1

    if 'deviceMemory' in raw_fingerprint:
        score += 10
        components += 1

    # Canvas fingerprint (20 points - very identifying)
    if 'canvas' in raw_fingerprint:
        score += 20
        components += 1

    # WebGL info (15 points - fairly identifying)
    if 'webgl' in raw_fingerprint:
        score += 15
        components += 1

    # Fonts (10 points)
    if 'fonts' in raw_fingerprint:
        font_count = len(raw_fingerprint['fonts'])
        score += min(font_count // 10, 10)  # Up to 10 points based on font count
        components += 1

    # Plugins (5 points)
    if 'plugins' in raw_fingerprint:
        score += 5
        components += 1

    return min(score, 100)


def compare_fingerprints(fp1_hash: str, fp2_hash: str) -> float:
    """
    Compare two fingerprint hashes for similarity

    Args:
        fp1_hash: First fingerprint hash
        fp2_hash: Second fingerprint hash

    Returns:
        Similarity score from 0.0-1.0 (1.0 = identical)
    """
    if fp1_hash == fp2_hash:
        return 1.0

    # For hash-based fingerprints, they're either identical or completely different
    # In the future, we could implement fuzzy matching for more sophisticated comparison
    return 0.0


def extract_device_info(raw_fingerprint: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract device information from fingerprint data

    Args:
        raw_fingerprint: Raw fingerprint data from browser

    Returns:
        Dictionary with device information
    """
    device_info = {}

    user_agent = raw_fingerprint.get('userAgent', '')

    # Extract browser name and version
    if 'Chrome' in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'Safari' in user_agent:
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
    elif 'Linux' in user_agent:
        device_info['os'] = 'Linux'
    elif 'Android' in user_agent:
        device_info['os'] = 'Android'
    elif 'iOS' in user_agent:
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