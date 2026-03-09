"""
Input sanitization utilities for user-generated content.
Prevents XSS and injection attacks.
"""
import re
from html import escape
from typing import List, Optional

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


# Default allowed HTML tags for rich text content
DEFAULT_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'strike', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
]

# Default allowed attributes
DEFAULT_ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title', 'target'],
    'code': ['class'],
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(
    content: Optional[str],
    allowed_tags: Optional[List[str]] = None,
    allowed_attributes: Optional[dict] = None,
    strip: bool = True
) -> str:
    """
    Sanitize HTML content from users using bleach.
    
    Args:
        content: Raw HTML content
        allowed_tags: List of allowed HTML tags
        allowed_attributes: Dict of allowed attributes per tag
        strip: If True, remove disallowed tags; if False, escape them
        
    Returns:
        Sanitized HTML string
    """
    if not content:
        return ""
    
    if not isinstance(content, str):
        content = str(content)
    
    if BLEACH_AVAILABLE:
        return bleach.clean(
            content,
            tags=allowed_tags or DEFAULT_ALLOWED_TAGS,
            attributes=allowed_attributes or DEFAULT_ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=strip
        )
    else:
        # Fallback: strip all HTML tags
        return strip_html_tags(content)


def strip_html_tags(content: Optional[str]) -> str:
    """
    Remove all HTML tags from content.
    
    Args:
        content: Raw HTML content
        
    Returns:
        Plain text with tags removed
    """
    if not content:
        return ""
    
    # Remove script and style blocks first
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Decode common HTML entities
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&amp;', '&')
    content = content.replace('&quot;', '"')
    
    return content.strip()


def escape_html(text: Optional[str]) -> str:
    """
    Escape HTML special characters.
    
    Args:
        text: Raw text that might contain HTML
        
    Returns:
        Escaped text safe for HTML insertion
    """
    if not text:
        return ""
    return escape(str(text))


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent path traversal and invalid characters.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = filename.replace('\\', '/')
    filename = filename.split('/')[-1]
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) > 31)
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Limit length while preserving extension
    if len(filename) > max_length:
        name, ext = split_filename(filename)
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        filename = name[:max_name_length] + (f".{ext}" if ext else "")
    
    # Ensure not empty
    if not filename or filename == '.':
        filename = "unnamed"
    
    return filename


def split_filename(filename: str) -> tuple:
    """
    Split filename into name and extension.
    
    Args:
        filename: Filename to split
        
    Returns:
        Tuple of (name, extension_without_dot)
    """
    if '.' in filename:
        parts = filename.rsplit('.', 1)
        return parts[0], parts[1]
    return filename, ""


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID format
    """
    if not uuid_string:
        return False
    
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string.lower()))


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query input.
    Removes SQL-like special characters that could cause issues.
    
    Args:
        query: Raw search query
        
    Returns:
        Sanitized query
    """
    if not query:
        return ""
    
    # Remove SQL special characters
    # Keep alphanumeric, spaces, and basic punctuation
    query = re.sub(r'[%_\\]', '', query)
    
    # Limit length
    query = query[:200]
    
    return query.strip()
