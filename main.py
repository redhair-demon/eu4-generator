import csv
import random
import re
import region_gen as rg
from PIL import Image
import os
import yaml

mod = """name="{}"
replace_path="history/provinces"
replace_path="history/diplomacy"
replace_path="history/wars"
replace_path="history/countries"
#replace_path="missions"
replace_path="common/bookmarks"
replace_path="common/province_names"
tags={{
	"map"
}}
picture="nameofapicture.png"
supported_version="1.35.*"
path="mod/{}"
"""

def rgb(pixel): return f"{pixel[0]}-{pixel[1]}-{pixel[2]}"

def find_neighbors(image_path, provinces):
    img = Image.open(image_path)
    width, height = img.size
    print(f"Proceeding {image_path}:")
    temp = img.getpixel((0,0))
    for i in range(1, width * height-1):
        pixel = img.getpixel((i % width, i // width))
        provinces[rgb(pixel)]['pixels'].append([i % width, i // width])
        
        if (pixel != temp):
            provinces[rgb(pixel)]['adj'].add(rgb(temp))
            provinces[rgb(temp)]['adj'].add(rgb(pixel))
        temp = pixel
        if (i % (width*height//10) == 0): print(f"{(i*100 / (width*height)).__ceil__()}%")
    
    for i in range(width):
        temp = img.getpixel((i,0))
        for k in range(height):
            pixel = img.getpixel((i, k))
            if (pixel != temp):
                provinces[rgb(pixel)]['adj'].add(rgb(temp))
                provinces[rgb(temp)]['adj'].add(rgb(pixel))
            temp = pixel

    for i in provinces:
        provinces[i]['xy'] = center(provinces[i]['pixels']) # [sum(provinces[i]['tdlr'][:2])//2, sum(provinces[i]['tdlr'][2:])//2]

    return provinces

def center(pixels: list):
    x = sum([i[0] for i in pixels]) // len(pixels)
    y = sum([i[1] for i in pixels]) // len(pixels)
    return [x, y]

def read_neighbors(file_path):
    # regexp = r"(\d+-\d+-\d+): {'province': '(\d+)', 'red': '(\d+)', 'green': '(\d+)', 'blue': '(\d+)', 'name': '([^'\r]+)', 'x': 'x', 'adj': {((?:'\d+-\d+-\d+'(?:, )?)+)}, 'tdlr': \[(\d+), (\d+), (\d+), (\d+)\], 'xy': \[(\d+), (\d+)\]}"
    regexp = r"(\d+-\d+-\d+): {'province': '(\d+)', 'red': '(\d+)', 'green': '(\d+)', 'blue': '(\d+)', 'type': '([^'\r]+)', 'adj': {((?:'\d+-\d+-\d+'(?:, )?)+)}, 'xy': \[(\d+), (\d+)\]}"
    result = {}
    with open(file_path, 'r') as file:
        for line in file:
            mat = re.search(regexp, line)
            rgb, id, r, g, b, name, adj_str, x, y = mat.group(1), mat.group(2), mat.group(3), mat.group(4), mat.group(5), mat.group(6), mat.group(7), mat.group(8), mat.group(9)
            adj = set(adj_str.replace("'", "").split(", "))
            # result[rgb] = {'province': id, 'red': r, 'green': g, 'blue': b, 'type': name, 'adj': adj, 'tdlr': [int(top), int(down), int(left), int(right)], 'xy': [int(x), int(y)]}
            result[rgb] = {'province': id, 'red': r, 'green': g, 'blue': b, 'type': name, 'adj': adj, 'xy': [int(x), int(y)]}
    return result
            
def write_neighbors(file_path, neighbors, skip = ['x', 'pixels']):
    with open(file_path, 'w') as file:
        nn = neighbors.copy()
        for i in nn:
            for k in skip:
                if k in nn[i]: nn[i].pop(k)
            file.write(f"{i}: {nn[i]}\n")

def create_files_from_csv(file_path):
    provinces = {}
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=";", fieldnames=['province', 'red', 'green', 'blue', 'type', 'x'],)
        next(reader, None)
        for row in reader:
            row['adj'] = set()
            row['pixels'] = []
            provinces.update({f"{row['red']}-{row['green']}-{row['blue']}": row})
            # id = row['province']
            # name = row['name']
            # base = '../mods/mod1/RandomMap/history/provinces/'
            # file_name = f"{base}{id}-{name}.txt"
            # with open(file_name, 'w') as new_file:
            #     if (name.find('PROVINCE') >= 0):
            #         new_file.write(f"base_manpower = {2}\nbase_tax = {2}\nbase_production = {2}\ncapital = \"{name}_cap\"")
    return provinces

def read_dict(path, prim_pop, inner_pop):
    prim = r"^(\w+)\s*=\s*{"
    inner = r"^\t(\w+)\s*=\s*{"
    dictionary = {}
    with open(path, 'r') as file:
        for line in file:
            mat = re.search(prim, line)
            if mat != None:
                current = mat.group(1)
                dictionary[current] = set()
                # print(f"{current}")
            else:
                mat = re.search(inner, line)
                if mat != None:
                    dictionary[current].add(mat.group(1))
                    # print(f"\t{mat.group(1)}")
    for p in prim_pop:
        if p in dictionary: dictionary.pop(p)
    for c in dictionary:
        dictionary[c].difference_update(inner_pop)
    return dictionary

def gen_adj(path):
    provinces = create_files_from_csv(f'{path}/map/definition.csv')
    image_path = f'{path}/map/provinces.bmp'
    neighbors = find_neighbors(image_path, provinces)
    write_neighbors(f'{path}/adj.txt', neighbors)


if __name__ == '__main__':
    config = yaml.safe_load(open("config.yml", encoding='utf-8'))
    game_folder = config['game_folder']
    path_mod = config['mod_folder']
    mod_name = config['mod_name']

    path = f"{path_mod}/{mod_name}"

    if not os.path.exists(f"{path}/adj.txt"):
        gen_adj(path)
    neighbors = read_neighbors(f"{path}/adj.txt")

    
    pp = f"{path}/history/provinces"
    if os.path.exists(pp):
        for file in os.listdir(pp):
            os.remove(f"{pp}/{file}")
    else: os.mkdir(pp)

    if os.path.exists(f"{path}/common/cultures/00_cultures.txt"):
        cultures = read_dict(f"{path}/common/cultures/00_cultures.txt", ['lost_cultures_group'], ['graphical_culture', 'male_names', 'female_names', 'dynasty_names'])
    else:
        cultures = read_dict(f"{game_folder}/common/cultures/00_cultures.txt", ['lost_cultures_group'], ['graphical_culture', 'male_names', 'female_names', 'dynasty_names'])
    
    if os.path.exists(f"{path}/common/religions/00_religion.txt"):
        religions = read_dict(f"{path}/common/religions/00_religion.txt", [], ['flag_emblem_index_range', 'reformed', 'anglican', 'protestant', 'religious_schools'])
    else:
        religions = read_dict(f"{game_folder}/common/religions/00_religion.txt", [], ['flag_emblem_index_range', 'reformed', 'anglican', 'protestant', 'religious_schools'])

    if os.path.exists(f"{path}/common/technology.txt"):
        techs = read_dict(f"{path}/common/technology.txt", ['tables'], [])
    else:
        techs = read_dict(f"{game_folder}/common/technology.txt", ['tables'], [])

    for i, t in enumerate(sorted(list(techs['groups']))):
        with open(f"{path}/history/countries/R{i:02d} - {t}_country.txt", 'w') as country_file:
            country_file.write(f"technology_group = {t}\ngovernment = republic\nreligion = orthodox\nprimary_culture = russian\ncapital = {i+1}")
        with open(f"{path}/common/countries/{t}_country.txt", 'w') as country_file:
            country_file.write(f"""graphical_culture = westerngfx
    random_nation_chance = 0
    color = {{ {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(0, 255)} }}
    historical_idea_groups = {{	
        administrative_ideas
        quantity_ideas
        defensive_ideas	
        humanist_ideas
        trade_ideas
        quality_ideas
        economic_ideas	
        maritime_ideas
    }}
    monarch_names = {{
        \"Olga #0\"
    }}
    leader_names = {{
        Tropik Tropinin
    }}""")
    with open(f"{path}/common/country_tags/01_countries.txt", 'w') as country_file:
        for i, t in enumerate(sorted(list(techs['groups']))):
            country_file.write(f"R{i:02d} = \"countries/{t}_country.txt\"\n")
    
    areas = rg.gen_areas(neighbors, path, cultures, religions, sorted(list(techs['groups'])), 42)

    with open(f"{path_mod}/{mod_name}.mod", 'w') as mod_file:
        mod_file.write(mod.format(mod_name, mod_name))

    print("Done")

