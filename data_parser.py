import re
import os
import csv
import yaml
import main

def read_dict_conts(path, prim_pop = [], inner_pop = []):
    prim = r"^([\w_]+)\s*=\s*{"
    inner = r"^\t((?:(?:\d+) *)+)"
    dictionary = {}
    with open(path, 'r') as file:
        for line in file:
            mat = re.search(prim, line)
            if mat != None:
                current = mat.group(1)
                dictionary[current] = {'mem': set(), 'culture_group': {}}
            else:
                mat = re.search(inner, line)
                if mat != None:
                    dictionary[current]['mem'].update([x for x in mat.group(1).split(" ") if x.isnumeric()])
    for p in prim_pop:
        if p in dictionary: dictionary.pop(p)
    for c in dictionary:
        dictionary[c]['mem'].difference_update(inner_pop)
    return dictionary

def create_files_from_csv(file_path):
    provinces = {}
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=";", fieldnames=['province', 'red', 'green', 'blue', 'type', 'x'],)
        next(reader, None)
        for row in reader:
            provinces.update({row['province']: {'name': row['type']}})
            
    return provinces

def read_all_prov_files(path, props = [], regex = r"^(\d+)"):
    provs = {}
    files = next(os.walk(path), (None, None, []))[2]
    for filename in files:
        with open(f"{path}/{filename}") as file:
            id = re.search(regex, filename).group(1)
            provs[id] = {}
            for line in file:
                mat = re.search(r"^(\w+) *= *(\S+)", line)
                if mat != None:
                    if mat.group(1) in props:
                        provs[id][mat.group(1)] = mat.group(2).strip("\"\'")
                    if all([x in provs[id] for x in props]): break
    return provs

def add_to_dict(continents: dict, c: str, provs: dict, p:str, religions: dict, cultures: dict, cat_name: str, group_name: str = 'culture_group', culture_name: str = 'culture'):
    rel = provs[p][cat_name] if cat_name in provs[p] else None
    cul = provs[p][culture_name] if culture_name in provs[p] else None
    if rel != None and cul != None:
        # print(c, group_name, cultures[cul], cat_name, religions[rel], rel)
        if cultures[cul] in continents[c][group_name]:
            if cat_name in continents[c][group_name][cultures[cul]]:
                if religions[rel] in continents[c][group_name][cultures[cul]][cat_name]:
                    if rel in continents[c][group_name][cultures[cul]][cat_name][religions[rel]]:
                        continents[c][group_name][cultures[cul]][cat_name][religions[rel]][rel] += 1
                    else:
                        continents[c][group_name][cultures[cul]][cat_name][religions[rel]][rel] = 1
                else:
                    continents[c][group_name][cultures[cul]][cat_name][religions[rel]] = {rel: 1}
            else:
                continents[c][group_name][cultures[cul]][cat_name] = {religions[rel]: {rel: 1}}
        else:
            continents[c][group_name][cultures[cul]] = {cat_name: {religions[rel]: {rel: 1}}}


def add_to_dict_from_owner(continents: dict, c: str, provs: dict, p:str, religions: dict, cultures: dict, cat_name: str, owner_cat_name: str, group_name: str = 'culture_group', culture_name: str = 'culture'):
    # rel = provs[p][cat_name] if cat_name in provs[p] else None
    rel = provs[p][owner_cat_name] if owner_cat_name in provs[p] else None
    cul = provs[p][culture_name] if culture_name in provs[p] else None
    if rel != None and cul != None:
        # print(c, group_name, cultures[cul], cat_name, religions[rel], rel)
        if cultures[cul] in continents[c][group_name]:
            if cat_name in continents[c][group_name][cultures[cul]]:
                if religions[rel][cat_name] in continents[c][group_name][cultures[cul]][cat_name]:
                    continents[c][group_name][cultures[cul]][cat_name][religions[rel][cat_name]] +=1
                else:
                    continents[c][group_name][cultures[cul]][cat_name][religions[rel][cat_name]] = 1
            else:
                continents[c][group_name][cultures[cul]][cat_name] = {religions[rel][cat_name]: 1}
        else:
            continents[c][group_name][cultures[cul]] = {cat_name: {religions[rel][cat_name]: 1}}

def read_dict_positions(path, prim_pop = [], inner_pop = []):
    prim = r"^([\d_]+)\s*=\s*{"
    inner = r"^\tposition\s*=\s*{"
    univ = r"(\d+)\s*=\s*{\n\tposition\s*=\s*{\n\t\t(\d+).\d+ (\d+)"
    dictionary = {}
    with open(path, 'r') as file:
        text = file.read()
        for mat in re.finditer(univ, text):
            dictionary[int(mat.group(1))] = {'xy': [int(mat.group(2)), int(mat.group(3))]}
        # for line in file:
        #     mat = re.search(prim, line)
        #     if mat != None:
        #         current = mat.group(1)
        #         dictionary[current] = {'xy': []}
        #     else:
        #         mat = re.search(inner, line)
        #         if mat != None:
        #             dictionary[current]['mem'].update([x for x in mat.group(1).split(" ") if x.isnumeric()])
    # for p in prim_pop:
    #     if p in dictionary: dictionary.pop(p)
    # for c in dictionary:
    #     dictionary[c]['mem'].difference_update(inner_pop)
    return dictionary

def dict_inv(d: dict):
    temp = {}
    for k, v in d.items():
        for vv in v:
            temp[vv] = k
    return temp

def plot_feat(provs, feature):
    printable = list(filter(lambda x: feature in provs[x], list(provs.keys())))
    features = {v: i for i, v in enumerate(set([provs[x][feature] for x in printable]))}
    print(len(printable), len([provs[x]['xy'][0] for x in printable]), len([provs[x]['xy'][1] for x in printable]))
    plt.scatter([provs[x]['xy'][0] for x in printable], [provs[x]['xy'][1] for x in printable], c=[features[provs[x][feature]] for x in printable])
    plt.show()

if __name__ == "__main__":
    game_folder = 'D:/steam/steamapps/common/Europa Universalis IV'
    pos = read_dict_positions(f"{game_folder}/map/positions.txt")

    import matplotlib.pyplot as plt
    print(sum([x['xy'][0] == x['xy'][1] == 1 for x in pos.values()]))
    print(sum([x['xy'][0] == x['xy'][1] for x in pos.values()]))
    
    # for i in range(max(pos.keys())):
    #     if i not in pos:
    #         print(i)

# if __name__ == "__main__":
# def continents_data():
    game_folder = 'D:/steam/steamapps/common/Europa Universalis IV'
    continents = read_dict_conts(f"{game_folder}/map/continent.txt", prim_pop=['island_check_provinces', 'new_world'])
    print([{x: len(continents[x]['mem'])} for x in continents])
    provs = create_files_from_csv(f"{game_folder}/map/definition.csv")
    provs.update(read_all_prov_files(f"{game_folder}/history/provinces", ['culture', 'religion', 'owner']))

    for k, v in provs.items():
        provs[k]['xy'] = pos[int(k)]['xy']
        # if 'religion' not in v: print(k, v)
    plot_feat(provs, 'religion')
    plot_feat(provs, 'culture')
    
    countries = read_all_prov_files(f"{game_folder}/history/countries", ['primary_culture', 'religion', 'technology_group'], r"^(\w{3})")

    cultures = dict_inv(main.read_dict(f"{game_folder}/common/cultures/00_cultures.txt", [], ['graphical_culture', 'male_names', 'female_names', 'dynasty_names']))
    religions = dict_inv(main.read_dict(f"{game_folder}/common/religions/00_religion.txt", [], ['flag_emblem_index_range', 'religious_schools']))

    for c in continents:
        for p in continents[c]['mem']:
            add_to_dict(continents, c, provs, p, cultures, cultures, 'culture')
            add_to_dict(continents, c, provs, p, religions, cultures, 'religion')
            add_to_dict_from_owner(continents, c, provs, p, countries, cultures, 'technology_group', 'owner')
            # add_to_dict_from_owner(continents, c, provs, p, countries, 'owner', 'technology_group')

    # yaml.dump(continents, open('default_data.yml', 'w'), sort_keys=False)

def write_data(continents):
    with open('default_data.yml', 'w') as file:
        for c in continents:
            continents[c].pop('mem')
            for cat in ['culture_group']:
                for cg in continents[c][cat]:
                    for subc in ['culture', 'religion']:
                        for group in continents[c][cat][cg][subc]:
                            continents[c][cat][cg][subc][group]['total'] = sum(v for v in continents[c][cat][cg][subc][group].values())
                        continents[c][cat][cg][subc]['total'] = sum(v['total'] for v in continents[c][cat][cg][subc].values())
                    for subc in ['technology_group']:
                        if subc in continents[c][cat][cg]:
                            continents[c][cat][cg][subc]['total'] = sum(v for v in continents[c][cat][cg][subc].values())
                continents[c][cat]['total'] = sum(v['culture']['total'] for v in continents[c][cat].values())
        file.write(yaml.dump(continents, sort_keys=False))
    
    # for c, cats in continents.items():
    #     print(cats)
    #     for cat, groups in cats.items():
    #         for gr, i in groups.items():
    #             print(c, cat, gr, sum(val for val in i.values()))
    # print([{k: {kk: {kkk: sum([i for i in vvv.values()]) for kkk, vvv in vv.items()} for kk, vv in v.items()}} for k, v in continents.items()])
    # print([{c: {{cat: {{group: sum([i for i in continents[c][cat][group].values()])} for group in continents[c][cat]}}for cat in continents[c]} for c in continents}])