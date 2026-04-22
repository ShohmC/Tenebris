from config import *

class Tile(pygame.sprite.Sprite):
    def __init__(self, screen, x, y, image, layer, tile_size_multiplier):
        pygame.sprite.Sprite.__init__(self)
        self.screen = screen
        self.image = pygame.transform.scale(pygame.image.load(image).convert_alpha(),
                                            (TILESIZE * tile_size_multiplier, TILESIZE * tile_size_multiplier))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.layer = layer