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

from config import *  # TILESIZE, ENEMY_LAYER, pygame, etc.
import os


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
                 health, damage, exp_on_kill, defense=0):
        super().__init__()

        # --- Flag watched by Game.update() to trigger combat state ---
        self.initiate_battle_sequence = False

        self.screen = screen
        self.initial_x_location = initial_x_location
        self.initial_y_location = initial_y_location
        self.initial_image = initial_image

        # Load all directional animation frames
        self.image = self._load_image(initial_image)
        self.combat_image = self._load_image(initial_image, combat_size=True)
        self.up_img_1 = self._load_image(up_img_1)
        self.up_img_2 = self._load_image(up_img_2)
        self.down_img_1 = self._load_image(down_img_1)
        self.down_img_2 = self._load_image(down_img_2)
        self.left_img_1 = self._load_image(left_img_1)
        self.left_img_2 = self._load_image(left_img_2)
        self.right_img_1 = self._load_image(right_img_1)
        self.right_img_2 = self._load_image(right_img_2)

        self.rect = self.image.get_rect(topleft=(initial_x_location, initial_y_location))
        self._layer = ENEMY_LAYER

        # velocity is recalculated each frame from direction toward the player.
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 2

        # --- Stats ---
        self.max_health = health
        self.health = health
        self.damage = damage
        self.exp_on_kill = exp_on_kill
        self.defense = defense

        # --- Status Effects System ---
        self.active_statuses = {}
        self.status_data = {}

        # Previous-frame position used by animation() to infer movement direction.
        self.previous_x_location = self.rect.x
        self.previous_y_location = self.rect.y

        # Battle cooldown
        self.battle_cooldown = 0

        # Per-direction animation counters
        self.up_counter = 0
        self.down_counter = 0
        self.left_counter = 0
        self.right_counter = 0

        # Reference to combat handler for floaters
        self.combat_handler = None

    # -------------------------------------------------------------------------
    # Helper Methods (MUST be at class level, NOT inside __init__)
    # -------------------------------------------------------------------------

    def _load_image(self, path, combat_size=False):
        """Load an enemy image with fallback to colored placeholder."""
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if combat_size:
                    img = pygame.transform.scale(img, (120, 120))
                else:
                    img = pygame.transform.scale(img, (28, 28))
                return img
            else:
                # Create placeholder
                size = (120, 120) if combat_size else (28, 28)
                surf = pygame.Surface(size)
                surf.fill((150, 80, 80))
                pygame.draw.rect(surf, (100, 50, 50), surf.get_rect(), 2)
                return surf
        except Exception:
            size = (120, 120) if combat_size else (28, 28)
            surf = pygame.Surface(size)
            surf.fill((150, 80, 80))
            return surf

    # -------------------------------------------------------------------------
    # Status Effects
    # -------------------------------------------------------------------------

    def set_combat_handler(self, handler):
        """Set reference to combat handler for displaying floaters."""
        self.combat_handler = handler

    def apply_status_effect(self, effect, duration, combat_handler=None):
        """Apply a status effect to the enemy."""
        if combat_handler:
            self.combat_handler = combat_handler

        self.active_statuses[effect] = duration

        if effect == "poison":
            self.status_data["poison"] = {"damage": 5, "last_tick": 0}
        elif effect == "burn":
            self.status_data["burn"] = {"damage": 8, "last_tick": 0}
        elif effect == "slow":
            self.status_data["slow"] = {"speed_multiplier": 0.5}
        elif effect == "energy_drain":
            self.status_data["energy_drain"] = {"drain_amount": 10}

        if self.combat_handler:
            self.combat_handler.floaters.append({
                "text": f"{effect.upper()}!",
                "color": (180, 100, 255),
                "x": WINDOW_WIDTH // 1.5 + 100,
                "y": WINDOW_HEIGHT // 6.25 - 100,
                "timer": 60
            })

    def remove_status_effect(self, effect):
        """Remove a specific status effect from the enemy."""
        if effect in self.active_statuses:
            del self.active_statuses[effect]
        if effect in self.status_data:
            del self.status_data[effect]

    def clear_all_status_effects(self):
        """Clear all status effects from the enemy."""
        self.active_statuses.clear()
        self.status_data.clear()

    def update_status_effects(self, turn_action=False):
        """Update enemy status effects."""
        damage_dealt = 0
        effects_to_remove = []

        for effect, duration in list(self.active_statuses.items()):
            new_duration = duration - 1
            if new_duration <= 0:
                effects_to_remove.append(effect)
                continue
            else:
                self.active_statuses[effect] = new_duration

            if turn_action:
                if effect == "poison":
                    poison_damage = self.status_data.get("poison", {}).get("damage", 5)
                    self.health -= poison_damage
                    damage_dealt += poison_damage

                    if self.combat_handler:
                        self.combat_handler.floaters.append({
                            "text": f"-{poison_damage} (Poison)",
                            "color": (160, 80, 255),
                            "x": WINDOW_WIDTH // 1.5 + 80,
                            "y": WINDOW_HEIGHT // 6.25 - 40,
                            "timer": 50
                        })

                elif effect == "burn":
                    burn_damage = self.status_data.get("burn", {}).get("damage", 8)
                    self.health -= burn_damage
                    damage_dealt += burn_damage

                    if self.combat_handler:
                        self.combat_handler.floaters.append({
                            "text": f"-{burn_damage} (Burn)",
                            "color": (255, 100, 50),
                            "x": WINDOW_WIDTH // 1.5 + 80,
                            "y": WINDOW_HEIGHT // 6.25 - 40,
                            "timer": 50
                        })

        for effect in effects_to_remove:
            self.remove_status_effect(effect)
            if self.combat_handler:
                self.combat_handler.floaters.append({
                    "text": f"{effect.upper()} wore off",
                    "color": (200, 200, 200),
                    "x": WINDOW_WIDTH // 1.5 + 80,
                    "y": WINDOW_HEIGHT // 6.25 - 80,
                    "timer": 40
                })

        if damage_dealt > 0:
            return {"damage": damage_dealt, "effects": list(self.active_statuses.keys())}
        return None

    def get_speed_multiplier(self):
        """Return current speed multiplier based on status effects."""
        multiplier = 1.0
        if "slow" in self.active_statuses:
            multiplier *= self.status_data.get("slow", {}).get("speed_multiplier", 0.5)
        return multiplier

    def has_status(self, effect):
        """Check if enemy has a specific status effect."""
        return effect in self.active_statuses

    def get_active_statuses(self):
        """Return list of active status effects."""
        return list(self.active_statuses.keys())

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    def _animate_direction(self, counter_name, frame_1, frame_2):
        """Shared animation stepper."""
        counter = (getattr(self, counter_name) + 1) % 20
        setattr(self, counter_name, counter)
        self.image = frame_1 if counter < 10 else frame_2

    def animation(self):
        """Determines movement direction and animates."""
        if self.rect.y < self.previous_y_location:
            self._animate_direction("up_counter", self.up_img_1, self.up_img_2)
        elif self.rect.y > self.previous_y_location:
            self._animate_direction("down_counter", self.down_img_1, self.down_img_2)
        elif self.rect.x < self.previous_x_location:
            self._animate_direction("left_counter", self.left_img_1, self.left_img_2)
        elif self.rect.x > self.previous_x_location:
            self._animate_direction("right_counter", self.right_img_1, self.right_img_2)

        # Store current position for next frame's comparison.
        self.previous_x_location = self.rect.x
        self.previous_y_location = self.rect.y

    def idle_animation(self):
        """Placeholder for when the enemy is stationary."""
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
            if self.battle_cooldown <= 0:
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
        """
        # Tick down battle cooldown
        if self.battle_cooldown > 0:
            self.battle_cooldown -= 1
            return

        direction = pygame.math.Vector2(
            player_rect.x - self.rect.x,
            player_rect.y - self.rect.y
        )
        distance = direction.length()

        if distance <= TILESIZE * 8:
            if distance > 0:
                direction.normalize_ip()
                current_speed = self.speed * self.get_speed_multiplier()
                self.velocity = direction * current_speed
                self.rect.move_ip(self.velocity)
                self.check_collision(tile_collision_group, player_collision_group)
            else:
                self.idle_animation()

            self.animation()

    # -------------------------------------------------------------------------
    # Run from battle
    # -------------------------------------------------------------------------

    def reset_to_spawn(self, cooldown_frames=180):
        """
        Teleports the enemy back to its original spawn location and starts a
        cooldown during which it won't chase or trigger combat.

        Parameters
        ----------
        cooldown_frames : int — number of frames to stay passive (180 ≈ 3 sec at 60 FPS)
        """
        self.rect.x = self.initial_x_location
        self.rect.y = self.initial_y_location
        self.health = self.max_health
        self.initiate_battle_sequence = False
        self.battle_cooldown = cooldown_frames
        self.clear_all_status_effects()


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
            "Enemy/Bat/left1.png",
            "Enemy/Bat/left1.png", "Enemy/Bat/left2.png",
            "Enemy/Bat/right1.png", "Enemy/Bat/right2.png",
            "Enemy/Bat/left1.png", "Enemy/Bat/left2.png",
            "Enemy/Bat/right1.png", "Enemy/Bat/right2.png",
            health, 10, 35, defense=2
        )
        self.speed = 2.5


# =============================================================================
# Concrete Enemy: Slime
# =============================================================================

class Slime(Enemies):
    def __init__(self, screen, initial_x_location, initial_y_location, health):
        super().__init__(
            screen,
            initial_x_location,
            initial_y_location,
            # Slime has no directional sprites — reuse the same walk frames
            # for every direction so it just wobbles regardless of heading.
            "Enemy/Slime/idle.png",
            "Enemy/Slime/up1.png",
            "Enemy/Slime/up2.png",
            "Enemy/Slime/down1.png",
            "Enemy/Slime/down2.png",
            "Enemy/Slime/left1.png",
            "Enemy/Slime/left2.png",
            "Enemy/Slime/right1.png",
            "Enemy/Slime/right2.png",
            health=health,
            damage=4,
            exp_on_kill=25,
        )


# =============================================================================
# Concrete Enemy: Wolf
# =============================================================================

class Wolf(Enemies):
    def __init__(self, screen, initial_x_location, initial_y_location, health):
        super().__init__(
            screen,
            initial_x_location,
            initial_y_location,
            "Enemy/Wolf/down1.png",
            # up/down use the upright front/back frames
            "Enemy/Wolf/up1.png",
            "Enemy/Wolf/up2.png",
            "Enemy/Wolf/down1.png",
            "Enemy/Wolf/down2.png",
            # left/right use the side-on running frames for a more natural look
            "Enemy/Wolf/run_left1.png",
            "Enemy/Wolf/run_left2.png",
            "Enemy/Wolf/run_right1.png",
            "Enemy/Wolf/run_right2.png",
            health=health,
            damage=12,
            exp_on_kill=80,
        )


# =============================================================================
# Concrete Enemy: Skeleton
# =============================================================================

class Skeleton(Enemies):
    def __init__(self, screen, initial_x_location, initial_y_location, health):
        super().__init__(
            screen,
            initial_x_location,
            initial_y_location,
            # default / idle image
            "Enemy/Skeleton/down1.png",
            # up frames
            "Enemy/Skeleton/up1.png",
            "Enemy/Skeleton/up2.png",
            # down frames
            "Enemy/Skeleton/down1.png",
            "Enemy/Skeleton/down2.png",
            # left frames
            "Enemy/Skeleton/left1.png",
            "Enemy/Skeleton/left2.png",
            # right frames
            "Enemy/Skeleton/right1.png",
            "Enemy/Skeleton/right2.png",
            health=health,
            damage=8,
            exp_on_kill=60,
        )