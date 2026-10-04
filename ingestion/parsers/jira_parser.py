"""Fetch JIRA tickets via REST API and yield text chunks."""
import json
import os
from pathlib import Path
from typing import Iterator

import requests
from loguru import logger


def _get_client() -> tuple[str, tuple[str, str]]:
    base = os.environ["JIRA_BASE_URL"].rstrip("/")
    auth = (os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
    return base, auth


def fetch_and_cache(jql: str, cache_dir: Path, max_results: int = 500) -> list[dict]:
    """Fetch all tickets matching JQL, cache as JSON, return list of issue dicts."""
    base, auth = _get_client()
    cache_dir.mkdir(parents=True, exist_ok=True)

    issues = []
    start_at = 0
    batch = 100

    while True:
        resp = requests.get(
            f"{base}/rest/api/3/search",
            auth=auth,
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": batch,
                "fields": "summary,description,issuetype,status,priority,labels,"
                          "assignee,reporter,comment,created,updated,project,fixVersions",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        batch_issues = data.get("issues", [])
        issues.extend(batch_issues)
        logger.info(f"JIRA fetch: {len(issues)}/{data['total']} tickets")

        if len(issues) >= data["total"] or len(issues) >= max_results or not batch_issues:
            break
        start_at += batch

    cache_file = cache_dir / "jira_cache.json"
    cache_file.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    logger.info(f"Cached {len(issues)} JIRA tickets to {cache_file}")
    return issues


def parse_from_cache(cache_dir: Path) -> Iterator[dict]:
    """Parse cached JIRA JSON into chunks."""
    cache_file = cache_dir / "jira_cache.json"
    if not cache_file.exists():
        logger.warning("No JIRA cache found. Run fetch first.")
        return

    issues = json.loads(cache_file.read_text(encoding="utf-8"))
    for issue in issues:
        yield from _issue_to_chunks(issue)


def parse_live(jql: str, cache_dir: Path, max_results: int = 500) -> Iterator[dict]:
    """Fetch live then parse."""
    issues = fetch_and_cache(jql, cache_dir, max_results)
    for issue in issues:
        yield from _issue_to_chunks(issue)


def _issue_to_chunks(issue: dict) -> Iterator[dict]:
    fields = issue.get("fields", {})
    key = issue.get("key", "UNKNOWN")
    project = fields.get("project", {}).get("key", "")
    base_meta = {
        "source_file": f"jira://{key}",
        "source_type": "jira",
        "jira_key": key,
        "jira_project": project,
        "jira_type": fields.get("issuetype", {}).get("name", ""),
        "jira_status": fields.get("status", {}).get("name", ""),
        "jira_priority": (fields.get("priority") or {}).get("name", ""),
        "labels": fields.get("labels", []),
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
    }

    # Main ticket chunk: title + description
    summary = fields.get("summary", "")
    desc_raw = fields.get("description") or {}
    description = _extract_adf_text(desc_raw) if isinstance(desc_raw, dict) else str(desc_raw)
    main_text = f"[{key}] {summary}\n\n{description}".strip()

    yield {"text": main_text, "metadata": {**base_meta, "chunk_part": "main"}}

    # Comments as separate chunks
    comments = (fields.get("comment") or {}).get("comments", [])
    for ci, comment in enumerate(comments):
        body_raw = comment.get("body", {})
        body = _extract_adf_text(body_raw) if isinstance(body_raw, dict) else str(body_raw)
        author = (comment.get("author") or {}).get("displayName", "")
        comment_text = f"[{key}] Comment by {author}:\n{body}".strip()
        if comment_text:
            yield {
                "text": comment_text,
                "metadata": {**base_meta, "chunk_part": f"comment_{ci}"},
            }


def _extract_adf_text(node: dict) -> str:
    """Recursively extract plain text from Atlassian Document Format."""
    if not isinstance(node, dict):
        return str(node)
    parts = []
    if node.get("type") == "text":
        parts.append(node.get("text", ""))
    for child in node.get("content", []):
        parts.append(_extract_adf_text(child))
    return " ".join(p for p in parts if p).strip()
