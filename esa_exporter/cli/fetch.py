import argparse
from pathlib import Path

import requests

from esa_exporter.core import (
    DEFAULT_TEAM,
    DEFAULT_USER,
    RESPONCE_ROOT,
    fetch_posts,
    load_token,
)


def run(args: argparse.Namespace) -> None:
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
