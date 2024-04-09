import random
import networkx as nx
import matplotlib.pyplot as plt
import yaml
import gen_names as gn
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
import numpy as np


def group_kmean(subg: dict, n, typ, disp=False, def_conts=[], def_names=False):
    print(f"Generating {typ}s from {len(subg)} items...")

    X, nodes = [], []
    for u in subg:
        nodes.append(u)
        X.append(subg[u]['xy'])
    
    if def_conts == []:
        names = gn.generate_names(len(X)//n)
        model = KMeans(n_clusters=len(X)//n, tol=0.1).fit(X)
        clusters = model.labels_
    else:
        names = def_conts # if def_names else gn.generate_names(len(def_conts))
        model = KMeans(n_clusters=len(def_conts), tol=0.1).fit(X)
        clusters = model.labels_

    groups = {f"{names[i]}_{typ}": {'name': f"{names[i]}_{typ}", 'xy': x, 'in': set([n for ii, n in enumerate(nodes) if clusters[ii]==i])} for i, x in enumerate(model.cluster_centers_)}
    for g in groups:
        for i in groups[g]['in']:
            subg[i]['par'] = g
    if disp:
        plt.scatter([x[0] for x in X], [x[1] for x in X], c=clusters)
        plot_g(groups)
    return groups

def distance(a, b, cyl=False, width=5632):
    if cyl: return (min(abs(a[1] - b[1]), width - abs(a[1] - b[1])))**2 + (a[0] - b[0])**2
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def group_agg_both(subg_dict: list, n, typ, all_provs, disp=False, def_conts=[], def_names=False, is_sea=False):
    
    print(f"Generating {typ}s...")
    
    all_subg = nx.Graph()
    all_subg.add_nodes_from([(k, v) for k, v in all_provs.items()])

    for u in all_subg:
        for adj in all_provs[u]['adj']:
            if adj in all_provs:
                all_subg.add_edge(u, adj, weight=weight(all_provs[u]['type'], all_provs[adj]['type'], is_sea))
    
    # print(coords)
    # all_pairs = dict(nx.all_pairs_shortest_path_length(all_subg, cutoff))
    # print("all_pairs done")
    
    land_groups = group_agg(subg_dict[0], n, typ, all_provs, disp=disp, def_conts=def_conts, def_names=def_names)
    if is_sea:
        sea_groups = group_agg(subg_dict[1], n, f"sea_{typ}", all_provs, disp=disp, def_conts=def_conts, def_names=def_names)
    else:
        sea_groups = {}
    for groups in [land_groups, sea_groups]:
        for g in groups:
            for i in groups[g]['in']:
                for adj in all_provs[i]['adj']:
                    if all_provs[adj]['par'] == None:
                        groups[g]['adj'].add(adj)
                    else:
                        groups[g]['adj'].add(all_provs[adj]['par'])
            groups[g]['adj'].difference_update([g])
    all_groups = {}
    for k, v in all_provs.items():
        # print(k, v)
        if v['par'] in land_groups:
            all_groups[v['par']] = land_groups[v['par']]
        elif v['par'] in sea_groups:
            all_groups[v['par']] = sea_groups[v['par']]
        else:
            all_groups[k] = all_provs[k]
    print(len(all_groups), len(land_groups), len(sea_groups), len(all_provs))
    return [land_groups, sea_groups, all_groups]

def group_agg(subg_dict: dict, n, typ, all_provs, disp=False, def_conts=[], def_names=False, is_sea=False):
    subg = nx.Graph()
    subg.add_nodes_from([(k, v) for k, v in subg_dict.items()])
    print(f"Generating {typ}s from {len(subg_dict)} items...")
    
    for u in subg:
        for adj in all_provs[u]['adj']:
            if adj in subg.nodes:
                subg.add_edge(u, adj, weight=weight(all_provs[u]['type'], all_provs[adj]['type']))
    
    coords = nx.get_node_attributes(subg, 'xy')
    nodes = subg.nodes
    X = nx.adjacency_matrix(subg)

    if len(subg_dict) < 2:
        if len(def_conts) == 0:
            names = gn.generate_names(1)
        else:
            names = random.sample(list(def_conts.keys()), counts=list(def_conts.values()), k=1)     
        clusters = [0]
        n_clusters = 1       
    else:
        if len(subg_dict) < len(def_conts):
            def_conts = {k: def_conts[k] for k in random.sample(list(def_conts.keys()), counts=list(def_conts.values()),k=len(subg_dict))}

        # print(X)
        if len(def_conts) == 0:
            # print(X)
            names = gn.generate_names(len(coords)//n)
            model = AgglomerativeClustering(n_clusters=len(subg)//n, linkage='ward', connectivity=X).fit(list(coords.values()))    
        else:
            names = list(def_conts.keys()) if def_names else gn.generate_names(len(def_conts))
            model = AgglomerativeClustering(n_clusters=len(def_conts), linkage='ward', connectivity=X).fit(list(coords.values()))

        clusters = model.labels_
        n_clusters = model.n_clusters_

    groups = {f"{names[i]}_{typ}": {
        'name': f"{names[i]}_{typ}", 
        'xy': center([xy for k, xy in enumerate(coords.values()) if clusters[k]==i]), 
        'in': set([n for ii, n in enumerate(nodes) if clusters[ii]==i]),
        'type': 'SEA' if is_sea else 'PROV',
        'adj': set()
        } for i in range(n_clusters)}
    
    for g in groups:
        for i in groups[g]['in']:
            subg_dict[i]['par'] = g
        
    if disp:
        print("display")
        plt.scatter([x[0] for x in coords.values()], [x[1] for x in coords.values()], c=clusters)
        plot_g(groups)
    return groups

def weight(a, b, is_sea=False):
    typa = 'prov' if 'PROV' in a else 'sea' if 'SEA' in a else 'lake' if 'LAKE' in a else 'waste'
    typb = 'prov' if 'PROV' in b else 'sea' if 'SEA' in b else 'lake' if 'LAKE' in b else 'waste'
    if is_sea: return 0.2 if typa == typb == 'sea' else 2 if typa == typb == 'prov' else 3 if typa+typb == 'provsea' or typa+typb == 'seaprov' else 10000 if 'waste' in typa+typb else 1000
    return 0.2 if typa == typb == 'prov' else 1 if typa == typb == 'sea' else 2 if typa+typb == 'provsea' or typa+typb == 'seaprov' else 10000 if 'waste' in typa+typb else 1000

def center(xy: list):
    x = sum(x[0] for x in xy)//len(xy)
    y = sum(y[1] for y in xy)//len(xy)
    return [x, y]

def plot_g(g):
    if type(g) != nx.Graph:
        tg = nx.Graph()
        tg.add_nodes_from([(k, v) for k, v in g.items()])
        g = tg
    
    pos = nx.get_node_attributes(g, "xy")
    nx.draw_networkx(g, pos, font_size=9, alpha=0.7, node_size=200)
    
    plt.gca().invert_yaxis()
    plt.show()

if __name__ == "__main__":
    all_pairs = None
    types = ['land']*5 + ['sea']*5
    nodes = {i: {'type': types[i], 'xy': [2*i, i**2]} for i in range(10)}
    print(nodes)
    conns = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 0]]

    subg_dict = {
        '64-64-0': {'province': '1', 'red': '64', 'green': '64', 'blue': '0', 'type': 'PROVINCE_0', 'adj': {'64-101-0'}, 'xy': [1823, 1063]},
        '64-101-0': {'province': '2', 'red': '64', 'green': '101', 'blue': '0', 'type': 'PROVINCE_1', 'adj': {'64-64-0'}, 'xy': [1853, 1049]}
    }

    g = nx.Graph()
    g.add_nodes_from([(k, v) for k, v in nodes.items()])
    g.add_edges_from([(conns[i][0], conns[i][1], {'weight': v})for i, v in enumerate([1 if nodes[x[0]]['type'] == nodes[x[1]]['type'] else 3 for x in conns])])
    # print(nx.adjacency_matrix(g).todense())
    group_agg(subg_dict, 2, 'test', True)
    # print(nx.get_node_attributes(g, "xy"))
    # plot_g(g)