"""
combine:
    Combines the captions in `captions/{party}` to a file
    `captions/{party}/combined.txt`. Use argument `all` to combine
    captions from all fetched parties.

Options:

--channel-resource(str):
Specifies the json file containing information about political parties
and related Youtube channels.
It should have the following structure:
```
{
    "<party1>": [
        {
            "name": "<channel1 name>",
            "id": "<channel1 ID>"
        },
        {
            "name": "<channel2 name>",
            "id": "<channel2 ID>"
        },
        \\ ...
    ],
    "<party2>": [...],
    "<party3>": [...],
    \\ ...
}
```
Default: "rsc/channels.json".

--from-date(string):
Combines subtitles from videos uploaded on or after a specific date.
Specification: `<DAY>.<MONTH>.<YEAR>`
Default: 01.06.2017

--until-date(string):
Combines subtitles from videos uploaded on or before a specific date.
Specification: `<DAY>.<MONTH>.<YEAR>`
Default: 24.09.2017
"""
import sys
import os
from datetime import datetime as dt
from helper import status, usage, error, bold_blue, load_json
try:
    import click
    import nltk
except ImportError:
    sys.exit(error + "You need the following python packages: \nclick, \nnltk")


@click.command()
@click.argument('parties', nargs=-1)
@click.option('--channels-resource',
              default='rsc/channels.json',
              type=click.Path(exists=True))
@click.option('--from-date', default="01.06.2017")
@click.option('--until-date', default="24.09.2017")
def combine(parties, channels_resource, from_date, until_date):
    party_channels = load_json(channels_resource)
    avail_parties = list(party_channels.keys())
    # Check party input
    if len(parties) == 1 and parties[0] == "all":
        parties = avail_parties
    elif not parties or not all(party in avail_parties for party in parties):
        print(usage + "connect.py combine [OPTIONS] PARTIES...")
        print(bold_blue("Available parties: ") +
              ", ".join(["all"] + avail_parties))
        return
    # Check date input
    try:
        until_date = dt.strptime(until_date, '%d.%m.%Y')
        from_date = dt.strptime(from_date, '%d.%m.%Y')
    except ValueError:
        print(usage, "connect.py fetch [OPTIONS] PARTIES...")
        print(bold_blue("Datetime: ") + "{DAY}.{MONTH}.{YEAR}")
        return
    # Combine captions of each party
    for party in parties:
        print(status + "Combining: ", bold_blue(party.upper()))
        combined_tokens = []
        for caption in os.listdir(os.path.join("captions", party)):
            # Check file validity
            if not caption.lower().endswith(".txt") or caption == "combined.txt":
                continue
            # Check time range
            try:
                upload_date = dt.strptime(caption.split('-')[1], '%Y%m%d')
            except ValueError:
                print(error, "Invalid subtitle filename: {}".format(caption))
                return
            if not from_date <= upload_date or not upload_date <= until_date:
                continue
            caption_path = os.path.join("captions", party, caption)
            raw_caption = open(caption_path, 'r').read()
            combined_tokens.extend(nltk.word_tokenize(raw_caption))
        # Saving combined dataset
        print(status + "Combined: {}: {} words!".format(bold_blue(party.upper()),
                                                        len(combined_tokens)))
        with open(os.path.join("captions", party, "combined.txt"), 'w') as f:
            f.write(" ".join(combined_tokens))
