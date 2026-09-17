"""Collect MCP server repos from the GitHub search API and write data.json.

Run: python collect.py   (needs `gh auth login`, uses `gh api`)
"""
import json, re, subprocess, datetime, sys

QUERIES = [
    "mcp-server in:name stars:>200",
    "mcp in:name stars:>500",
    "mcp-servers in:name stars:>200",
    '"model context protocol" in:description stars:>400',
]
NOISE = re.compile(r"mod coder pack|minecraft|mcpe|bedrock", re.I)
MCPISH = re.compile(r"model context protocol|mcp server|mcp-server|\bmcp\b", re.I)

# owner -> the vendor whose product this server exposes (official first-party servers)
OFFICIAL = {
    "github": "GitHub", "microsoft": "Microsoft", "ChromeDevTools": "Google Chrome", "googleapis": "Google",
    "awslabs": "AWS", "Azure": "Azure", "stripe": "Stripe", "supabase": "Supabase", "supabase-community": "Supabase",
    "makenotion": "Notion", "cloudflare": "Cloudflare", "grafana": "Grafana", "elastic": "Elastic",
    "mongodb-js": "MongoDB", "redis": "Redis", "neo4j-contrib": "Neo4j", "firecrawl": "Firecrawl",
    "mendableai": "Firecrawl", "upstash": "Upstash", "getsentry": "Sentry", "sentry": "Sentry",
    "PostHog": "PostHog", "hashicorp": "HashiCorp", "docker": "Docker", "gitlab-org": "GitLab",
    "atlassian": "Atlassian", "slackapi": "Slack", "linear": "Linear", "vercel": "Vercel", "netlify": "Netlify",
    "Shopify": "Shopify", "square": "Square", "paypal": "PayPal", "twilio-labs": "Twilio", "zapier": "Zapier",
    "apify": "Apify", "browserbase": "Browserbase", "e2b-dev": "E2B", "modelcontextprotocol": "MCP project",
    "anthropics": "Anthropic", "openai": "OpenAI", "Tencent": "Tencent", "alibaba": "Alibaba",
    "JetBrains": "JetBrains", "chroma-core": "Chroma", "qdrant": "Qdrant", "pinecone-io": "Pinecone",
    "weaviate": "Weaviate", "influxdata": "InfluxData", "clickhouse": "ClickHouse", "snowflakedb": "Snowflake",
    "databricks": "Databricks", "heroku": "Heroku", "render-examples": "Render", "railwayapp": "Railway",
    "hubspot": "HubSpot", "salesforce": "Salesforce", "intercom": "Intercom", "airtable": "Airtable",
    "asana": "Asana", "canva-public": "Canva", "figma": "Figma", "wix": "Wix", "webflow": "Webflow",
}
CATS = [
    ("spec & sdk", r"\bsdk\b|specification|modelcontextprotocol/(modelcontextprotocol|registry|inspector)|protocol schema"),
    ("lists & learning", r"awesome|curated|for-beginners|tutorial|course|collection of"),
    ("design & 3d", r"figma|blender|unity|godot|cad|3d|comfyui|image gen|video gen|canva|design"),
    ("browser & web", r"browser|playwright|puppeteer|chrome|scrape|crawl|web search|fetch url|website"),
    ("data & db", r"database|postgres|mysql|\bsql\b|mongo|redis|vector|duckdb|warehouse|clickhouse|snowflake|bigquery|neo4j|qdrant|chroma"),
    ("cloud & infra", r"aws|azure|\bgcp\b|kubernetes|docker|terraform|cloudflare|deploy|infra|devops|monitoring|grafana|sentry"),
    ("business apps", r"slack|gmail|email|calendar|\bcrm\b|hubspot|salesforce|stripe|payment|shopify|jira|linear|notion|sheet|excel|office|powerpoint|word|airtable|asana"),
    ("code & repos", r"github|gitlab|code|repo|\bide\b|jetbrains|editor|\blsp\b|refactor|review|xcode|unity"),
    ("desktop & os", r"desktop|windows|macos|computer use|filesystem|shell|terminal|apple|automation of"),
    ("memory & docs", r"memory|knowledge graph|\brag\b|embedding|recall|documentation|docs\b|obsidian"),
    ("frameworks & clients", r"framework|client|gateway|proxy|router|registry|inspector|use\b|build your own"),
    ("security & re", r"ghidra|ida pro|security|pentest|malware|reverse engineer|vulnerab"),
    ("social & messaging", r"whatsapp|telegram|discord|twitter|reddit|xiaohongshu|wechat|line bot|instagram"),
    ("mobile", r"mobile|android|ios app|appium|flutter"),
    ("science & research", r"zotero|research|paper|arxiv|bio|chem|dataset|analytics"),
]


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf8").stdout


def category(name, desc):
    blob = re.sub(r"model context protocol|\bmcp\b|mcp server|server for ai", " ", (name + " " + desc).lower())
    for cat, pat in CATS:
        if re.search(pat, blob):
            return cat
    return "other"


def main():
    seen = {}
    for q in QUERIES:
        for page in (1, 2):
            out = gh("api", "-X", "GET", "search/repositories", "-f", "q=" + q, "-f", "sort=stars",
                     "-f", "order=desc", "-f", "per_page=100", "-f", "page=%d" % page,
                     "--jq", ".items[] | {full_name, stars: .stargazers_count, pushed: .pushed_at[0:10], "
                             "license: (.license.spdx_id // \"none\"), desc: (.description // \"\"), "
                             "forks: .forks_count, url: .html_url}")
            for line in out.splitlines():
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if NOISE.search(r["desc"] + " " + r["full_name"]):
                    continue
                if not MCPISH.search(r["desc"] + " " + r["full_name"]):
                    continue
                seen[r["full_name"]] = r
    rows = []
    for r in seen.values():
        owner, name = r["full_name"].split("/")
        r["owner"] = owner
        r["name"] = name
        r["vendor"] = OFFICIAL.get(owner, "")
        r["official"] = bool(r["vendor"])
        r["cat"] = category(name, r["desc"])
        rows.append(r)
    rows.sort(key=lambda r: -r["stars"])
    data = {"updated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "count": len(rows), "stars": sum(r["stars"] for r in rows), "rows": rows}
    with open("data.json", "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("repos", len(rows), "stars", data["stars"], "official", sum(1 for r in rows if r["official"]))


if __name__ == "__main__":
    main()
