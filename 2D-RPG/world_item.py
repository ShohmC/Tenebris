# =============================================================================
# world_item.py — World-Space Collectible Item Sprite
# =============================================================================
# WorldItem wraps an Item instance as a pygame sprite placed directly on the map.
# When the player's rect overlaps the sprite, the item effect fires immediately
# and the sprite is removed from all groups.
#
# Integration:
#   • Create WorldItem instances in TilemapHandler.create_tutorial_map() for
#     map characters 'h', 's', 'a' (or whatever chars you choose).
#   • Add to tilemap_handler.item_sprite_group.
#   • In Game.update() (playing state), iterate item_sprite_group and call
#     world_item.check_pickup(player_character).
#   • In Game.draw_world(), iterate item_sprite_group and blit each item via
#     the camera, then call world_item.draw_label(screen, camera).
#
# Swapping to inventory-based pickup:
#   Replace item.use(player) in check_pickup() with:
#       inventory.add_item(self.item)
#   once the inventory API supports direct item insertion.
#
# Adding new item types on the map:
#   1. Define an Item instance in items.py.
#   2. Pick a new map character (e.g. 'x') in tilemaps.py.
#   3. Handle it in TilemapHandler.create_tutorial_map():
#          if column == 'x':
#              wi = WorldItem(self.screen, j * TILESIZE, i * TILESIZE, your_item)
#              self.item_sprite_group.add(wi)
# =============================================================================

import pygame
from config import *

ITEM_SPRITE_LAYER = 2   # Above grass (layer 1), below player/enemies (layer 3)


class WorldItem(pygame.sprite.Sprite):
    """
    A collectible item rendered as a sprite in world-space.

    Visual design:
      • Uses the Item's pre-loaded image scaled down to fit within one tile.
      • A soft glowing border is composited around the image so items are
        easy to spot against the tilemap.
      • A small name label is drawn just below the sprite (optional, call
        draw_label() from Game.draw_world()).
    """

    # Class-level font so it is created once, not once per instance.
    # Initialized to None; set on first WorldItem creation.
    _label_font = None

    def __init__(self, screen, x, y, item):
        """
        Parameters
        ----------
        screen : pygame.Surface — main display surface (stored for future use)
        x, y   : int — world-space pixel coordinates (top-left corner of sprite)
        item   : Item — the item whose effect fires on pickup
        """
        super().__init__()
        self.screen = screen
        self.item   = item
        self._layer = ITEM_SPRITE_LAYER

        # ------------------------------------------------------------------
        # Build the display surface
        # ------------------------------------------------------------------
        icon_size = TILESIZE - 8   # Slightly smaller than a tile (24 px at TILESIZE=32)

        if item.image is not None:
            # item.image is already a pygame.Surface from Item.__init__();
            # scale it down to world-item size (Item stores it at 2×TILESIZE).
            icon = pygame.transform.scale(item.image, (icon_size, icon_size))
        else:
            # Fallback: solid gold square for items without artwork
            icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            icon.fill((255, 215, 0))

        # Glow border: a slightly larger surface with a semi-transparent rim.
        # This makes items pop visually against grass and dirt without being
        # too distracting when the player isn't looking for them.
        glow_pad   = 4
        total_size = icon_size + glow_pad * 2
        self.image = pygame.Surface((total_size, total_size), pygame.SRCALPHA)

        # Draw the glow rim (filled rounded rect at full alpha)
        pygame.draw.rect(
            self.image, (255, 255, 160, 180),
            self.image.get_rect(), border_radius=5
        )
        # Blit the icon centered inside the glow border
        self.image.blit(icon, (glow_pad, glow_pad))

        self.rect = self.image.get_rect(topleft=(x, y))

        # Initialize the shared label font on first WorldItem creation
        if WorldItem._label_font is None:
            WorldItem._label_font = pygame.font.Font(None, 18)

    # -------------------------------------------------------------------------
    # Pickup — call every frame from Game.update()
    # -------------------------------------------------------------------------

    def check_pickup(self, player):
        """
        Tests for overlap with the player's rect every frame.

        On overlap:
          • Calls item.use(player) to apply the item effect immediately.
          • Calls self.kill() which removes this sprite from every group it
            belongs to, so it stops rendering and updating automatically.

        To switch to inventory-based pickup in future, replace item.use(player)
        with something like inventory.add_item(self.item) and remove the
        item.use call, then still call self.kill().
        """
        if self.rect.colliderect(player.rect):
            self.item.use(player)
            self.kill()

    # -------------------------------------------------------------------------
    # Drawing helpers — call from Game.draw_world()
    # -------------------------------------------------------------------------

    def draw_label(self, screen, camera):
        """
        Renders the item's name in small text just below the sprite in
        screen-space.  Optional — omit the call if you prefer a cleaner look.

        Parameters
        ----------
        camera : Camera — camera.apply(self) translates world pos → screen pos.
        """
        pos   = camera.apply(self)
        label = WorldItem._label_font.render(self.item.name, True, (255, 255, 180))
        label_x = pos[0] + (self.rect.width - label.get_width()) // 2
        label_y = pos[1] + self.rect.height + 2
        screen.blit(label, (label_x, label_y))

    # -------------------------------------------------------------------------
    # Update — stub, called by sprite group if .update() is invoked on the group
    # -------------------------------------------------------------------------

    def update(self):
        """
        Reserved for future per-frame logic (bobbing animation, sparkle effect,
        despawn timer, etc.).  Currently a no-op; pickup is driven by
        check_pickup() called explicitly from Game.update().
        """
        pass
