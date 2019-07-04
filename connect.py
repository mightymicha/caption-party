""" Caption Party

This script allows to download and analyze subtitles from Youtube
channels grouped by their belonging to a political party.

Arguments:

fetch:
    Download video captions from one or multiple parties to
    `subtitles\{party}\{video}`. Use argument `all` to fetch videos
    from every party specified in the json file.

combine:
    Combines the captions in `captions/{party}` to a file
    `captions/{party}/combined.txt`. Use argument `all` to combine
    captions from all fetched parties.

analyze:
    TBA

Options:
    See the documentation in `commands\{command}.py` or
    execute `connect.py {command} --help`.
"""

import sys
from helper import error, VERSION
from commands import combine, analyze, fetch
try:
    import click
except ImportError:
    sys.exit(error + "You need the following python packages: click")


@click.group()
@click.version_option(version=VERSION)
def main():
    pass


main.add_command(fetch.fetch)
main.add_command(combine.combine)
main.add_command(analyze.analyze)


if __name__ == '__main__':
    main()
