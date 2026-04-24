# =============================================================================
# player.py — Player Sprite: Movement, Animation & HUD
# =============================================================================
# The Player class represents the character controlled by the keyboard.
# It handles:
#   1. Frame-based walking animation (2 frames per direction)
#   2. Velocity-based movement with delta-time scaling
#   3. Tile collision resolution
#   4. Drawing the health bar HUD directly onto the screen
#
# Inheritance chain:
#   pygame.sprite.Sprite  ←  Player
# =============================================================================

from config import *   # Imports TILESIZE, PLAYER_X/Y_VELOCITY, player_image_*, etc.

class Player(pygame.sprite.Sprite):
    """
    The player character.

    Relevant sprite group memberships (set in TilemapHandler):
      • player_sprite_group        — iterated in Game.update() for movement updates
      • collision_enemy_sprite_group (also contains enemies) — enemies check against
        this group to trigger combat
    """

    def __init__(self, screen, initial_x_location, initial_y_location):
        super().__init__()

        self.screen = screen

        # velocity is a 2D vector reset to (0,0) every frame; direction keys
        # set one or both components before check_collision() applies the move.
        self.velocity = pygame.math.Vector2(0, 0)

        # Default facing image (right-facing frame 1), scaled to fit within a tile.
        self.image = pygame.transform.scale(
            pygame.image.load("Player/right1.png").convert_alpha(),
            (TILESIZE - 4, TILESIZE - 4)   # Slightly smaller than tile to avoid edge clipping
        )
        self.rect = self.image.get_rect(topleft=(initial_x_location, initial_y_location))
        self._layer = PLAYER_LAYER   # Controls draw order in LayeredUpdates groups

        # --- Attack Cooldown ---
        self.cooldown = 0
        self.cooldown_time = 200   # milliseconds between attacks (not yet used in game loop)

        # --- Animation Frame Counters ---
        # Each counter cycles 0–19 (mod 20); frame 1 shown for 0–9, frame 2 for 10–19.
        # Separate counters per direction prevent blending artifacts when changing direction.
        self.up_counter    = 0
        self.left_counter  = 0
        self.down_counter  = 0
        self.right_counter = 0

        # --- Player Stats ---
        self.health         = 100
        self.exp            = 0
        self.level          = 1
        self.upgrade_points = 0

        # --- HUD Fonts ---
        # Font(None, size) uses pygame's built-in font; replace None with a .ttf path for custom fonts.
        self.health_label_font = pygame.font.Font(None, 48)
        self.health_value_font = pygame.font.Font(None, 36)

        # --- Animation Frame Tuples ---
        # Pre-scaled surfaces stored as (frame_1, frame_2) pairs.
        # Stored in __init__ so images are scaled once, not every frame.
        self.up_frames    = (pygame.transform.scale(player_image_up_1,    (28, 28)),
                             pygame.transform.scale(player_image_up_2,    (28, 28)))
        self.left_frames  = (pygame.transform.scale(player_image_left_1,  (28, 28)),
                             pygame.transform.scale(player_image_left_2,  (28, 28)))
        self.down_frames  = (pygame.transform.scale(player_image_down_1,  (28, 28)),
                             pygame.transform.scale(player_image_down_2,  (28, 28)))
        self.right_frames = (pygame.transform.scale(player_image_right_1, (28, 28)),
                             pygame.transform.scale(player_image_right_2, (28, 28)))

    # -------------------------------------------------------------------------
    # HUD
    # -------------------------------------------------------------------------

    def draw_player_health_bar(self, screen):
        """
        Draws a fixed-position health bar in the top-left of the screen.
        This is drawn in SCREEN space (not world space), so the camera offset
        is NOT applied here — it always appears at the same screen position.

        The green bar width scales linearly with self.health (0–100).
        """
        screen.blit(self.health_label_font.render("Health", True, BLACK), (50, 50))
        pygame.draw.rect(screen, RED,   (175, 55, 150, 25))                          # Background (full bar)
        pygame.draw.rect(screen, GREEN, (175, 55, 150 * (self.health / 100), 25))    # Foreground (current HP)
        screen.blit(self.health_value_font.render(str(self.health), True, BLACK), (230, 56))

    # -------------------------------------------------------------------------
    # Collision
    # -------------------------------------------------------------------------

    def check_collision(self, tile_collision_group):
        """
        Moves self.rect by self.velocity, then checks for overlap with any tile
        in the collision group. If a collision is found, the move is reversed.

        This is an AABB (axis-aligned bounding box) approach — simple but it can
        cause the player to "stick" to walls when pressing diagonally. A more
        robust approach would separate x and y axes. Something to explore!
        See: https://www.pygame.org/docs/ref/sprite.html#pygame.sprite.spritecollideany
        """
        self.rect.move_ip(self.velocity)
        if pygame.sprite.spritecollideany(self, tile_collision_group):
            self.rect.move_ip(-self.velocity.x, -self.velocity.y)

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    def animate(self, counter_name, frames):
        """
        Generic animation stepper shared by all four directions.

        Uses getattr/setattr to read and write the correct counter by name
        (e.g. "up_counter") without needing four near-identical methods.
        The counter wraps at 20 via modulo; self.image is set to frame[0] or
        frame[1] depending on which half of the cycle we're in.
        """
        counter = (getattr(self, counter_name) + 1) % 20
        setattr(self, counter_name, counter)
        self.image = frames[0] if counter < 10 else frames[1]

    # -------------------------------------------------------------------------
    # Movement
    # -------------------------------------------------------------------------

    def movement(self, dt):
        """
        Reads keyboard state and sets self.velocity accordingly.
        dt (delta-time) scales velocity so movement speed is consistent
        regardless of frame rate fluctuations.

        pygame.key.get_pressed() returns the state of EVERY key simultaneously,
        which allows diagonal movement (unlike KEYDOWN events which fire once).
        See: https://www.pygame.org/docs/ref/key.html#pygame.key.get_pressed
        """
        keys = pygame.key.get_pressed()
        self.velocity.update(0, 0)   # Reset each frame so the player stops when no key held

        if keys[pygame.K_w]:
            self.animate("up_counter", self.up_frames)
            self.velocity.y = -PLAYER_Y_VELOCITY * dt
        if keys[pygame.K_a]:
            self.animate("left_counter", self.left_frames)
            self.velocity.x = -PLAYER_X_VELOCITY * dt
        if keys[pygame.K_s]:
            self.animate("down_counter", self.down_frames)
            self.velocity.y = PLAYER_Y_VELOCITY * dt
        if keys[pygame.K_d]:
            self.animate("right_counter", self.right_frames)
            self.velocity.x = PLAYER_X_VELOCITY * dt

    # -------------------------------------------------------------------------
    # Main Update (called by sprite group)
    # -------------------------------------------------------------------------

    def update(self, tile_collision_group, enemy_collision_group, dt):
        """
        Called once per frame by player_sprite_group.update(...) in Game.update().
        Order matters: movement() sets velocity first, then check_collision() applies
        and potentially cancels it.

        enemy_collision_group is accepted here but collision with enemies is
        handled from the enemy side (enemies.py check_collision).
        """
        self.movement(dt)
        self.check_collision(tile_collision_group)