# =============================================================================
# enemies.py — Enemy Base Class & Concrete Enemy Types
# =============================================================================
# Defines the Enemies base class (shared AI, animation, collision logic) and
# concrete subclasses for specific enemy types (currently: Bat).
#
# Adding a new enemy type means:
#   1. Create a subclass of Enemies
#   2. Pass the correct image paths and stats to super().__init__()
#   3. Optionally override update_movement() or animation() for unique behavior
#
# Inheritance chain:
#   pygame.sprite.Sprite  ←  Enemies  ←  Bat  (and future enemy types)
# =============================================================================

from config import *   # TILESIZE, ENEMY_LAYER, pygame, etc.


def load_enemy_image(path):
    """
    Helper function: loads an image from disk and scales it to 28×28 pixels.
    Extracted into a standalone function so both Enemies.__init__ and any
    future code can reuse it without duplicating the scale call.
    convert_alpha() ensures transparency is preserved correctly.
    """
    return pygame.transform.scale(
        pygame.image.load(path).convert_alpha(),
        (28, 28)
    )


class Enemies(pygame.sprite.Sprite):
    """
    Base class for all enemy sprites.

    Responsibilities:
      • Stores stats (health, damage, exp_on_kill)
      • Tracks directional animation frames and counters
      • Moves toward the player when within detection range (TILESIZE * 8)
      • Detects tile and player collision
      • Sets initiate_battle_sequence = True when touching the player

    Subclasses only need to supply image paths and stat values via __init__.
    """

    def __init__(self, screen, initial_x_location, initial_y_location,
                 initial_image,
                 up_img_1, up_img_2,
                 down_img_1, down_img_2,
                 left_img_1, left_img_2,
                 right_img_1, right_img_2,
                 health, damage, exp_on_kill):
        super().__init__()

        # --- Flag watched by Game.update() to trigger combat state ---
        # When True, the main loop transitions game_state to "combat".
        self.initiate_battle_sequence = False

        self.screen = screen
        self.initial_x_location = initial_x_location
        self.initial_y_location = initial_y_location
        self.initial_image = initial_image   # Path string kept so combat screen can reload it

        # Load all directional animation frames at init time (not each frame).
        self.image    = load_enemy_image(initial_image)
        self.up_img_1 = load_enemy_image(up_img_1)
        self.up_img_2 = load_enemy_image(up_img_2)
        self.down_img_1  = load_enemy_image(down_img_1)
        self.down_img_2  = load_enemy_image(down_img_2)
        self.left_img_1  = load_enemy_image(left_img_1)
        self.left_img_2  = load_enemy_image(left_img_2)
        self.right_img_1 = load_enemy_image(right_img_1)
        self.right_img_2 = load_enemy_image(right_img_2)

        self.rect   = self.image.get_rect(topleft=(initial_x_location, initial_y_location))
        self._layer = ENEMY_LAYER

        # velocity is recalculated each frame from direction toward the player.
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed    = 2   # Pixels per frame (not dt-scaled — consider scaling for consistency)

        # --- Stats ---
        self.health      = health
        self.damage      = damage
        self.exp_on_kill = exp_on_kill   # XP awarded to player on defeat (not yet implemented)

        # Previous-frame position used by animation() to infer movement direction.
        self.previous_x_location = self.rect.x
        self.previous_y_location = self.rect.y

        # Per-direction animation counters (same 0–19 cycle as Player).
        self.up_counter    = 0
        self.down_counter  = 0
        self.left_counter  = 0
        self.right_counter = 0

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    def _animate_direction(self, counter_name, frame_1, frame_2):
        """
        Shared animation stepper — identical in concept to Player.animate().
        Uses getattr/setattr to work with any directional counter by name.
        """
        counter = (getattr(self, counter_name) + 1) % 20
        setattr(self, counter_name, counter)
        self.image = frame_1 if counter < 10 else frame_2

    def animation(self):
        """
        Determines the current movement direction by comparing the current
        position to the previous frame's position, then calls _animate_direction.

        NOTE: This approach only checks one axis at a time (y before x), so
        diagonal movement always plays the vertical animation. A priority system
        or velocity-based check would be more accurate.
        """
        if self.rect.y < self.previous_y_location:
            self._animate_direction("up_counter",    self.up_img_1,    self.up_img_2)
        elif self.rect.y > self.previous_y_location:
            self._animate_direction("down_counter",  self.down_img_1,  self.down_img_2)
        elif self.rect.x < self.previous_x_location:
            self._animate_direction("left_counter",  self.left_img_1,  self.left_img_2)
        elif self.rect.x > self.previous_x_location:
            self._animate_direction("right_counter", self.right_img_1, self.right_img_2)

        # Store current position for next frame's comparison.
        self.previous_x_location = self.rect.x
        self.previous_y_location = self.rect.y

    def idle_animation(self):
        """Placeholder for when the enemy is stationary. Override in subclasses."""
        pass

    # -------------------------------------------------------------------------
    # Collision
    # -------------------------------------------------------------------------

    def check_collision(self, tile_collision_group, player_collision_group):
        """
        Two collision checks per frame:
          1. Tile collision: reverses last move if overlapping a solid tile.
          2. Player collision: sets the battle flag if touching the player.

        The velocity after a tile collision is set to (-1, -1) which effectively
        nudges the enemy away. This is a simple but imprecise approach.

        See pygame collision docs:
        https://www.pygame.org/docs/ref/sprite.html#pygame.sprite.spritecollideany
        """
        if pygame.sprite.spritecollideany(self, tile_collision_group):
            self.rect.move_ip(-self.velocity.x, -self.velocity.y)
            self.velocity.update(-1, -1)
        if pygame.sprite.spritecollideany(self, player_collision_group):
            self.initiate_battle_sequence = True

    # -------------------------------------------------------------------------
    # AI / Movement
    # -------------------------------------------------------------------------

    def update_movement(self, player_rect, tile_collision_group, player_collision_group):
        """
        Simple "chase player" AI:
          1. Compute a vector from the enemy to the player.
          2. If the player is within detection range (8 tiles), normalize the
             direction vector and scale by self.speed to get velocity.
          3. Apply collision checks.
          4. Move the rect and animate.

        normalize_ip() scales the vector to length 1 so diagonal movement is
        the same speed as cardinal movement.
        See: https://www.pygame.org/docs/ref/math.html#pygame.math.Vector2.normalize_ip

        Called from Game.update() for every enemy each frame.
        """
        direction = pygame.math.Vector2(
            player_rect.x - self.rect.x,
            player_rect.y - self.rect.y
        )
        distance = direction.length()

        if distance <= TILESIZE * 8:   # Detection / aggro radius
            if distance > 0:
                direction.normalize_ip()
                self.velocity = direction * self.speed
                self.check_collision(tile_collision_group, player_collision_group)
            else:
                self.idle_animation()

            self.rect.move_ip(self.velocity)
            self.animation()


# =============================================================================
# Concrete Enemy: Bat
# =============================================================================

class Bat(Enemies):
    """
    A specific enemy type. Supplies image paths and stat values to the base
    class — no new logic needed for basic behavior.

    To create a new enemy type, copy this pattern and change:
      • The image folder paths
      • health, damage, exp_on_kill values
      • Optionally override update_movement() for unique movement patterns
    """
    def __init__(self, screen, initial_x_location, initial_y_location, health):
        super().__init__(
            screen, initial_x_location, initial_y_location,
            # initial_image (also used as the combat screen portrait)
            "Enemy/Bat/left1.png",
            # up frames
            "Enemy/Bat/left1.png", "Enemy/Bat/left2.png",
            # down frames
            "Enemy/Bat/right1.png", "Enemy/Bat/right2.png",
            # left frames
            "Enemy/Bat/left1.png", "Enemy/Bat/left2.png",
            # right frames
            "Enemy/Bat/right1.png", "Enemy/Bat/right2.png",
            # stats: health, damage, exp_on_kill
            health, 1, 35
        )