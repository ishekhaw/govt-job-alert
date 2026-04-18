from urllib.parse import urljoin
import re
from datetime import datetime, timedelta


def normalize_whitespace(value):
    return " ".join((value or "").split())


def extract_listing_description(link, title):
    title = normalize_whitespace(title)
    candidates = []

    for attr in ("title", "aria-label"):
        value = normalize_whitespace(link.get_attribute(attr))
        if value and value != title:
            candidates.append(value)

    current = link

    for _ in range(4):
        if current is None:
            break

        text = normalize_whitespace(current.text_content())

        if text:
            cleaned = text.replace(title, " ").strip(" -|:")
            cleaned = normalize_whitespace(cleaned)

            if cleaned and cleaned != title:
                candidates.append(cleaned)

        current = current.evaluate_handle("node => node.parentElement").as_element()

    for candidate in candidates:
        if 24 <= len(candidate) <= 320:
            return candidate

    return title


def absolute_link(base_url, href):
    return urljoin(base_url, href or "")


def matches_keywords(text, keywords):
    lowered = normalize_whitespace(text).lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def extract_date(text):
    """Extract date from text using common patterns."""
    patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',  # YYYY/MM/DD
        r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b',  # DD Month YYYY
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',  # Month DD, YYYY
    ]
    
    months = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                try:
                    if pattern == patterns[0]:  # DD/MM/YYYY
                        day, month, year = map(int, groups)
                    elif pattern == patterns[1]:  # YYYY/MM/DD
                        year, month, day = map(int, groups)
                    elif pattern == patterns[2]:  # DD Month YYYY
                        day = int(groups[0])
                        month = months[groups[1].capitalize()]
                        year = int(groups[2])
                    elif pattern == patterns[3]:  # Month DD, YYYY
                        month = months[groups[0].capitalize()]
                        day = int(groups[1])
                        year = int(groups[2])
                    
                    return datetime(year, month, day)
                except ValueError:
                    continue
    return None


def is_within_last_month(date):
    """Check if the date is within the last month from today."""
    if not date:
        return False
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)  # Approximate last month
    return date >= one_month_ago
