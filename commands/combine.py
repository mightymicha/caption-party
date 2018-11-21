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
"""
import sys
import os
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
def combine(parties, channels_resource):
    party_channels = load_json(channels_resource)
    avail_parties = list(party_channels.keys())
    # Check input
    if len(parties) == 1 and parties[0] == "all":
        parties = avail_parties
    elif not parties or not all(party in avail_parties for party in parties):
        print(usage + "connect.py combine [OPTIONS] PARTIES...")
        print(bold_blue("Available parties: ") +
              ", ".join(["all"] + avail_parties))
        return
    # Combine captions of each party
    for party in parties:
        print(status + "Combining: ", bold_blue(party.upper()))
        combined_tokens = []
        for caption in os.listdir(os.path.join("captions", party)):
            raw_caption = open(os.path.join(
                "captions", party, caption), 'r').read()
            combined_tokens.extend(nltk.word_tokenize(raw_caption))
        # Saving combined dataset
        with open(os.path.join("captions", party, "combined.txt"), 'w') as f:
            f.write(" ".join(combined_tokens))
