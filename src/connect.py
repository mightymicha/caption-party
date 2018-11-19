""" Caption Party

This script allows to download and analyze subtitles from Youtube
channels grouped by their belonging to a political party.

Arguments:

fetch:
Download video captions from one or multiple parties to
`subtitles\{party}\{video}`. Use argument `all` to fetch videos
from every party specified in the json file.

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

--videos-per-channel(int):
Specifies the maximal number of videos per channel.
Recent videos will get processed first.
The value '-1' corresponds to unlimited videos.
Default: 20

--key(str):
The key variable specifies the name of a file that
contains the OAuth 2.0 information for this application,
including its client_id and client_secret.
You can acquire an OAuth 2.0 client ID and client secret from
the GoogleCloud Console at https://cloud.google.com/console.
Default: "rsc/client_secret.json"

--after_date(string):
Download subtitles from videos uploaded on and after a specific date.
Specification: `<DAY>.<MONTH>.<YEAR>`
Default: 01.01.2018
"""

import os
import sys
import json
import re
import glob
import datetime
try:
    import click
    import nltk
    from nltk.corpus import stopwords
    from nltk import FreqDist
    from apiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit(
        "[ERROR] You need the following python packages:\nclick\nnltk\napiclient\ngoogle_auth_oauthlib")

VERSION = '1.1.0'


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


status = color.BOLD + color.PURPLE + "[STATUS] " + color.END


@click.group()
@click.version_option(version=VERSION)
def main():
    pass


@main.command()
@click.argument('parties', nargs=-1)
@click.option('--channels-resource', default='rsc/channels.json', type=click.Path(exists=True))
@click.option('--videos-per-channel', default=20)
@click.option('--key', default='rsc/client_secret.json', type=click.Path(exists=True))
@click.option('--after-date', default="01.06.2017")
@click.option('--before-date', default="24.09.2017")
def fetch(parties, channels_resource, videos_per_channel, key, after_date, before_date):
    # Get specified parties
    party_channels = load_json(channels_resource)
    available_parties = list(party_channels.keys())
    # Get Google Dev handle
    handle = get_handle(key)
    # Check input
    if len(parties) == 0:
        return
    if len(parties) == 1 and parties[0] == "all":
        parties = available_parties
    elif not all(party in available_parties for party in parties):
        print("Usage: connect.py fetch [OPTIONS] PARTIES...")
        print("Available parties: " + ", ".join(["all"] + available_parties))
        return
    try:
        after_date = datetime.datetime.strptime(after_date, '%d.%m.%Y')
        before_date = datetime.datetime.strptime(before_date, '%d.%m.%Y')
    except ValueError:
        print("Usage: connect.py fetch [OPTIONS] PARTIES...")
        print("Datetime: {DAY}.{MONTH}.{YEAR}")
        return
    # Print script information
    print_information(parties, videos_per_channel, after_date, before_date)
    # Download subtitles
    for party in parties:
        print(status + "Party: ", color.BOLD +
              color.BLUE + party.upper() + color.END)
        for channel in party_channels[party]:
            print(status + "Channel: ", color.BOLD +
                  color.RED + channel['name'] + color.END)
            playlist_id = get_channel_uploads_id(handle, channel['id'])
            for video in get_playlist_items(handle, playlist_id, after_date, before_date, videos_per_channel):
                download_sub(party, channel['region'], video)
        # Filter captions
        print(status + "Start filtering {0} captions".format(party))
        filter_subs("./captions/" + party)


@main.command()
@click.argument('parties', nargs=-1)
@click.option('--channels-resource', default='rsc/channels.json', type=click.Path(exists=True))
@click.option('--remove-stop-words/--leave-stop-words', default=True)
def combine(parties, channels_resource, remove_stop_words):
    party_channels = load_json(channels_resource)
    available_parties = list(party_channels.keys())
    # Check input
    if len(parties) == 0:
        return
    if len(parties) == 1 and parties[0] == "all":
        parties = available_parties
    elif not all(party in available_parties for party in parties):
        print("Usage: connect.py combine [OPTIONS] PARTIES...")
        print("Available parties: " + ", ".join(["all"] + available_parties))
        return
    # Combine captions of each party
    for party in parties:
        print(status + "Combining: ", color.BOLD +
              color.BLUE + party.upper() + color.END)
        combined_tokens = []
        for caption in os.listdir(os.path.join("captions", party)):
            raw_caption = open(os.path.join(
                "captions", party, caption), 'r').read()
            combined_tokens.extend(nltk.word_tokenize(raw_caption))
        if remove_stop_words:
            # Filter tokens
            stopwords_en = stopwords.words("english")
            stopwords_de = stopwords.words("german")
            combined_tokens = [w for w in combined_tokens
                               if w.isalpha()
                               and not len(w) < 3
                               and not w in stopwords_de
                               and not w in stopwords_en]
        # Saving combined dataset
        with open(os.path.join("captions", party, "combined.txt"), 'w') as f:
            f.write(" ".join(combined_tokens))


@main.command()
@click.argument('party', nargs=1)
@click.option('--channels-resource', default='rsc/channels.json', type=click.Path(exists=True))
def analyze(party, channels_resource):
    party_channels = load_json(channels_resource)
    available_parties = list(party_channels.keys())
    # Check input
    if len(party) == 0:
        return
    elif not party in available_parties:
        print("Usage: connect.py analyze [OPTIONS] PARTY...")
        print("Available parties: " + ", ".join(["all"] + available_parties))
        return
    # Combine captions of each party
    print(status + "Analyzing: ", color.BOLD +
          color.BLUE + party.upper() + color.END)


def load_json(path):
    """Opens a json file and returns the content as a python dictonary.

    Parameters:
        path(str): Path of json file
    """
    if not path.lower().endswith('.json'):
        raise ValueError("Wrong file format!")
    with open(path) as f:
        return json.load(f)


def print_information(parties, videos_per_channel, after_date, before_date):
    print("==============================")
    print("==== CAPTION PARTY v{0} ====".format(VERSION))
    print("==============================")
    print("Fetching: " + ", ".join(parties))
    if videos_per_channel < 0:
        print("Subtitles per channel: unlimited")
    else:
        print("Subtitles per channel: " + str(videos_per_channel))
    print("Uploaded after: " + str(after_date))
    print("Uploaded before: " + str(before_date))
    print("==============================\n")


def download_sub(party, region, video_id):
    """Runs a command to download subtitles from a specific video.

    Parameters:
        party(str): Subtitles get downloaded to `captions/{party}/id`.
    """

    cmd = [
        "youtube-dl",
        "--write-auto-sub",
        "--skip-download",
        "--sub-lang de",
        "--no-progress",
        "--sub-format ttml",
        "-o '" + os.path.join("captions", party, region + "_%(id)s'"),
        video_id
    ]
    os.system(" ".join(cmd))


def filter_subs(directory):
    """Removes tags and redundant whitespace from files in a directory.

    Parameters:
        directory(str): folder in which all files get filtered
    """

    unfiltered_files = glob.glob(os.path.join(directory, "*.ttml"))
    for cap in unfiltered_files:
        with open(cap, "r") as f:
            text = f.read()
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        # text = re.sub(r'[^a-zA-ZäöüÄÖÜß\s]*', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        with open(cap[:-8] + ".txt", "w+") as f:
            f.write(text)
        os.remove(cap)


def get_playlist_items(handle, playlist_id, after_date, before_date, max_videos):
    videos = []
    json_result = handle.playlistItems().list(part='contentDetails',
                                              maxResults=50,
                                              playlistId=playlist_id).execute()
    videos.extend(json_result['items'])

    nextPageToken = json_result.get('nextPageToken')
    while nextPageToken is not None:
        nextPage = handle.playlistItems().list(part="contentDetails",
                                               playlistId=playlist_id,
                                               maxResults=50,
                                               pageToken=nextPageToken).execute()
        videos.extend(nextPage['items'])
        nextPageToken = nextPage.get('nextPageToken')

    filtered_items = []
    for video in videos:
        time_str = video['contentDetails']['videoPublishedAt'][:10]
        time = datetime.datetime.strptime(time_str, "%Y-%m-%d")
        if after_date < time and time < before_date:
            filtered_items.append(video['contentDetails']['videoId'])
    if max_videos >= 0 and len(filtered_items) > max_videos:
        return filtered_items[:max_videos]
    else:
        return filtered_items


# from apiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# handle = get_handle("rsc/client_secret.json")
# after = datetime.datetime.strptime("2015-09-29", "%Y-%m-%d")
# before = datetime.datetime.strptime("2019-10-05", "%Y-%m-%d")
# len(get_playlist_items(handle, "UUSmbK1WtpYn2sOGLvSSXkKw", after, before, 5))
# get_channel_uploads_id(handle, "UCSmbK1WtpYn2sOGLvSSXkKw")


def get_handle(key):
    """Authorize further requests and return youtube handle.

    Parameters:
        key(str): The key variable specifies the name of a file that
        contains the OAuth 2.0 information for this application,
        including its client_id and client_secret.
        You can acquire an OAuth 2.0 client ID and client secret from
        the GoogleCloud Console at https://cloud.google.com/console.
    """
    scope = ['https://www.googleapis.com/auth/youtube.force-ssl']
    api_service_name = "youtube"
    api_version = "v3"
    flow = InstalledAppFlow.from_client_secrets_file(key, scope)
    credentials = flow.run_local_server(
        host='localhost',
        port=8080,
        authorization_prompt_message='Please visit this URL:\n{url}',
        success_message='The auth flow is complete; you may close this window.',
        open_browser=True)
    # credentials = flow.run_console()
    return build(api_service_name, api_version, credentials=credentials)


# For given channel_id, return the 'upload playlist' id
def get_channel_uploads_id(handle, channel_id):
    json_result = handle.channels().list(
        part='snippet,contentDetails', id=channel_id).execute()
    return json_result['items'][0]['contentDetails']['relatedPlaylists']['uploads']


# +-+-+--- DEPRECATED ---+-+-+-
# Methods used before changing to youtube_dl


# def fetch_channel_videos(handle, max_videos_per_channel):
#     words = []
#     for sub_file in get_sub_files(party):
#         sentences = set()
#         for caption in webvtt.read(sub_file):
#             sentences.add(caption.text)
#         words += [sent.split() for sent in sentences]
#     filtered_words = [
#         item for sublist in words for item in sublist if item.isalpha()]
#     with open(party + "_corpora.txt", "w") as f:
#         f.write(" ".join(filtered_words))


# def filter_text(text):
#     fixed_umlaute = str(text).replace('\\xc3\\xbc', 'ü').replace(
#         '\\xc3\\xb6', 'ö').replace('\\xc3\\xa4', 'ä').replace('\\xc3\\x9f', 'ß')
#     fixed_breaks = fixed_umlaute.replace('\\n', ' ').replace('\n', ' ')
#     only_alpha = re.sub("[^a-zA-ZäÄöÖüÜß€ ]", ' ', fixed_breaks)
#     return re.sub('\s+', ' ', only_alpha).strip()


# def get_caption_id(handle, video_id):
#     json_result = handle.captions().list(part='snippet', videoId=video_id).execute()
#     captions_list = json_result['items']
#     if len(captions_list) >= 2:
#         print("OMG More than two captions!")
#     return captions_list[0]['id']


# def get_caption_text(handle, caption_id):
#     return handle.captions().download(id=caption_id).execute()

# import webvtt
# from apiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow

# --key(str):
# The key variable specifies the name of a file that
# contains the OAuth 2.0 information for this application,
# including its client_id and client_secret.
# You can acquire an OAuth 2.0 client ID and client secret from
# the GoogleCloud Console at https://cloud.google.com/console.
# Default: "client_secret.json"

if __name__ == '__main__':
    main()
