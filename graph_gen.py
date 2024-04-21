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
    
    land_groups = group_agg(subg_dict[0], n, typ, all_provs, disp=disp, def_conts=def_conts, def_names=def_names)
    if is_sea:
        sea_groups = group_agg(subg_dict[1], n, f"sea_{typ}", all_provs, disp=disp, def_conts=def_conts, def_names=def_names)
    else:
        sea_groups = {}
    
    for groups in [land_groups, sea_groups]:
        for g in groups:
            for i in groups[g]['in']:
                for adj in all_provs[i]['adj']:
                    if 'par' not in all_provs[adj] or all_provs[adj]['par'] == None:
                        all_provs[adj]['par'] = None
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
    
    if disp:
        plot_g(all_groups)

    print(len(all_groups), len(land_groups), len(sea_groups), len(all_provs))
    return [land_groups, sea_groups, all_groups]

def group_agg(subg_dict: dict, n, typ, all_provs, disp=False, def_conts={}, def_names=False, is_sea=False):
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
        # print(X)
        if len(def_conts) == 0:
            # print(X)
            names = gn.generate_names(len(coords)//n)
            model = AgglomerativeClustering(n_clusters=len(subg)//n, linkage='ward', connectivity=X).fit(list(coords.values()))    
        else:
            if len(subg_dict) < len(def_conts):
                def_conts = {k: def_conts[k] for k in random.choices(list(def_conts.keys()), weights=list(def_conts.values()),k=len(subg_dict))}
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
    
    if def_names:        
        tdf = groups.copy()
        ff = list(tdf.keys())
        tgr = {ff[0]: tdf.pop(ff[0])}
        for i, v in enumerate(ff):
            if i < 1: continue
            tgr[v] = tdf.pop(sort_closest(groups[ff[i-1]], tdf, cyl=True)[0])
        for k in tgr:
            tgr[k]['name'] = k
        groups = tgr

    for g in groups:
        for i in groups[g]['in']:
            subg_dict[i]['par'] = g
        
    if disp:
        from scipy.spatial import ConvexHull
        print("display")
        x, y = np.array([x[0] for x in coords.values()]), np.array([x[1] for x in coords.values()])
        for corners in [[i for i in filter(lambda a: c == clusters[a], range(len(clusters)))] for c in set(clusters)]:
            if len(corners) > 3:
                ttf = ([[x[i], y[i]] for i in corners])
                hull = ConvexHull(ttf)
                plt.fill([ttf[x1][0] for x1 in hull.vertices], [ttf[y1][1] for y1 in hull.vertices], alpha=0.25, facecolor='grey', edgecolor='black', linewidth=3)
            else:
                plt.fill(x[corners], y[corners], alpha=0.25, facecolor='grey', edgecolor='black', linewidth=3)
        plt.scatter(x, y, c=clusters)
        plot_g(groups)
    return groups

def group_agg_w(subg_dict: dict, n, typ, all_provs, disp=False, def_conts={}, def_names=True, weights=[], is_sea=False):
    if len(subg_dict) == 0: return {}
    subg = nx.Graph()
    subg.add_nodes_from([(k, v) for k, v in subg_dict.items()])
    print(f"Generating {typ}s from {len(subg_dict)} items...")
    
    for u in subg:
        for adj in all_provs[u]['adj']:
            if adj in subg.nodes:
                subg.add_edge(u, adj, weight=weight(all_provs[u]['type'], all_provs[adj]['type']))
    
    coords = nx.get_node_attributes(subg, 'xy')
    nodes = list(subg.nodes)
    X = nx.adjacency_matrix(subg)

    if len(subg_dict) < 2:
        if len(def_conts) == 0:
            names = gn.generate_names(1)
        else:
            names = random.sample(list(def_conts.keys()), counts=list(def_conts.values()), k=1)     
        clusters = [0]
        n_clusters = 1       
    else:
        import graph_gen_weight as ggs
        if len(weights) > 0:
            if len(def_conts) == 0:
                names = gn.generate_names(len(coords)//n)
            else:
                if len(subg_dict) < len(def_conts):
                    def_conts = {k: def_conts[k] for k in random.choices(list(def_conts.keys()), weights=list(def_conts.values()),k=len(subg_dict))}
                names = list(def_conts.keys()) if def_names else gn.generate_names(len(def_conts))
            model = AgglomerativeClustering(n_clusters=min(sum(weights), len(subg)), linkage='ward', connectivity=X).fit(list(coords.values()))
            clusters = ggs.group_weight(model, coords, nodes, weights)
            n_clusters = len(weights)
            
        else:
            if len(def_conts) == 0:
                names = gn.generate_names(len(coords)//n)
                model = AgglomerativeClustering(n_clusters=len(subg)//n, linkage='ward', connectivity=X).fit(list(coords.values()))
            else:
                if len(subg_dict) < len(def_conts):
                    def_conts = {k: def_conts[k] for k in random.choices(list(def_conts.keys()), weights=list(def_conts.values()),k=len(subg_dict))}
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
    
    if def_names:        
        tdf = groups.copy()
        ff = list(tdf.keys())
        tgr = {ff[0]: tdf.pop(ff[0])}
        for i, v in enumerate(ff):
            if i < 1: continue
            tgr[v] = tdf.pop(sort_closest(groups[ff[i-1]], tdf, cyl=True)[0])
        for k in tgr:
            tgr[k]['name'] = k
        groups = tgr

    for g in groups:
        for i in groups[g]['in']:
            subg_dict[i]['par'] = g
        
    if disp:
        from scipy.spatial import ConvexHull
        print("display")
        x, y = np.array([x[0] for x in coords.values()]), np.array([x[1] for x in coords.values()])
        for corners in [[i for i in filter(lambda a: c == clusters[a], range(len(clusters)))] for c in set(clusters)]:
            if len(corners) > 3:
                ttf = ([[x[i], y[i]] for i in corners])
                hull = ConvexHull(ttf)
                plt.fill([ttf[x1][0] for x1 in hull.vertices], [ttf[y1][1] for y1 in hull.vertices], alpha=0.25, facecolor='grey', edgecolor='black', linewidth=3)
            else:
                plt.fill(x[corners], y[corners], alpha=0.25, facecolor='grey', edgecolor='black', linewidth=3)
        plt.scatter(x, y, c=clusters)
        plot_g(groups)
    return groups

def weight(a, b, is_sea=False):
    typa = 'prov' if 'PROV' in a else 'sea' if 'SEA' in a else 'lake' if 'LAKE' in a else 'waste'
    typb = 'prov' if 'PROV' in b else 'sea' if 'SEA' in b else 'lake' if 'LAKE' in b else 'waste'
    if is_sea: return 0.2 if typa == typb == 'sea' else 2 if typa == typb == 'prov' else 3 if typa+typb == 'provsea' or typa+typb == 'seaprov' else 10000 if 'waste' in typa+typb else 1000
    return 0.2 if typa == typb == 'prov' else 1 if typa == typb == 'sea' else 2 if typa+typb == 'provsea' or typa+typb == 'seaprov' else 10000 if 'waste' in typa+typb else 1000

def center(xy: list):
    if len(xy) == 0: return [-1, -1]
    x = sum(x[0] for x in xy)//len(xy)
    y = sum(y[1] for y in xy)//len(xy)
    return [x, y]

def distance(a, b, cyl=False, WIDTH=5632):
    if cyl: return (min(abs(a[1] - b[1]), WIDTH - abs(a[1] - b[1])))**2 + (a[0] - b[0])**2
    return (a[0] - b[0])**2 + (a[1] - b[1])**2

def sort_closest(prov: dict, all_provs: dict, sorting = None, cyl=False):
    if sorting == None: sorting = all_provs.keys()
    return sorted(sorting, key=lambda p: distance(prov['xy'], all_provs[p]['xy'], cyl=cyl) )# (prov['xy'][0] - all_provs[p]['xy'][0])**2 + (prov['xy'][1] - all_provs[p]['xy'][1])**2)

def plot_g(g):
    if type(g) != nx.Graph:
        tg = nx.Graph()
        tg.add_nodes_from([(k, v) for k, v in g.items()])
        for u in g:
            for adj in g[u]['adj']:
                if adj in g:
                    tg.add_edge(u, adj)
        g = tg
    
    pos = nx.get_node_attributes(g, "xy")
    nx.draw_networkx(g, pos, font_size=9, alpha=0.7, node_size=200)
    
    plt.gca().invert_yaxis()
    plt.show()

if __name__ == "__main__":
    all_pairs = None
    # types = ['land']*5 + ['sea']*5
    # nodes = {i: {'type': types[i], 'xy': [2*i, i**2]} for i in range(10)}
    # print(nodes)
    # conns = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 0]]

    subg_dict = {
        '64-64-0': {'province': '1', 'red': '64', 'green': '64', 'blue': '0', 'type': 'PROVINCE_0', 'adj': {'67-191-0', '65-168-0', '67-154-0', '65-94-0', '64-101-0'}, 'xy': [1823, 1063]},
        '64-101-0': {'province': '2', 'red': '64', 'green': '101', 'blue': '0', 'type': 'PROVINCE_1', 'adj': {'66-87-0', '67-228-0', '72-193-0', '65-168-0', '64-64-0', '64-138-0', '64-212-0', '65-94-0', '65-242-0'}, 'xy': [1853, 1049]},
        '64-138-0': {'province': '3', 'red': '64', 'green': '138', 'blue': '0', 'type': 'PROVINCE_2', 'adj': {'66-161-0', '67-228-0', '66-235-0', '64-212-0', '67-80-0', '64-101-0'}, 'xy': [1902, 1046]},
        '64-175-0': {'province': '4', 'red': '64', 'green': '175', 'blue': '0', 'type': 'PROVINCE_3', 'adj': {'67-228-0', '67-191-0', '66-124-0', '65-94-0', '65-131-0'}, 'xy': [1865, 1103]},
        '64-212-0': {'province': '5', 'red': '64', 'green': '212', 'blue': '0', 'type': 'PROVINCE_4', 'adj': {'64-138-0', '66-87-0', '66-161-0', '64-101-0'}, 'xy': [1884, 1035]},
        '64-249-0': {'province': '6', 'red': '64', 'green': '249', 'blue': '0', 'type': 'PROVINCE_5', 'adj': {'65-168-0', '67-154-0', '11-108-174', '69-251-0', '80-211-0', '68-221-0', '65-205-0'}, 'xy': [1770, 1043]},
        '65-94-0': {'province': '7', 'red': '65', 'green': '94', 'blue': '0', 'type': 'PROVINCE_6', 'adj': {'67-228-0', '67-191-0', '64-64-0', '64-101-0', '64-175-0'}, 'xy': [1846, 1075]},
        '65-131-0': {'province': '8', 'red': '65', 'green': '131', 'blue': '0', 'type': 'PROVINCE_7', 'adj': {'67-228-0', '66-124-0', '66-235-0', '100-108-0', '64-175-0', '66-198-0', '11-111-160'}, 'xy': [1902, 1124]},
        '65-168-0': {'province': '9', 'red': '65', 'green': '168', 'blue': '0', 'type': 'PROVINCE_8', 'adj': {'64-64-0', '67-154-0', '64-101-0', '68-221-0', '65-242-0', '64-249-0'}, 'xy': [1806, 1045]},
        '65-205-0': {'province': '10', 'red': '65', 'green': '205', 'blue': '0', 'type': 'PROVINCE_9', 'adj': {'68-73-0', '135-233-0', '67-191-0', '67-154-0', '67-117-0', '11-108-174', '10-81-182', '64-249-0'}, 'xy': [1776, 1097]},
        '65-242-0': {'province': '11', 'red': '65', 'green': '242', 'blue': '0', 'type': 'PROVINCE_10', 'adj': {'72-193-0', '64-101-0', '68-221-0', '65-168-0'}, 'xy': [1832, 1033]},
        '66-87-0': {'province': '12', 'red': '66', 'green': '87', 'blue': '0', 'type': 'PROVINCE_11', 'adj': {'66-161-0', '72-193-0', '64-212-0', '68-184-0', '71-89-0', '64-101-0'}, 'xy': [1873, 1006]},
        '66-124-0': {'province': '13', 'red': '66', 'green': '124', 'blue': '0', 'type': 'PROVINCE_12', 'adj': {'10-88-211', '135-233-0', '67-191-0', '67-117-0', '65-131-0', '64-175-0', '66-198-0'}, 'xy': [1850, 1143]},
        '66-161-0': {'province': '14', 'red': '66', 'green': '161', 'blue': '0', 'type': 'PROVINCE_13', 'adj': {'69-140-0', '66-87-0', '64-138-0', '89-185-0', '64-212-0', '67-80-0', '68-147-0', '71-89-0'}, 'xy': [1903, 992]},
        '66-198-0': {'province': '15', 'red': '66', 'green': '198', 'blue': '0', 'type': 'PROVINCE_14', 'adj': {'66-124-0', '10-88-211', '65-131-0', '11-111-160'}, 'xy': [1883, 1164]},
        '66-235-0': {'province': '16', 'red': '66', 'green': '235', 'blue': '0', 'type': 'PROVINCE_15', 'adj': {'130-231-0', '67-228-0', '64-138-0', '100-108-0', '110-223-0', '67-80-0', '10-189-233', '11-171-139', '65-131-0'}, 'xy': [1944, 1078]},
        '67-80-0': {'province': '17', 'red': '67', 'green': '80', 'blue': '0', 'type': 'PROVINCE_16', 'adj': {'130-231-0', '66-161-0', '64-138-0', '66-235-0', '68-147-0'}, 'xy': [1933, 1042]},
        '67-117-0': {'province': '18', 'red': '67', 'green': '117', 'blue': '0', 'type': 'PROVINCE_17', 'adj': {'10-88-211', '68-73-0', '135-233-0', '66-124-0', '11-169-136', '10-72-150', '134-240-0', '65-205-0'}, 'xy': [1800, 1160]},
        '67-154-0': {'province': '19', 'red': '67', 'green': '154', 'blue': '0', 'type': 'PROVINCE_18', 'adj': {'67-191-0', '64-64-0', '65-168-0', '64-249-0', '65-205-0'}, 'xy': [1800, 1074]},
        '67-191-0': {'province': '20', 'red': '67', 'green': '191', 'blue': '0', 'type': 'PROVINCE_19', 'adj': {'135-233-0', '64-64-0', '66-124-0', '67-154-0', '65-94-0', '64-175-0', '65-205-0'}, 'xy': [1827, 1096]},
        '67-228-0': {'province': '21', 'red': '67', 'green': '228', 'blue': '0', 'type': 'PROVINCE_20', 'adj': {'64-138-0', '66-235-0', '65-94-0', '65-131-0', '64-101-0', '64-175-0'}, 'xy': [1884, 1080]},
        '68-73-0': {'province': '22', 'red': '68', 'green': '73', 'blue': '0', 'type': 'PROVINCE_21', 'adj': {'67-117-0', '10-81-182', '10-72-150', '65-205-0'}, 'xy': [1756, 1131]},
        '68-110-0': {'province': '23', 'red': '68', 'green': '110', 'blue': '0', 'type': 'PROVINCE_22', 'adj': {'95-143-0', '68-184-0', '71-89-0', '69-177-0', '80-211-0'}, 'xy': [1835, 969]},
        '68-147-0': {'province': '24', 'red': '68', 'green': '147', 'blue': '0', 'type': 'PROVINCE_23', 'adj': {'130-231-0', '66-161-0', '108-200-0', '251-235-1', '201-178-1', '89-185-0', '67-80-0', '70-170-0'}, 'xy': [1955, 991]},
        '68-184-0': {'province': '25', 'red': '68', 'green': '184', 'blue': '0', 'type': 'PROVINCE_24', 'adj': {'68-110-0', '66-87-0', '72-193-0', '71-89-0', '80-211-0', '68-221-0'}, 'xy': [1838, 998]},
        '68-221-0': {'province': '26', 'red': '68', 'green': '221', 'blue': '0', 'type': 'PROVINCE_25', 'adj': {'72-193-0', '65-168-0', '68-184-0', '80-211-0', '65-242-0', '64-249-0'}, 'xy': [1813, 1018]},
        '69-66-0': {'province': '27', 'red': '69', 'green': '66', 'blue': '0', 'type': 'PROVINCE_26', 'adj': {'70-207-0', '137-244-2', '93-182-2', '249-65-7', '75-98-0', '119-86-0', '82-86-0'}, 'xy': [2066, 836]},
        '69-103-0': {'province': '28', 'red': '69', 'green': '103', 'blue': '0', 'type': 'PROVINCE_27', 'adj': {'70-133-0', '75-135-0', '110-223-0', '126-74-0', '102-107-4'}, 'xy': [2021, 1097]},
        '69-140-0': {'province': '29', 'red': '69', 'green': '140', 'blue': '0', 'type': 'PROVINCE_28', 'adj': {'66-161-0', '89-185-0', '69-177-0', '71-89-0', '70-170-0', '90-178-0'}, 'xy': [1883, 943]},
        '69-177-0': {'province': '30', 'red': '69', 'green': '177', 'blue': '0', 'type': 'PROVINCE_29', 'adj': {'68-110-0', '69-140-0', '95-143-0', '77-195-0', '71-89-0', '90-178-0'}, 'xy': [1850, 947]}
    }

    # g = nx.Graph()
    # g.add_nodes_from([(k, v) for k, v in nodes.items()])
    # g.add_edges_from([(conns[i][0], conns[i][1], {'weight': v})for i, v in enumerate([1 if nodes[x[0]]['type'] == nodes[x[1]]['type'] else 3 for x in conns])])
    # print(nx.adjacency_matrix(g).todense())

    # print(group_agg_w(subg_dict, 2, 'test', subg_dict, True))

    weights = [i for i in range(len(subg_dict)//2)]
    print(weights)
    print(group_agg_w(subg_dict, 2, 'test', subg_dict, True, weights=weights))

    def_conts = {'a': 50, 'b': 20, 'c': 30, 'd': 5}
    print(group_agg_w(subg_dict, 2, 'test', subg_dict, disp=True, def_conts=def_conts, weights=[v for v in def_conts.values()]))

    # print(nx.get_node_attributes(g, "xy"))
    # plot_g(g)