# =============================================================================
# tilemap_handler.py — Map Builder & Sprite Group Manager
# =============================================================================
# TilemapHandler is the central hub for the game world. It:
#   1. Owns ALL sprite groups (tiles, player, enemies, NPCs, chests, items)
#   2. Parses ASCII tilemaps (from tilemaps.py) to create Tile/Player/Enemy sprites
#   3. Exposes player_character so other systems (camera, enemies, combat) can
#      reference the player directly
#
# The global `tilemap_handler` instance is created in main.py and referenced
# everywhere via that module-level name.
#
# Sprite groups used:
#   tile_sprite_group           — all visual tiles (drawn by camera in Game.draw_world)
#   collision_tile_sprite_group — solid tiles (used by player & enemy collision checks)
#   enemy_sprite_group          — all active enemies (iterated in Game.update)
#   collision_enemy_sprite_group— enemies as collision targets for the player
#   npc_sprite_group            — NPCs (not yet implemented)
#   chest_sprite_group          — interactive chests
#   item_sprite_group           — dropped items (not yet implemented)
#   player_sprite_group         — single-element group containing the player
# =============================================================================

from enemies import Bat
from tiles import *      # Tile class + config imports (includes TransitionTile)
from player import *     # Player class
from npc import NPC
from tilemaps import *   # TEST_TILEMAP_1, TUTORIAL_TILEMAP, etc.

# NPC definitions — keyed by map name.
# Each entry: (tile_col, tile_row, name, dialogue_lines, image_path)
NPC_DEFINITIONS = {
    "tutorial": [
        (16, 23, "Elder", [
            "Welcome, traveler, to the village of Tenebris.",
            "Dark creatures have been spotted in the eastern forest.",
            "Head through the gate to the east if you dare.",
        ], "Player/npc_default.png"),
        (12, 8, "Merchant", [
            "I have potions for sale... well, not yet.",
            "Check your inventory with I — you might have some already.",
        ], "Player/npc_default.png"),
    ],
    "test": [
        (10, 3, "Scout", [
            "Watch out! Bats lurk in these woods.",
            "Press F on the dirt path at the far left to return to the village.",
        ], "Player/npc_default.png"),
    ],
}

# Transition tile definitions — keyed by map name.
# Each entry: (tile_col, tile_row, target_map_name, dest_col, dest_row)
TRANSITION_DEFINITIONS = {
    "tutorial": [
        (20, 0, "test", 42, 3),    # top gate leads to test map
    ],
    "test": [
        (0, 4, "tutorial", 20, 1),  # left edge leads back to tutorial
    ],
}

class TilemapHandler(pygame.sprite.Sprite):
    """
    Parses tilemap strings into sprite objects and manages all sprite groups.

    The create_*_tilemap() methods are the entry points — call one to populate
    the world before the game loop starts.
    """

    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen

        # --- Tilemap State Flags ---
        # Track which map is currently active for transition logic.
        # (Transition system in update() is currently a stub — see below.)
        self.tutorial_tilemap_boolean = True
        self.tilemap_boolean          = False
        self.tilemap_boolean_2        = False

        # --- Sprite Groups ---
        # LayeredUpdates is a group that draws sprites in layer order.
        # See: https://www.pygame.org/docs/ref/sprite.html#pygame.sprite.LayeredUpdates
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

    def draw_tile(self, column, tile_letter, j, i, image, layer, is_a_collision_tile, tile_size_multiplier):
        """
        Creates a Tile sprite at grid position (j, i) if `column` matches
        `tile_letter`, then adds it to tile_sprite_group. Optionally also
        adds it to collision_tile_sprite_group.

        Parameters
        ----------
        column              : str  — the character at position (j, i) in the tilemap string
        tile_letter         : str  — the character this call is responsible for (e.g. "T" for trees)
        j, i                : int  — column and row index in the tilemap
        image               : str  — asset path from tiles_dictionary
        layer               : int  — draw layer
        is_a_collision_tile : bool — whether this tile should block movement
        tile_size_multiplier: int  — scale factor passed to Tile
        """
        if column == tile_letter:
            tile_name = Tile(self.screen, j * TILESIZE, i * TILESIZE, image, layer, tile_size_multiplier)
            self.tile_sprite_group.add(tile_name)
            if is_a_collision_tile:
                self.collision_tile_sprite_group.add(tile_name)

    def spawn_enemy(self, enemy_name, j, i, health):
        """
        Convenience method to spawn any enemy subclass at a grid position.
        Adds the enemy to both the enemy group and the collision group.

        NOTE: This method exists but create_test_tilemap() spawns Bat directly
        rather than using this helper. Consider standardizing.
        """
        enemy = enemy_name(self.screen, j * TILESIZE, i * TILESIZE, health)
        self.enemy_sprite_group.add(enemy)
        self.collision_enemy_sprite_group.add(enemy)

    def spawn_npcs(self, map_name):
        """
        Spawns NPCs defined in NPC_DEFINITIONS for the given map.
        Adds each NPC to both tile_sprite_group (for drawing) and npc_sprite_group
        (for interaction checks) and collision_tile_sprite_group (so player can't walk through).
        """
        for col, row, name, dialogue, img in NPC_DEFINITIONS.get(map_name, []):
            npc = NPC(self.screen, col * TILESIZE, row * TILESIZE, name, dialogue, img)
            self.tile_sprite_group.add(npc)
            self.npc_sprite_group.add(npc)
            self.collision_tile_sprite_group.add(npc)

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

    def create_test_tilemap(self, preserve_player=False):
        """
        Parses TEST_TILEMAP_1 and populates all sprite groups.

        For every cell in the map:
          • A grass tile is always placed as the base layer.
          • Additional tiles (Dirt, Tree) are placed on top if the character matches.
          • 'P' spawns the player and stores a reference in self.player_character.
          • 'E' spawns a Bat enemy.

        If preserve_player is True, the existing player_character is kept and
        re-added to the group instead of creating a new one (used during transitions).
        """
        old_player = self.player_character if preserve_player and hasattr(self, 'player_character') else None
        self.clear_all_tiles()
        self.current_map = "test"
        for i, row in enumerate(TEST_TILEMAP_1):
            for j, column in enumerate(row):
                # Base grass layer — placed for every cell regardless of character.
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                                   tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)

                if column == "P" and old_player is None:
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)

                if column == "E":
                    bat = Bat(self.screen, j * TILESIZE, i * TILESIZE, 100)
                    self.enemy_sprite_group.add(bat)

                self.draw_tile(column, "D", j, i, tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i, tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)

        if old_player is not None:
            self.player_character = old_player
            self.player_sprite_group.add(self.player_character)

        self.spawn_npcs("test")
        self.spawn_transitions("test")

    def create_tutorial_tilemap(self, preserve_player=False):
        """
        Parses TUTORIAL_TILEMAP. Same structure as create_test_tilemap() but
        includes Chest tiles ('C') and no enemies.

        If preserve_player is True, the existing player_character is kept.
        """
        old_player = self.player_character if preserve_player and hasattr(self, 'player_character') else None
        self.clear_all_tiles()
        self.current_map = "tutorial"
        self.tutorial_tilemap_boolean = True
        for i, row in enumerate(TUTORIAL_TILEMAP):
            for j, column in enumerate(row):
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                                   tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)

                if column == "P" and old_player is None:
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)

                self.draw_tile(column, "C", j, i, tiles_dictionary["Chests"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i, tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "D", j, i, tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)

        if old_player is not None:
            self.player_character = old_player
            self.player_sprite_group.add(self.player_character)

        self.spawn_npcs("tutorial")
        self.spawn_transitions("tutorial")

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------

    def clear_all_tiles(self):
        """
        Empties every sprite group. Must be called before loading a new map to
        prevent sprites from the previous map lingering in the groups.
        """
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
        """Resets the active-map flags. Called before switching to a new map."""
        self.tutorial_tilemap_boolean = False
        # self.tilemap_boolean = False    # Commented out — not yet needed
        # self.tilemap_boolean_2 = False

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
    "tutorial": TilemapHandler.create_tutorial_tilemap,
}