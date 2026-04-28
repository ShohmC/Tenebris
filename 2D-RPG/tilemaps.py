# =============================================================================
# tilemaps.py — Map Data (ASCII Tilemap Strings)
# =============================================================================
# Each tilemap is a Python list of strings. TilemapHandler iterates over these
# in (row, column) order to place tiles and spawn entities.
#
# Character legend (defined in tilemap_handler.py):
#   '.'  — Empty (grass base only)
#   'P'  — Player spawn point
#   'E'  — Enemy (Bat) spawn point
#   'D'  — Dirt tile (walkable, non-collision)
#   'T'  — Tree tile (collision wall)
#   'C'  — Chest tile (collision, visual)
#   'N'  — NPC spawn (assigned top-to-bottom/left-to-right to NPC_CONFIGS list)
#   'G'  — Enemy (Slime) spawn point
#   'X'  — Enemy (Wolf) spawn point
#   'K'  — Enemy (Skeleton) spawn point
#   'h'  — WorldItem: Health Potion (contact pickup)
#   's'  — WorldItem: Speed Boost   (contact pickup)
#   'a'  — WorldItem: Antidote      (contact pickup)
#   'W'  — Water tile (handler support pending)
#
# ADDING A NEW MAP:
#   1. Define a list of strings here.
#   2. Add create_*_map() in tilemap_handler.py.
#   3. Update this legend.
#   4. Call it from Game.main().
# =============================================================================


# =============================================================================
# TUTORIAL_MAP
# =============================================================================
# Intended player flow (south → north):
#
#   [P] Spawn (row 15)
#    ↓  open grass
#   [N] Village Guide (row 13, west side) — explains movement, combat, items
#    →  [E] Bat enemy (row 13, east side) — first combat encounter
#    ↓  (after victory, path opens north)
#   [h] Health Potion on the ground (row 11) — reward / refuel after fight
#    ↓  dirt path merges from a fork
#   ←→  forking path: left branch straight up, right branch holds [s] Speed Boost
#    ↓  path leads into the Inner Sanctum
#   [N] Elder Mage (row 4) — explains chests and advanced mechanics
#   [C] Chest (row 4) — interactive object tutorial
#   [a] Antidote (row 5) — status effect item tutorial
#
# Teaching moments in order:
#   1. Movement (WASD)
#   2. NPC dialogue (E key)
#   3. Turn-based combat (Fight / Items buttons)
#   4. Ground item pickup (walk over glowing item)
#   5. Inventory (I key)
#   6. Environmental navigation (branching paths)
#   7. Chests and status items
# =============================================================================

TUTORIAL_MAP = [
    # row  0 — north boundary wall (gap at cols 20-21 shows transition exit)
    'TTTTTTTTTTTTTTTTTTTT..TTTTTTTTTTTTTTTT',
    # row  1 — transition gateway at cols 20-21
    'T...................DD...............T',
    # row  2 — sanctum top: dirt floor begins
    'T....DDDDDDDDDDDDDDDDDDDDDDDDDDD.....T',
    # row  3 — sanctum interior (open space)
    'T....D.........................D.....T',
    # row  4 — Elder Mage NPC (col 13) + Chest (col 25)
    'T....D.......N...........C.....D.....T',
    # row  5 — Antidote sits near the chest (col 25 area)
    'T....D......................a..D.....T',
    # row  6 — sanctum south wall; path forks below here
    'T....DDDDDDDDDDDDDDDDD..DDDDDDDDD....T',
    # row  7 — left branch col ~13, right branch col ~22
    'T............D........D..............T',
    # row  8 — Speed Boost on right branch (col ~29)
    'T............D........D......s.......T',
    # row  9
    'T............D........D..............T',
    # row 10 — both branches merge back to single column
    'T............DDDDDDDDDD..............T',
    # row 11 — Health Potion on open grass (col ~19) — post-fight reward
    'T..................h.................T',
    # row 12 — open corridor
    'T....................................T',
    # row 13 — COMBAT ROW: Village Guide (col 5) warns the player,
    #           Bat enemy (col 28) blocks the northward path.
    #           Player must win the fight to safely explore north.
    'T....N.....................E.........T',
    # row 14 — open approach area
    'T....................................T',
    # row 15 — player spawn (col 19)
    'T.................P..................T',
    # row 16 — buffer before south wall
    'T....................................T',
    # row 17 — south boundary wall
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
]


# =============================================================================
# TEST_TILEMAP_1 — Original small combat test map
# =============================================================================

TEST_TILEMAP_1 = [
    # 46 columns wide, 30 rows tall
    # row  0 — north boundary wall
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    # row  1 — open top area
    'T............................................T',
    # row  2 — Slime zone (east side, easy)
    'T........TTTTTTTTT...........................T',
    # row  3
    'T........T.......T...........................T',
    # row  4 — Slime spawns
    'T........T..G..G.T...........................T',
    # row  5
    'T........T.......T...........................T',
    # row  6
    'T........TTT..TTTT...........................T',
    # row  7 — open corridor connecting zones
    'T............................................T',
    # row  8 — Bat zone (west side)
    'T..........................TTTTTTTTT.........T',
    # row  9
    'T..........................T.......T.........T',
    # row 10 — Bat spawns
    'T..........................T..E..E.T.........T',
    # row 11
    'T..........................T.......T.........T',
    # row 12
    'T..........................TTT..TTTT.........T',
    # row 13 — health potion in middle corridor
    'T.....................h......................T',
    # row 14 — open area
    'T............................................T',
    # row 15 — Wolf zone (east side, dangerous)
    'T........TTTTTTTTT...........................T',
    # row 16
    'T........T.......T...........................T',
    # row 17 — Wolf spawns
    'T........T..X....T...........................T',
    # row 18
    'T........T.......T...........................T',
    # row 19
    'T........TTT..TTTT...........................T',
    # row 20 — open corridor
    'T............................................T',
    # row 21 — Skeleton zone (center, hardest)
    'T.................TTTTTTTTTTT................T',
    # row 22
    'T.................T.........T................T',
    # row 23 — Skeleton spawns
    'T.................T...K.....T................T',
    # row 24
    'T.................T.........T................T',
    # row 25
    'T.................TTTT..TTTTT................T',
    # row 26 — open area with speed boost
    'T...............s............................T',
    # row 27 — player arrival area
    'T....................P.......................T',
    # row 28 — transition back to tutorial (cols 20-21)
    'T....................DD......................T',
    # row 29 — south boundary wall (gap at cols 20-21 for transition)
    'TTTTTTTTTTTTTTTTTTTTTT..TTTTTTTTTTTTTTTTTTTTTT',
]


# =============================================================================
# TUTORIAL_TILEMAP — Legacy diamond-path layout (kept for reference)
# =============================================================================

TUTORIAL_TILEMAP = [
    'TTTTTTTTTTTTTTTTTTTTtTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTDTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTDTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTDTTTTTTTTTTTTTTTTTTTT',
    '...................DDD...................',
    '.................DD...DD.................',
    '................DD.....DD................',
    '...............DD.......DD..M.C..........',
    '..............DD..F......DD..............',
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
    '................D...P....................',
]


# =============================================================================
# TILEMAP / TILEMAP2 — Extended / scratch maps (not yet connected to handler)
# =============================================================================

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

TILEMAP2 = [
    '.......',
    '...P....................t',
    '.......',
    '.......',
]
