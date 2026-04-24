# =============================================================================
# combat_handler.py — Combat Screen: Transition & Menu Rendering
# =============================================================================
# Manages two distinct phases of the combat experience:
#
#   1. TRANSITION  — A "circle wipe" animation that plays when the player
#                    touches an enemy. A shrinking circle reveals the white
#                    background, signaling entry into combat.
#
#   2. COMBAT MENU — Static screen showing the player sprite, the enemy
#                    sprite, and two action buttons (Fight / Items).
#
# State flow in main.py:
#   game_state == "playing"
#       → enemy.initiate_battle_sequence triggers combat.start_transition()
#       → game_state set to "combat"
#   game_state == "combat"
#       → draw_transition() plays until transition_finished == True
#       → then draw_combat_menu() takes over
# =============================================================================

import math
from config import *   # WINDOW_WIDTH/HEIGHT, TILESIZE, color constants, pygame


class CombatHandler(pygame.sprite.Sprite):
    """
    Handles the visual rendering of the combat screen.
    Does NOT yet contain combat logic (damage calculation, turn order, etc.) —
    that would be the next area to expand.
    """

    def __init__(self):
        super().__init__()

        # max_radius is the diagonal of the window — the largest circle that can
        # fully cover the screen. math.hypot(a, b) = sqrt(a² + b²).
        self.max_radius = int(math.hypot(WINDOW_WIDTH, WINDOW_HEIGHT))

        # transition_radius starts at max_radius and shrinks to 0 each transition.
        self.transition_radius = self.max_radius

        # How many pixels the radius shrinks per frame.
        # Higher = faster wipe. At 60 FPS and radius ≈ 1600, 20px/frame ≈ 1.3 seconds.
        self.transition_speed = 20

        # Flags that control the two-phase state machine of the transition.
        self.transition_active   = False   # True while the circle is still shrinking
        self.transition_finished = False   # True after circle reaches 0 (menu can render)

        self.button_font = pygame.font.Font(None, 48)

    # -------------------------------------------------------------------------
    # Transition
    # -------------------------------------------------------------------------

    def start_transition(self):
        """
        Resets and starts the circle-wipe animation.
        Called from Game.update() when an enemy collision is detected.
        """
        self.transition_radius   = self.max_radius
        self.transition_active   = True
        self.transition_finished = False

    def draw_transition(self, screen):
        """
        Draws one frame of the circle-wipe effect.

        Technique:
          1. Create a white SRCALPHA Surface (fully opaque).
          2. Cut a transparent circle out of it using draw.circle with RGBA (0,0,0,0).
             The hole reveals the game world drawn underneath.
          3. Blit the overlay onto the screen — outside the circle is white,
             inside is transparent (world shows through).
          4. Shrink the radius by transition_speed each frame.

        SRCALPHA flag:  https://www.pygame.org/docs/ref/surface.html#pygame.Surface.__init__
        draw.circle:    https://www.pygame.org/docs/ref/draw.html#pygame.draw.circle
        """
        if not self.transition_active:
            return

        # SRCALPHA allows per-pixel alpha on this surface.
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255))   # Start fully white

        center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        # Punch a transparent circle — everything inside is see-through.
        pygame.draw.circle(
            overlay,
            (0, 0, 0, 0),           # RGBA: fully transparent
            center,
            max(0, int(self.transition_radius))
        )

        screen.blit(overlay, (0, 0))

        # Shrink the hole each frame until it disappears (radius → 0).
        self.transition_radius -= self.transition_speed

        if self.transition_radius <= 0:
            self.transition_radius   = 0
            self.transition_active   = False
            self.transition_finished = True   # Game.draw() will now render the menu

    # -------------------------------------------------------------------------
    # Combat Menu
    # -------------------------------------------------------------------------

    def draw_combat_menu(self, screen, player, enemy):
        """
        Renders the static combat screen after the transition completes.

        Parameters
        ----------
        screen : pygame.Surface — the main display
        player : pygame.Surface — player sprite image (passed in from Game.draw)
        enemy  : pygame.Surface — enemy sprite image (loaded when combat begins)

        Layout (approximate):
          Left side  : Player sprite (scaled up 5×)
          Right side : Enemy sprite  (scaled up 6×)
          Bottom     : Fight button (left), Items button (right)

        The button Rects are also used for click detection (not yet implemented —
        see events() in main.py for where MOUSEBUTTONDOWN handling would go).
        """
        screen.fill((255, 255, 255))   # White background

        # Scale sprites up for dramatic effect; combat is close-up view.
        screen.blit(
            pygame.transform.scale(player, (TILESIZE * 5, TILESIZE * 5)),
            (WINDOW_WIDTH // 6, WINDOW_HEIGHT // 3.5)
        )
        screen.blit(
            pygame.transform.scale(enemy, (TILESIZE * 6, TILESIZE * 6)),
            (WINDOW_WIDTH // 1.5, WINDOW_HEIGHT // 6.25)
        )

        # Define button Rects — these could later be returned or stored so
        # Game.events() can check pygame.mouse.get_pos() against them.
        fight_button = pygame.Rect(WINDOW_WIDTH // 3.5,              WINDOW_HEIGHT // 1.6, 250, 100)
        items_button = pygame.Rect(WINDOW_WIDTH // 2 + WINDOW_WIDTH // 40, WINDOW_HEIGHT // 1.6, 250, 100)

        # Fill then border: drawing the filled rect first, then a colored border on top.
        pygame.draw.rect(screen, BLACK, fight_button)
        pygame.draw.rect(screen, BLACK, items_button)
        pygame.draw.rect(screen, GREEN, fight_button, 4)   # 4px border
        pygame.draw.rect(screen, BLUE,  items_button, 4)

        # Render text and center it within each button's Rect.
        fight_text = self.button_font.render("Fight", True, (255, 0, 0))
        items_text = self.button_font.render("Items", True, (0, 255, 0))

        screen.blit(fight_text, fight_text.get_rect(center=fight_button.center))
        screen.blit(items_text, items_text.get_rect(center=items_button.center))