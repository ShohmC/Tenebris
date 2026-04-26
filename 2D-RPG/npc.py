# =============================================================================
# npc.py — NPC Sprite: Dialogue & Interaction
# =============================================================================
# NPCs are stationary sprites placed on the map via tilemap characters.
# When the player is within interaction range and presses E, a dialogue
# box appears. Pressing E again advances to the next line; after the last
# line the dialogue closes.
#
# Inheritance chain:
#   pygame.sprite.Sprite  ←  NPC
# =============================================================================

from config import *


class NPC(pygame.sprite.Sprite):
    """
    A non-player character that displays dialogue when interacted with.

    Parameters
    ----------
    screen : pygame.Surface
    x, y   : int — pixel position (already multiplied by TILESIZE)
    name   : str — displayed above the dialogue text
    dialogue : list[str] — lines shown one at a time on E press
    image_path : str — path to the NPC sprite image
    """

    def __init__(self, screen, x, y, name, dialogue, image_path):
        super().__init__()
        self.screen = screen
        self.name = name
        self.dialogue = dialogue  # list of strings

        # Sprite setup
        self.image = pygame.transform.scale(
            pygame.image.load(image_path).convert_alpha(),
            (TILESIZE, TILESIZE)
        )
        self.rect = self.image.get_rect(topleft=(x, y))
        self._layer = PLAYER_LAYER

        # Dialogue state
        self.dialogue_index = 0
        self.dialogue_active = False
        self.interaction_range = TILESIZE * 2  # pixels — how close the player must be

        # Fonts
        self.name_font = pygame.font.Font(None, 32)
        self.dialogue_font = pygame.font.Font(None, 28)
        self.prompt_font = pygame.font.Font(None, 22)

    # -------------------------------------------------------------------------
    # Interaction
    # -------------------------------------------------------------------------

    def is_player_in_range(self, player_rect):
        """Returns True if the player rect center is within interaction_range."""
        dx = self.rect.centerx - player_rect.centerx
        dy = self.rect.centery - player_rect.centery
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance <= self.interaction_range

    def interact(self):
        """
        Called when E is pressed and the player is in range.
        Opens dialogue or advances to the next line.
        Returns True if the dialogue is still active, False if it just closed.
        """
        if not self.dialogue_active:
            self.dialogue_active = True
            self.dialogue_index = 0
            return True
        else:
            self.dialogue_index += 1
            if self.dialogue_index >= len(self.dialogue):
                self.dialogue_active = False
                self.dialogue_index = 0
                return False
            return True

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def draw_dialogue_box(self, screen):
        """Draws the dialogue box at the bottom of the screen."""
        if not self.dialogue_active:
            return

        box_width = WINDOW_WIDTH - 80
        box_height = 120
        box_x = 40
        box_y = WINDOW_HEIGHT - box_height - 30

        # Semi-transparent background
        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box_surface.fill((20, 20, 30, 220))
        screen.blit(box_surface, (box_x, box_y))

        # Border
        pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2)

        # NPC name
        name_surface = self.name_font.render(self.name, True, (255, 220, 50))
        screen.blit(name_surface, (box_x + 15, box_y + 10))

        # Dialogue text — simple word wrap
        if self.dialogue_index < len(self.dialogue):
            text = self.dialogue[self.dialogue_index]
            words = text.split()
            lines = []
            current_line = ""
            max_width = box_width - 30
            for word in words:
                test = f"{current_line} {word}" if current_line else word
                if self.dialogue_font.size(test)[0] < max_width:
                    current_line = test
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            for i, line in enumerate(lines[:2]):
                line_surface = self.dialogue_font.render(line, True, WHITE)
                screen.blit(line_surface, (box_x + 15, box_y + 40 + i * 26))

        # Prompt
        if self.dialogue_index < len(self.dialogue) - 1:
            prompt = self.prompt_font.render("[E] Continue", True, (150, 150, 150))
        else:
            prompt = self.prompt_font.render("[E] Close", True, (150, 150, 150))
        screen.blit(prompt, (box_x + box_width - 120, box_y + box_height - 25))

    def draw_interact_prompt(self, screen, camera_offset):
        """Draws a small '[E]' prompt above the NPC when the player is nearby."""
        if self.dialogue_active:
            return
        prompt = self.prompt_font.render("[E]", True, (255, 220, 50))
        prompt_x = self.rect.centerx + camera_offset.x - prompt.get_width() // 2
        prompt_y = self.rect.top + camera_offset.y - 18
        screen.blit(prompt, (prompt_x, prompt_y))

    def update(self):
        """Placeholder for future NPC animations or behavior."""
        pass
