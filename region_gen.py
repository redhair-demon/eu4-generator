import random
import networkx as nx
import matplotlib.pyplot as plt

WIDTH = 5632

conts = ['europe', 'asia', 'africa', 'north_america', 'south_america', 'oceania']
conttxt = """europe = {
	
}

asia = {
	
}

africa = {
	
}

north_america = {
	
}

south_america = {
	
}

oceania = {
	
}

island_check_provinces = {
	
}

# Used for RNW
new_world = {
}

"""

prov_file_format = """base_manpower = {}
base_tax = {}
base_production = {}

culture = {}
religion = {}
"""

def set_lakes(provinces: dict):
    for p in provinces:
        if ('SEA_ZONE' in provinces[p]['name'] and 
            all(['SEA_ZONE' not in provinces[x]['name'] for x in provinces[p]['adj']])):
            provinces[p]['name'] = provinces[p]['name'].replace("SEA_ZONE", "LAKE")
    return provinces

def split_lwsl(provinces: dict):
    lands, wastes, seas, lakes = {}, {}, {}, {}
    for p in provinces:
        name = provinces[p]['name']
        if 'SEA_ZONE' in name: seas[p] = provinces[p]
        elif 'PROVINCE' in name: lands[p] = provinces[p]
        elif 'WASTELAND' in name: wastes[p] = provinces[p]
        elif 'LAKE' in name: lakes[p] = provinces[p]
    return lands, wastes, seas, lakes

def add_areas(provs: dict, all_provs: dict, limit: int = 3):
    areas = {}
    temp = provs.copy()
    print(len(temp))

    for l in provs:
        if l in temp:
            paired = False
            prov = temp.pop(l)
            for adj in prov['adj']: 
                if adj in temp:
                    temp.pop(adj)
                    areas[l] = {'in': set([l, adj]), 'adj': set()}
                    paired = True
                    break
            if not paired:
                for adj in prov['adj']:
                    if paired: break
                    if adj in provs:
                        for a in areas:
                            if adj in areas[a]['in'] and len(areas[a]['in']) <= limit*3: 
                                areas[a]['in'].add(l)
                                paired = True
                                break
            if not paired:
                for adj in prov['adj']:
                    if paired: break
                    for a in areas:
                        near = [provs[x]['adj'] for x in areas[a]['in']]
                        if adj in near and len(areas[a]['in']) <= limit*3:
                            areas[a]['in'].add(l)
                            paired = True
                            break
            if not paired: 
                areas[l] = {'in': set([l]), 'adj': set()}
    
    print(sum([len(x['in']) for x in areas.values()]), len(areas))
    # return areas

    temp = {}
    result = {}
    provs_copy = provs.copy()
    for a in areas: 
        if len(areas[a]['in']) < limit: temp[a] = areas[a]
        else: 
            result[a] = areas[a]
            for i in result[a]['in']:
                provs_copy.pop(i)
    
    skipped = set()
    for a in temp:
        paired = False
        if a in skipped: continue
        for ar in temp:
            if paired: break
            if ar in skipped: continue
            if a != ar:
                near = set()
                for x in [provs[t]['adj'] for t in temp[a]['in']]:
                    near.update(x)
                
                if any([x in temp[ar]['in'] and x not in temp[a]['in'] and x in provs_copy for x in near]):
                    result[a] = temp[a]
                    result[a]['in'].update(temp[ar]['in'])
                    result[a]['adj'].update(temp[ar]['adj'])
                    result[a]['adj'].difference_update(result[a]['in'])
                    paired = True
                    skipped.update([a, ar])
                    break

    for a in temp:
        if a not in skipped:
            result[a] = temp[a]

    for a in result:
        near = set()
        for t in [provs[x]['adj'] for x in result[a]['in']]:
            near.update(t)
        near.difference_update(result[a]['in'])
        result[a]['adj'] = near

    print(len(temp), len(areas), len(result), sum([len(x) for x in result.values()]))
    return result

def print_areas(file, areas, provinces, prefix = "Group areas"):
    file.write(f'\n# {prefix}\n\n')
    for key in areas: file.write(f'{areas[key]["name"]} = {{ # N={len(areas[key]["in"])}\n\t{" ".join([provinces[x]["province"] for x in areas[key]["in"]])} \n}}\n')

def print_regions(file, regions, prefix = "Group regions"):
    file.write(f'\n# {prefix}\n\n')
    for key in regions: file.write(f'{regions[key]["name"]} = {{\n\tareas = {{\n\t\t{" ".join([x for x in regions[key]["in"]])}\n\t}}\n}}\n')

def print_sr(file, srs, prefix = "Group superregions"):
    file.write(f'\n# {prefix}\n\n')
    for key in srs: file.write(f'{srs[key]["name"]} = {{\n\t{" ".join([x for x in srs[key]["in"]])} \n}}\n')

def print_continents(file, cont, srs, rs, ars, all_provs, path, prefix, cultures, religions):
    # file.write(conttxt)
    file.write(f'\n# {prefix}\n\n')
    n = 0
    for key in cont: 
        provs = set()
        for sr in cont[key]['in']:
            srs[sr]['rel'] = random.choice(list(religions.keys()))
            for r in srs[sr]['in']:
                rs[r]['rel'] = random.choice(list(religions[srs[sr]['rel']]))
                rs[r]['cult'] = random.choice(list(cultures.keys()))
                for a in rs[r]['in']:
                    ars[a]['cult'] = random.choice(list(cultures[rs[r]['cult']]))
                    for p in ars[a]['in']:
                        provs.add(p)
                        all_provs[p]['cult'] = ars[a]['cult']
                        all_provs[p]['rel'] = rs[r]['rel']
        for x in provs:
            if "WASTE" in all_provs[x]["name"]: continue
            with open(f"{path}/history/provinces/{all_provs[x]['province']} - {all_provs[x]['name']}.txt", 'w') as prov_file:
                prov_file.write(prov_file_format.format(2, 2, 2, all_provs[x]['cult'], all_provs[x]['rel']))
        file.write(f'{cont[key]["name"]} = {{\n\t{" ".join([all_provs[x]["province"] for x in provs])} \n}}\n')
        # file.write(f'{conts[n]} = {{\n\t{" ".join([all_provs[x]["province"] for x in provs])} \n}}\n')
        n+=1

def print_trade_g(g: nx.DiGraph, trades, all_provs, file):
    for node in g:
        if trades[node]['printed']: continue
        print_trade_g(g.subgraph(g.pred[node]), trades, all_provs, file)
        outgoing = "\n\t".join([f"outgoing={{\n\t\tname=\"{x}\"\n\t}}" for x in g.succ[node]])
        file.write(f'{trades[node]["name"]} = {{\n\tlocation={trades[node]["loc"]} \n\t{outgoing} \n\tmembers={{\n\t\t{" ".join([all_provs[x]["province"] for x in trades[node]["mem"]])}\n\t}} \n}}\n')
        trades[node]['printed'] = True

def print_trade_node(node, g: nx.DiGraph, trades, all_provs, file):
    if not trades[node]['printed']:
        for pr in g.pred[node]:
            if trades[pr]['printed']: continue
            print_trade_node(pr, g, trades, all_provs, file)
        outgoing = "\n\t".join([f"outgoing={{\n\t\tname=\"{x}\"\n\t}}" for x in g.succ[node]])
        file.write(f'{trades[node]["name"]} = {{\n\tlocation={trades[node]["loc"]} \n\t{outgoing} \n\tmembers={{\n\t\t{" ".join([all_provs[x]["province"] for x in trades[node]["mem"]])}\n\t}} \n}}\n')
        trades[node]['printed'] = True

def connect(input_cc, g: nx.DiGraph, provs):
    sorted_cc = sorted(input_cc, key=len)
    done = []
    for cc in sorted_cc:
        if cc in done: continue
        closest = {'dist': None, 'from': None, 'to': None}
        for cc2 in filter(lambda b: sorted_cc.index(b)>sorted_cc.index(cc), sorted_cc):
            if cc2 in done: continue
            for cc_i in cc:
                cl = sort_closest(provs[cc_i], provs, cc2, cyl=True)
                if closest['dist'] == None or (distance(provs[cc_i]['xy'], provs[cl[0]]['xy']) < closest['dist']):
                    closest['dist'] = distance(provs[cc_i]['xy'], provs[cl[0]]['xy'])
                    closest['from'] = cc_i
                    closest['to'] = cl[0]
                    if (closest['dist'] == 0): print("zerooo")
        g.add_edge(closest['from'], closest['to'])

        done.append(cc)
        for x in sorted_cc:
            if closest['to'] in x: 
                done.append(x)
                break
    return g

def connets(g: nx.DiGraph, provs: dict, limit_dist: int, limit_size: int):
    # for n in g.nodes:
    #     cl = sort_closest(provs[n], provs, cyl=True)
    #     for c in cl:
    #         if c == n or nx.has_path(g, c, n) or len(g[n]) + len(g.pred[n]) >= limit_size//2 or len(list(nx.all_simple_paths(g, n, c))) >= 1:
    #             continue
    #         g.add_edge(n, c)
    for n in g.nodes:
        cl = sort_closest(provs[n], provs, cyl=True)
        for c in cl:
            if c == n or nx.has_path(g, c, n) or len(g[n]) + len(g.pred[n]) >= limit_size or distance(provs[c]['xy'], provs[n]['xy'], cyl=True) > limit_dist**2 or len(list(nx.all_simple_paths(g, n, c))) >= 1:
                continue
            g.add_edge(n, c)
        if len(g[n]) + len(g.pred[n]) == 0:
            g.add_edge(n, cl[1])

    if not nx.is_weakly_connected(g):
        g = connect(nx.weakly_connected_components(g), g, provs)

    return g

def print_trades(file, trades, ars, all_provs, path, limit_dist, limit_size):
    keys = list(trades.keys())
    G = nx.DiGraph()
    for key in keys: 
        trades[key]['out'] = set()
        G.add_nodes_from([(key, {"xy": (trades[key]['xy'][1], -trades[key]['xy'][0])})])
    G = connets(G, trades, limit_dist, limit_size)
    pos = nx.get_node_attributes(G, "xy")
    nx.draw_networkx(G, pos)
    plt.show()
    
    for key in keys: 
        provs = set()
        for a in trades[key]['in']:
            for p in ars[a]['in']:
                provs.add(p)
        trades[key]['loc'] = all_provs[list(provs)[0]]["province"]
        trades[key]['mem'] = provs
        trades[key]['posts'] = random.choices(list(trades[key]['mem']), k=hash(key) % 6 + 2)
        trades[key]['printed'] = False
        for post in trades[key]['posts']:
            with open(f"{path}/history/provinces/{all_provs[post]['province']} - {all_provs[post]['name']}.txt", 'a') as prov_file:
                prov_file.write(f"\ncenter_of_trade = 1\n")

    for node in G:
        print_trade_node(node, G, trades, all_provs, file)
    # print_trade_g(G, trades, all_provs, file)
    # print(G.['trade_area_76-240-5'])
    
def center(prov_keys, all_provs):
    x = sum([all_provs[i]['xy'][0] for i in prov_keys])//len(prov_keys)
    y = sum([all_provs[i]['xy'][1] for i in prov_keys])//len(prov_keys)
    return [x, y]

def distance(a, b, cyl=False):
    if cyl: return (min(abs(a[1] - b[1]), WIDTH - abs(a[1] - b[1])))**2 + (a[0] - b[0])**2
    return (a[0] - b[0])**2 + (a[1] - b[1])**2

def sort_closest(prov: dict, all_provs: dict, sorting = None, cyl=False):
    if sorting == None: sorting = all_provs.keys()
    return sorted(sorting, key=lambda p: distance(prov['xy'], all_provs[p]['xy'], cyl=cyl) )# (prov['xy'][0] - all_provs[p]['xy'][0])**2 + (prov['xy'][1] - all_provs[p]['xy'][1])**2)

def group_by_xy(provs: dict, limit_size: list = [3, 10], limit_dist: int = 150, typ: str = "area"):
    areas = {}
    print(len(provs))

    for l in provs:
        if provs[l]['par'] == None:
            cl = sort_closest(provs[l], provs)
            for p in filter(lambda a: a!=l, cl):
                if provs[p]['par'] == None:
                    if distance(provs[p]['xy'], provs[l]['xy']) <= (limit_dist)**2:
                        areas[f"{typ}_{l}"] = {'in': set([l, p]), 'par': None, 'xy': center([l, p], provs), 'name': f"{typ}_{l}"}
                        provs[p]['par'] = f"{typ}_{l}"
                        provs[l]['par'] = f"{typ}_{l}"
                        break
                else:
                    if len(areas[provs[p]['par']]['in']) > limit_size[1] or distance(areas[provs[p]['par']]['xy'], provs[l]['xy']) > (limit_dist)**2:
                        continue
                    else:
                        areas[provs[p]['par']]['in'].add(l)
                        areas[provs[p]['par']]['xy'] = center(areas[provs[p]['par']]['in'], provs)
                        provs[l]['par'] = provs[p]['par']
                        break
            if provs[l]['par'] == None:
                areas[f"{typ}_{l}"] = {'in': set([l]), 'par': None, 'xy': center([l], provs), 'name': f"{typ}_{l}"}
                provs[l]['par'] = f"{typ}_{l}"
    
    temp = areas.copy()
    for a in temp:
        if a in areas and len(areas[a]['in']) < limit_size[0]:
            cl = sort_closest(areas[a], areas)
            for ar in filter(lambda d: d!=a, cl):
                if len(areas[a]['in']) > limit_size[0]: break
                if distance(areas[a]['xy'], areas[ar]['xy']) <= (limit_dist)**2:
                    deleted = areas.pop(ar)
                    areas[a]['in'].update(deleted['in'])
                    for l in deleted['in']: provs[l]['par'] = a

    # mm = [0, '']
    # for a in areas:
    #     tt = [[x, sort_closest(provs[x], provs, areas[a]['in'])[-1]] for x in areas[a]['in']]
    #     areas[a]['dist'] = math.sqrt(max([((provs[x[0]]['xy'][0] - provs[x[1]]['xy'][0])**2 + (provs[x[0]]['xy'][1] - provs[x[1]]['xy'][1])**2) for x in tt])).__floor__()
    #     if areas[a]['dist'] > mm[0]: 
    #         mm = [areas[a]['dist'], a]
    # with open('output.txt', 'w') as file:
    #     for a in sorted(areas, key=lambda b: -areas[b]['dist']):
    #         file.write(f"{a}: {areas[a]}\n")
    # print(sum([len(x['in']) for x in areas.values()]), len(areas), mm)
    return areas

def gen_areas(provinces: dict, path: str, cultures: dict, religions: dict):
    provinces = set_lakes(provinces)
    temp = provinces.copy()
    for i in temp:
        temp[i]['par'] = None
    lands, wastes, seas, lakes = split_lwsl(temp)
    land_areas = group_by_xy(lands, [3, 8])
    sea_areas = group_by_xy(seas, [5, 12])
    # waste_areas = add_areas_xy(wastes, [3, 5])

    with open(f'{path}/map/area.txt', 'w') as file:
        print_areas(file, land_areas, provinces, "Land areas")
        print_areas(file, sea_areas, provinces, "Sea areas")

    land_regions = group_by_xy(land_areas, [4, 6], 400, "region")
    sea_regions = group_by_xy(sea_areas, [4, 8], 700, "sea_region")
    # waste_regions = add_areas_xy(waste_areas, [2, 3])

    with open(f'{path}/map/region.txt', 'w') as file:
        print_regions(file, land_regions, "Land regions")
        print_regions(file, sea_regions, "Sea regions")

    land_sr = group_by_xy(land_regions, [4, 8], 1000, "superregion")
    sea_sr = group_by_xy(sea_regions, [6, 10], 1000, "sea_superregion")
    # waste_sr = add_areas_xy(waste_regions, [2, 3])/

    with open(f'{path}/map/superregion.txt', 'w') as file:
        print_sr(file, land_sr, "Land superregions")
        print_sr(file, sea_sr, "Sea superregions")

    
    continents = group_by_xy(land_sr, [3, 6], 2000, "continent")

    # adding wastelands to continents begin
    waste_areas = {x: {'in': set([x]), 'par': x, 'xy': provinces[x]['xy'], 'name': f"waste_{x}"} for x in wastes}
    lw_sr, lw_reg, lw_ar = land_sr.copy(), land_regions.copy(), land_areas.copy()
    lw_sr.update(waste_areas)
    lw_reg.update(waste_areas)
    lw_ar.update(waste_areas)

    for w in waste_areas:
        cl = sort_closest(waste_areas[w], lands)
        continents[land_sr[land_regions[land_areas[lands[cl[0]]['par']]['par']]['par']]['par']]['in'].add(w)
    # end

    with open(f'{path}/map/continent.txt', 'w') as file:
        print_continents(file, continents, lw_sr, lw_reg, lw_ar, provinces, path, "custom continents", cultures, religions)

    temp = {}
    for l in reversed(list(land_areas.keys())):
        temp[l] = land_areas[l]
        temp[l]['par'] = None
    trades = group_by_xy(temp, [6, 12], 900, "trade")
    print(len(trades))
    with open(f"{path}/common/tradenodes/00_tradenodes.txt", 'w') as file:
        print_trades(file, trades, land_areas, lands, path, 500, 3)

    return land_areas
    

        