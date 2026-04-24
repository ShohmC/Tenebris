# =============================================================================
# inventory.py — Inventory Grid UI
# =============================================================================
# Renders a grid-based inventory panel over the game world when the player
# presses I. Supports slot selection via mouse click.
#
# Current state: UI rendering only — items are not yet stored or displayed
# inside slots. The next steps would be:
#   • Define an Item class
#   • Store Item references in self.inventory[row][col]
#   • Render item images/icons inside each slot rect
# =============================================================================

from config import *   # TILESIZE, WINDOW_WIDTH/HEIGHT, tiles_dictionary, BLACK, etc.

class Inventory(pygame.sprite.Sprite):
    """
    Draws a 9×3 slot inventory panel and tracks which slot is selected.

    Grid terminology used here:
      rows    = number of COLUMNS across  (9)  — confusingly named, see note below
      columns = number of ROWS down       (3)

    NOTE: The variable names self.rows and self.columns are swapped relative
    to typical convention (rows usually = vertical count). This is existing code;
    be aware when iterating so you don't mix them up.
    """

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        # Slot background images — loaded once and reused for every slot blit.
        self.inventory_slot_image = pygame.transform.scale(
            pygame.image.load(tiles_dictionary["Hotbar"]).convert_alpha(),
            (TILESIZE * 2, TILESIZE * 2)
        )
        self.inventory_selected_slot_image = pygame.transform.scale(
            pygame.image.load(tiles_dictionary["Selected Hotbar"]).convert_alpha(),
            (TILESIZE * 2, TILESIZE * 2)
        )

        # Grid dimensions (see naming note above).
        self.rows    = 9   # Horizontal slot count
        self.columns = 3   # Vertical slot count

        # self.inventory holds Rect objects for each slot (set in draw_inventory_menu).
        # Initialized as None; populated each draw call so positions stay accurate
        # if the window were ever resized.
        self.inventory = [[None for _ in range(self.rows)] for _ in range(self.columns)]

        # Parallel boolean grid tracking which slot is currently selected.
        self.selected_slot = [[False for _ in range(self.rows)] for _ in range(self.columns)]

        self.title_font = pygame.font.Font(None, 48)

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    # Placeholder for future per-frame inventory logic
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
        panel_width  = (self.rows    * slot_size) + 80
        panel_height = (self.columns * slot_size) + 120

        # Center the panel on screen.
        panel_x = (WINDOW_WIDTH  - panel_width)  // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 4

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (60, 60, 60), panel_rect)   # Fill
        pygame.draw.rect(screen, BLACK, panel_rect, 4)        # Border

        title_surface = self.title_font.render("Inventory", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 20, panel_y + 15))

        # The grid starts with a small left offset to center it within the panel.
        grid_size = self.rows * slot_size + (self.rows - 1) * padding
        start_x = panel_x + (panel_width - grid_size) // 2
        start_y = panel_y + 70

        for row in range(self.columns):      # Iterates 0, 1, 2 (vertical)
            for col in range(self.rows):     # Iterates 0..8 (horizontal)
                x = start_x + col * (slot_size + padding)
                y = start_y + row * (slot_size + padding)

                slot = pygame.Rect(x, y, slot_size, slot_size)
                self.inventory[row][col] = slot   # Update rect position each draw

                pygame.draw.rect(screen, BLACK, slot)   # Slot background

                # Swap image based on selection state.
                if self.selected_slot[row][col]:
                    screen.blit(self.inventory_selected_slot_image, slot)
                else:
                    screen.blit(self.inventory_slot_image, slot)

    # -------------------------------------------------------------------------
    # Input
    # -------------------------------------------------------------------------

    def select_inventory_slot(self):
        """
        Called on MOUSEBUTTONDOWN (left click) from Game.events().
        Checks each slot Rect against the mouse position; if a match is found,
        clears all selections and marks that slot as selected.

        collidepoint() returns True if a point lies within a Rect:
        https://www.pygame.org/docs/ref/rect.html#pygame.Rect.collidepoint
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for row in range(self.columns):
            for col in range(self.rows):
                slot = self.inventory[row][col]
                if slot and slot.collidepoint(mouse_x, mouse_y):
                    # Deselect everything, then select the clicked slot.
                    for r in range(self.columns):
                        for c in range(self.rows):
                            self.selected_slot[r][c] = False
                    self.selected_slot[row][col] = True
                    return   # Stop after first match