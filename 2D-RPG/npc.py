# =============================================================================
# npc.py — NPC Sprite with Dialogue System
# =============================================================================
# Defines the NPC class for stationary characters that display multi-line
# dialogue when the player presses [E] nearby.
#
# Integration:
#   • Spawn NPCs in TilemapHandler.create_tutorial_map() using 'N' cells.
#   • Add to tilemap_handler.npc_sprite_group.
#   • In Game.events(), dialogue is managed via the "dialogue" game state.
#   • In Game.draw_world(), call npc.draw_interact_prompt(screen, player, camera).
#   • In Game.draw(), call npc.draw_dialogue(screen) when dialogue is active.
#
# Adding a new NPC type:
#   Subclass NPC and override __init__() to supply different colors/images,
#   or just instantiate NPC directly with different dialogue_lines and a name.
# =============================================================================

import pygame
from config import *

NPC_LAYER = PLAYER_LAYER   # Renders at the same depth as the player


class NPC(pygame.sprite.Sprite):
    """
    A stationary NPC sprite that shows a multi-line dialogue box.

    Dialogue flow:
      1. Player walks within INTERACT_RADIUS tiles of the NPC.
      2. A small '[E]' prompt appears above the NPC.
      3. Player presses E → first dialogue line appears in a bottom-screen panel.
      4. Each subsequent E press advances to the next line.
      5. Pressing E on the last line closes the panel.
    """

    # How close (in pixels) the player must be to interact.
    INTERACT_RADIUS = TILESIZE * 2.5

    def __init__(self, screen, x, y, name, dialogue_lines, color=(90, 160, 240),
                 image_path=None):
        """
        Parameters
        ----------
        screen         : pygame.Surface — main display surface
        x, y           : int — world-space pixel coordinates (top-left)
        name           : str — displayed in the dialogue box header
        dialogue_lines : list[str] — each string is one page of dialogue
        color          : tuple — RGB fill color for the placeholder sprite rectangle.
        image_path     : str | None — path to an NPC sprite image. If provided,
                         the image is loaded from disk instead of drawing a
                         colored rectangle.
        """
        super().__init__()
        self.screen = screen
        self.name = name
        self.dialogue_lines = dialogue_lines
        self.dialogue_index = 0
        self.showing_dialogue = False
        self._layer = NPC_LAYER

        # ------------------------------------------------------------------
        # Sprite image — load from file if image_path given, else placeholder
        # ------------------------------------------------------------------
        if image_path:
            self.image = pygame.transform.scale(
                pygame.image.load(image_path).convert_alpha(),
                (TILESIZE, TILESIZE)
            )
        else:
            size = TILESIZE - 4
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            self.image.fill(color)
            # White dot near top-center to suggest a "face" / facing direction
            pygame.draw.circle(self.image, (255, 255, 255), (size // 2, size // 4), 4)
            # Dark outline for contrast against any tile background
            pygame.draw.rect(self.image, (30, 30, 60), self.image.get_rect(), 2)

        self.rect = self.image.get_rect(topleft=(x, y))

        # Fonts initialized here (not per-frame) to avoid repeated allocation
        self._dialogue_font = pygame.font.Font(None, 28)
        self._name_font     = pygame.font.Font(None, 34)
        self._prompt_font   = pygame.font.Font(None, 22)

    # -------------------------------------------------------------------------
    # Proximity
    # -------------------------------------------------------------------------

    def _dist_to_player(self, player):
        """Euclidean pixel distance from this NPC's center to the player's center."""
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        return (dx * dx + dy * dy) ** 0.5

    def is_near_player(self, player):
        """True when the player is within INTERACT_RADIUS pixels of this NPC."""
        return self._dist_to_player(player) <= self.INTERACT_RADIUS

    # -------------------------------------------------------------------------
    # Interaction — driven by the "dialogue" game state in main.py
    # -------------------------------------------------------------------------

    def open_dialogue(self):
        """Opens the dialogue box at the first line."""
        self.dialogue_index = 0
        self.showing_dialogue = True

    def advance_dialogue(self):
        """
        Advances to the next dialogue line.
        Returns True if dialogue is still active, False if it just closed.
        """
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.dialogue_lines):
            self.showing_dialogue = False
            self.dialogue_index = 0
            return False
        return True

    # -------------------------------------------------------------------------
    # Drawing helpers — called from Game.draw_world() / Game.draw()
    # -------------------------------------------------------------------------

    def draw_interact_prompt(self, screen, player, camera):
        """
        Renders a small '[E]' label above the NPC in screen-space when the player
        is nearby and no dialogue is currently open.
        """
        if self.showing_dialogue or not self.is_near_player(player):
            return

        pos = camera.apply(self)
        prompt_surf = self._prompt_font.render("[E]", True, WHITE)
        label_x = pos[0] + (self.rect.width - prompt_surf.get_width()) // 2
        label_y = pos[1] - 20
        screen.blit(prompt_surf, (label_x, label_y))

    def draw_dialogue(self, screen):
        """
        Renders a fixed-position dialogue panel at the bottom of the screen.
        Call this AFTER draw_world() so it composites on top of all world sprites.
        """
        if not self.showing_dialogue:
            return

        pad    = 16
        box_x  = 60
        box_y  = WINDOW_HEIGHT - 195
        box_w  = WINDOW_WIDTH  - 120
        box_h  = 145

        # --- Panel background and border ---
        pygame.draw.rect(screen, (16, 16, 28),    (box_x, box_y, box_w, box_h),    border_radius=10)
        pygame.draw.rect(screen, (170, 195, 240), (box_x, box_y, box_w, box_h), 2, border_radius=10)

        # --- Speaker name ---
        name_surf = self._name_font.render(self.name, True, (255, 215, 80))
        screen.blit(name_surf, (box_x + pad, box_y + pad))

        # Divider line under the name
        div_y = box_y + pad + name_surf.get_height() + 4
        pygame.draw.line(screen, (60, 70, 100),
                         (box_x + pad, div_y), (box_x + box_w - pad, div_y))

        # --- Current dialogue line ---
        line_surf = self._dialogue_font.render(
            self.dialogue_lines[self.dialogue_index], True, (230, 230, 230)
        )
        screen.blit(line_surf, (box_x + pad, div_y + 10))

        # --- Page indicator (e.g. "2 / 4") ---
        total = len(self.dialogue_lines)
        page_text = f"{self.dialogue_index + 1} / {total}"
        page_surf = self._prompt_font.render(page_text, True, (100, 110, 140))
        screen.blit(page_surf, (box_x + pad, box_y + box_h - 26))

        # --- Advance / close hint (right-aligned) ---
        is_last   = self.dialogue_index >= total - 1
        hint_text = "[E] Close" if is_last else "[E] Next"
        hint_surf = self._prompt_font.render(hint_text, True, (130, 145, 175))
        screen.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - pad,
                                box_y + box_h - 26))

    # -------------------------------------------------------------------------
    # Update — called by npc_sprite_group.update() each frame
    # -------------------------------------------------------------------------

    def update(self):
        """
        Reserved for future NPC behavior (patrol routes, idle animations, etc.).
        Currently a no-op; all state changes are driven by Game.events().
        """
        pass
