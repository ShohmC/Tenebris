import pygame

class Camera(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2(0, 0)

    def apply(self, sprite):
        return sprite.rect.move(self.offset)

    def update(self, target_group):
        if target_group.sprites():
            target_sprite = target_group.sprites()[0]
            target_center = pygame.math.Vector2(target_sprite.rect.x + target_sprite.rect.width / 2,
                                                target_sprite.rect.y + target_sprite.rect.height / 2)
            self.offset = pygame.math.Vector2(self.display_surface.get_width() / 2,
                                              self.display_surface.get_height() / 2) - target_center
