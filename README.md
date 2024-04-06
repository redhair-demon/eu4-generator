# EU4 Game Files Generator
### This python project generates files for playing EU4 with [Random Setup](https://eu4.paradoxwikis.com/Options#:~:text=are%20disabled.-,Random%20Setup,-The%20map%20will) Dynamic Nations from _pre-generated_ [`map`](https://eu4.paradoxwikis.com/Map_modding).

## How to use
0. Pre-generate all files in `{mod name}/map` folder until `area.txt`
1. In `config.yml` place your paths to EU4 game folder, EU4 mod folder and mod name
2. Run `main.py`
3. When it`s Done run EU4 with your mod selected
4. Choose Single Player
5. Create your Custom Nation
6. Set Custom Setup settings
   - Nations: Random Setup
   - Random Nations: Dynamic

![image](https://github.com/redhair-demon/eu4-generator/assets/90033866/02218e7f-8786-45e1-9ad2-69f191e87df9)

7. Click Play

**After this EU4 should generate Random Nations all over the map named after their province/area/region name**


## Generator uses following files from mod directory:
- `provinces.bmp` (currently needs to be default EU4 size: 5632 * 2048)
- `definition.csv` (list of all provinces from `provinces.bmp` file with **r-g-b** values for each)

 If present in mod directory, else from game directory:
- `common/cultues/00_cultures.txt`
- `common/religions/00_religions.txt`
- `common/technology.txt`

## Generator creates following files in mod directory:
- `adj.txt` - Service file, includes information about all provinces parced from `provinces.bmp` and `definition.csv`, generates once.
- `map/`
  - `area.txt`, `region.txt`, `superregion.txt`, `continent.txt` -
Define separation of map for areas, regions, superregions and continents, respectively.
- `common/`
  - `countries/{technology}` - Service countries, each country has technology from `common/technology.txt` file.
Used to distribute technologies on map.
  - `country_tags/01_countries.txt` - Service countries listed.
  - `trade_companies/00_trade_companies.txt` - List of all trade companies (currently trade companies = trade nodes).
  - `tradenodes/00_tradenodes.txt` - List of all trade nodes (connected with some way).
- `history/`
  - `countries/R{id} - {technology}` - Similarly to `common/countries`.
  - `provinces/{id} - {province name}` - All provinces listed with their culture, religion and technology.
- `localisation/random_map_mod_loc_l_english.yml` - Localisation file, incudes *normalized* names of all objects (provinces, areas, regions, etc.).
### Outside mod directory: 
- `{mod name}.mod` - Mod descriptor.
