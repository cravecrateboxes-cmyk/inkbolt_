"""Surface classes for every palette cell (tactical look plan, sections 4.3 and Stage 5A).

classify(family, name) -> (class_id, emit_weight). Name rules first, then per-family overrides (OVERRIDES).
A new family needs no entry here: the name rules give every cell a class. Overrides are corrections found by
looking at the family's swatch sheet (Source/dist/surfaces/<family>.png, written by tools/gen_surfaces.py).

Classes (ids are fixed, the shader depends on them):
 0 paint / plastic   1 concrete   2 metal, bare   3 metal, painted   4 wood   5 fabric   6 soil / sand / gravel
 7 vegetation   8 rock   9 brick   10 tile / ceramic / marble   11 glass   12 rubber / asphalt   13 snow / ice
 14 water   15 emissive
Emit weight (only for class 15): how strongly the cell lights the room (Stage 4). Lamps 1.0, fire 1.2, neon 0.6,
screens and LEDs 0.35, holograms 0.25, far city windows 0 (glows, lights nothing).
"""
import re

CLASS_NAMES = ['paint', 'concrete', 'metal', 'painted-metal', 'wood', 'fabric', 'soil', 'vegetation', 'rock',
               'brick', 'tile', 'glass', 'rubber', 'snow', 'water', 'emissive']
#        gloss  metal  (section 4.3)
CLASS_GM = [(0.30, 0.0), (0.10, 0.0), (0.55, 0.85), (0.38, 0.25), (0.16, 0.0), (0.04, 0.0), (0.03, 0.0), (0.06, 0.0),
            (0.08, 0.0), (0.08, 0.0), (0.55, 0.0), (0.92, 0.10), (0.14, 0.0), (0.25, 0.0), (0.95, 0.0), (0.30, 0.0)]

# (regex on the lower-case name, class, emit weight). First match wins.
RULES = [
    (r'^(hull|ink)$', 12, 0),
    # emitters
    (r'^(scrdead|screend|lampshade|lightrail)$', 11, 0),
    (r'^(fire\d?$|flame|ember|lava|torch)', 15, 1.2),
    (r'^neon', 15, 0.6),
    (r'^holo', 15, 0.25),
    (r'^(scr|screen|led|code|monitor|tv)', 15, 0.35),
    (r'^farlit', 15, 0.0),
    (r'^far(rock|bark|d|s|\d)?$', 0, 0),   # painted distant backdrop: never emissive, no material detail
    (r'^(lamp|light|glow|beacon|lit[a-z]?$|lit$|sodium|exitg|bulb|spark|starw)', 15, 1.0),
    # glass and water
    (r'^(glass|window|win[a-z]?$|windark|mirror|lens|optic|skyglass|twglass|twwin|glround|domein|interior|intd$)', 11, 0),
    (r'^(water|pool|sea$|ocean|puddle|murk|deep$)', 14, 0),
    # snow / ice
    (r'^(snow|ice|frost|firn|drift|farsnow)', 13, 0),
    # rubber / asphalt
    (r'^(asph|tire|tyre|rubber|hose|cable|sole|boot|road|lane$)', 12, 0),
    # metal
    (r'^(rust)', 2, 0),
    (r'^(steel|iron|metal|chrome|galv|alu$|brass|gold|cgold|copper|bronze|tin\d?$|silver|zinc|wire|chain|mesh|grate|'
     r'rail|rivet|gun|mplate|plate|tread|perf|spring|tbar|weld|can\d?$|canlid|canband|blade|servo|pipe$)', 2, 0),
    (r'^(beam|mframe|frame|corr|clad|mach|tank|drum|barrel|cont\d|truck|car(b|blue|cream|g|mint|o|p|r|red|t|w|y)$|cab[a-z]?\d?$|cabin|shut|'
     r'haz|mhaz|pipe[a-z]|panel|lift|locker|rack|mail|hydrant|cart|engg|hold|hawk|el$|eld$|jet|tug|taxi|train|hood|'
     r'mech|bin\d?$|drum|cone|ext\d?$|fuel|solar|vent|duct|stack|truss|girder)', 3, 0),
    # masonry and ground
    (r'^(brick|brk|twbrick)', 9, 0),
    (r'^(tile|marble|grout|vct|vinyl|terra|terr|ceramic|porcel|epoxy|esd)', 10, 0),
    (r'^(rock|cave|stone|granite|slate|cliff|boulder|hill|quarry|ceilrock|bdstone|cobble|coal|'
     r'bdslate|onyx)', 8, 0),
    (r'^(conc|cement|plaster|drywall|stucco|stu[a-z]?$|ceil|curb|kerb|block|column|cornice|ledge|lowwall|step|slab|'
     r'pave|paver|gconc|mortar|quarry|bdwall|wall|roofedge|seam|joint|walk|ramp|platform|pier)', 1, 0),
    (r'^(soil|sand|dirt|mud|earth|dust|gravel|ground|ballast|duff|clay|land|sedim|ash$|dry$|pit$|track|path)', 6, 0),
    # living things
    (r'^(grass|leaf|moss|hedge|fern|frond|bush|canopy|tree|lawn|meadow|clover|flower|blossom|bloom|reed|cattail|lily|'
     r'tulip|hibis|bougain|cypress|pine|maple|scrub|field|hay|vine|ivy|turf|needle|shrub|palm|cocog|mush)', 7, 0),
    # wood
    (r'^(wood|plank|oak|walnut|teak|timber|log|bark|trunk|board|crate|birch|bamboo|cork|rattan|pencilwood|shelf|furn|'
     r'joist|wains|parquet|deck|floorp|pallet|ply|cardb|cardboard|stool|bench|table|desk)', 4, 0),
    # fabric
    (r'^(bag|sack|canvas|tarp|cloth|fab|blanket|linen|curtain|carpet|rug|rope|flag|banner|leather|cushion|sofa|felt|'
     r'thatch|net|wool|towel|mattress|knit|silk|cotton|uniform|suit|sleeve|vest|webbing|strap|pouch|glove|awn|'
     r'membrane|camo|seat|ticking|wrap)', 5, 0),
]
_RULES = [(re.compile(p), c, e) for p, c, e in RULES]

# per-family corrections: {family: {cell name: class or (class, emit)}}. Names not in the family are an error
# (checked by gen_surfaces.py) so a typo cannot silently do nothing.
OVERRIDES = {
    'kit-datacenter': {'fireR': 3, 'field': (15, 0.15), 'frost': 11},
    'kit-bedroom': {'wall1': 0, 'wall1u': 0, 'wall2': 0, 'wall2u': 0, 'wall3': 0, 'wall3u': 0, 'ceil': 0, 'lampshade': 5},
    'kit-downtown': {'mull': 3},
    'kit-parking': {'stain': 1},
    # Stage 5A.4 review (usage checked in each family's modules)
    'kit-academy': {'board': 0},
    'kit-airfield7': {'scrub': 7, 'scrubD': 7, 'fire': 3},
    'kit-cargoship': {'fireR': 3, 'hullR': 3, 'hullRD': 3},
    'kit-castle': {'fireY': (15, 1.2)},
    'kit-classroom': {'board': 0, 'boardDk': 0, 'land': 0, 'ocean': 0},
    'kit-coalmine': {'board': 0},
    'kit-gemmine': {'board': 0},
    'kit-factory': {'pool': 1, 'pool2': 1, 'core': (15, 0.35), 'hot2': (15, 0.35)},
    'kit-factory2': {'pool': 1, 'pool2': 1, 'lane': 0, 'core': (15, 0.35), 'spark': (15, 0.6), 'spark2': (15, 0.6)},
    'kit-foundry': {'spark': (15, 0.6)},
    'kit-garden': {'plY': 0},
    'kit-grove': {'shelf': 7, 'cabin': 4, 'cabin2': 4},
    'kit-highrise': {'screen2': 11, 'frost': 11},
    'kit-hotel': {'wine': 5, 'emerald': 5, 'navy': 5, 'teal2': 5, 'shade': 5, 'crystal': 11, 'crystal2': 11,
                  'vein': 10, 'nero': 10},
    'kit-riviera': {'wine': 5, 'emerald': 5, 'navy': 5, 'teal2': 5, 'shade': 5, 'crystal': 11, 'crystal2': 11,
                    'vein': 10, 'nero': 10},
    'kit-icecream': {'quarry': 10, 'quarryD': 10, 'cotton': 0},
    'kit-island': {'drift': 4, 'drift2': 4, 'wet': 6},
    'kit-resort': {'wet': 6},
    'kit-livingroom': {'block': 4},
    'kit-observatory': {'starW': (15, 0.25)},
    'kit-office': {'ledge': 1, 'vein': 10, 'tank': 4, 'frost': 11},
    'kit-pelagic': {'fire': 3, 'hull': 3, 'hullD': 3},
    'kit-police': {'peg': 4, 'peg2': 4, 'acou': 5, 'acou2': 5},
    'kit-seabase': {'hull': 3, 'hullD': 3, 'fireR': 3},
    'kit-spire': {'onyx': 10, 'cap': 1, 'vein': 10, 'tickG': (15, 0.35)},
    'kit-techhq': {'board': 0},
    'kit-venetian': {'roof': 10, 'roofD': 10, 'bottle': 11},
}


def classify_name(name):
    s = name.lower()
    for rx, c, e in _RULES:
        if rx.search(s):
            return c, e
    return 0, 0


def classify(family, name):
    o = OVERRIDES.get(family, {}).get(name)
    if o is not None:
        return (o, 0.0 if o != 15 else 1.0) if isinstance(o, int) else tuple(o)
    return classify_name(name)
