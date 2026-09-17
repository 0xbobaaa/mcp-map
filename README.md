# the mcp map

Every MCP server on GitHub with 200+ stars, in one table: stars, licence, last commit,
category, and whether the repo lives in the org of the product it connects to.

**Site:** https://0xbobaaa.github.io/mcp-map/

- `collect.py` — pulls the GitHub search API and writes `data.json`
- `data.json` — the dataset (regenerated daily by GitHub Actions)
- `index.html` — the table, search and filters. No build step, no dependencies.

Missing a server, or a category is wrong? Open an issue or a PR editing `collect.py`.

Kept by [@0xbobaaa](https://x.com/0xbobaaa).
