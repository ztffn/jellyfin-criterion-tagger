# Jellyfin MDblist Tagger

Automatically tag Jellyfin movies that appear in a provided list (local JSON or remote API like MDblist).

## What It Does

Scans your Jellyfin library and tags any movies that match your source list. Uses fuzzy matching to handle title variations.

## Usage

```bash
# From bundled JSON (default)
python3 mdblist-tagger.py

# Or fetch from a remote URL (must return JSON)
python3 mdblist-tagger.py --url https://example.com/list.json

# Example: MDblist (requires API key)
# Docs: https://mdblist.docs.apiary.io/
# You can request a list endpoint and pass auth via headers or query params.
# Common patterns:
#  - As apikey query and header
python3 mdblist-tagger.py --url "https://api.mdblist.com/lists/<user>/<slug>/items" \
  --api-key "$MDBLIST_API_KEY" --dry-run

#  - As bearer token
python3 mdblist-tagger.py --url "https://api.mdblist.com/lists/<user>/<slug>/items" \
  --bearer "$MDBLIST_API_TOKEN" --dry-run

# If the API returns a wrapped structure, map fields explicitly:
python3 mdblist-tagger.py --url "https://api.example.com/list" \
  --items-field data.items --title-field title --year-field year --dry-run

# Common options
python3 mdblist-tagger.py \
  --db-path /srv/media-server/jellyfin/config/data/library.db \
  --json example-list.json \
  --min-similarity 0.92 \
  --tag-name list --tag-name mdblist \
  --yes            # auto-confirm
```

The script will:
1. Find Criterion Collection movies in your library
2. Show you what it found
3. Ask for confirmation before tagging

## Requirements

- Python 3.7+
- Access to Jellyfin database file

## Configuration

You can supply the database path via `--db-path` or env var `JELLYFIN_DB_PATH`.
Default: `/srv/media-server/jellyfin/config/data/library.db`.

By default a local JSON file is used (`example-list.json`). You can:
- Provide a different file with `--json`
- Fetch from a URL with `--url`
- Map fields with `--items-field`, `--title-field`, `--year-field` when the JSON shape differs

## How It Works

- Compares your movies against the provided source list
- Uses fuzzy title matching (default 0.90 similarity, configurable via `--min-similarity`)
- Matches on both title and year
- Safe to run multiple times (won't re-tag)
- Tags are stored directly in Jellyfin's database

## After Tagging

Use Jellyfin's built-in filters or create a SmartPlaylist:
- Filter by your chosen tag(s)
- Or use SmartPlaylist plugin with rule: `Tags contains "criterion"`

## Files

- `mdblist-tagger.py` - Main script
- `example-list.json` - Example list file (fallback if not using `--url`)

## License

MIT
