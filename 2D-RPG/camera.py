# camera.py — Keeps the player centered on screen by computing a per-frame offset.
# Camera.apply() shifts a sprite's draw position without touching its real rect,
# so world-space collision detection is unaffected.

import pygame

class Camera(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        # offset is subtracted from every sprite's world position before drawing
        self.offset = pygame.math.Vector2(0, 0)

    # Returns a new shifted Rect for blitting — does NOT modify sprite.rect
    def apply(self, sprite):
        return sprite.rect.move(self.offset)

    # Recalculates offset so the first sprite in target_group stays screen-centered.
    # Called every frame from Game.update().
    def update(self, target_group):
        if target_group.sprites():
            target_sprite = target_group.sprites()[0]
            target_center = pygame.math.Vector2(target_sprite.rect.x + target_sprite.rect.width / 2,
                                                target_sprite.rect.y + target_sprite.rect.height / 2)
            self.offset = pygame.math.Vector2(self.display_surface.get_width() / 2,
                                              self.display_surface.get_height() / 2) - target_center