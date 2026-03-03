import argparse
from pathlib import Path

from esa_exporter.core import IMAGES_ROOT, POSTS_ROOT, RESPONCE_ROOT

from .fetch import run as run_fetch
from .save import run as run_save


def run(args: argparse.Namespace) -> None:
    run_fetch(args)
    run_save(args)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "pull", help="Fetch posts and save markdown/images in one command"
    )
    parser.add_argument("--team", required=True, help="esa team name (default: vdslab)")
    parser.add_argument(
        "--user",
        dest="screen_name",
        required=True,
        help="esa screen name (default: ito_hal)",
    )
    parser.add_argument(
        "--responses-dir",
        type=Path,
        default=RESPONCE_ROOT,
        help="directory to store/read raw API responses",
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
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="path to .env containing the access token",
    )
    parser.add_argument(
        "--no-wip", action="store_true", help="exclude draft (wip) posts"
    )
    parser.set_defaults(func=run)
