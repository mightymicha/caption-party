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
    {
        party1: [
            channel1: [
                name: {channel name},
                id: {channel ID}
                ]
            ...
            ]
        ...
     }
Default: "channels.json".

--key(str):
The key variable specifies the name of a file that
contains the OAuth 2.0 information for this application,
including its client_id and client_secret.
You can acquire an OAuth 2.0 client ID and client secret from
the GoogleCloud Console at https://cloud.google.com/console.
Default: "client_secret.json"

--videos-per-channel(int):
Specifies the maximal number of videos per channel to fetch subtitles from.
Recent videos will get downloaded first.
Default: 5

--captions-format(str):
Specifies format of the subtitles.
Options: srt, ass, vtt, lrc, ttml
Default: ttml
"""

import os
import sys
import json
import re
import glob
try:
    import click
    import webvtt
    from apiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit(
        "[ERROR] You need the following python packages:\nclick, webvtt, apiclient, google_auth_oauthlib")

VERSION = '1.0.0'


@click.group()
@click.version_option(version=VERSION)
def main():
    pass


@main.command()
@click.argument('parties', nargs=-1)
@click.option('--channels-resource', default='./channels.json', type=click.Path(exists=True))
@click.option('--key', default='./client_secret.json', type=click.Path(exists=True))
@click.option('--videos-per-channel', default=5)
@click.option('--captions-format', default='ttml', type=click.Choice(['srt', 'ass', 'vtt', 'ttml']))
def fetch(parties, channels_resource, key, videos_per_channel, captions_format):
    # Get specified parties
    party_channels = load_json(channels_resource)
    available_parties = list(party_channels.keys())
    # Check input
    if len(parties) == 0:
        return
    if len(parties) == 1 and parties[0] == "all":
        parties = available_parties
    elif not all(party in available_parties for party in parties):
        print("Usage: connect.py fetch [OPTIONS] PARTIES...")
        print("Available parties: " + ", ".join(["all"] + available_parties))
        return
    # Print script information
    print_information(parties)
    # Get youtube api handle for uploads fetching
    handle = get_handle(key)
    # Download subtitles
    for party in parties:
        print("[STATUS] Party: " + party.upper())
        for channel in party_channels[party]:
            print("[STATUS] Channel: " + channel["name"])
            uploads = get_channel_uploads_id(handle, channel["id"])
            download_subs(party, uploads, videos_per_channel, captions_format)
        # Filter captions
        print("[STATUS] Start filtering {0} captions".format(party))
        filter_subs("./captions/" + party)


def load_json(path):
    """Opens a json file and returns the content as a python dictonary.

    Parameters:
        path(str): Path of json file
    """
    if not path.lower().endswith('.json'):
        raise ValueError("Wrong file format!")
    with open(path) as f:
        return json.load(f)


def print_information(parties):
    print("==============================")
    print("==== CAPTION PARTY v{0} ====".format(VERSION))
    print("==============================")
    print("Fetching: " + ", ".join(parties))
    print("==============================\n")


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

# For given channel_id, return the 'upload playlist' id


def get_channel_uploads_id(handle, channel_id):
    json_result = handle.channels().list(
        part='snippet,contentDetails', id=channel_id).execute()
    return json_result['items'][0]['contentDetails']['relatedPlaylists']['uploads']


def download_subs(party, playlist, max_subtitles, captions_format):
    """Runs a command to download captions from a specific playlist.

    Parameters:
        party(str): Subtitles get downloaded to `captions/{party}/id`.
        playlist(str): The Youtube playlist ID
        max_videos_per_channel(int): Maximal subtitles to download
        captions_format(str): Specifies caption format preference
    """

    cmd = [
        "youtube-dl",
        "--write-auto-sub",
        "--skip-download",
        "--sub-lang de",
        "--no-progress",
        "--max-downloads " + str(max_subtitles),
        "--sub-format " + captions_format,
        "-o 'captions/" + party + "/%(id)s'",
        playlist
    ]
    os.system(" ".join(cmd))


def filter_subs(directory):
    """Removes tags and redundant whitespace from files in a directory.

    Parameters:
        directory(str): folder in which all files get filtered
    """

    unfiltered_files = glob.glob(directory + "/*.ttml")
    for cap in unfiltered_files:
        with open(cap, "r") as f:
            text = f.read()
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        with open(directory + "/" + cap[:-5] + ".txt", "w+") as f:
            f.write(text)
        os.remove(cap)


# handle = get_handle()
# handle = None
# generate_corpus(handle, "afd", 2)

# videos = get_playlist_items(handle, playlist)
# caption = get_caption_id(handle, videos[3])
# subtitle = get_caption_text(handle, caption)
# filter_text(subtitle[::1000])


# +-+-+--- DEPRECATED ---+-+-+-
# Methods used before changing to youtube_dl

def get_playlist_items(handle, playlist_id):
    json_result = handle.playlistItems().list(part='contentDetails',
                                              maxResults=5,
                                              playlistId=playlist_id).execute()
    video_array = json_result['items']
    for ix, video in enumerate(video_array):
        video_array[ix] = video['contentDetails']['videoId']
    return video_array


def filter_text(text):
    fixed_umlaute = str(text).replace('\\xc3\\xbc', 'ü').replace(
        '\\xc3\\xb6', 'ö').replace('\\xc3\\xa4', 'ä').replace('\\xc3\\x9f', 'ß')
    fixed_breaks = fixed_umlaute.replace('\\n', ' ').replace('\n', ' ')
    only_alpha = re.sub("[^a-zA-ZäÄöÖüÜß€ ]", ' ', fixed_breaks)
    return re.sub('\s+', ' ', only_alpha).strip()


def get_caption_id(handle, video_id):
    json_result = handle.captions().list(part='snippet', videoId=video_id).execute()
    captions_list = json_result['items']
    if len(captions_list) >= 2:
        print("OMG More than two captions!")
    return captions_list[0]['id']


def get_caption_text(handle, caption_id):
    return handle.captions().download(id=caption_id).execute()


if __name__ == '__main__':
    main()

