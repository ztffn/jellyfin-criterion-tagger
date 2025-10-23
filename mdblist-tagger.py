#!/usr/bin/env python3
"""
Jellyfin MDblist Tagger

Tags Jellyfin movies whose titles match a provided list source.

Sources supported:
- Local JSON file (default)
- Remote URL returning JSON via --url (e.g., MDblist)

Basic usage:
  python3 mdblist-tagger.py

With URL source (e.g., MDblist):
  python3 mdblist-tagger.py --url https://example.com/list.json

Other options:
  --db-path PATH         Path to Jellyfin SQLite database
  --json PATH            Local JSON file with titles (default)
  --url URL              Remote URL returning JSON list of titles
  --min-similarity NUM   Similarity threshold 0.0-1.0 (default 0.90)
  --tag-name NAME        Tag to apply (repeatable; default "list")
  --yes                  Auto-confirm tagging (non-interactive)
  --dry-run              Show what would be tagged but do not write
  --api-key KEY          Append apikey query param and header for URL requests
  --bearer TOKEN         Authorization: Bearer TOKEN header for URL requests
  --http-header H:V      Additional HTTP header (repeatable)
  --items-field PATH     Dotted path to array within payload (optional)
  --title-field PATH     Dotted path to title within each item (optional)
  --year-field PATH      Dotted path to year/date within each item (optional)
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
import urllib.parse
from difflib import SequenceMatcher

DB_PATH = "/srv/media-server/jellyfin/config/data/library.db"
SOURCE_JSON = "example-list.json"

def normalize(title):
    title = re.sub(r'^(The|A|An)\s+', '', title, flags=re.IGNORECASE)
    return re.sub(r'[^\w\s]', '', title.lower()).strip()

def similarity(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tag Jellyfin movies whose titles match a provided list",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--json",
        dest="json_path",
        default=SOURCE_JSON,
        help="Local JSON file containing titles",
    )
    source.add_argument(
        "--url",
        dest="url",
        help="Remote URL returning JSON list of titles",
    )

    parser.add_argument(
        "--db-path",
        default=os.environ.get("JELLYFIN_DB_PATH", DB_PATH),
        help="Path to Jellyfin SQLite database file",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.90,
        help="Similarity threshold between 0.0 and 1.0",
    )
    parser.add_argument(
        "--tag-name",
        dest="tag_names",
        action="append",
        help="Tag to apply (repeat this flag to add multiple tags)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        dest="yes",
        action="store_true",
        help="Auto-confirm tagging without interactive prompt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show matches but do not write any changes",
    )

    # URL auth and headers (useful for MDblist and similar APIs)
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=os.environ.get("API_KEY"),
        help="API key for URL requests (adds apikey query param and header)",
    )
    parser.add_argument(
        "--bearer",
        dest="bearer_token",
        default=os.environ.get("BEARER_TOKEN"),
        help="Bearer token for URL requests (Authorization header)",
    )
    parser.add_argument(
        "--http-header",
        dest="http_headers",
        action="append",
        default=[],
        help="Extra HTTP header 'Key: Value' (repeatable)",
    )

    # Optional JSON mapping for arbitrary APIs (e.g., MDblist)
    parser.add_argument(
        "--items-field",
        dest="items_field",
        help="Dotted path to list of items within payload",
    )
    parser.add_argument(
        "--title-field",
        dest="title_field",
        help="Dotted path to title within each item",
    )
    parser.add_argument(
        "--year-field",
        dest="year_field",
        help="Dotted path to year/date within each item",
    )

    return parser.parse_args()


def _coerce_year(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_by_dotted(obj, path):
    if not path:
        return None
    cur = obj
    for part in path.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _parse_year_like(value):
    # Accept int, string year, or date-like strings (YYYY-MM-DD)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        s = value.strip()
        # Extract leading 4-digit year
        m = re.match(r"^(\d{4})", s)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return None
        try:
            return int(s)
        except ValueError:
            return None
    return None


def _extract_title_year(item, title_field=None, year_field=None):
    # If explicit fields provided, use them (support dotted paths)
    if title_field:
        t = _get_by_dotted(item, title_field)
    else:
        t = (
            item.get("title")
            or item.get("name")
            or item.get("Title")
            or item.get("Name")
        )

    if year_field:
        y_raw = _get_by_dotted(item, year_field)
    else:
        y_raw = (
            item.get("year")
            or item.get("release_year")
            or item.get("releaseYear")
            or item.get("Year")
            or item.get("released")
            or item.get("release_date")
            or item.get("date")
        )

    return t, _parse_year_like(y_raw)


def _parse_headers(header_list):
    headers = {}
    for entry in header_list or []:
        if not entry:
            continue
        if ":" not in entry:
            # skip invalid header format
            continue
        key, value = entry.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def _append_query_param(url, key, value):
    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        if key not in query:
            query[key] = [value]
        new_query = urllib.parse.urlencode(query, doseq=True)
        new_url = urllib.parse.urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )
        return new_url
    except Exception:
        return url


def load_list(json_path=None, url=None, api_key=None, bearer_token=None, extra_headers=None, items_field=None, title_field=None, year_field=None):
    # If URL provided, fetch from network
    if url:
        request_url = url
        headers = {"User-Agent": "Jellyfin-List-Tagger/1.1", "Accept": "application/json"}

        # Apply API key as query param if provided
        if api_key:
            request_url = _append_query_param(request_url, "apikey", api_key)
            headers.setdefault("apikey", api_key)

        # Apply bearer token header if provided
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        # Merge extra headers
        headers.update(_parse_headers(extra_headers))

        req = urllib.request.Request(request_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except urllib.error.URLError as e:
            print(f"Error fetching URL: {e}", file=sys.stderr)
            sys.exit(2)

        try:
            payload = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from URL: {e}", file=sys.stderr)
            sys.exit(2)

    else:
        path = json_path or SOURCE_JSON
        if not os.path.exists(path):
            print(f"JSON file not found: {path}", file=sys.stderr)
            sys.exit(2)
        with open(path, "r", encoding="utf-8") as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON file: {e}", file=sys.stderr)
                sys.exit(2)

    # Normalize to a list of {title, year}
    if isinstance(payload, dict):
        # Use explicit items_field if provided
        candidates = _get_by_dotted(payload, items_field) if items_field else None
        if candidates is None:
            # Try common wrappers
            for key in ("titles", "items", "data", "results"):
                if key in payload and isinstance(payload[key], list):
                    candidates = payload[key]
                    break
        if candidates is None:
            print("Unsupported JSON structure: missing list of titles", file=sys.stderr)
            sys.exit(2)
        items = candidates
    elif isinstance(payload, list):
        items = payload
    else:
        print("Unsupported JSON structure: expected list or object", file=sys.stderr)
        sys.exit(2)

    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title, year = _extract_title_year(item, title_field=title_field, year_field=year_field)
        if not title:
            continue
        result.append({"title": str(title), "year": _coerce_year(year)})
    return result

def get_jellyfin_movies(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT guid, Name, ProductionYear, Tags
        FROM TypedBaseItems
        WHERE type = 'MediaBrowser.Controller.Entities.Movies.Movie'
        """
    )
    return cursor.fetchall()

def main():
    args = parse_args()

    # Load list from chosen source
    source_list = load_list(
        json_path=args.json_path,
        url=args.url,
        api_key=args.api_key,
        bearer_token=args.bearer_token,
        extra_headers=args.http_headers,
        items_field=args.items_field,
        title_field=args.title_field,
        year_field=args.year_field,
    )

    # Build simple index by year to reduce comparisons
    by_year = {}
    for item in source_list:
        y = _coerce_year(item.get("year"))
        if y is None:
            # Titles without a year are grouped under None
            by_year.setdefault(None, []).append(item)
        else:
            by_year.setdefault(y, []).append(item)

    # Connect to Jellyfin
    conn = sqlite3.connect(args.db_path)
    try:
        rows = get_jellyfin_movies(conn)
        matches = []
        for guid, name, year, tags in rows:
            existing_tags = (tags or "")
            # Prepare tags to apply
            configured_tags = args.tag_names or [
                os.environ.get("DEFAULT_TAG_NAME")
                or os.environ.get("CRITERION_TAG_NAME")
                or "list"
            ]

            # Skip if all configured tags already present
            existing_lower = {t.strip().lower() for t in existing_tags.split("|") if t}
            if all(t.strip().lower() in existing_lower for t in configured_tags):
                continue

            norm = normalize(name)

            candidates = []
            if year in by_year:
                candidates.extend(by_year[year])
            # Also consider yearless entries
            if None in by_year:
                candidates.extend(by_year[None])

            found = False
            for c in candidates:
                if similarity(norm, normalize(c["title"])) >= args.min_similarity:
                    matches.append((guid, name, year, existing_tags))
                    found = True
                    break
            if found:
                continue

        if not matches:
            print("No new matches found")
            return

        # Show matches
        print(f"Found {len(matches)} movies:\n")
        for _, m_name, m_year, _ in matches:
            if m_year is None:
                print(f"  • {m_name}")
            else:
                print(f"  • {m_name} ({m_year})")

        if args.dry_run:
            print("\nDry run: no changes written")
            return

        if not args.yes:
            if input(f"\nTag these {len(matches)} movies? (yes/no): ").strip().lower() != "yes":
                print("Aborted")
                return

        cursor = conn.cursor()
        updated = 0
        configured_tags = args.tag_names or [
            os.environ.get("DEFAULT_TAG_NAME")
            or os.environ.get("CRITERION_TAG_NAME")
            or "list"
        ]
        configured_tags = [t.strip() for t in configured_tags if t and t.strip()]
        for guid, m_name, _m_year, existing_tags in matches:
            # Merge tags without duplicates (case-insensitive)
            existing_list = [t for t in existing_tags.split("|") if t]
            existing_lower = {t.lower() for t in existing_list}
            to_add = [t for t in configured_tags if t.lower() not in existing_lower]
            if to_add:
                new_tags = (existing_tags + ("|" if existing_tags else "") + "|".join(to_add)) if existing_tags else "|".join(to_add)
            else:
                new_tags = existing_tags
            cursor.execute(
                "UPDATE TypedBaseItems SET Tags = ? WHERE guid = ?",
                (new_tags, guid),
            )
            updated += 1
            print(f"  ✓ {m_name}")

        conn.commit()
        print(f"\n✓ Tagged {updated} movies")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
