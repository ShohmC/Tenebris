from config import *

class Inventory(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.inventory_slot_image = pygame.transform.scale(
            pygame.image.load(tiles_dictionary["Hotbar"]).convert_alpha(),
            (TILESIZE * 2, TILESIZE * 2)
        )
        self.inventory_selected_slot_image = pygame.transform.scale(
            pygame.image.load(tiles_dictionary["Selected Hotbar"]).convert_alpha(),
            (TILESIZE * 2, TILESIZE * 2)
        )

        self.rows = 9
        self.columns = 3

        self.inventory = [[None for _ in range(self.rows)] for _ in range(self.columns)]
        self.selected_slot = [[False for _ in range(self.rows)] for _ in range(self.columns)]

        self.title_font = pygame.font.Font(None, 48)

    def update_menu(self):
        pass

    def draw_inventory_menu(self, screen):
        panel_width = (self.rows * TILESIZE * 2) + 80
        panel_height = (self.columns * TILESIZE * 2) + 120

        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 4

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        pygame.draw.rect(screen, (60, 60, 60), panel_rect)
        pygame.draw.rect(screen, BLACK, panel_rect, 4)

        title_surface = self.title_font.render("Inventory", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 20, panel_y + 15))

        slot_size = TILESIZE * 2
        padding = 4

        grid_size = self.rows * slot_size + (self.rows - 1) * padding

        start_x = panel_x + (panel_width - grid_size) // 2
        start_y = panel_y + 70

        for row in range(self.columns):
            for col in range(self.rows):
                x = start_x + col * (slot_size + padding)
                y = start_y + row * (slot_size + padding)

                slot = pygame.Rect(x, y, slot_size, slot_size)
                self.inventory[row][col] = slot

                pygame.draw.rect(screen, BLACK, slot)

                if self.selected_slot[row][col]:
                    screen.blit(self.inventory_selected_slot_image, slot)
                else:
                    screen.blit(self.inventory_slot_image, slot)

    def select_inventory_slot(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for row in range(self.columns):
            for col in range(self.rows):
                slot = self.inventory[row][col]
                if slot and slot.collidepoint(mouse_x, mouse_y):
                    for r in range(self.columns):
                        for c in range(self.rows):
                            self.selected_slot[r][c] = False

                    self.selected_slot[row][col] = True
                    return
