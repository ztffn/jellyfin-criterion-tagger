# Contributing to Jellyfin Criterion Tagger

## Updating the Criterion Collection List

The Criterion Collection adds ~2 new titles per month. To keep the list current:

### Adding New Titles

1. Check for new releases at: https://www.criterion.com/shop/browse/list
2. Edit `criterion-collection.json`
3. Add entries in alphabetical order:

```json
{
  "title": "Movie Title",
  "year": 2024,
  "slug": "movie-title"
}
```

4. Submit a pull request

### JSON Format

- **title**: Official Criterion title (as shown on their site)
- **year**: Release year of the film (not Criterion release year)
- **slug**: Lowercase, hyphenated version of title (used for reference)

### Example

```json
{
  "title": "The New Movie",
  "year": 2024,
  "slug": "the-new-movie"
}
```

### Validation

After editing, verify the JSON is valid:
```bash
python3 -c "import json; json.load(open('criterion-collection.json'))"
```

## Reporting Issues

- **False matches**: Script tagged wrong movie
- **Missing matches**: Criterion film not detected
- **Update needed**: New Criterion releases to add

Open an issue with movie title and year.

## Improving Matching

The fuzzy matching threshold is currently 90% similarity. If you're getting false positives or missing real matches, suggest threshold adjustments.

## Other Contributions

- Additional curated lists (AFI Top 100, Sight & Sound, etc.)
- Support for TV shows
- Better error handling
- Installation improvements

All contributions welcome!
