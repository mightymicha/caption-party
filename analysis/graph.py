import numpy as np
from pandas import DataFrame
from pygermanet import Synset, load_germanet
from igraph import Graph
import igraph
import cairo
from itertools import combinations, chain
from collections import defaultdict

%matplotlib tk

gn = load_germanet()
sim_funcs = {'lch': (Synset.sim_lch, np.average),
             'res': (Synset.sim_res,  np.max),
             'lin': (Synset.sim_lin,  np.max)}
# 'jcn': (Synset.dist_jcn, np.min), ### bad results


def get_words(n=20):
    words = DataFrame(columns=['imp', 'party'])
    for party in parties:
        for w, val in sorted(tfidfs[party], reverse=True, key=lambda x: x[1])[:n]:
            lem = gn.lemmatise(w)[0]
            synsets = gn.synsets(lem)
            if len(synsets) > 0 and not any(x in flatten(map(lambda s: s.hypernym_paths, synsets)) for x in stop_syns):
                try:
                    words.at[lem, 'imp'] += val
                    words.at[lem, 'party'] = "mixed"
                except KeyError:
                    words.loc[lem] = dict(imp=val, party=party)
    return words


# test_words = ["Auto", "Straße", "Ampel", "Zebrastreifen", "Wald", "Tier",
#               "Umwelt", "Vogel", "Klima", "Steuern", "Artenschutz", "Gefahr",
#               "Obst", "Leben", "Blut", "Mord", "Mindestlohn", "Mensch", "Haut",
#               "Hand", "Finger", "Baum", "Handy", "Angst", "Terror", "Amoklauf",
#               "Sicherheit", "Politik", "Polizei", "Geld", "Wirtschaft", "Parlament",
#               "Wohnen", "Haus", "Wohnung", "Miete", "Mietspiegel", "Mietbremse"]
# distance("Ökosystem", "Rechtschreibung", *sim_funcs['lch'])
# a.sim_lch(b)


def normalize_column(column):
    if len(column) > 1:
        return (column - column.min())/(column.max() - column.min())
    else:
        if column.min().item() > 1:
            return 1/column
        else:
            return column


def distance(word1, word2, sim_func, comb_func):
    try:
        synsets1 = gn.synsets(word1)
        synsets2 = gn.synsets(word2)
        values = np.array([sim_func(s1, s2)
                           for s1 in synsets1 for s2 in synsets2])
        if len(values) > 0:
            return comb_func(values)
        else:
            return None
    except ValueError:
        return None


def get_edge_matrix(words, f=sim_funcs['lch']):
    edges = DataFrame(columns=['w1', 'w2'])
    # for party in parties:
    combs = combinations(words.index.values, 2)
    edges = edges.append([dict(w1=comb[0], w2=comb[1]) for comb in combs])
    sim = edges.apply(lambda row: distance(row['w1'], row['w2'], *f), axis=1)
    return normalize_column(edges['sim'])


distance("Flüchtli", "Flucht", *sim_funcs['lch'])
gn.synsets("Flüchtling")
gn.synset("Flüchtling.n.1").hypernym_paths
x in chain.from_iterable(map(lambda s: s.hypernym_paths, synsets)) for x in politic_syns):

def flatten(L):
    for item in L:
        try:
            yield from flatten(item)
        except TypeError:
            yield item


politic_syns1 = [gn.synset("Handlung.n.1"),
                gn.synset("Handlung.n.2"),
                gn.synset("Beziehung.n.1"),
                gn.synset("Mensch.n.1"),
                gn.synset("Gruppe.n.1"),
                gn.synset("Bewaldung.n.1"),
                gn.synset("Besitz.n.1"),
                gn.synset("Zahlung.n.1"),
                gn.synset("Wohnviertel.n.1"),
                gn.synset("Zahlungsmittel.n.1"),
                gn.synset("Geldsumme.n.1")]

list(chain.from_iterable(gn.synsets("Zuwanderer")[0].hypernym_paths))
politic_syns = [gn.synset("Ansicht.n.1"),
                gn.synset("Meinung.n.1"),
                gn.synset("Ideologie.n.1"),
                gn.synset("Mensch.n.1"),
                gn.synset("Ökonomik.n.1"),
                # gn.synset("öffentliche Institution.n.1"),
                # gn.synset("staatliche Institution.n.1"),
                gn.synset("Migration.n.1"),
                gn.synset("Strafdelikt.n.1"),
                gn.synset("Gewalthandlung.n.1"),
                gn.synset("Wohnungsknappheit.n.1"),
                gn.synset("Digitalisierung.n.1"),
                gn.synset("politische Handlung.n.1"),
                gn.synset("negativer Vorfall.n.1"),
                gn.synset("Vernichtung.n.1"),
                gn.synset("Business.n.1"),
                gn.synset("Naturkatastrophe.n.1"),
                gn.synset("Waffenlieferung.n.1"),
                gn.synset("Klima.n.1"),
                gn.synset("Mark.n.3"),
                gn.synset("Klimakatastrophe.n.1"),
                gn.synset("Flüchtling.n.1"),
                gn.synset("Denkmal.n.1")]
# politic_syns= [gn.synset("Geldsumme.n.1")]

stop_syns = [gn.synset("Verwaltungsgebiet.n.1")]
words = get_words(n=500)
words['imp'] = words.groupby('party').transform(lambda x: normalize_column(x))
# words[300:400]
edges = get_edge_matrix(words)
# filtered_edges = edges[edges['sim'].mean() > edges['sim']]
filtered_edges = edges[edges.notnull()].nlargest(200,'sim')
# nodes = get_node_matrix()
g = Graph.DictList(vertices=[dict(name=vertex) for vertex in words.index[:200]], edges=[dict(source=row["w1"], target=row["w2"], sim=row["sim"]) for _, row in filtered_edges.iterrows()])

visual_style = {}
visual_style["vertex_size"] = [words.at[w,"imp"]*20 + 15 for w in g.vs["name"]]
visual_style["vertex_label"] = g.vs["name"]
# visual_style["background_color"] = "grey"
visual_style["vertex_label_size"] = [words.at[w,"imp"]*5 + 10 for w in g.vs["name"]]
# visual_style["vertex_label_color"] = "grey"
visual_style["vertex_color"] = [colors[words.at[word, "party"]] if words.at[word, "party"] != "mixed" else "black" for word in g.vs["name"]]
visual_style["edge_width"] = [sim for sim in g.es["sim"]]
# visual_style["edge_color"] = [colors[party] for party in g.es["party"]]
visual_style["layout"] = g.layout("kk")
visual_style["bbox"] = (1000,550)
# visual_style["margin"] = 60
visual_style["fname"] = "graph.svg"
plot = igraph.plot(g, **visual_style)
plot.show()
