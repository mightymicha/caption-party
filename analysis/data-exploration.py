%matplotlib tk
import pandas as pd
# import numpy as np
import matplotlib.pylab as plt
import matplotlib.dates as mdates

data = pd.read_csv('../rsc/data.csv')
data.set_index('videoId', inplace=True)
data['publishedAt'] = pd.to_datetime(data['publishedAt'])
data['updated'] = pd.to_datetime(data['publishedAt'])

# Colors
parties = ['linke', 'spd', 'grüne', 'cdu', 'fdp', 'afd']
colors = {'linke': '#FFC0CB',
          'grüne': '#42923bff',
          'spd': '#e2001aff',
          'cdu': '#252422ff',
          'fdp': '#ffec01ff',
          'afd': '#009ee0ff'}


# Jamaika
# plt.axvspan("10.24.2017", "11.20.2017", alpha=.2, color='r')
# trans = plt.get_xaxis_transform()
# # plt.text(20, 1, 'test', transform=trans)
# plt.annotate("Jamaika-Verhandlungen scheitern", xy=('2017-11-20', 230),  xycoords='data', bbox=dict(boxstyle="round", fc="none", ec="gray"), xytext=(0, 30), textcoords='offset points', ha='center', arrowprops=dict(arrowstyle='-[, widthB=1.0, lengthB=1.0'))


# Upload analysis
# Without party grouping
# MONTHLY
style = dict(size=10, color='gray')
plt.title("Uploads monthly")
count_month = data.groupby(data["publishedAt"].dt.to_period('M'))[
    'title'].count()
count_month.plot(color='black')

plt.title("Uploads weekly")
count_week = data.groupby(data["publishedAt"].dt.to_period('W'))[
    'title'].count()
count_week.plot(color='black')
# WEEKLY
plt.title("Uploads by party weekly")
count_party_week = data.groupby([data["publishedAt"].dt.week, data['party']])[
    'title'].count().unstack()
count_party_week.plot(color=count_party_week.apply(
    lambda x: colors[x.name]), kind='bar')

data[data['publishedAt'] > '10.10.2017']['publishedAt']

peak2 = data.query(
    'publishedAt > "10.10.2017" and publishedAt < "10.20.2017"').index
for title in data.loc[peak2]['title']:
    print(title)


# SPD
count_party_month = data[data['party'] == 'spd'].groupby(
    [data["publishedAt"].dt.to_period('W'), data['party']])['viewCount'].sum().unstack()
count_party_month.plot(color=colors['spd'])
plt.title("View Count grouped by week")

peak1_spd = data.query(
    'publishedAt >= "06.26.2017" and publishedAt <= "07.02.2017" and party=="spd"').index
peak2_spd = data.query(
    'publishedAt >= "09.18.2017" and publishedAt <= "09.24.2017" and party=="spd"').index

# Ehe für alle
data.loc[peak1_spd][['title', 'viewCount']].sort_values('viewCount', ascending=False)
# Werbespot
data.loc[peak2_spd][['title', 'viewCount']].sort_values('viewCount', ascending=False)

plt.annotate("National election", xy=('2017-09-24', 700000),  xycoords='data', bbox=dict(boxstyle="round", fc="none", ec="gray"), xytext=(-60, -30), textcoords='offset points', ha='center', arrowprops=dict(arrowstyle="->"))
plt.annotate("Same-sex marriage", xy=('2017-06-30', 510000),  xycoords='data', bbox=dict(boxstyle="round", fc="none", ec="gray"), xytext=(0, 30), textcoords='offset points', ha='center', arrowprops=dict(arrowstyle="->"))


# AfD
count_party_month = data[data['party'] == 'afd'].groupby(
    [data["publishedAt"].dt.to_period('W'), data['party']])['viewCount'].sum().unstack()
count_party_month.plot(color=colors['afd'], kind='bar')
plt.title("View Count grouped by week")

peak1_afd = data.query(
    'publishedAt >= "08.28.2017" and publishedAt <= "09.03.2017" and party=="afd"').index

# Werbespot / Afd Lied
data.loc[peak1_afd][['title', 'viewCount']].sort_values(
    'viewCount', ascending=False)

count_party_month.plot(color=colors['afd'])
plt.title("View Count grouped by week")
plt.annotate("National election", xy=('2017-09-24', 100000),  xycoords='data', bbox=dict(boxstyle="round", fc="none", ec="gray"), xytext=(30, 30), textcoords='offset points', ha='center', arrowprops=dict(arrowstyle="->"))


# Linke
count_party_month = data[data['party'] == 'linke'].groupby(
    [data["publishedAt"].dt.to_period('W'), data['party']])['viewCount'].sum().unstack()
count_party_month.plot(color=colors['afd'], kind='bar')
plt.title("View Count grouped by week")

peak1_linke = data.query(
    'publishedAt >= "05.29.2017" and publishedAt <= "06.25.2017" and party=="linke"').index

# Werbespot / Reden Sahra Wagenknecht
data.loc[peak1_linke][['title', 'viewCount']].sort_values(
    'viewCount', ascending=False)

count_party_month.plot(color=colors['linke'])
plt.title("View Count grouped by week")
# plt.annotate("National election", xy=('2017-09-24', 100000),  xycoords='data', bbox=dict(boxstyle="round", fc="none", ec="gray"), xytext=(30, 30), textcoords='offset points', ha='center', arrowprops=dict(arrowstyle="->"))
