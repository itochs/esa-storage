#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time
import requests
import json

DEFAULT_TEAM = "vdslab"
DEFAULT_USER = "ito_hal"
POSTS_ROOT = Path(__file__).parent / "posts"
IMAGES_ROOT = Path(__file__).parent / "images"
RESPONCE_ROOT = Path(__file__).parent / "responce"
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
                # Fallback: treat a single-line .env that only contains the token.
                return line

    raise RuntimeError(
        "Set an esa access token in ESA_ACCESS_TOKEN (or ESA_TOKEN / ESA_API_TOKEN) or .env"
    )


def fetch_posts(
    session: requests.Session,
    team: str,
    screen_name: str,
    include_wip: bool = True,
    responses_dir: Path = RESPONCE_ROOT,
) -> List[Dict]:
    responses_dir.mkdir(parents=True, exist_ok=True)
    base_url = f"https://api.esa.io/v1/teams/{team}/posts"
    queries = [f"user:{screen_name}"]
    if include_wip:
        queries.append(f"wip:true user:{screen_name}")

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
                if post["number"] in seen_ids:
                    continue
                seen_ids.add(post["number"])
                posts.append(post)
            next_page = payload.get("next_page")
            if not next_page:
                break
            page = next_page
            time.sleep(8)

    return posts


def load_posts_from_responses(responses_dir: Path = RESPONCE_ROOT) -> List[Dict]:
    posts: List[Dict] = []
    seen_ids = set()
    if not responses_dir.exists():
        return posts

    for path in sorted(responses_dir.glob("esa_page_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for post in payload.get("posts", []):
            number = post.get("number")
            if number in seen_ids:
                continue
            seen_ids.add(number)
            posts.append(post)
    return posts


def ensure_post_path(
    posts_root: Path, category: Optional[str], title: str, number: int
) -> Path:
    parts = [p for p in (category or "").split("/") if p]
    target_dir = posts_root.joinpath(*parts)
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = sanitize_filename(title) or f"post-{number}"
    candidate = target_dir / f"{base_name}.md"
    if candidate.exists():
        candidate = target_dir / f"{base_name}-p{number}.md"
    return candidate


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
    pattern = re.compile(r"!\[([^\]]*)\]\((\S+?)(?:\s+\"[^\"]*\")?\)")

    def replacer(match: re.Match) -> str:
        alt_text, url = match.group(1), match.group(2)
        if not url.lower().startswith(("http://", "https://")):
            return match.group(0)
        local_path = download_image(
            session, url, images_root, post_number, cache, used_names
        )
        rel_path = os.path.relpath(local_path, start=post_path.parent)
        return f"![{alt_text}]({rel_path})"

    return pattern.sub(replacer, body_md)


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export esa posts for a specific user."
    )
    parser.add_argument(
        "--team", default=os.getenv("ESA_TEAM", DEFAULT_TEAM), help="esa team name"
    )
    parser.add_argument(
        "--user",
        dest="screen_name",
        default=os.getenv("ESA_SCREEN_NAME", DEFAULT_USER),
        help="esa screen name",
    )
    parser.add_argument(
        "--posts-dir",
        type=Path,
        default=POSTS_ROOT,
        help="destination root for markdown posts",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=IMAGES_ROOT,
        help="destination root for downloaded images",
    )
    parser.add_argument(
        "--responses-dir",
        type=Path,
        default=RESPONCE_ROOT,
        help="directory to store raw API responses",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="path to .env containing the access token",
    )
    parser.add_argument(
        "--no-wip", action="store_true", help="exclude draft (wip) posts"
    )
    args = parser.parse_args()

    token = load_token(args.env_file)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})

    fetch_posts(
        session,
        args.team,
        args.screen_name,
        include_wip=not args.no_wip,
        responses_dir=args.responses_dir,
    )
    posts = load_posts_from_responses(args.responses_dir)
    if not posts:
        print("No posts found for the specified user.")
        return

    cache: Dict[str, Path] = {}
    used_names: Dict[str, Path] = {}

    for post in posts:
        post_path = ensure_post_path(
            args.posts_dir,
            post.get("category"),
            post.get("name", ""),
            post.get("number"),
        )
        rewritten_body = rewrite_images(
            session=session,
            body_md=post.get("body_md", ""),
            images_root=args.images_dir,
            post_path=post_path,
            post_number=post.get("number"),
            cache=cache,
            used_names=used_names,
        )
        content = format_post(post, rewritten_body)
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(content, encoding="utf-8")
        print(f"Wrote {post_path}")


if __name__ == "__main__":
    main()
