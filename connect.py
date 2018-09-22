import click
import os
import json
import glob
import webvtt
import re
from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

VERSION = '1.0.0'


@click.group()
@click.version_option(version=VERSION)
def main():
    pass


@main.command()
@click.argument('parties', nargs=-1)
@click.option('--channels', default='channels.json', type=click.Path(exists=True))
@click.option('--api_token', default='client_secret.json', type=click.Path(exists=True))
def fetch(parties, channels, api_token):
    # Get specified parties
    available_parties = get_parties(channels)
    # Check input
    if len(parties) is 0 or not all(party in available_parties for party in parties):
        print("Usage: connect.py fetch [OPTIONS] PARTIES...")
        print("Available parties: " + ", ".join(available_parties))
        return
    # Print information
    print_information(parties)
    # Get handle
    handle = get_handle(api_token)
    for party in parties:
        fetch_party_channels(handle, party, 2)


def get_parties(channel_file):
    with open(channel_file) as f:
        return json.load(f).keys()


def get_channels(channel_file, party):
    with open(channel_file) as f:
        return json.load(f)[party]


def print_information(parties):
    print("==============================")
    print("==== CAPTION PARTY v{0} ====".format(VERSION))
    print("==============================\n")


# Returns the service handle
def get_handle(key):
    scope = ['https://www.googleapis.com/auth/youtube.force-ssl']
    api_service_name = "youtube"
    api_version = 'V3'
    flow = InstalledAppFlow.from_client_secrets_file(key, scope)
    credentials = flow.run_console()
    return build(api_service_name, api_version, credentials=credentials)


def fetch_party_channels(handle, party, max_videos_per_channel):
    download_subs(handle, party, max_videos_per_channel)
    words=[]
    for sub_file in get_sub_files(party):
        sentences=set()
        for caption in webvtt.read(sub_file):
            sentences.add(caption.text)
        words += [sent.split() for sent in sentences]
    filtered_words=[
        item for sublist in words for item in sublist if item.isalpha()]
    with open(party + "_corpora.txt", "w") as f:
        f.write(" ".join(filtered_words))


# For given channel_id, return the 'upload playlist' id
def get_channel_uploads_id(handle, channel_id):
    json_result=handle.channels().list(
        part='snippet,contentDetails', id=channel_id).execute()
    return json_result['items'][0]['contentDetails']['relatedPlaylists']['uploads']


def get_automatic_caption(handle, party, playlist_id, max_videos_per_channel):
    cmd=[
        "youtube-dl",
        "--write-auto-sub",
        "--skip-download",
        "--sub-lang de",
        "--max-downloads " + str(max_videos_per_channel),
        "-o 'captions/" + party + "/%(id)s'",
        playlist_id
    ]
    run_ytdl_cmd(cmd)


def run_ytdl_cmd(cmd):
    os.system(" ".join(cmd))


def get_sub_files(party):
    return glob.glob("./captions/" + party + "/*.vtt")


def download_subs(handle, party, max_videos_per_channel):
    channels=get_channels(party)
    for channel in channels:
        print("[STATUS] Channel: " + channel["name"])
        uploads_playlist=get_channel_uploads_id(handle, channel["id"])
        get_automatic_caption(
            handle, party, uploads_playlist, max_videos_per_channel)


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
    json_result=handle.playlistItems().list(part='contentDetails',
                                              maxResults=5,
                                              playlistId=playlist_id).execute()
    video_array=json_result['items']
    for ix, video in enumerate(video_array):
        video_array[ix]=video['contentDetails']['videoId']
    return video_array


def filter_text(text):
    fixed_umlaute=str(text).replace('\\xc3\\xbc', 'ü').replace(
        '\\xc3\\xb6', 'ö').replace('\\xc3\\xa4', 'ä').replace('\\xc3\\x9f', 'ß')
    fixed_breaks=fixed_umlaute.replace('\\n', ' ').replace('\n', ' ')
    only_alpha=re.sub("[^a-zA-ZäÄöÖüÜß€ ]", ' ', fixed_breaks)
    return re.sub('\s+', ' ', only_alpha).strip()


def get_caption_id(handle, video_id):
    json_result=handle.captions().list(part='snippet', videoId=video_id).execute()
    captions_list=json_result['items']
    if len(captions_list) >= 2:
        print("OMG More than two captions!")
    return captions_list[0]['id']


def get_caption_text(handle, caption_id):
    return handle.captions().download(id=caption_id).execute()


if __name__ == '__main__':
    main()
