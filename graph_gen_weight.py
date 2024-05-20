import random
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull

def reduce_w(weights, n):
    tw = []
    for i, v in enumerate(weights):
        tw.append(round((n-sum(tw))*(v/sum(weights[i:]))))
    return tw

def group_weight(model, coords, nodes, weights, disp=False):
    clusters = model.labels_
    n_clusters = model.n_clusters_
    if sum(weights) != n_clusters: weights = reduce_w(weights, n_clusters)
    tg_m = {i: {
        'xy': center([xy for k, xy in enumerate(coords.values()) if clusters[k]==i]), 
        'in': set([n for ii, n in enumerate(nodes) if clusters[ii]==i]),
        } for i in set(clusters)}
    tg = tg_m.copy()
    group = {i: {'in': set(), 'xy': [-1, -1], 'inc': set()} for i in range(len(weights))}
    for i, v in enumerate(weights):
        if v > 0:
            if len(tg) > 3:
                ttf = {index: [tg_m[index]['xy'][0], tg_m[index]['xy'][1]] for index in tg}
                hull = ConvexHull(list(ttf.values()))
                ttg_key = random.choice([list(ttf.keys())[index] for index in hull.vertices])
            else:
                ttg_key = random.choice(list(tg.keys()))
            ttg_val = tg.pop(ttg_key)
            group[i]['in'].update(ttg_val['in'])
            group[i]['xy'] = ttg_val['xy']
            group[i]['inc'].add(ttg_key)
            tg_m[ttg_key]['par'] = i
            for _ in range(v-1):
                key = sort_closest(ttg_val, tg)[0]
                group[i]['in'].update(tg.pop(key)['in'])
                group[i]['inc'].add(key)
                tg_m[key]['par'] = i
    labels = [g for n in nodes for g in group if n in group[g]['in']]
    if disp:
        print(n_clusters, weights)
        print({k: len(v['in']) for k, v in group.items()})
        print({k: v['xy'] for k, v in group.items()})

        print("display")
        cds = {k: v['xy'] for k, v in tg_m.items()}
        cls = [v['par'] for k, v in tg_m.items()]
        draw_hull(cds, cls)
        plot_g(group)
        
        draw_hull(coords, clusters)
        plot_g(group)
                
        draw_hull(coords, labels)
        plot_g(group)

    return labels

def draw_hull(coords: dict, labels):
    x, y = np.array([x[0] for x in coords.values()]), np.array([x[1] for x in coords.values()])
    for corners in [[i for i in filter(lambda a: c == labels[a], range(len(labels)))] for c in set(labels)]:
        if len(corners) > 3:
            ttf = ([[x[i], y[i]] for i in corners])
            hull = ConvexHull(ttf)
            plt.fill([ttf[x1][0] for x1 in hull.vertices], [ttf[y1][1] for y1 in hull.vertices], alpha=0.25, facecolor='grey', edgecolor='black', linewidth=3)
        else:
            plt.fill(x[corners], y[corners], alpha=0.25, facecolor='grey', edgecolor='black', linewidth=3)
    plt.scatter(x, y, c=labels)

def distance(a, b, cyl=False, width=5632):
    if cyl: return (min(abs(a[1] - b[1]), width - abs(a[1] - b[1])))**2 + (a[0] - b[0])**2
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def sort_closest(prov: dict, all_provs: dict, sorting = None, cyl=False):
    if sorting == None: sorting = all_provs.keys()
    return sorted(sorting, key=lambda p: distance(prov['xy'], all_provs[p]['xy'], cyl=cyl) )# (prov['xy'][0] - all_provs[p]['xy'][0])**2 + (prov['xy'][1] - all_provs[p]['xy'][1])**2)

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