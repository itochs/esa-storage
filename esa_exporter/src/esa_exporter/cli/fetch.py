import argparse
from pathlib import Path

import requests

from esa_exporter.core import (
    DEFAULT_TEAM,
    DEFAULT_USER,
    RESPONCE_ROOT,
    fetch_posts,
    load_posts_from_responses,
    load_token,
    load_last_sync_date,
    save_last_sync_date,
)


def run(args: argparse.Namespace) -> None:
    token = load_token(args.env_file)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    sync_marker = args.responses_dir / ".last_sync_date"
    last_sync = load_last_sync_date(sync_marker)
    print(f"Last sync date: {last_sync or 'none'}")
    fetch_posts(
        session,
        args.team,
        args.screen_name,
        include_wip=not args.no_wip,
        updated_after=last_sync,
        responses_dir=args.responses_dir,
    )
    posts = load_posts_from_responses(args.responses_dir)
    if posts:
        latest_updated = max((p.get("updated_at") or "") for p in posts)
        if latest_updated:
            date_part = latest_updated[:10]
            save_last_sync_date(date_part, sync_marker)
            print(f"Updated last sync date to {date_part}")
    print(f"Saved responses to {args.responses_dir}")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "fetch", help="Fetch posts and store raw API responses"
    )
    parser.add_argument(
        "--team", default=DEFAULT_TEAM, help="esa team name (default: vdslab)"
    )
    parser.add_argument(
        "--user",
        dest="screen_name",
        default=DEFAULT_USER,
        help="esa screen name (default: ito_hal)",
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
    parser.set_defaults(func=run)
