import csv
import random
import re
import region_gen as rg
from PIL import Image
import os
import yaml
import shutil as sh

mod_desc = """name="{}"
replace_path="history/provinces"
replace_path="common/bookmarks"
replace_path="common/province_names"
tags={{
	"map"
}}
picture="nameofapicture.png"
supported_version="1.35.*"
path="mod/{}"
"""
country_desc = """graphical_culture = westerngfx
random_nation_chance = 0
color = {{ {} {} {} }}
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
}}"""

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
        provinces[i]['xy'] = center(provinces[i]['pixels'])

    return provinces

def center(pixels: list):
    x = sum([i[0] for i in pixels]) // len(pixels)
    y = sum([i[1] for i in pixels]) // len(pixels)
    return [x, y]

def read_neighbors(file_path):
    regexp = r"(\d+-\d+-\d+): {'province': '(\d+)', 'red': '(\d+)', 'green': '(\d+)', 'blue': '(\d+)', 'type': '([^'\r]+)', 'adj': {((?:'\d+-\d+-\d+'(?:, )?)+)}, 'xy': \[(\d+), (\d+)\]}"
    result = {}
    with open(file_path, 'r') as file:
        for line in file:
            mat = re.search(regexp, line)
            rgb, id, r, g, b, name, adj_str, x, y = mat.group(1), mat.group(2), mat.group(3), mat.group(4), mat.group(5), mat.group(6), mat.group(7), mat.group(8), mat.group(9)
            adj = set(adj_str.replace("'", "").split(", "))
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
            else:
                mat = re.search(inner, line)
                if mat != None:
                    dictionary[current].add(mat.group(1))
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

def write_positions(provinces, path, size):
    offset = [[0, 0], [8, 2], [4, 4], [-2, -2], [10, 10], [0, 0], [0, 0]]
    with open(path, 'w') as file:
        for prov in provinces.values():
            position = " ".join([f"{prov['xy'][0]+s[0]:.3f} {abs((prov['xy'][1]+s[1])-size[1]):.3f}" for s in offset[:-1]] + ["0.000 0.000"])
            rot = " ".join(["0.000" for i in range(7)])
            height = " ".join([f"{s:.3f}" for s in [0, 0, 1, 0, 0, 0, 0]])
            file.write(f"{prov['province']}={{\n\tposition={{\n\t\t {position} \n\t}}\n\trotation={{\n\t\t {rot} \n\t}}\n\theight={{\n\t\t {height} \n\t}}\n}}\n")

def write_defines(defines: dict, path):
    with open(f'{path}/common/defines/00_randommap_defines.lua', 'w') as file:
        for k, v in defines.items():
            for value in v:
                file.write(f"NDefines.{k}.{value}\n")

def write_tech_countries(i, tech, path):
    with open(f"{path}/history/countries/R{i:02d} - {tech}_country.txt", 'w') as country_file:
        country_file.write(f"technology_group = {tech}\ngovernment = republic\nreligion = orthodox\nprimary_culture = russian\ncapital = {i+1}")
    with open(f"{path}/common/countries/{tech}_country.txt", 'w') as country_file:
        country_file.write(country_desc.format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    with open(f"{path}/common/country_tags/01_countries.txt", 'w') as country_file:
        country_file.write(f"R{i:02d} = \"countries/{tech}_country.txt\"\n")


if __name__ == '__main__':
    print("Press Enter to start generation")
    input()
    print("Generating...")
    config = yaml.safe_load(open("config.yml", encoding='utf-8'))
    default_conts = yaml.safe_load(open("default_data.yml", encoding='utf-8'))
    game_folder = config['game_folder']
    path_mod = config['mod_folder']
    mod_name = config['mod_name']

    path = f"{path_mod}/{mod_name}"
    print(f'removing from {path}:')
    for child in os.listdir(path):
        if child not in ['map', 'adj.txt', '.unused']:
            print(f'\t/{child}')
            if os.path.isfile(f'{path}/{child}'):
                os.remove(f'{path}/{child}')
            else:
                sh.rmtree(f'{path}/{child}')
    sh.copytree('mod_files', f"{path_mod}/{mod_name}", dirs_exist_ok=True)

    size = Image.open(f'{path}/map/provinces.bmp').size
    print(size)
    if not os.path.exists(f"{path}/adj.txt"):
        gen_adj(path)
    neighbors = read_neighbors(f"{path}/adj.txt")

    write_positions(neighbors, f"{path_mod}/{mod_name}/map/positions.txt", size)

    # Read cultures, religions & technology groups
    cultures = read_dict(f"{game_folder}/common/cultures/00_cultures.txt", ['lost_cultures_group'], ['graphical_culture', 'male_names', 'female_names', 'dynasty_names'])
    religions = read_dict(f"{game_folder}/common/religions/00_religion.txt", [], ['flag_emblem_index_range', 'reformed', 'anglican', 'protestant', 'religious_schools'])
    techs = read_dict(f"{game_folder}/common/technology.txt", ['tables'], [])

    # Create temporary countries for technology groups
    for i, t in enumerate(sorted(list(techs['groups']))):
        write_tech_countries(i, t, path)
    
    # Distribute coal by continents
    coal = [27/827, 17/1133, 1/438, 7/535, 2/249, 3/90]
    for i, k in enumerate(default_conts.keys()):
        default_conts[k]['coal'] = coal[i]
    
    # Run main generation function
    defines = rg.gen_areas(neighbors, path, cultures, religions, sorted(list(techs['groups'])), 42, def_conts=default_conts, width=size[0])

    write_defines(defines, path)

    # Create mod descriptors
    with open(f"{path_mod}/{mod_name}.mod", 'w') as mod_file:
        mod_file.write(mod_desc.format(mod_name, mod_name))
    with open(f"{path_mod}/{mod_name}/descriptor.mod", 'w') as mod_file:
        mod_file.write(mod_desc.format(mod_name, mod_name))

    # Add objects from main game as empty objects (required for work without errors)
    # map files
    for file_path in ['map/area.txt', 'map/region.txt', 'map/superregion.txt']:
        with open(f"{path_mod}/{mod_name}/{file_path}", 'a') as mod_file:
            mod_file.write("\n".join([f"{x} = {{}}" for x in sorted(list(read_dict(f"{game_folder}/{file_path}", [], []).keys()))]))
    # colonial regions and trade companies
    for file_path in ['common/colonial_regions/00_colonial_regions.txt', 'common/trade_companies/00_trade_companies.txt']:
        with open(f"{path_mod}/{mod_name}/{file_path}", 'a') as mod_file:
            mod_file.write("\n# default items\n")
            mod_file.write("\n".join([f"{x} = {{provinces={{0}}}}" for i, x in enumerate(sorted(list(read_dict(f"{game_folder}/{file_path}", [], []).keys())))]))
    # tradenodes
    for file_path in ['common/tradenodes/00_tradenodes.txt']:
        with open(f"{path_mod}/{mod_name}/{file_path}", 'a') as mod_file:
            max_provs = len(neighbors)+1
            mod_file.write("\n# default items\n")
            mod_file.write("\n".join([f"{x} = {{location={max_provs}\tmembers={{{max_provs}}}}}" for i, x in enumerate(sorted(list(read_dict(f"{game_folder}/{file_path}", [], []).keys())))]))

    print("Done")
    print("Press Enter key to exit.")
    input()

