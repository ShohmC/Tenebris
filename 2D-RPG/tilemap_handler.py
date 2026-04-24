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
from tiles import *      # Tile class + config imports
from player import *     # Player class
from tilemaps import *   # TEST_TILEMAP_1, TUTORIAL_TILEMAP, etc.

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

    # -------------------------------------------------------------------------
    # Map Loaders
    # -------------------------------------------------------------------------

    def create_test_tilemap(self):
        """
        Parses TEST_TILEMAP_1 and populates all sprite groups.

        For every cell in the map:
          • A grass tile is always placed as the base layer.
          • Additional tiles (Dirt, Tree) are placed on top if the character matches.
          • 'P' spawns the player and stores a reference in self.player_character.
          • 'E' spawns a Bat enemy.

        IMPORTANT: self.player_character must be set before any code that calls
        e.g. enemy.update_movement(tilemap_handler.player_character.rect, ...).
        If 'P' is missing from the map, this will raise an AttributeError.
        """
        self.clear_all_tiles()
        for i, row in enumerate(TEST_TILEMAP_1):
            for j, column in enumerate(row):
                # Base grass layer — placed for every cell regardless of character.
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                                   tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)

                if column == "P":
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)

                if column == "E":
                    bat = Bat(self.screen, j * TILESIZE, i * TILESIZE, 100)
                    self.enemy_sprite_group.add(bat)

                self.draw_tile(column, "D", j, i, tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i, tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)

    def create_tutorial_tilemap(self):
        """
        Parses TUTORIAL_TILEMAP. Same structure as create_test_tilemap() but
        includes Chest tiles ('C') and no enemies.

        NOTE: Chests are added to collision_tile_sprite_group but NOT to
        chest_sprite_group here — that may need to be wired up for
        chest.on_chest_open() to work properly.
        """
        self.clear_all_tiles()
        self.tutorial_tilemap_boolean = True
        for i, row in enumerate(TUTORIAL_TILEMAP):
            for j, column in enumerate(row):
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE,
                                   tiles_dictionary["Grass Tile"], GRASS_LAYER, TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)

                if column == "P":
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)

                self.draw_tile(column, "C", j, i, tiles_dictionary["Chests"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i, tiles_dictionary["Tree Tile"], 2, True,  TILESIZE_MULTIPLIER)
                self.draw_tile(column, "D", j, i, tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)

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
        self.chest_sprite_group.empty()
        self.item_sprite_group.empty()
        self.player_sprite_group.empty()

    def reset_boolean_database(self):
        """Resets the active-map flags. Called before switching to a new map."""
        self.tutorial_tilemap_boolean = False
        # self.tilemap_boolean = False    # Commented out — not yet needed
        # self.tilemap_boolean_2 = False

    # -------------------------------------------------------------------------
    # Update (STUB — not called from Game loop yet)
    # -------------------------------------------------------------------------

    def update(self):
        """
        Intended to handle tilemap transition tiles (stepping on a special tile
        to move between maps). Currently a stub/work-in-progress — it is NOT
        called from Game.update() so this logic is inactive.

        TransitionTile is referenced here but not yet imported or defined.
        This is the area to build out when map transitions are needed.
        """
        for tiles in self.tile_sprite_group.sprites():
            if isinstance(tiles, TransitionTile) and tiles.is_key_pressed(self.player_character):
                if self.tutorial_tilemap_boolean:
                    tiles.tilemap_transition_handler(self.reset_boolean_database(), self.create_tilemap())
                elif self.tilemap_boolean:
                    tiles.tilemap_transition_handler(self.reset_boolean_database(), self.create_tilemap2())
                elif self.tilemap_boolean_2:
                    tiles.tilemap_transition_handler(self.reset_boolean_database(), self.create_tilemap())