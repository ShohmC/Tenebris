# =============================================================================
# tiles.py — Base Tile Sprite
# =============================================================================
# Defines the Tile class, the most basic building block of every map.
# TilemapHandler (tilemap_handler.py) creates Tile instances for every cell
# in a tilemap string and adds them to sprite groups for rendering and collision.
#
# Inheritance chain:
#   pygame.sprite.Sprite  ←  Tile
# =============================================================================

from config import *   # Pulls in TILESIZE, tiles_dictionary, pygame, etc.

class Tile(pygame.sprite.Sprite):
    """
    A single map tile rendered at a fixed grid position.

    Key pygame.sprite.Sprite concepts used here:
      • self.image  — the Surface pygame draws to the screen
      • self.rect   — a Rect that stores position and is used for collision detection
    Both attributes are REQUIRED by the pygame sprite system.
    """

    def __init__(self, screen, x, y, image, layer, tile_size_multiplier):
        """
        Parameters
        ----------
        screen              : pygame.Surface  — the main display (stored but not
                              used directly here; kept for potential future use)
        x, y                : int  — pixel coordinates for this tile's top-left corner
                              (calculated in TilemapHandler as col * TILESIZE, row * TILESIZE)
        image               : str  — file path to the tile's PNG asset
        layer               : int  — drawing layer (GRASS_LAYER=1 draws beneath PLAYER_LAYER=3)
        tile_size_multiplier: int  — scales the tile; 1 = 32×32 px, 2 = 64×64 px, etc.
        """
        pygame.sprite.Sprite.__init__(self)

        self.screen = screen

        # Load the image from disk, convert it to the display format for faster
        # blitting, and scale it to the desired tile size.
        # convert_alpha() preserves transparency channels (important for non-square sprites).
        self.image = pygame.transform.scale(
            pygame.image.load(image).convert_alpha(),
            (TILESIZE * tile_size_multiplier, TILESIZE * tile_size_multiplier)
        )

        # get_rect() creates a Rect whose top-left corner is at (x, y).
        # The Camera class uses self.rect to determine where to draw each tile
        # relative to the player's position.
        self.rect = self.image.get_rect(topleft=(x, y))

        # Layer value used by pygame.sprite.LayeredUpdates to control draw order.
        self.layer = layer