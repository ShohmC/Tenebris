from enemies import Bat
from tiles import *
from player import *
from tilemaps import *

class TilemapHandler(pygame.sprite.Sprite):
    def __init__(self, screen):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen
        self.tutorial_tilemap_boolean = True
        self.tilemap_boolean = False
        self.tilemap_boolean_2 = False

        self.tile_sprite_group = pygame.sprite.LayeredUpdates()
        self.collision_tile_sprite_group = pygame.sprite.LayeredUpdates()
        self.enemy_sprite_group = pygame.sprite.LayeredUpdates()
        self.collision_enemy_sprite_group = pygame.sprite.LayeredUpdates()
        self.npc_sprite_group = pygame.sprite.LayeredUpdates()
        self.chest_sprite_group = pygame.sprite.LayeredUpdates()
        self.item_sprite_group = pygame.sprite.LayeredUpdates()
        self.player_sprite_group = pygame.sprite.LayeredUpdates()

    def draw_tile(self, column, tile_letter, j, i, image, layer, is_a_collision_tile, tile_size_multiplier):
        if column == tile_letter:
            tile_name = Tile(self.screen, j * TILESIZE, i * TILESIZE, image, layer, tile_size_multiplier)
            self.tile_sprite_group.add(tile_name)
            if is_a_collision_tile:
                self.collision_tile_sprite_group.add(tile_name)

    def spawn_enemy(self, enemy_name, j, i, health):
        enemy = enemy_name(self.screen, j * TILESIZE, i * TILESIZE, health)
        self.enemy_sprite_group.add(enemy)
        self.collision_enemy_sprite_group.add(enemy)

    def create_test_tilemap(self):
        self.clear_all_tiles()
        for i, row in enumerate(TEST_TILEMAP_1):
            for j, column in enumerate(row):
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE, tiles_dictionary["Grass Tile"], GRASS_LAYER,
                                   TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)
                if column == "P":
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)
                if column == "E":
                    bat = Bat(self.screen, j * TILESIZE, i * TILESIZE, 100)
                    self.enemy_sprite_group.add(bat)
                self.draw_tile(column, "D", j, i, tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i, tiles_dictionary["Tree Tile"], 2, True, TILESIZE_MULTIPLIER)
    def create_tutorial_tilemap(self):
        self.clear_all_tiles()
        self.tutorial_tilemap_boolean = True
        for i, row in enumerate(TUTORIAL_TILEMAP):
            for j, column in enumerate(row):
                grass_tiles = Tile(self.screen, j * TILESIZE, i * TILESIZE, tiles_dictionary["Grass Tile"], GRASS_LAYER,
                                   TILESIZE_MULTIPLIER)
                self.tile_sprite_group.add(grass_tiles)
                if column == "P":
                    self.player_character = Player(self.screen, j * TILESIZE, i * TILESIZE)
                    self.player_sprite_group.add(self.player_character)
                self.draw_tile(column, "C", j, i, tiles_dictionary["Chests"], 2, True, TILESIZE_MULTIPLIER)
                self.draw_tile(column, "T", j, i, tiles_dictionary["Tree Tile"], 2, True, TILESIZE_MULTIPLIER)
                self.draw_tile(column, "D", j, i, tiles_dictionary["Dirt Tile"], 2, False, TILESIZE_MULTIPLIER)


    def clear_all_tiles(self):
        self.tile_sprite_group.empty()
        self.collision_tile_sprite_group.empty()
        self.enemy_sprite_group.empty()
        self.collision_enemy_sprite_group.empty()
        self.chest_sprite_group.empty()
        self.item_sprite_group.empty()
        self.player_sprite_group.empty()

    def reset_boolean_database(self):
        self.tutorial_tilemap_boolean = False
        #self.tilemap_boolean = False
        #self.tilemap_boolean_2 = False


    # IGNORE THIS FOR NOW THIS METHOD DOES ABSOLUTELY NOTHING
    def update(self):
        for tiles in self.tile_sprite_group.sprites():
            if isinstance(tiles, TransitionTile) and tiles.is_key_pressed(self.player_character):
                if self.tutorial_tilemap_boolean:
                    tiles.tilemap_transition_handler(self.reset_boolean_database(), self.create_tilemap())
                elif self.tilemap_boolean:
                    tiles.tilemap_transition_handler(self.reset_boolean_database(), self.create_tilemap2())
                elif self.tilemap_boolean_2:
                    tiles.tilemap_transition_handler(self.reset_boolean_database(), self.create_tilemap())
