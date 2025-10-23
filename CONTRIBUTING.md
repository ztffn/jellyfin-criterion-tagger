# Contributing to Jellyfin MDblist Tagger

# Contributing

We welcome improvements that make the tagger more flexible and reliable with list sources like MDblist.

## Example list file

If you want to use a local list file, keep it simple:

```json
[
  {"title": "Seven Samurai", "year": 1954},
  {"title": "The Red Shoes", "year": 1948}
]
```

Validate JSON:

```bash
python3 -c "import json; json.load(open('example-list.json'))"
```

## Reporting Issues

- **False matches**: Script tagged wrong movie
- **Missing matches**: Film in list not detected
- **Update needed**: New list mapping or field support

Open an issue with movie title and year.

## Improving Matching

The fuzzy matching threshold is currently 90% similarity. If you're getting false positives or missing real matches, suggest threshold adjustments or provide examples.

## Other Contributions

- Additional curated lists (AFI Top 100, Sight & Sound, etc.)
- Support for TV shows (MDblist `shows` array)
- Better error handling
- Installation improvements

All contributions welcome!
