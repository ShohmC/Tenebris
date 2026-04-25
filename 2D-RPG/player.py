# =============================================================================
# player.py — Player Sprite: Movement, Animation & HUD
# =============================================================================
# The Player class represents the character controlled by the keyboard.
# It handles:
#   1. Frame-based walking animation (2 frames per direction)
#   2. Velocity-based movement with delta-time scaling
#   3. Tile collision resolution
#   4. Drawing the health bar HUD directly onto the screen
#   5. Per-frame status effect processing (poison, speed boost, slow)
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
        # Multiplied into velocity each frame; modified by speed_boost and slow effects
        self.velocity_multiplier = 1

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

        # --- Player Status Effects ---
        # active_statuses holds string names of currently active effects (e.g. "poison").
        # status_timers holds per-effect timing and value data; written by Item.use()
        # and read each frame by status(). Default values are placeholders — real values
        # are set when an item is used.
        self.active_statuses = set()
        self.status_timers = {
            "poison":      {"damage": 2, "last_tick": 0, "end": 0},
            "speed_boost": {"multiplier": 0, "end": 0},
            "slow":        {"multiplier": 0, "end": 0}
        }
        self.status_icons = {
            "poison": pygame.transform.scale(
                pygame.image.load("Items/Potions/poisonpotion.png").convert_alpha(),
                (32, 32)),
            "speed_boost": pygame.transform.scale(
                pygame.image.load("Items/Potions/speedpotion.png").convert_alpha(),
                (32, 32)),
            "slow": pygame.transform.scale(
                pygame.image.load("Items/Potions/slowpotion.png").convert_alpha(),
                (32, 32))
        }

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

    # Draws fixed-position health bar in screen space (no camera offset applied)
    def draw_player_health_bar(self, screen):
        screen.blit(self.health_label_font.render("Health", True, BLACK), (50, 50))
        pygame.draw.rect(screen, WHITE,   (175, 55, 150, 25))
        pygame.draw.rect(screen, GREEN, (175, 55, 150 * (self.health / 100), 25))
        screen.blit(self.health_value_font.render(str(self.health), True, BLACK), (230, 56))

    # Draws status symbols to the right of health bar
    def draw_player_status_effects(self, screen):
        x_offset = 340
        y = 55
        for status in self.active_statuses:
            if status in self.status_icons:
                screen.blit(self.status_icons[status], (x_offset, y))
                x_offset += 36

    # -------------------------------------------------------------------------
    # Collision
    # -------------------------------------------------------------------------

    # Moves rect by velocity, then reverses if overlapping a solid tile
    def check_collision(self, tile_collision_group):
        self.rect.move_ip(self.velocity)
        if pygame.sprite.spritecollideany(self, tile_collision_group):
            self.rect.move_ip(-self.velocity.x, -self.velocity.y)

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    # Steps the animation counter and swaps self.image; uses getattr/setattr to
    # work with any directional counter by name without duplicating logic
    def animate(self, counter_name, frames):
        counter = (getattr(self, counter_name) + 1) % 20
        setattr(self, counter_name, counter)
        self.image = frames[0] if counter < 10 else frames[1]

    # -------------------------------------------------------------------------
    # Movement
    # -------------------------------------------------------------------------

    # Reads held keys and sets velocity; velocity_multiplier is applied here so
    # speed_boost and slow effects are reflected immediately each frame
    def movement(self, dt):
        keys = pygame.key.get_pressed()
        self.velocity.update(0, 0)

        if keys[pygame.K_w]:
            self.animate("up_counter", self.up_frames)
            self.velocity.y = -PLAYER_Y_VELOCITY * dt * self.velocity_multiplier
        if keys[pygame.K_a]:
            self.animate("left_counter", self.left_frames)
            self.velocity.x = -PLAYER_X_VELOCITY * dt * self.velocity_multiplier
        if keys[pygame.K_s]:
            self.animate("down_counter", self.down_frames)
            self.velocity.y = PLAYER_Y_VELOCITY * dt * self.velocity_multiplier
        if keys[pygame.K_d]:
            self.animate("right_counter", self.right_frames)
            self.velocity.x = PLAYER_X_VELOCITY * dt * self.velocity_multiplier

    # -------------------------------------------------------------------------
    # Status Effects
    # -------------------------------------------------------------------------

    # Processes all active status effects once per frame.
    # Poison ticks damage on an interval; speed_boost and slow apply a velocity
    # multiplier until their duration expires. All timing uses pygame.time.get_ticks().
    def status(self):
        current_time = pygame.time.get_ticks()

        if "poison" in self.active_statuses:
            if current_time > self.status_timers["poison"]["end"]:
                self.active_statuses.remove("poison")
            elif current_time - self.status_timers["poison"]["last_tick"] > 1000:
                self.health = max(0, self.health - self.status_timers["poison"]["damage"])
                self.status_timers["poison"]["last_tick"] = current_time

        if "speed_boost" in self.active_statuses:
            self.velocity_multiplier = self.status_timers["speed_boost"]["multiplier"]
            if current_time > self.status_timers["speed_boost"]["end"]:
                self.velocity_multiplier = 1
                self.active_statuses.remove("speed_boost")

        if "slow" in self.active_statuses:
            self.velocity_multiplier = self.status_timers["slow"]["multiplier"]
            if current_time > self.status_timers["slow"]["end"]:
                self.velocity_multiplier = 1
                self.active_statuses.remove("slow")

    # -------------------------------------------------------------------------
    # Main Update (called by sprite group)
    # -------------------------------------------------------------------------

    # Called by player_sprite_group.update() each frame; order matters —
    # movement() sets velocity, check_collision() applies and potentially cancels it,
    # status() processes any active effects
    def update(self, tile_collision_group, enemy_collision_group, dt):
        self.movement(dt)
        self.check_collision(tile_collision_group)
        self.status()