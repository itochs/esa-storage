import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

# Default to the current working directory so CLI commands write next to where
# they are executed instead of inside the installed package location.
BASE_DIR = Path.cwd()
POSTS_ROOT = BASE_DIR / "posts"
IMAGES_ROOT = BASE_DIR / "images"
RESPONCE_ROOT = BASE_DIR / "responce"
LAST_SYNC_FILE = RESPONCE_ROOT / ".last_sync_date"
TOKEN_ENV_NAMES = ("ESA_ACCESS_TOKEN", "ESA_TOKEN", "ESA_API_TOKEN")


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned


def load_token(env_path: Path) -> str:
    for env_name in TOKEN_ENV_NAMES:
        val = os.getenv(env_name)
        if val:
            return val.strip()

    if env_path.exists():
        raw_lines = [
            line.strip()
            for line in env_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for line in raw_lines:
            if line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                if key.strip() in TOKEN_ENV_NAMES and val.strip():
                    return val.strip()
            else:
                return line

    raise RuntimeError(
        "Set an esa access token in ESA_ACCESS_TOKEN (or ESA_TOKEN / ESA_API_TOKEN) or .env"
    )


def build_queries(
    screen_name: str, include_wip: bool, updated_after: Optional[str]
) -> List[str]:
    updated_clause = f" updated:>={updated_after}" if updated_after else ""
    queries = [f"user:{screen_name}{updated_clause}"]
    if include_wip:
        queries.append(f"wip:true user:{screen_name}{updated_clause}")
    return queries


def fetch_posts(
    session: requests.Session,
    team: str,
    screen_name: str,
    include_wip: bool = True,
    updated_after: Optional[str] = None,
    responses_dir: Path = RESPONCE_ROOT,
) -> List[Dict]:
    responses_dir.mkdir(parents=True, exist_ok=True)
    base_url = f"https://api.esa.io/v1/teams/{team}/posts"
    queries = build_queries(screen_name, include_wip, updated_after)

    posts: List[Dict] = []
    seen_ids = set()

    for idx, q in enumerate(queries, start=1):
        page = 1
        while True:
            params = {"q": q, "page": page, "per_page": 100}
            resp = session.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            (responses_dir / f"esa_page_{idx}_{page}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            for post in payload.get("posts", []):
                number = post.get("number")
                if number in seen_ids:
                    continue
                seen_ids.add(number)
                posts.append(post)
            next_page = payload.get("next_page")
            if not next_page:
                break
            page = next_page
            time.sleep(8)
    return posts


def load_posts_from_responses(responses_dir: Path = RESPONCE_ROOT) -> List[Dict]:
    posts_by_number: Dict[int, Dict] = {}
    if not responses_dir.exists():
        return []

    for path in sorted(responses_dir.glob("esa_page_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for post in payload.get("posts", []):
            number = post.get("number")
            if number is None:
                continue
            existing = posts_by_number.get(number)
            if existing:
                prev_updated = existing.get("updated_at") or ""
                new_updated = post.get("updated_at") or ""
                if new_updated > prev_updated:
                    posts_by_number[number] = post
            else:
                posts_by_number[number] = post
    return list(posts_by_number.values())


def ensure_post_path(
    posts_root: Path, category: Optional[str], title: str, number: int
) -> Path:
    """Return a stable path for the post. If it exists, we overwrite.

    File name is anchored by post number to avoid duplicates when the title changes.
    """
    parts = [p for p in (category or "").split("/") if p]
    target_dir = posts_root.joinpath(*parts)
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = sanitize_filename(title) or f"post-{number}"
    filename = f"{number}_{base_name}.md"
    return target_dir / filename


def download_image(
    session: requests.Session,
    url: str,
    images_root: Path,
    post_number: int,
    cache: Dict[str, Path],
    used_names: Dict[str, Path],
) -> Path:
    if url in cache:
        return cache[url]

    parsed = urlparse(url)
    filename = sanitize_filename(Path(parsed.path).name) or f"post_{post_number}"
    stem = Path(filename).stem
    suffix = Path(filename).suffix

    counter = 1
    while filename in used_names:
        filename = f"{stem}_{counter}{suffix}"
        counter += 1

    images_root.mkdir(parents=True, exist_ok=True)
    dest = images_root / filename

    with session.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
        time.sleep(8)

    cache[url] = dest
    used_names[filename] = dest
    return dest


def rewrite_images(
    session: requests.Session,
    body_md: str,
    images_root: Path,
    post_path: Path,
    post_number: int,
    cache: Dict[str, Path],
    used_names: Dict[str, Path],
) -> str:
    md_pattern = re.compile(r"!\[([^\]]*)\]\((\S+?)(?:\s+\"[^\"]*\")?\)")
    html_pattern = re.compile(
        r"(<img\b[^>]*?\bsrc\s*=\s*)([\"'])(https?://[^\"']+)(\2)([^>]*>)",
        re.IGNORECASE,
    )

    def replacer_markdown(match: re.Match) -> str:
        alt_text, url = match.group(1), match.group(2)
        if not url.lower().startswith(("http://", "https://")):
            return match.group(0)
        local_path = download_image(
            session, url, images_root, post_number, cache, used_names
        )
        rel_path = os.path.relpath(local_path, start=post_path.parent)
        return f"![{alt_text}]({rel_path})"

    def replacer_html(match: re.Match) -> str:
        prefix, quote, url, _, suffix = match.groups()
        local_path = download_image(
            session, url, images_root, post_number, cache, used_names
        )
        rel_path = os.path.relpath(local_path, start=post_path.parent)
        return f"{prefix}{quote}{rel_path}{quote}{suffix}"

    body_md = md_pattern.sub(replacer_markdown, body_md)
    return html_pattern.sub(replacer_html, body_md)


def format_post(post: Dict, body_md: str) -> str:
    tags = ", ".join(f'"{tag}"' for tag in (post.get("tags") or []))
    category = (post.get("category") or "").replace('"', r"\"")
    header = [
        "---",
        f"id: {post.get('id')}",
        f"number: {post.get('number')}",
        f"wip: {str(post.get('wip', False)).lower()}",
        f'category: "{category}"',
        f"tags: [{tags}]",
        f"url: {post.get('url', '')}",
        f"updated_at: {post.get('updated_at', '')}",
        f"created_at: {post.get('created_at', '')}",
        "---",
        "",
    ]
    return "\n".join(header) + body_md.strip() + "\n"


def load_local_index(posts_root: Path) -> Dict[int, str]:
    """
    Build a mapping of post number -> updated_at from existing markdown files.
    Only entries with both fields are recorded.
    """
    index: Dict[int, str] = {}
    if not posts_root.exists():
        return index

    for path in posts_root.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        m_num = re.search(r"^number:\s*(\d+)\s*$", text, re.MULTILINE)
        m_updated = re.search(r"^updated_at:\s*([^\n]+)\s*$", text, re.MULTILINE)
        if not (m_num and m_updated):
            continue

        num = int(m_num.group(1))
        updated = m_updated.group(1).strip()
        index[num] = updated

    return index


def load_last_sync_date(path: Path = LAST_SYNC_FILE) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def save_last_sync_date(date_str: str, path: Path = LAST_SYNC_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(date_str, encoding="utf-8")
