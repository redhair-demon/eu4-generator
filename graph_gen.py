import networkx as nx
import matplotlib.pyplot as plt
import gen_names as gn
from sklearn.cluster import KMeans

def group_kmean(subg: dict, n, typ, disp=False):
    print(f"Generating {typ}s from {len(subg)} items...")

    colors = ["red","green","blue","yellow","pink","black","orange","purple"]
    X, nodes = [], []
    for u in subg:
        nodes.append(u)
        X.append(subg[u]['xy'])
    
    names = gn.generate_names(len(X)//n)

    model = KMeans(n_clusters=len(X)//n, tol=0.1).fit(X)
    clusters = model.labels_
    
    groups = {f"{names[i]}_{typ}": {'name': f"{names[i]}_{typ}", 'xy': x, 'in': set([n for ii, n in enumerate(nodes) if clusters[ii]==i])} for i, x in enumerate(model.cluster_centers_)}
    for g in groups:
        for i in groups[g]['in']:
            subg[i]['par'] = g
    if disp:
        plt.scatter([x[0] for x in X], [x[1] for x in X], c=[colors[i%len(colors)] for i in clusters])
        plot_g(groups)
    return groups

def plot_g(g):
    pos = nx.get_node_attributes(g, "xy")
    nx.draw_networkx(g, pos, font_size=9, alpha=0.7, node_size=200)
    plt.gca().invert_yaxis()
    plt.show()

