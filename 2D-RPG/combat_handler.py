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
        self.fight_button = None
        self.items_button = None
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
        screen.blit(pygame.transform.scale(player.image, (TILESIZE * 5, TILESIZE * 5)),
                (WINDOW_WIDTH // 6, WINDOW_HEIGHT // 3.5))
    

        # Player health bar
        player_bar_width = 200
        player_bar_height = 20
        player_bar_x = 1.5 + 50
        player_bar_y = 100
        pygame.draw.rect(screen, RED, (player_bar_x, player_bar_y, player_bar_width, player_bar_height))
        player_health_percent = player.health / 100
        pygame.draw.rect(screen, GREEN, (player_bar_x, player_bar_y, player_bar_width * player_health_percent, player_bar_height))
        player_font = pygame.font.Font(None, 36)
        player_health_text = player_font.render("Health", True, BLACK)
        screen.blit(player_health_text, (player_bar_x, player_bar_y - 25))
    
        enemy_surface = pygame.image.load(enemy.initial_image).convert_alpha()
        enemy_surface = pygame.transform.scale(enemy_surface, (TILESIZE * 6, TILESIZE * 6))
        screen.blit(enemy_surface, (WINDOW_WIDTH // 1.5, WINDOW_HEIGHT // 6.25))
        fight_x = WINDOW_WIDTH // 3.5
        items_x = WINDOW_WIDTH // 2 + WINDOW_WIDTH // 40
        fight_y = WINDOW_HEIGHT // 1.6
    
        # Enemy health bar
        bar_width = 200
        bar_height = 20
        bar_x = WINDOW_WIDTH // 1.5 + 50
        bar_y = WINDOW_HEIGHT // 6.25 - 30
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        health_percent = enemy.health / 100
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * health_percent, bar_height))
        font = pygame.font.Font(None, 36)
        health_text = font.render("Health", True, BLACK)
        screen.blit(health_text, (bar_x, bar_y - 25))
    
        self.fight_button = pygame.Rect(fight_x, fight_y, 250, 100)
        self.items_button = pygame.Rect(items_x, fight_y, 250, 100)
        print(f"DEBUG: Fight button rect: {self.fight_button}")  
        pygame.draw.rect(screen, BLACK, self.fight_button)
        pygame.draw.rect(screen, BLACK, self.items_button)
        pygame.draw.rect(screen, GREEN, self.fight_button, 4)
        pygame.draw.rect(screen, BLUE,  self.items_button, 4)
        fight_text = self.button_font.render("Fight", True, (255, 0, 0))
        items_text = self.button_font.render("Items", True, (0, 255, 0))
        screen.blit(fight_text, fight_text.get_rect(center=self.fight_button.center))
        screen.blit(items_text, items_text.get_rect(center=self.items_button.center)) 
    def handle_click(self, mouse_pos, player, enemy, inventory):
        print(f"DEBUG: handle_click called with mouse_pos: {mouse_pos}")
        print(f"DEBUG: self.fight_button = {self.fight_button}")
        if self.fight_button and self.fight_button.collidepoint(mouse_pos):
            print("DEBUG: Fight button clicked")
            player_attack = player.get_attack()
            enemy_defense = getattr(enemy, 'defense', 0)
            damage = max(1, player_attack - enemy_defense)
            enemy.health -= damage
            print(f"DEBUG: Player attack {player_attack}, enemy defense {enemy_defense}, damage {damage}, enemy health now {enemy.health}")
            if enemy.health <= 0:
                player.exp += enemy.exp_on_kill
                enemy.kill()
                return "victory"
            else:
                enemy_attack = enemy.damage
                player_defense = player.get_defense()
                enemy_damage = max(1, enemy_attack - player_defense)
                player.take_damage(enemy_damage)
                print(f"DEBUG: Enemy attack {enemy_attack}, player defense {player_defense}, enemy damage {enemy_damage}, player health now {player.health}")
                if player.health <= 0:
                    return "game_over"
                return "turn_done"
        elif self.items_button and self.items_button.collidepoint(mouse_pos):
            print("DEBUG: Items button clicked")
            return "open_inventory"
        print("DEBUG: No button clicked")
        return None
