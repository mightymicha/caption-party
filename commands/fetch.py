"""
fetch:
Download video subtitles from one or multiple parties to
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
Download subtitles from videos uploaded on or after a specific date.
Specification: `<DAY>.<MONTH>.<YEAR>`
Default: 01.06.2017

--before_date(string):
Download subtitles from videos uploaded on or before a specific date.
Specification: `<DAY>.<MONTH>.<YEAR>`
Default: 01.01.2100
"""

import os
import sys
import re
import glob
import pandas as pd
from pandas.errors import EmptyDataError
from datetime import datetime
from helper import status, usage, error, warning, bold_purple, bold_blue, load_json, VERSION
try:
    import click
    from apiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit(error + """Install the following python packages:
                click
                apiclient
                google_auth_oauthlib""")


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
@click.option('--before-date', default="01.01.2100")
@click.option('--dataset', default='rsc/data.csv', type=click.Path(exists=True))
def fetch(parties,
          channels_resource,
          videos_per_channel,
          key,
          after_date,
          before_date,
          dataset):
    # Get specified parties
    party_channels = load_json(channels_resource)
    available_parties = list(party_channels.keys())
    # Check input
    if len(parties) == 1 and parties[0] == "all":
        parties = available_parties
    elif not parties or not all(party in available_parties for party in parties):
        print(usage, "connect.py fetch [OPTIONS] PARTIES...")
        print(bold_blue("Available parties: ") +
              ", ".join(["all"] + available_parties))
        return
    try:
        # Format date
        after_date = datetime.strptime(after_date, '%d.%m.%Y')
        before_date = datetime.strptime(before_date, '%d.%m.%Y')
    except ValueError:
        print(usage, "connect.py fetch [OPTIONS] PARTIES...")
        print(bold_blue("Datetime: ") + "{DAY}.{MONTH}.{YEAR}")
        return
    # Print script information
    print_information(parties, videos_per_channel, after_date, before_date)
    # Get Google Dev handle
    handle = get_handle(key)
    # Download subtitles and data
    rows = []
    for party in parties:
        print(status + "Party: ", bold_purple(party.upper()))
        for channel in party_channels[party]:
            print(status + "Channel: ", bold_blue(channel['name']))
            playlist_id = get_channel_uploads_id(handle, channel['id'])
            for video_id in get_playlist_items(handle, playlist_id, after_date, before_date, videos_per_channel):
                print(status + "Scraping and processing video:", video_id)
                # Subtitles
                subtitle_path = os.path.join(
                    "subtitles", party, video_id + ".txt")
                download_sub(party, video_id, subtitle_path)
                try:
                    subtitle = filter_subtitles(subtitle_path)
                except FileNotFoundError:
                    print(warning + "Subtitles couldn't be downloaded.")
                    continue
                # Other video data
                raw_video_json = get_raw_video_json(handle, video_id)
                # Merge to datarow
                data_row = create_datarow(video_id, party, channel['region'],raw_video_json, subtitle)
                rows.append(data_row)
    updating_and_saving(rows, dataset)

def updating_and_saving(rows, csv_path):
    # Check whether a dataset already exists
    old_dataset = None
    try:
        old_dataset = pd.read_csv(csv_path).set_index("videoId")
        print(status + "Dataset found. Updating entries.")
    except FileNotFoundError as e:
        print(warning + "No dataset found. Creating new csv file: " + csv_path)
    except EmptyDataError as e:
        print(warning + "Empty dataset found. Overwriting.")

    new_dataset = pd.DataFrame(rows).set_index("videoId")
    if old_dataset:
        new_dataset = new_dataset.combine_first(old_dataset)
    new_dataset.to_csv(csv_path)



def download_sub(party, video_id, path):
    """Runs a command to download subtitles from a specific video.

    Parameters:
        party(str): Subtitles get downloaded to `subtitles/{party}/id`.
    """

    cmd = [
        "youtube-dl",
        "--write-auto-sub",
        "--skip-download",
        "--sub-lang de",
        "--no-progress",
        "--sub-format ttml",
        # "--exec 'mv -v {} " + video_id + ".txt'",
        "-o '{}'".format(path),
        video_id
    ]
    # print(" ".join(cmd))
    os.system(" ".join(cmd))


def filter_subtitles(path):
    # TODO: Workaround until youtube-dl fix
    real_path = path.split('.')[0] + ".de.ttml"
    with open(real_path, "r") as f:
        text = f.read()
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    # text = re.sub(r'[^a-zA-ZäöüÄÖÜß\s]*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    with open(path, "w+") as f:
        f.write(text)
    return text


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

    def get_video_ids(json_list):
        items = []
        # Filter time
        for video in json_list:
            time_str = video['contentDetails']['videoPublishedAt'][:10]
            time = datetime.strptime(time_str, "%Y-%m-%d")
            if after_date < time and time < before_date:
                items.append(video['contentDetails']['videoId'])
        return items

    filtered_videos = []
    json_result = handle.playlistItems().list(part='contentDetails',
                                              maxResults=50,
                                              playlistId=playlist_id).execute()
    filtered_videos.extend(get_video_ids(json_result['items']))

    nextPageToken = json_result.get('nextPageToken')
    while nextPageToken is not None and len(filtered_videos) < max_videos:
        nextPage = handle.playlistItems().list(part="contentDetails",
                                               playlistId=playlist_id,
                                               maxResults=50,
                                               pageToken=nextPageToken).execute()
        filtered_videos.extend(get_video_ids(nextPage['items']))
        nextPageToken = nextPage.get('nextPageToken')

    if max_videos >= 0 and len(filtered_videos) > max_videos:
        return filtered_videos[:max_videos]
    else:
        return filtered_videos


def get_raw_video_json(handle, video_id):
    json_result = handle.videos().list(
        part='snippet,contentDetails,statistics', id=video_id).execute()
    return json_result


def create_datarow(video_id, party, region, json, subtitle):
    if json['pageInfo']['totalResults'] >= 2:
        raise ValueError("Videos have only one result!")
    snippet = json['items'][0]['snippet']
    statistics = json['items'][0]['statistics']
    contentDetails = json['items'][0]['contentDetails']
    row = {"videoId": video_id,
           **snippet,
           **contentDetails,
           **statistics,
           "subtitle": subtitle,
           "party": party,
           "region": region,
           "fetched": str(datetime.now())}
    unwanted = ["thumbnails", "localized"]
    for key in unwanted:
        row.pop(key, None)
    return row


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
