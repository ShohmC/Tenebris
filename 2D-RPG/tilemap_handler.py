# =============================================================================
# tilemap_handler.py — Map Builder & Sprite Group Manager
# =============================================================================
# TilemapHandler is the central hub for the game world. It:
#   1. Owns ALL sprite groups
#   2. Parses ASCII tilemaps to create Tile / Player / Enemy / NPC / WorldItem sprites
#   3. Exposes player_character for camera, enemy AI, and combat systems
#
# ADDING A NEW MAP:
#   1. Add a map string to tilemaps.py.
#   2. Add a create_*_map() method here following the create_tutorial_map() pattern.
#   3. Register it in MAP_LOADERS at the bottom of this file.
#   4. Call it from Game.main().
#
# ADDING A NEW TILE CHARACTER:
#   1. Add the image path to tiles_dictionary in config.py (if needed).
#   2. Handle the character in the relevant create_*_map() loop below.
#   3. Document it in tilemaps.py's legend comment.
# =============================================================================

from enemies    import Bat, Slime, Wolf, Skeleton
from npc        import NPC
from world_item import WorldItem
from tiles      import *       # Tile, TransitionTile + config (TILESIZE, tiles_dictionary, etc.)
from player     import *       # Player class
from tilemaps   import *       # All tilemap strings

# Transition tile definitions — keyed by map name.
# Each entry: (tile_col, tile_row, target_map_name, dest_col, dest_row)
TRANSITION_DEFINITIONS = {
    "tutorial": [
        (20, 0, "test", 20, 27),   # top gate exit (left tile, outermost)
        (21, 0, "test", 21, 27),   # top gate exit (right tile, outermost)
        (20, 1, "test", 20, 27),   # top gate entry (left tile)
        (21, 1, "test", 21, 27),   # top gate entry (right tile)
    ],
    "test": [
        (20, 29, "tutorial", 20, 1),  # south gate exit (left, outermost row)
        (21, 29, "tutorial", 21, 1),  # south gate exit (right, outermost row)
        (20, 28, "tutorial", 20, 1),  # south gate entry (left)
        (21, 28, "tutorial", 21, 1),  # south gate entry (right)
    ],
}


class TilemapHandler(pygame.sprite.Sprite):

    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen

        self.tutorial_tilemap_boolean = True
        self.tilemap_boolean          = False
        self.tilemap_boolean_2        = False

        # LayeredUpdates draws in ascending layer order.
        self.tile_sprite_group            = pygame.sprite.LayeredUpdates()
        self.collision_tile_sprite_group  = pygame.sprite.LayeredUpdates()
        self.enemy_sprite_group           = pygame.sprite.LayeredUpdates()
        self.collision_enemy_sprite_group = pygame.sprite.LayeredUpdates()
        self.npc_sprite_group             = pygame.sprite.LayeredUpdates()
        self.chest_sprite_group           = pygame.sprite.LayeredUpdates()
        self.item_sprite_group            = pygame.sprite.LayeredUpdates()
        self.player_sprite_group          = pygame.sprite.LayeredUpdates()
        self.transition_sprite_group      = pygame.sprite.LayeredUpdates()

        # Track which map is currently loaded (used by transition system)
        self.current_map = None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def draw_tile(self, column, tile_letter, j, i, image, layer,
                  is_a_collision_tile, tile_size_multiplier):
        """Creates a Tile at grid (j, i) if column matches tile_letter."""
        if column == tile_letter:
            tile = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                        image, layer, tile_size_multiplier)
            self.tile_sprite_group.add(tile)
            if is_a_collision_tile:
                self.collision_tile_sprite_group.add(tile)

    def spawn_enemy(self, enemy_class, j, i, health):
        """Spawns an enemy at grid (j, i) into both enemy groups."""
        enemy = enemy_class(self.screen, j * TILESIZE, i * TILESIZE, health)
        self.enemy_sprite_group.add(enemy)
        self.collision_enemy_sprite_group.add(enemy)

    def spawn_transitions(self, map_name):
        """
        Spawns TransitionTiles defined in TRANSITION_DEFINITIONS for the given map.
        Transition tiles are walkable — they don't go into collision_tile_sprite_group.
        """
        for col, row, target, dest_col, dest_row in TRANSITION_DEFINITIONS.get(map_name, []):
            t = TransitionTile(
                self.screen, col * TILESIZE, row * TILESIZE,
                tiles_dictionary["Transition Tile"], 2, TILESIZE_MULTIPLIER,
                target, dest_col, dest_row
            )
            self.tile_sprite_group.add(t)
            self.transition_sprite_group.add(t)

    # -------------------------------------------------------------------------
    # Map Loaders
    # -------------------------------------------------------------------------

    def create_tutorial_map(self, preserve_player=False):
        """
        Parses TUTORIAL_MAP and populates all sprite groups.

        Character handling:
          'T'  — Tree tile  (collision)
          'D'  — Dirt tile  (walkable)
          'C'  — Chest tile (collision; TODO: replace with Chest() class)
          'P'  — Player spawn
          'E'  — Bat enemy (added to enemy_sprite_group + collision_enemy_sprite_group)
          'N'  — NPC (assigned in scan order from NPC_CONFIGS)
          'h'  — WorldItem: Health Potion
          's'  — WorldItem: Speed Boost
          'a'  — WorldItem: Antidote

        If preserve_player is True, the existing player_character is kept and
        re-added to the group instead of creating a new one (used during transitions).
        """
        from items import health_potion, speed_boost_item, antidote
        old_player = self.player_character if preserve_player and hasattr(self, 'player_character') else None
        self.clear_all_tiles()
        self.current_map = "tutorial"
        self.tutorial_tilemap_boolean = True

        # ------------------------------------------------------------------
        # NPC configuration table
        # NPCs are assigned in top-to-bottom / left-to-right scan order.
        # Append a new dict here to add another NPC without touching the loop.
        # ------------------------------------------------------------------
        NPC_CONFIGS = [
            {
                # First 'N' in scan order: row 4 — Elder Mage in the Inner Sanctum
                "name": "Elder Mage",
                "color": (180, 100, 240),
                "image_path": "Player/npc_default.png",
                "dialogue_lines": [
                    "You made it through the Bat. I knew you had what it takes.",
                    "The chest beside me is yours — a reward for your courage.",
                    "The Antidote nearby cures poison. Keep it close.",
                    "Open your inventory with [I] any time to use your items.",
                    "There are greater dangers ahead. Train well, traveler.",
                ],
            },
            {
                # Second 'N' in scan order: row 13 — Village Guide near spawn
                "name": "Village Guide",
                "color": (90, 200, 120),
                "image_path": "Player/npc_default.png",
                "dialogue_lines": [
                    "Welcome! Press [W][A][S][D] to move around.",
                    "There is a dangerous Bat lurking to the east — be careful!",
                    "Walk into it to start a turn-based fight.",
                    "In combat: click Fight to attack, or Items to use a potion.",
                    "There is a Health Potion to the north — grab it before the Bat!",
                ],
            },
        ]

        npc_count = 0

        for i, row in enumerate(TUTORIAL_MAP):
            for j, column in enumerate(row):

                # Base grass — rendered under every cell
                grass = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                             tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass)

                # --- Player ---
                if column == "P" and old_player is None:
                    self.player_character = Player(
                        self.screen, j * TILESIZE, i * TILESIZE
                    )
                    self.player_sprite_group.add(self.player_character)

                # --- Structural tiles ---
                self.draw_tile(column, "T", j, i,
                               tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "D", j, i,
                               tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)
                # Chest — visual + collision.
                # TODO: swap draw_tile() for a Chest() instantiation and add to
                # chest_sprite_group when a Chest class with on_chest_open() exists.
                self.draw_tile(column, "C", j, i,
                               tiles_dictionary["Chests"], 2, True,    TILESIZE_MULTIPLIER)

                # --- Enemy spawn ---
                # 'E' spawns a Bat with 60 HP (lower than the test map's 100
                # so a new player can realistically win the tutorial fight).
                if column == "E":
                    self.spawn_enemy(Bat, j, i, 60)
                elif column == "G":
                    self.spawn_enemy(Slime, j, i, 30)
                elif column == "X":
                    self.spawn_enemy(Wolf, j, i, 80)
                elif column == "K":
                    self.spawn_enemy(Skeleton, j, i, 120)

                # --- NPC spawn ---
                if column == "N":
                    if npc_count < len(NPC_CONFIGS):
                        cfg = NPC_CONFIGS[npc_count]
                        npc = NPC(
                            screen         = self.screen,
                            x              = j * TILESIZE,
                            y              = i * TILESIZE,
                            name           = cfg["name"],
                            dialogue_lines = cfg["dialogue_lines"],
                            color          = cfg["color"],
                            image_path     = cfg.get("image_path"),
                        )
                        self.npc_sprite_group.add(npc)
                    npc_count += 1

                # --- World item spawns ---
                if column == "h":
                    self.item_sprite_group.add(
                        WorldItem(self.screen, j * TILESIZE, i * TILESIZE, health_potion)
                    )
                elif column == "s":
                    self.item_sprite_group.add(
                        WorldItem(self.screen, j * TILESIZE, i * TILESIZE, speed_boost_item)
                    )
                elif column == "a":
                    self.item_sprite_group.add(
                        WorldItem(self.screen, j * TILESIZE, i * TILESIZE, antidote)
                    )

        if old_player is not None:
            self.player_character = old_player
            self.player_sprite_group.add(self.player_character)

        self.spawn_transitions("tutorial")

    def create_test_tilemap(self, preserve_player=False):
        """Parses TEST_TILEMAP_1. Expanded combat map with 4 enemy zones."""
        from items import health_potion, speed_boost_item
        old_player = self.player_character if preserve_player and hasattr(self, 'player_character') else None
        self.clear_all_tiles()
        self.current_map = "test"
        for i, row in enumerate(TEST_TILEMAP_1):
            for j, column in enumerate(row):
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                                   tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)

                if column == "P" and old_player is None:
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)

                if column == "E":
                    self.spawn_enemy(Bat, j, i, 100)
                elif column == "G":
                    self.spawn_enemy(Slime, j, i, 30)
                elif column == "X":
                    self.spawn_enemy(Wolf, j, i, 80)
                elif column == "K":
                    self.spawn_enemy(Skeleton, j, i, 120)

                # --- World item spawns ---
                if column == "h":
                    self.item_sprite_group.add(
                        WorldItem(self.screen, j * TILESIZE, i * TILESIZE, health_potion)
                    )
                elif column == "s":
                    self.item_sprite_group.add(
                        WorldItem(self.screen, j * TILESIZE, i * TILESIZE, speed_boost_item)
                    )

                self.draw_tile(column, "D", j, i,
                               tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i,
                               tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)

        if old_player is not None:
            self.player_character = old_player
            self.player_sprite_group.add(self.player_character)

        self.spawn_transitions("test")

    def create_tutorial_tilemap(self, preserve_player=False):
        """Legacy diamond-path layout. Kept for backwards compatibility."""
        old_player = self.player_character if preserve_player and hasattr(self, 'player_character') else None
        self.clear_all_tiles()
        self.current_map = "tutorial_legacy"
        self.tutorial_tilemap_boolean = True
        for i, row in enumerate(TUTORIAL_TILEMAP):
            for j, column in enumerate(row):
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                                   tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)

                if column == "P" and old_player is None:
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)

                self.draw_tile(column, "C", j, i,
                               tiles_dictionary["Chests"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i,
                               tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "D", j, i,
                               tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)

        if old_player is not None:
            self.player_character = old_player
            self.player_sprite_group.add(self.player_character)

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------

    def clear_all_tiles(self):
        """Empties every sprite group before loading a new map."""
        self.tile_sprite_group.empty()
        self.collision_tile_sprite_group.empty()
        self.enemy_sprite_group.empty()
        self.collision_enemy_sprite_group.empty()
        self.npc_sprite_group.empty()
        self.chest_sprite_group.empty()
        self.item_sprite_group.empty()
        self.player_sprite_group.empty()
        self.transition_sprite_group.empty()

    def reset_boolean_database(self):
        """Resets the active-map flags before switching maps."""
        self.tutorial_tilemap_boolean = False

    # -------------------------------------------------------------------------
    # Map Transition
    # -------------------------------------------------------------------------

    # Map loader lookup — maps target_map strings to loader methods.
    # Populated after class definition (see below).
    MAP_LOADERS = {}

    def transition_to_map(self, target_map, dest_x, dest_y):
        """
        Loads the target map while preserving the player's stats/inventory.
        Repositions the player at (dest_x, dest_y) in pixel coordinates.

        Called from Game.events() when F is pressed on a TransitionTile.
        """
        loader = self.MAP_LOADERS.get(target_map)
        if loader is None:
            print(f"No loader found for map: {target_map}")
            return

        # Load the new map, keeping the existing player object
        loader(self, preserve_player=True)

        # Reposition the player at the destination
        self.player_character.rect.x = dest_x
        self.player_character.rect.y = dest_y


# Wire up the loader lookup after the class is defined so methods are resolved.
TilemapHandler.MAP_LOADERS = {
    "test":     TilemapHandler.create_test_tilemap,
    "tutorial": TilemapHandler.create_tutorial_map,
}
