from sync4s2m import __version__
from sync4s2m.tool import Sync4Shikimori2MAL
from pathlib import Path

import requests
import sys
import argparse
import textwrap
import json


def handle_args():
    parser = argparse.ArgumentParser(
        description="Script for lists synchronization between Shikimori (source) and MyAnimeList (target)",
        prog="sync4s2m",
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "-t",
        "--template",
        type=str,
        help="per title template line for printing uni lists, raw json for default",
    )
    parser.add_argument("-c", "--config", type=Path, help="override config directory")
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        default=False,
        help="Wrap output lines into json array",
    )

    command_parser = parser.add_subparsers(
        help="list of commands", dest="command", required=True, metavar="command"
    )

    list_parser = command_parser.add_parser(
        "list", help="show your listing from one of the sites"
    )
    list_parser.add_argument(
        "source",
        choices=["shikimori", "myanimelist"],
        help="Site of your list: shikimori and myanimelist",
        metavar="source",
    )

    format_parser = command_parser.add_parser(
        "template", help="show formatting names for uni lists"
    )

    delta_parser = command_parser.add_parser(
        "delta", help="show delta between two sites"
    )
    delta_parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        default=False,
        help="use myanimelist as source instead of shikimori",
    )
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args(sys.argv[1:])


def template():
    out = textwrap.dedent(
        """
        Meta fields:
        {modify_type} - type of title change in list: unmodified, added, edited or deleted
        {title_type} - type of title: anime, manga or ranobe (ranobe is manga in myanimelist)
        * ranobe type is a manga parsed from shikimori but with /ranobe/ in URL

        Status fields:
        {watch_status} - watch status: planned, watching, completed, on_hold, rewatching, dropped
        {score} - score in list: int [0..10]
        {episodes} - number of anime episodes watched or 0 for manga/ranobe
        {chapters} - number of manga/ranobe chapters readed or 0 for anime
        {volumes} - number of manga/ranobe volumes readed or 0 for anime
        {watch_count} - max({episodes}, {chapters})
        {rewatches} - count of rewatches
        {comment} - comment or empty string
        {delta} - difference of same title entry in json format on both sites or empty object

        Title fields:
        {id} - id (used in title url and API)
        {name} - title
        """
    )
    print(out)


def get_list(args):
    tool = Sync4Shikimori2MAL(args)
    if args.source == "shikimori":
        tool.shikimori.login()
        result = tool.get_shikimori_list()
    elif args.source == "myanimelist":
        tool.myanimelist.login()
        result = tool.get_myanimelist_list()
    else:
        raise NotImplemented(f"{args.source} not supported")
    if args.template:
        result.print_list(args.template)
    else:
        print(json.dumps(result.to_list()))


def get_delta(args):
    tool = Sync4Shikimori2MAL(args)
    tool.login()
    result = tool.get_delta(source="myanimelist") if args.reverse else tool.get_delta()
    if args.template:
        result.print_list(args.template)
    else:
        print(json.dumps(result.to_list()))


def main():
    args = handle_args()
    if args.command == "template":
        template(args)
    elif args.command == "list":
        get_list(args)
    elif args.command == "delta":
        get_delta(args)
    else:
        ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
