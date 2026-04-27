# =============================================================================
# inventory.py — Inventory Grid UI
# =============================================================================
# Renders a grid-based inventory panel over the game world when the player
# presses I. Supports slot selection via mouse click.
#
# Current state: Items and their respective status are displayed, infinite item uses
# inside slots. The next steps would be:
#   • Add item consumption
# =============================================================================

from config import *   # TILESIZE, WINDOW_WIDTH/HEIGHT, tiles_dictionary, BLACK, etc.
from item import *

class Inventory(pygame.sprite.Sprite):
    """
    Draws a 9×3 slot inventory panel and tracks which slot is selected.

    Grid terminology used here:
      cols = number of slots across  (9)  — horizontal
      rows = number of slots down    (3)  — vertical
    """

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        from items import health_potion, max_potion, poison_item, antidote, speed_boost_item, slow_item

        # Slot background images — loaded once and reused for every slot blit.
        self.inventory_slot_image = pygame.transform.scale(
            pygame.image.load(tiles_dictionary["Hotbar"]).convert_alpha(),
            (TILESIZE * 2, TILESIZE * 2)
        )
        self.inventory_selected_slot_image = pygame.transform.scale(
            pygame.image.load(tiles_dictionary["Selected Hotbar"]).convert_alpha(),
            (TILESIZE * 2, TILESIZE * 2)
        )

        self.cols = 9   # Horizontal slot count
        self.rows = 3   # Vertical slot count

        # self.inventory holds Rect objects for each slot (set in draw_inventory_menu).
        # Initialized as None; populated each draw call so positions stay accurate.
        self.inventory = [[{"rect": None, "item": None} for _ in range(self.cols)] for _ in range(self.rows)]

        # default inventory for testing
        self.inventory[0][0]["item"] = health_potion
        self.inventory[0][1]["item"] = antidote
        self.inventory[0][2]["item"] = poison_item
        self.inventory[0][3]["item"] = speed_boost_item
        self.inventory[0][4]["item"] = slow_item
        self.inventory[0][5]["item"] = max_potion

        # Parallel boolean grid tracking which slot is currently selected.
        self.selected_slot = [[False for _ in range(self.cols)] for _ in range(self.rows)]

        self.title_font = pygame.font.Font(None, 48)
        self.inventory_tooltip_font = pygame.font.Font(None, 18)
        # Back button rect (will be set in draw_inventory_menu)
        self.back_button_rect = None

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    # Placeholder for future per-frame inventory logic (drag-and-drop, tooltips, etc.)
    def update_menu(self):
        pass

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def draw_inventory_menu(self, screen):
        """
        Draws the full inventory panel centered on screen.

        Layout:
          • Dark grey panel background with black border
          • "Inventory" title text
          • 9×3 grid of slot images (selected slot uses a different image)

        The slot Rects stored in self.inventory[row][col] are later used by
        select_inventory_slot() for hit-testing mouse clicks.

        Useful pygame docs:
          pygame.draw.rect: https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect
          Surface.blit:     https://www.pygame.org/docs/ref/surface.html#pygame.Surface.blit
        """
        slot_size = TILESIZE * 2   # 64px per slot
        padding   = 4              # Pixels between slots

        # Panel dimensions derived from grid size + margin.
        panel_width  = (self.cols * slot_size) + 80
        panel_height = (self.rows * slot_size) + 120

        # Center the panel on screen.
        panel_x = (WINDOW_WIDTH  - panel_width)  // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 4

        mouse_x, mouse_y = pygame.mouse.get_pos()

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (60, 60, 60), panel_rect)   # Fill
        pygame.draw.rect(screen, BLACK, panel_rect, 4)        # Border

        title_surface = self.title_font.render("Inventory", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 20, panel_y + 15))

        # Draw a "Back" button in the top‑right corner of the panel
        back_button_width = 80
        back_button_height = 30
        back_button_x = panel_x + panel_width - back_button_width - 10
        back_button_y = panel_y + 10
        self.back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
        pygame.draw.rect(screen, (100, 100, 100), self.back_button_rect)
        back_text = self.title_font.render("Back", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button_rect.center))
        # The grid starts with a small left offset to center it within the panel.
        grid_size = self.cols * slot_size + (self.cols - 1) * padding
        start_x = panel_x + (panel_width - grid_size) // 2
        start_y = panel_y + 70

        for row in range(self.rows):      # Iterates 0, 1, 2 (vertical)
            for col in range(self.cols):  # Iterates 0..8 (horizontal)
                x = start_x + col * (slot_size + padding)
                y = start_y + row * (slot_size + padding)

                slot = pygame.Rect(x, y, slot_size, slot_size)
                self.inventory[row][col]["rect"] = slot   # Update rect position each draw

                pygame.draw.rect(screen, BLACK, slot)   # Slot background

                # Swap image based on selection state.
                if self.selected_slot[row][col]:
                    screen.blit(self.inventory_selected_slot_image, slot)
                else:
                    screen.blit(self.inventory_slot_image, slot)

                # Item image drawn last so it appears on top of the slot graphic
                if self.inventory[row][col]["item"] is not None:
                    if self.inventory[row][col]["item"].image is not None:
                        screen.blit(self.inventory[row][col]["item"].image, (x + 4, y + 4))

        # Tooltip drawn after all slots so nothing renders on top
        for row in range(self.rows):
            for col in range(self.cols):
                slot = self.inventory[row][col]["rect"]
                if slot and slot.collidepoint(mouse_x, mouse_y):
                    if self.inventory[row][col]["item"] is not None:
                        tooltip = self.inventory_tooltip_font.render(
                            self.inventory[row][col]["item"].name, True, (255, 255, 255)
                        )
                        tooltip_rect = tooltip.get_rect(centerx=x + slot_size // 2, top=y + slot_size + 4)
                        screen.blit(tooltip, tooltip_rect)

    # -------------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------------

    def select_inventory_slot(self, player):
        """
        Called on MOUSEBUTTONDOWN (left click) from Game.events().
        Checks each slot Rect against the mouse position; if a match is found,
        clears all selections and marks that slot as selected.

        collidepoint() returns True if a point lies within a Rect:
        https://www.pygame.org/docs/ref/rect.html#pygame.Rect.collidepoint
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Check if Back button was clicked
        if self.back_button_rect and self.back_button_rect.collidepoint(mouse_x, mouse_y):
            return "close"

        for row in range(self.rows):
            for col in range(self.cols):
                slot = self.inventory[row][col]["rect"]
                if slot and slot.collidepoint(mouse_x, mouse_y):
                    # Deselect everything, then select the clicked slot.
                    for r in range(self.rows):
                        for c in range(self.cols):
                            self.selected_slot[r][c] = False
                    self.selected_slot[row][col] = True
                    if self.inventory[row][col]["item"] is not None:
                        self.inventory[row][col]["item"].use(player)
                        if self.inventory[row][col]["item"].consumable:
                            self.inventory[row][col]["item"] = None
                    return   # Stop after first match
        return None
