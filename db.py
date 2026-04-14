import json
import sqlite3
from pathlib import Path
from urllib.parse import urljoin

DB_PATH = Path("jobs.db")
EXPORT_PATH = Path("jobs-data.js")
SOURCE_BASE_URLS = {
    "SSC": "https://ssc.nic.in/",
    "IBPS": "https://www.ibps.in/",
    "RRB": "https://www.rrbcdg.gov.in/",
    "UPSC": "https://upsc.gov.in/",
    "KVS": "https://kvsangathan.nic.in/",
    "NTA": "https://nta.ac.in/",
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT UNIQUE,
        source TEXT,
        description TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)

conn.commit()

existing_columns = {
    row["name"] for row in cursor.execute("PRAGMA table_info(jobs)").fetchall()
}

if "description" not in existing_columns:
    cursor.execute("ALTER TABLE jobs ADD COLUMN description TEXT")
    conn.commit()


def normalize_link(link, source):
    if not link:
        return ""

    if link.startswith(("http://", "https://")):
        return link

    return urljoin(SOURCE_BASE_URLS.get(source, ""), link)


def normalize_existing_links():
    rows = cursor.execute(
        "SELECT id, title, link, source, description, scraped_at FROM jobs ORDER BY id ASC"
    ).fetchall()

    for row in rows:
        normalized_link = normalize_link(row["link"], row["source"])

        if not normalized_link or normalized_link == row["link"]:
            continue

        duplicate = cursor.execute(
            "SELECT id FROM jobs WHERE link = ? AND id != ?",
            (normalized_link, row["id"]),
        ).fetchone()

        if duplicate:
            cursor.execute(
                """
                UPDATE jobs
                SET title = COALESCE(NULLIF(title, ''), ?),
                    source = COALESCE(NULLIF(source, ''), ?),
                    description = COALESCE(NULLIF(description, ''), ?),
                    scraped_at = MAX(scraped_at, ?)
                WHERE id = ?
                """,
                (
                    row["title"],
                    row["source"],
                    row["description"],
                    row["scraped_at"],
                    duplicate["id"],
                ),
            )
            cursor.execute("DELETE FROM jobs WHERE id = ?", (row["id"],))
        else:
            cursor.execute(
                "UPDATE jobs SET link = ? WHERE id = ?",
                (normalized_link, row["id"]),
            )

    conn.commit()


normalize_existing_links()


def build_job_record(row):
    title = " ".join((row["title"] or "").split())
    link = normalize_link(row["link"], row["source"])
    lower_text = f"{title} {link}".lower()
    has_pdf = ".pdf" in lower_text
    description = " ".join((row["description"] or "").split())

    if not description:
        description = title

    return {
        "id": row["id"],
        "title": title,
        "source": row["source"],
        "link": link,
        "type": "PDF Notice" if has_pdf else "Official Update",
        "tag": (row["source"] or "other").lower(),
        "scope": row["source"],
        "pdf": has_pdf,
        "description": description,
        "publishedLabel": f"Updated {row['scraped_at'][:10]}",
        "scrapedAt": row["scraped_at"],
    }


def save_job(title, link, source, description=""):
    cleaned_title = " ".join((title or "").split())
    cleaned_link = (link or "").strip()
    cleaned_description = " ".join((description or "").split())

    if not cleaned_title or not cleaned_link or not source:
        return

    cursor.execute(
        """
        INSERT INTO jobs (title, link, source, description)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(link) DO UPDATE SET
            title = excluded.title,
            source = excluded.source,
            description = CASE
                WHEN excluded.description IS NOT NULL AND excluded.description != ''
                    THEN excluded.description
                ELSE jobs.description
            END,
            scraped_at = CURRENT_TIMESTAMP
        """,
        (cleaned_title, cleaned_link, source, cleaned_description),
    )
    conn.commit()


def fetch_jobs(limit=None):
    query = (
        "SELECT id, title, link, source, description, scraped_at "
        "FROM jobs ORDER BY scraped_at DESC, id DESC"
    )
    params = []

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    rows = cursor.execute(query, params).fetchall()
    return [build_job_record(row) for row in rows]


def build_export_payload():
    jobs = fetch_jobs()
    source_counts = cursor.execute(
        """
        SELECT source, COUNT(*) AS total
        FROM jobs
        GROUP BY source
        ORDER BY total DESC, source ASC
        """
    ).fetchall()

    latest_scrape = cursor.execute(
        "SELECT MAX(scraped_at) FROM jobs"
    ).fetchone()[0]

    payload = {
        "generatedAt": latest_scrape,
        "totalJobs": len(jobs),
        "sourceCounts": [
            {"source": row["source"], "count": row["total"]}
            for row in source_counts
        ],
        "featuredJob": jobs[0] if jobs else None,
        "resourceJobs": [job for job in jobs if job["pdf"]][:6],
        "jobs": jobs,
    }

    return payload


def export_jobs_data():
    payload = build_export_payload()
    export_text = "window.__JOB_DATA__ = " + json.dumps(payload, indent=2) + ";\n"
    EXPORT_PATH.write_text(export_text, encoding="utf-8")
    return EXPORT_PATH
