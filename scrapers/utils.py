from urllib.parse import urljoin


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
