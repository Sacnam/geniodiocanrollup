import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import feedparser
import requests


async def validate_feed(url: str) -> Optional[Dict]:
    """Validate RSS/Atom feed URL."""
    try:
        headers = {
            "User-Agent": "GenioBot/1.0 (Feed Validator)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml",
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # Try to parse
        parsed = feedparser.parse(response.content)
        
        if not parsed.entries and not parsed.feed:
            return None
        
        return {
            "title": parsed.feed.get("title"),
            "description": parsed.feed.get("description"),
            "link": parsed.feed.get("link"),
            "is_valid": True,
        }
        
    except Exception:
        return None


def parse_opml(content: str) -> List[Dict]:
    """Parse OPML file and extract feed URLs."""
    feeds = []
    
    try:
        root = ET.fromstring(content)
        
        # Find all outline elements with xmlUrl
        for outline in root.iter("outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                feeds.append({
                    "title": outline.get("text", outline.get("title", "")),
                    "xmlUrl": xml_url,
                    "htmlUrl": outline.get("htmlUrl", ""),
                    "category": outline.get("category", ""),
                })
    except ET.ParseError:
        pass
    
    return feeds
