# caption-party

This script allows to download and analyze subtitles from Youtube
channels grouped by their belonging to a political party.


## Arguments:

- **fetch**:
*Download video captions from one or multiple parties to
`subtitles\{party}\{video}`.
Use argument `all` to fetch videos
from every party specified in the json file.*

- **combine**:
*Combines the captions in `captions/{party}` to a file
`captions/{party}/combined.txt`.
Use argument `all` to combine
captions from all fetched parties.*

- **analyze**:
*TBA*

## Requirements
- [Google API Client](https://github.com/googleapis/google-api-python-client)
- [Google Auth Library](https://github.com/googleapis/google-auth-library-python)
- [youtube-dl](https://github.com/rg3/youtube-dl)
- [click](https://github.com/pallets/click)
- [word_cloud](https://github.com/amueller/word_cloud)


`sudo pip install google-api-python-client google-auth youtube-dl click wordcloud`
