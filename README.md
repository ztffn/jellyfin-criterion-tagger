# Jellyfin Criterion Collection Tagger

Automatically tag Criterion Collection movies in your Jellyfin library.

## What It Does

Scans your Jellyfin library and tags movies that are part of the Criterion Collection (1,669 titles). Uses fuzzy matching to handle title variations.

## Usage

```bash
# From bundled JSON (default)
python3 tag-criterion.py

# Or fetch from a remote URL (must return JSON)
python3 tag-criterion.py --url https://example.com/criterion.json

# Example: MDblist (requires API key)
# Docs: https://docs.mdblist.com/docs/api
# You can request a list endpoint and pass auth via headers or query params.
# Common patterns:
#  - As apikey query and header
python3 tag-criterion.py --url "https://mdblist.com/l/your_list_id" \
  --api-key "$MDBLIST_API_KEY" --dry-run

#  - As bearer token
python3 tag-criterion.py --url "https://mdblist.com/l/your_list_id" \
  --bearer "$MDBLIST_API_TOKEN" --dry-run

# Common options
python3 tag-criterion.py \
  --db-path /srv/media-server/jellyfin/config/data/library.db \
  --json criterion-collection.json \
  --min-similarity 0.92 \
  --tag-name criterion --tag-name mdblist \
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

By default the Criterion list is loaded from `criterion-collection.json`. You can:
- Provide a different file with `--json`
- Fetch from a URL with `--url` (expects an array of objects with `title` and `year`, or a wrapper like `{ "titles": [...] }`)

## How It Works

- Compares your movies against the complete Criterion Collection list
- Uses fuzzy title matching (default 0.90 similarity, configurable via `--min-similarity`)
- Matches on both title and year
- Safe to run multiple times (won't re-tag)
- Tags are stored directly in Jellyfin's database

## After Tagging

Use Jellyfin's built-in filters or create a SmartPlaylist:
- Filter by tag: "criterion"
- Or use SmartPlaylist plugin with rule: `Tags contains "criterion"`

## Files

- `tag-criterion.py` - Main script
- `criterion-collection.json` - Complete list of 1,669 Criterion titles (fallback if not using `--url`)

## License

MIT
