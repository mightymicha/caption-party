# caption-party

This script allows downloading subtitles and other metadata
from Youtube channels using the [YouTube API v3](https://developers.google.com/youtube/v3/docs/) and [youtube-dl](https://github.com/ytdl-org/youtube-dl/) (avoiding heavy quota costs).

Topic and metadata analysis is done within [jupyter notebooks](https://jupyter.org/) in `analysis\`.

![Top 20 words in a period of 3 month before the Bundestag elections using (TF-IDF)[https://en.wikipedia.org/wiki/Tf%E2%80%93idf]](rsc/tfidf.png)

## Script arguments:

- **fetch**:
*Download video captions from one or multiple parties to
`subtitles\{party}\{video}`.
Use argument `all` to fetch videos
from every party specified in the json file.*

## Examples:
- `python connect.py fetch spd cdu --after-date 01.01.2017 --before-date 01.01.2018`
- `python connect.py fetch all --videos-per-channel -1 --key client_secret.json`

## Requirements:
- [Google API Client](https://github.com/googleapis/google-api-python-client)
- [Google Auth Library](https://github.com/googleapis/google-auth-library-python)
- [youtube-dl](https://github.com/rg3/youtube-dl)
- [click](https://github.com/pallets/click)
- [word_cloud](https://github.com/amueller/word_cloud)


`sudo pip install google-api-python-client google-auth youtube-dl click wordcloud`
