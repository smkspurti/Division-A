import requests
import json

def fetch_github_trending(domain: str, max_repos: int = 5) -> list[dict]:
    """
    Fetch trending GitHub repositories related to the student's domain
    using the GitHub Search API (no auth required for basic use).
    Returns a list of repo dicts with name, description, stars, topics.
    """
    # Map broad domains to GitHub search keywords
    domain_keywords = {
        "AI/ML":          "machine learning deep learning",
        "Healthcare":     "healthcare medical AI",
        "Education":      "edtech learning platform",
        "Cyber Security": "cybersecurity security tool",
        "IoT":            "iot embedded sensors",
        "Finance":        "fintech finance analytics",
        "Agriculture":    "agriculture smart farming",
        "Environment":    "environment climate sustainability",
    }
    keyword = domain_keywords.get(domain, domain)

    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"{keyword} stars:>50",
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos,
    }
    headers = {"Accept": "application/vnd.github+json"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {
                "name":        r.get("full_name", ""),
                "description": r.get("description", "") or "",
                "stars":       r.get("stargazers_count", 0),
                "topics":      r.get("topics", []),
                "url":         r.get("html_url", ""),
                "language":    r.get("language", ""),
            }
            for r in items
        ]
    except Exception:
        return []


def format_github_context(repos: list[dict]) -> str:
    """
    Format repo list into a compact string to inject into the prompt.
    """
    if not repos:
        return ""
    lines = ["Trending GitHub repositories in this domain (for context):"]
    for r in repos:
        topics = ", ".join(r["topics"][:5]) if r["topics"] else r["language"]
        lines.append(f"- {r['name']} ⭐{r['stars']}: {r['description'][:120]} [{topics}]")
    return "\n".join(lines)
