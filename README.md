# Jellyfin Criterion Collection Tagger

Automatically tag Criterion Collection movies in your Jellyfin library.

## What It Does

Scans your Jellyfin library and tags movies that are part of the Criterion Collection (1,669 titles). Uses fuzzy matching to handle title variations.

## Usage

```bash
python3 tag-criterion.py
```

The script will:
1. Find Criterion Collection movies in your library
2. Show you what it found
3. Ask for confirmation before tagging

## Requirements

- Python 3.7+
- Access to Jellyfin database file

## Configuration

Edit `DB_PATH` at the top of `tag-criterion.py` if your Jellyfin database is in a different location.

Default: `/srv/media-server/jellyfin/config/data/library.db`

## How It Works

- Compares your movies against the complete Criterion Collection list
- Uses fuzzy title matching (90% similarity threshold)
- Matches on both title and year
- Safe to run multiple times (won't re-tag)
- Tags are stored directly in Jellyfin's database

## After Tagging

Use Jellyfin's built-in filters or create a SmartPlaylist:
- Filter by tag: "criterion"
- Or use SmartPlaylist plugin with rule: `Tags contains "criterion"`

## Files

- `tag-criterion.py` - Main script
- `criterion-collection.json` - Complete list of 1,669 Criterion titles

## License

MIT
