handle = get_handle("rsc/client_secret.json")
playlist_id = get_channel_uploads_id(handle, "UC5AagLvRz7ejBrONZVaA13Q")
json_result = handle.playlistItems().list(part='contentDetails', maxResults=50,
                                          playlistId=playlist_id).execute()
video = json_result['items'][0]['contentDetails']['videoId']
json = get_video_info(handle, video)

rows = []
party = "csu"
after_date = datetime.strptime("01.01.2019", '%d.%m.%Y')
before_date = datetime.strptime("01.01.2100", '%d.%m.%Y')
for video_id in get_playlist_items(handle, playlist_id, after_date, before_date, 10):
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
    data_row = create_datarow(video_id, raw_video_json, subtitle)
    rows.append(data_row)

import pandas as pd
pd.read_csv("rsc/data.csv").set_index("videoId")
frame = pd.DataFrame(rows).set_index("videoId")
frame.keys()
list(info['items'][0]['snippet'])

info.keys()
info['items'][0]['contentDetails']
info['items'][0]['statistics']
info['items'][0]['snippet']
info['items'][0].keys()

rows[0] = []
for video in get_playlist_items(handle, playlist_id, after_date, before_date, 1000):
    data_row = process_video_json(get_video_info(handle, video))
    rows.append(data_row)
    print("OK")


pd.read_csv("rsc/datdfa.csv")



playlist_id = get_channel_uploads_id(handle, "UC-sMkrfoQDH-xzMxPNckGFw")
get_playlist_items(handle, "UC-sMkrfoQDH-xzMxPNckGFw", from_date, until_date, -1)
get_playlist_items(handle,'UU-sMkrfoQDH-xzMxPNckGFw', from_date, until_date, -1)
playlist_id = get_channel_uploads_id(handle, "UC5AagLvRz7ejBrONZVaA13Q")

from_date= datetime.strptime('27.05.2017', '%d.%m.%Y')
until_date = datetime.strptime('29.10.2018', '%d.%m.%Y')

    json_result = handle.playlistItems().list(part='contentDetails',
                                              maxResults=50,
                                              playlistId=playlist_id).execute()
video = json_result['items'][0]
time_str = video['contentDetails']['videoPublishedAt'][:10]
time = datetime.strptime(time_str, "%Y-%m-%d")
from_date < time
time < until_date
