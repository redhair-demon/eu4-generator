import csv
import re
import region_gen as rg
from PIL import Image

def rgb(pixel): return f"{pixel[0]}-{pixel[1]}-{pixel[2]}"

def find_neighbors(image_path, provinces):
    img = Image.open(image_path)
    width, height = img.size
    
    temp = img.getpixel((0,0))
    for i in range(1, width * height-1):
        pixel = img.getpixel((i % width, i // width))
        tdlr = provinces[rgb(pixel)]['tdlr']
        if tdlr[0] == None or tdlr[0] < i // width:
            provinces[rgb(pixel)]['tdlr'][0] = i // width
        if tdlr[1] == None or tdlr[1] > i // width:
            provinces[rgb(pixel)]['tdlr'][1] = i // width
        if tdlr[2] == None or tdlr[2] < i % width:
            provinces[rgb(pixel)]['tdlr'][2] = i % width
        if tdlr[3] == None or tdlr[3] > i % width:
            provinces[rgb(pixel)]['tdlr'][3] = i % width
        
        if (pixel != temp):
            provinces[rgb(pixel)]['adj'].add(rgb(temp))
            provinces[rgb(temp)]['adj'].add(rgb(pixel))
        temp = pixel
        if (i % 1000000 == 0): print(i)
    
    for i in range(width):
        temp = img.getpixel((i,0))
        for k in range(height):
            pixel = img.getpixel((i, k))
            if (pixel != temp):
                provinces[rgb(pixel)]['adj'].add(rgb(temp))
                provinces[rgb(temp)]['adj'].add(rgb(pixel))
            temp = pixel

    for i in provinces:
        provinces[i]['xy'] = [sum(provinces[i]['tdlr'][:2])//2, sum(provinces[i]['tdlr'][2:])//2]

    return provinces

def read_neighbors(file_path):
    regexp = r"(\d+-\d+-\d+): {'province': '(\d+)', 'red': '(\d+)', 'green': '(\d+)', 'blue': '(\d+)', 'name': '([^'\r]+)', 'x': 'x', 'adj': {((?:'\d+-\d+-\d+'(?:, )?)+)}, 'tdlr': \[(\d+), (\d+), (\d+), (\d+)\], 'xy': \[(\d+), (\d+)\]}"
    result = {}
    with open(file_path, 'r') as file:
        for line in file:
            mat = re.search(regexp, line)
            rgb, id, r, g, b, name, adj_str, top, down, left, right, x, y = mat.group(1), mat.group(2), mat.group(3), mat.group(4), mat.group(5), mat.group(6), mat.group(7), mat.group(8), mat.group(9), mat.group(10), mat.group(11), mat.group(12), mat.group(13)
            adj = set(adj_str.replace("'", "").split(", "))
            result[rgb] = {'province': id, 'red': r, 'green': g, 'blue': b, 'name': name, 'adj': adj, 'tdlr': [int(top), int(down), int(left), int(right)], 'xy': [int(x), int(y)]}
    return result
            


def create_files_from_csv(file_path):
    provinces = {}
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=";", fieldnames=['province', 'red', 'green', 'blue', 'name', 'x'],)
        next(reader, None)
        for row in reader:
            row['adj'] = set()
            row['tdlr'] = [None, None, None, None]
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


# provinces = create_files_from_csv('../mods/mod1/RandomMap/map/definition.csv')
# print(provinces.keys())
# print(provinces['7-111-132'])
# # Пример использования
# image_path = '../mods/mod1/RandomMap/map/provinces.bmp'
# neighbors = find_neighbors(image_path, provinces)
# with open('adj2.txt', 'w') as file:
#     for i in neighbors:
#         file.write(f"{i}: {neighbors[i]}\n")


neighbors = read_neighbors("adj2.txt")
# path = '../mods/mod1/RandomMap'
path = 'C:/Users/naego/OneDrive/Документы/Paradox Interactive/Europa Universalis IV/mod/RandomMap'


cultures = read_dict(f"{path}/common/cultures/00_cultures.txt", ['lost_cultures_group'], ['graphical_culture', 'male_names', 'female_names', 'dynasty_names'])
religions = read_dict(f"{path}/common/religions/00_religion.txt", [], ['flag_emblem_index_range', 'reformed', 'anglican', 'protestant', 'religious_schools'])
# with open('cul-reg.txt', 'w') as file:
#     file.write("# CULTURES:\n")
#     for i in sorted(cultures.keys()):
#         file.write(f"{i}: {cultures[i]}\n")
#     file.write("# RELIGIONS:\n")
#     for i in sorted(religions.keys()):
#         file.write(f"{i}: {religions[i]}\n")
# techs = read_dict(f"{path}/common/technology.txt", ['tables'], [])
# print(techs)

areas = rg.gen_areas(neighbors, path, cultures, religions)

print("done")

