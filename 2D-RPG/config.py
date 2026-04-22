import pygame

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 960


TILESIZE = 32
TILESIZE_MULTIPLIER = 1

PLAYER_X_VELOCITY = 20
PLAYER_Y_VELOCITY = 20

ATTACK_X_VELOCITY = 40
ATTACK_Y_VELOCITY = 40

GRASS_LAYER = 1
PLAYER_LAYER = 3
ENEMY_LAYER = 3

FPS = 60

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

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
    "Chests": "Tiles/Chest.png"
}

player_image_up_1 = pygame.image.load("Player/up1.png")
player_image_up_2 = pygame.image.load("Player/up2.png")
player_image_down_1 = pygame.image.load("Player/down1.png")
player_image_down_2 = pygame.image.load("Player/down2.png")
player_image_left_1 = pygame.image.load("Player/left1.png")
player_image_left_2 = pygame.image.load("Player/left2.png")
player_image_right_1 = pygame.image.load("Player/right1.png")
player_image_right_2 = pygame.image.load("Player/right2.png")
