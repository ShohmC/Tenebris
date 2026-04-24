# =============================================================================
# tilemaps.py — Map Data (ASCII Tilemap Strings)
# =============================================================================
# Each tilemap is a Python list of strings. TilemapHandler iterates over these
# in (row, column) order to place tiles and spawn entities.
#
# Each character is one tile cell (TILESIZE × TILESIZE pixels).
# TilemapHandler.create_*_tilemap() defines what each letter means.
#
# Current character legend (defined in tilemap_handler.py):
#   '.'  — Empty (only grass rendered underneath)
#   'P'  — Player spawn point
#   'E'  — Enemy (Bat) spawn point
#   'D'  — Dirt tile (non-collision)
#   'T'  — Tree tile (collision)
#   'C'  — Chest (collision, interactive)
#   'W'  — Water tile (not yet wired up in handler)
#   'M', 'F', 'L', '2', '8', 't', 'N' — Referenced in some maps but not yet
#          handled in create_*_tilemap() — placeholders for future tiles/NPCs.
#
# ADDING A NEW MAP:
#   1. Define a new list of strings here (keep all rows the same length).
#   2. Add a create_newmap_tilemap() method in TilemapHandler that iterates it.
#   3. Call that method from Game or a transition tile.
# =============================================================================


# --- Active test map used by create_test_tilemap() ---
# Small 6-row map, mainly to test enemy AI and combat flow.
# Row 4 is a long dirt path; row 5 has trees acting as walls.
TEST_TILEMAP_1 = [
    '.............................................',
    '.............................................',
    '....................E........................',   # Bat spawns here
    '..............................................',
    'DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDPDDDDD',  # P = player start
    'TTTTTTTDDD........TTT.TTTTTTTTT.....TTTTDDDDDD'   # Trees = collision walls
]

# --- Tutorial map used by create_tutorial_tilemap() ---
# Larger map with a diamond/path layout and chests.
# 'C' = chest, 'M'/'F' = not yet implemented (NPC/feature placeholders?)
TUTORIAL_TILEMAP = [
    'TTTTTTTTTTTTTTTTTTTTtTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTDTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTDTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTDTTTTTTTTTTTTTTTTTTTT',
    '...................DDD...................',
    '.................DD...DD.................',
    '................DD.....DD................',
    '...............DD.......DD..M.C..........',   # M = unhandled, C = Chest
    '..............DD..F......DD..............',   # F = unhandled
    '.............D.............D.............',
    'DDDDDDDDDDDDDD.............DDDDDDDDDDDDMD',
    'DDDDMDDDDDDDDD.............DDDDDDDDDDDDDD',
    '.............D.............D.............',
    '..............DD.........DD..............',
    '...............DD.......DD...............',
    '................DD.....DD................',
    '.................DD...DD.................',
    '...................DDD...................',
    '....................D....................',
    '....................D....................',
    '...................D..D..................',
    '.........................................',
    '......................D..................',
    '................D...P....................',   # P = player spawn
]

# --- Extended map (not yet connected to a create_ method in handler) ---
# Contains '8', '2', 'W', 'L', 'N' characters — these would need handling
# added to TilemapHandler before this map is usable.
TILEMAP = [
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8.................L.',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '..................DD8...................',
    '........E.E.......DD8...................',
    '......E..E..E.....DD8...................',
    '........E..E......DD8...................',
    '..................DD82222222222222222222',
    '..................DD8WWWWWWWWWWWWWWWWWWW',
    '..................DD8WWWWWWWWWWWWWWWWWWW',
    '..................DC8WWWWWWWWWWWWWWWWWWW',
    't.................DP8WWWWWWWWWWWWWWWWWWW',
]

# --- Minimal test map (unused) ---
TILEMAP2 = [
    '.......',
    '...P....................t',
    '.......',
    '.......',
]