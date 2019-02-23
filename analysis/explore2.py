%matplotlib tk

# Imports
import os
import glob
import numpy as np
import enchant
import matplotlib.pylab as plt
import nltk
from nltk.corpus import stopwords
import spacy
import math
import seaborn as sns
from itertools import chain
from wordcloud import WordCloud

# Nice party colors
parties = ['linke', 'spd', 'grüne', 'cdu', 'fdp', 'afd']
colors = {'linke': '#dc0000ff',
          'grüne': '#42923bff',
          'spd': '#e2001aff',
          'cdu': '#252422ff',
          'fdp': '#ffec01ff',
          'afd': '#009ee0ff'}
# Load data
raws = {party: open(os.path.join("captions", party, "combined.txt")).read()
        for party in parties}
raws_single = {party: [open(f).read() for f in glob.glob(
    os.path.join("captions", party, "*.txt"))] for party in parties}

# Dictionary filtering
dic = enchant.Dict("de_DE")
dic_filtered = {party: (word.capitalize() for word in raws[party].split(
) if not dic.check(word.lower()) and word.isalpha()) for party in parties}

# Stemming and lemmatization
nlp = spacy.load('de', disable=['parser', 'ner', 'tagger'])
nlp.max_length = 30_000_000

normalized = {party: (nlp(word)[0]
                      for word in dic_filtered[party]) for party in parties}


# Stop words removal
stop = set(stopwords.words('german'))
custom_stop = ["dass", "sagen", "mal", "ganz", "ja", "all", "immer",
               "müssen", "schon", "geben", "gut", "deshalb", "brauchen", "damen", "herren"]
corpus = {party: [w.lemma_ for w in normalized[party]
                  if w.lemma_ not in stop
                  and w.lemma_ not in custom_stop
                  and len(w.lemma_) > 3
                  and w.is_alpha]
          for party in parties}


# Corpus size
plt.figure()
plt.ylabel("Words")
plt.xlabel("Party")
plt.title("Corpus size per party")
plt.bar(parties,
        [len(corpus[key]) for key in parties],
        color=[colors[key] for key in parties])

# Word frequency
fdists = {party: nltk.FreqDist(
    [w for w in corpus[party] if dic.check(w)]) for party in parties}
# for party in parties:
#     fdist = fdists[party]
#     plt.figure()
#     fdist.plot(20)

# TF-IDF
tfidfs = {party: tfidf(fdists, party) for party in parties}
my_weights = {party: my_weighting(fdists, party) for party in parties}

fig, axs = plt.subplots(3, 2, figsize=(15, 30))
axis = chain.from_iterable(zip(*axs))
for party, ax in zip(parties, axis):
    ax.axis("off")
    ax.set_title(party.upper())
    word_weights = sorted(
        tfidfs[party], reverse=True, key=lambda x: x[1])[:30]
    wordcloud = WordCloud(background_color='white', max_font_size=25, height=100).generate_from_frequencies(
        dict(word_weights))
    ax.imshow(wordcloud, interpolation='bilinear')


def tfidf(fdists, name):
    """Term frequency - inverse document frequency."""

    def tf(token, fdist):
        return 0.5 + (0.5 * fdist.get(token))/fdist.most_common(1)[0][1]

    def idf(token):
        return math.log2(len(corpus)/(sum(1 for key in fdists.keys() if fdists.get(key).get(token) is not None)))
    fdist = fdists.get(name)
    return [(token, tf(token, fdist) * idf(token)) for token in fdist.keys()]


def my_weighting(fdists, name):
    """Term frequency - inverse document frequency."""

    def tf(token, fdist):
        return 0.5 + (0.5 * fdist.get(token))/fdist.most_common(1)[0][1]

    def idf(token):
        count = sum(1 for key in fdists.keys()
                    if fdists.get(key).get(token) is not None)
        if count <= 0 or count >= 2:
            return 0
        else:
            return math.log2(len(corpus)/count)
    fdist = fdists.get(name)
    return [(token, tf(token, fdist) * idf(token)) for token in fdist.keys()]