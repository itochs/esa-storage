import argparse

from .fetch import add_parser as add_fetch_parser
from .pull import add_parser as add_pull_parser
from .save import add_parser as add_save_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch and/or save esa posts for a specific user."
    )
    subparsers = parser.add_subparsers(dest="command")
    add_fetch_parser(subparsers)
    add_save_parser(subparsers)
    add_pull_parser(subparsers)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
