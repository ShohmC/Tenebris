# config.py — Global constants and pre-loaded assets shared across all files.
# Every module does `from config import *` to access these.

import pygame

# Window dimensions in pixels
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 960

# All map positions are in "tile units"; multiply by TILESIZE to get pixels
TILESIZE = 32
TILESIZE_MULTIPLIER = 1

# Raw velocity values; actual speed is scaled by dt in player.py
PLAYER_X_VELOCITY = 20
PLAYER_Y_VELOCITY = 20

ATTACK_X_VELOCITY = 40
ATTACK_Y_VELOCITY = 40

# LayeredUpdates draws in ascending layer order (higher = drawn on top)
GRASS_LAYER = 1
PLAYER_LAYER = 3
ENEMY_LAYER = 3

FPS = 60

RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

LOW_HEALTH_THRESHOLD = 95   # health below this triggers red blink


# Maps readable names to asset file paths — update paths here only
tiles_dictionary = {
    "Grass Tile": "Tiles/GrassTile.png",
    "Grass Ledge Up": "Tiles/GrassLedgeUp.png",
    "Grass Ledge Down": "Tiles/GrassLedgeDown.png",
    "Grass Ledge Left": "Tiles/GrassLedgeLeft.png",
    "Grass Ledge Right": "Tiles/GrassLedgeRight.png",

    "Dirt Tile": "Tiles/DirtTile.png",
    "Dirt Ledge Up": "Tiles/DirtLedgeUp.png",
    "Dirt Ledge Down": "Tiles/DirtLedgeDown.png",
    "Dirt Ledge Left": "Tiles/DirtLedgeLeft.png",
    "Dirt Ledge Right": "Tiles/DirtLedgeRight.png",

    "Hotbar": "ItemSlotImage/Hotbar.png",
    "Selected Hotbar": "ItemSlotImage/SelectedHotbar.png",

    "Wall Tile": "Tiles/WallTile.png",
    "Water Tile": "Tiles/WaterTile.png",
    "Tree Tile": "Tiles/TreeTile.png",
    "Chests": "Tiles/Chest.png",
    "Transition Tile": "Tiles/DirtTile.png",
}

# Player frames loaded once at startup — reusing surfaces is faster than
# calling pygame.image.load() every frame
player_image_up_1    = pygame.image.load("Player/up1.png")
player_image_up_2    = pygame.image.load("Player/up2.png")
player_image_down_1  = pygame.image.load("Player/down1.png")
player_image_down_2  = pygame.image.load("Player/down2.png")
player_image_left_1  = pygame.image.load("Player/left1.png")
player_image_left_2  = pygame.image.load("Player/left2.png")
player_image_right_1 = pygame.image.load("Player/right1.png")
player_image_right_2 = pygame.image.load("Player/right2.png")
