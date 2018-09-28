# caption-party

This script allows to download and analyze subtitles from Youtube
channels grouped by their belonging to a political party.


## Arguments:  

**fetch**:
*Download video captions from one or multiple parties to
`subtitles\{party}\{video}`.  
Use argument `all` to fetch videos
from every party specified in the json file.*


#### Argument Options:  

**--channel-resource**(str):
*Specifies the json file containing information about political parties
and related Youtube channels.
It should have the following structure:*
```json5
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
*Default: "channels.json".*


**--videos-per-channel**(int):
*Specifies the maximal number of videos per channel.
Recent videos will get processed first.  
Default: 5*


**--after_date**(string):
*Download subtitles from videos uploaded on and after a specific date.  
Specification: `<DAY>.<MONTH>.<YEAR>`  
Default: 01.01.2018*

## Requirements
- [youtube-dl](https://github.com/rg3/youtube-dl)
