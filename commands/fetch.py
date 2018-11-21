"""
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
import re
import glob
import datetime
from helper import status, usage, error, bold_purple, bold_blue, load_json, VERSION
try:
    import click
    from apiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit(error + """Install the following python packages:
                click
                apiclient
                google_auth_oauthlib""")

name = "fetch"


@click.command()
@click.argument('parties', nargs=-1)
@click.option('--channels-resource',
              default='rsc/channels.json',
              type=click.Path(exists=True))
@click.option('--videos-per-channel', default=20)
@click.option('--key',
              default='rsc/client_secret.json',
              type=click.Path(exists=True))
@click.option('--after-date', default="01.06.2017")
@click.option('--before-date', default="24.09.2017")
def fetch(parties,
          channels_resource,
          videos_per_channel,
          key,
          after_date,
          before_date):
    # Get specified parties
    party_channels = load_json(channels_resource)
    available_parties = list(party_channels.keys())
    # Check input
    if len(parties) == 1 and parties[0] == "all":
        parties = available_parties
    elif not parties or not all(party in available_parties for party in parties):
        print(usage, "connect.py fetch [OPTIONS] PARTIES...")
        print(bold_blue("Available parties: ") + ", ".join(["all"] + available_parties))
        return
    try:
        # Format date
        after_date = datetime.datetime.strptime(after_date, '%d.%m.%Y')
        before_date = datetime.datetime.strptime(before_date, '%d.%m.%Y')
    except ValueError:
        print(usage, "connect.py fetch [OPTIONS] PARTIES...")
        print(bold_blue("Datetime: ") + "{DAY}.{MONTH}.{YEAR}")
        return
    # Print script information
    print_information(parties, videos_per_channel, after_date, before_date)
    # Get Google Dev handle
    handle = get_handle(key)
    # Download subtitles
    for party in parties:
        print(status + "Party: ", bold_purple(party.upper()))
        for channel in party_channels[party]:
            print(status + "Channel: ", bold_blue(channel['name']))
            playlist_id = get_channel_uploads_id(handle, channel['id'])
            for video in get_playlist_items(handle, playlist_id, after_date, before_date, videos_per_channel):
                download_sub(party, channel['region'], video)
        # Filter captions
        print(status + "Start filtering {0} captions".format(party))
        filter_subs("./captions/" + party)


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


def get_playlist_items(handle,
                       playlist_id,
                       after_date,
                       before_date,
                       max_videos):
    """ Returns list of video IDs for given Playlist ID and filters.

    Parameters:
        handle(object):  Youtube handle for authorizing requests to the
            Youtube API. See function `get_handle` for further details.
        playlist_id(str): Unique Youtube Playlist ID
        after_date(str): Date in the format `dd.mm.YYYY`. Returned videos
            were uploaded on or after this date.
        before_date(str): Date in the format `dd.mm.YYYY`. Returned videos
            were uploaded on or before this date.
        max_videos(int): Specifies how many videos at most get returned.
    """
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


def get_channel_uploads_id(handle, channel_id):
    """ Returns 'upload playlist ID' for given channel_id

    Parameters:
        handle(object):  Youtube handle for authorizing requests to the
            Youtube API. See function `get_handle` for further details.
        channel_id(str): Unique channel identifier. To convert channel
            names to the identifier, see:
            http://johnnythetank.github.io/youtube-channel-name-converter/
    """

    json_result = handle.channels().list(
        part='snippet,contentDetails', id=channel_id).execute()
    return json_result['items'][0]['contentDetails']['relatedPlaylists']['uploads']


def get_handle(key):
    """Authorizes further requests and returns youtube handle.

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
        success_message='Auth flow is complete; you may close this window.',
        open_browser=True)
    # credentials = flow.run_console()
    return build(api_service_name, api_version, credentials=credentials)


def print_information(parties, videos_per_channel, after_date, before_date):
    """Prints command line tool information along with parameters."""

    print("==============================")
    print("==== ", bold_purple("CAPTION PARTY v" + str(VERSION)), " ====")
    print("==============================")
    print("Fetching: " + ", ".join(parties))
    if videos_per_channel < 0:
        print("Subtitles per channel: unlimited")
    else:
        print("Subtitles per channel: " + str(videos_per_channel))
    print("Uploaded after: " + str(after_date))
    print("Uploaded before: " + str(before_date))
    print("==============================\n")
