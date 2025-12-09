import argparse
from pathlib import Path
from typing import Dict

import requests

from esa_exporter.core import (
    POSTS_ROOT,
    IMAGES_ROOT,
    RESPONCE_ROOT,
    format_post,
    ensure_post_path,
    rewrite_images,
    load_posts_from_responses,
    load_token,
    load_local_index,
)


def run(args: argparse.Namespace) -> None:
    token = load_token(args.env_file)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})

    posts = load_posts_from_responses(args.responses_dir)
    if not posts:
        print("No posts found in responses directory.")
        return

    local_index = load_local_index(args.posts_dir)

    cache: Dict[str, Path] = {}
    used_names: Dict[str, Path] = {}
    changed = 0

    for post in posts:
        number = post.get("number")
        updated_remote = (post.get("updated_at") or "").strip()

        if (
            number is not None
            and number in local_index
            and local_index[number] == updated_remote
        ):
            continue

        post_path = ensure_post_path(
            args.posts_dir,
            post.get("category"),
            post.get("name", ""),
            number,
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
        changed += 1

    print(
        f"Exported {changed} updated/new posts; skipped {len(posts) - changed} unchanged."
    )


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "save", help="Save posts from cached JSON to markdown and images"
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
        help="directory to read raw API responses from",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="path to .env containing the access token",
    )
    parser.set_defaults(func=run)
