# EU4 Game Files Generator
### This python project generates files for playing EU4 with [Random Setup](https://eu4.paradoxwikis.com/Options#:~:text=are%20disabled.-,Random%20Setup,-The%20map%20will) Dynamic Nations from _pre-generated_ [`map`](https://eu4.paradoxwikis.com/Map_modding).

Was tested with [Haftetavenscrap`s EU4 Random Map Generator](https://forum.paradoxplaza.com/forum/threads/eu4-random-map-generator-revival-tech-alpha.1073599/), let me know if it works with others

## How to use
0. Pre-generate all files in `{mod name}/map` folder until `area.txt`
1. In `config.yml` place your paths to EU4 game folder, EU4 mod folder and mod name
2. Run `main.py`/`main.exe` (depending on whether you chose release archive or source code). At first launch on map it will generate `adj.txt`
3. When it`s Done run EU4 with your mod selected
4. Choose Single Player
5. Create your Custom Nation
6. Set Custom Setup settings
   - Nations: Random Setup
   - Random Nations: Dynamic

![image](https://github.com/redhair-demon/eu4-generator/assets/90033866/02218e7f-8786-45e1-9ad2-69f191e87df9)

7. Click Play

**After this EU4 should generate Random Nations all over the map named after their province/area/region name**

![image](https://github.com/redhair-demon/eu4-generator/assets/90033866/24fbb940-3b94-45a0-b087-d9eccbd677f3)


## Generator uses following files from mod directory:
- `provinces.bmp` (currently needs to be default EU4 size: 5632 * 2048)
- `definition.csv` (list of all provinces from `provinces.bmp` file with **r-g-b** values for each)

## Generator creates following files in mod directory:
- `adj.txt` - Service file, includes information about all provinces parced from `provinces.bmp` and `definition.csv`, generates once per map. For next launches on map script would use this file instead of parsing bitmap
- `map/`
  - `area.txt`, `region.txt`, `superregion.txt`, `continent.txt` -
Define separation of map for areas, regions, superregions and continents, respectively.
- `common/`
  - `bookmarks/a_new_world.txt` - Bookmark for game start (1444.11.11).
  - `colonial_regions/00_colonial_regions.txt` - Colonial regions list.
  - `countries/{technology}` - Service countries, each country has technology from `common/technology.txt` file.
Used to distribute technologies on map.
  - `country_tags/01_countries.txt` - Service countries listed.
  - `defines/00_randommap_defines.lua` - Some re-defined constants.
  - `institutions/00_Core.txt` - Edited institutions for correct working with random map.
  - `trade_companies/00_trade_companies.txt` - List of all trade companies.
  - `tradenodes/00_tradenodes.txt` - List of all trade nodes (connected with some way).
- `history/`
  - `countries/R{id} - {technology}` - Similarly to `common/countries`.
  - `provinces/{id} - {province name}` - All provinces listed with their culture, religion and technology.
- `localisation/random_map_mod_loc_l_english.yml` - Localisation file, incudes *normalized* names of all objects (provinces, areas, regions, etc.).
### Outside mod directory: 
- `{mod name}.mod` - Mod descriptor.

## Known issues
- For reason I don't understand sometimes `{mod name}.mod` file can be not changed, which may lead to some of problems described below
- Some decisions can`t work (often related to hard-coded conditions like `region = some_region` which can't be applied to random map where there are not default regions)
- For some reason Papal State can spawn everywhere and even have non-chistian religion. But according to game files Reformation is able to start.
