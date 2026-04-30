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
#                    sprite, and action buttons (Fight / Skills / Items / Run).
#
# State flow in main.py:
#   game_state == "playing"
#       → enemy.initiate_battle_sequence triggers combat.start_transition()
#       → game_state set to "combat"
#   game_state == "combat"
#       → draw_transition() plays until transition_finished == True
#       → then draw_combat_menu() takes over
#
# New in this version:
#   • current_turn tracking ("player" / "enemy") — turn label changes color
#   • action_queue: staggered combat steps with ms-based delays
#   • Buttons are locked while the queue is draining
#   • 1/20 critical hit chance on every attack; crit triggers log shake
#   • Enlarged, repositioned battle log panel
# =============================================================================

import math
import random
from config import *  # WINDOW_WIDTH/HEIGHT, TILESIZE, color constants, pygame

PLAYER_NAME = "Tenebris"

# Delay constants (milliseconds) — tweak these to taste
DELAY_PLAYER_LOG    = 300   # after Fight clicked → show player attack log
DELAY_TURN_SWITCH   = 800   # after player log → flip to enemy turn indicator
DELAY_ENEMY_ATTACK  = 1300  # after turn switch → enemy actually attacks + logs
DELAY_TURN_RESTORE  = 1900  # after enemy log → restore player turn indicator


class CombatHandler(pygame.sprite.Sprite):
    """
    Handles the visual rendering of the combat screen with skill system.
    """

    def __init__(self):
        super().__init__()

        self.max_radius = int(math.hypot(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.transition_radius = self.max_radius
        self.transition_speed = 20
        self.transition_active = False
        self.transition_finished = False

        self.button_font = pygame.font.Font(None, 48)
        self.float_font = pygame.font.Font(None, 40)
        self.fight_button = None
        self.items_button = None
        self.run_button = None

        # Skill system
        self.skills_button = None
        self.skill_menu_active = False
        self.skill_buttons = []
        self.back_button = None
        self.skill_button_font = pygame.font.Font(None, 32)

        # --- Custom fonts ---
        try:
            self.turn_font       = pygame.font.Font("Fonts/PressStart2P.ttf", 18)
            self.panel_name_font = pygame.font.Font("Fonts/PressStart2P.ttf", 10)
            self.log_font        = pygame.font.Font("Fonts/PressStart2P.ttf", 17)  # ~5 lines fit
        except Exception:
            self.turn_font       = pygame.font.Font(None, 48)
            self.panel_name_font = pygame.font.Font(None, 28)
            self.log_font        = pygame.font.Font(None, 40)  # ~5 lines fit fallback

        # Battle background
        self.battle_bg = None
        try:
            self.battle_bg = pygame.image.load("Backgrounds/combat_bg.png").convert()
            self.battle_bg = pygame.transform.scale(self.battle_bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except Exception:
            pass

        self.attack_sound = pygame.mixer.Sound("Music/punch2.mp3")
        self.attack_sound.set_volume(0.5)
        self.hurt_sound = pygame.mixer.Sound("Music/punch1.mp3")
        self.hurt_sound.set_volume(0.6)

        # Floating damage numbers
        self.floaters = []

        # --- Battle Log ---
        # Increased max_log_lines to fill the larger panel
        self.battle_log = []
        self.max_log_lines = 5
        self._add_to_log("Combat begins!")

        # --- Screen Shake (whole screen) ---
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_offset = (0, 0)

        # --- Log Box Shake (crit effect — only the log panel shakes) ---
        # Separate from screen shake so only the text box rattles on crit.
        self.log_shake_intensity = 0
        self.log_shake_duration  = 0   # frames remaining
        self.log_shake_offset    = (0, 0)

        # --- Post-Battle Screen ---
        self.battle_result = None

        # -----------------------------------------------------------------------
        # Turn / Action Queue
        # -----------------------------------------------------------------------
        # current_turn controls the label colour at the top of the screen.
        # "player" → gold   "enemy" → red
        self.current_turn = "player"

        # action_queue holds dicts: {"fn": callable, "trigger_at": int (ms)}
        # Steps are pushed in one go when the player clicks Fight / uses a skill.
        # Each frame, update_action_queue() fires any step whose trigger_at has
        # elapsed, then removes it.  Buttons are disabled while the queue is
        # non-empty (self.action_pending == True).
        self.action_queue   = []
        self.action_pending = False   # True while any steps are queued

        # Stores the pending combat result so the queue callbacks can signal
        # main.py.  Game.update() should poll combat.dequeue_result() each frame.
        self._queued_result = None

        # -----------------------------------------------------------------------
        # Attack Flash Animations
        # -----------------------------------------------------------------------
        # Each entry: {"side": "player"|"enemy", "timer": int, "color": RGB}
        # Drawn as an expanding, fading circle on the struck sprite side.
        self.flash_animations = []
        self._flash_max_timer = 22   # frames the flash lasts

        # -----------------------------------------------------------------------
        # Flavor Text Tables
        # -----------------------------------------------------------------------
        self._enemy_attack_lines = {
            "bat": [
                "{name} swoops in with razor wings for {dmg} damage!",
                "{name} dives at {player} for {dmg} damage!",
                "{name} screeches and rakes {player} for {dmg} damage!",
                "{name} latches on and bites {player} for {dmg} damage!",
            ],
            "slime": [
                "{name} hurls a glob of acid for {dmg} damage!",
                "{name} engulfs {player} in sticky ooze for {dmg} damage!",
                "{name} slams into {player} for {dmg} damage!",
            ],
            "goblin": [
                "{name} stabs at {player} with a rusty blade for {dmg} damage!",
                "{name} headbutts {player} for {dmg} damage!",
                "{name} lobs a rock at {player} for {dmg} damage!",
            ],
            "_generic": [
                "{name} strikes {player} for {dmg} damage!",
                "{name} lunges at {player} for {dmg} damage!",
                "{name} attacks {player} for {dmg} damage!",
                "{name} lashes out at {player} for {dmg} damage!",
            ],
        }

        self._player_attack_lines = {
            "_basic": [
                "{player} slashes at {name} for {dmg} damage!",
                "{player} drives a fist into {name} for {dmg} damage!",
                "{player} strikes {name} for {dmg} damage!",
                "{player} lands a clean hit on {name} for {dmg} damage!",
            ],
            "slash": [
                "{player} cuts clean through {name} for {dmg} damage!",
                "{player}'s blade arcs across {name} for {dmg} damage!",
                "{player} slashes {name} with precision for {dmg} damage!",
            ],
            "heavy_strike": [
                "{player} slams down on {name} with a crushing blow for {dmg}!",
                "{player} brings the full weight of their blade onto {name} for {dmg}!",
                "{player} hammers {name} into the ground for {dmg} damage!",
            ],
            "poison_strike": [
                "{player} drives a venomous blade into {name} for {dmg} damage!",
                "{player} coats {name} in poison for {dmg} damage!",
                "{player} lands a toxic strike on {name} for {dmg} damage!",
            ],
            "quick_slash": [
                "{player} dashes past {name} in a blur for {dmg} damage!",
                "{player} flicks a rapid cut at {name} for {dmg} damage!",
                "{player} nicks {name} with lightning speed for {dmg} damage!",
            ],
            "cleave": [
                "{player} sweeps through {name} in a wide arc for {dmg} damage!",
                "{player} cleaves {name} from shoulder to hip for {dmg} damage!",
            ],
            "life_steal": [
                "{player} drains the life from {name} for {dmg} damage!",
                "{player} saps {name}'s vitality for {dmg} damage!",
            ],
            "_generic_skill": [
                "{player} unleashes a skill on {name} for {dmg} damage!",
                "{player} attacks {name} with a special move for {dmg} damage!",
            ],
        }

        self._crit_lines = [
            "{attacker} found a weak point — CRITICAL HIT!",
            "CRITICAL! {attacker} strikes true!",
            "{attacker} hits with devastating force — CRITICAL!",
            "A perfect opening! {attacker} scores a CRITICAL HIT!",
        ]

    # =========================================================================
    # Transition
    # =========================================================================

    def start_transition(self):
        self.transition_radius = self.max_radius
        self.transition_active = True
        self.transition_finished = False

    def draw_transition(self, screen):
        if not self.transition_active:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255))
        center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        pygame.draw.circle(overlay, (0, 0, 0, 0), center, max(0, int(self.transition_radius)))
        screen.blit(overlay, (0, 0))
        self.transition_radius -= self.transition_speed

        if self.transition_radius <= 0:
            self.transition_radius = 0
            self.transition_active = False
            self.transition_finished = True

    # =========================================================================
    # Action Queue  (staggered combat steps)
    # =========================================================================

    def _enqueue(self, fn, delay_ms):
        """
        Schedule fn() to run `delay_ms` milliseconds from now.
        All steps for a single turn are pushed at once with increasing offsets,
        so they fire in sequence without any per-frame state machine.
        """
        trigger_at = pygame.time.get_ticks() + delay_ms
        self.action_queue.append({"fn": fn, "trigger_at": trigger_at})
        self.action_pending = True

    def update_action_queue(self):
        """
        Called every frame from Game.update() while game_state == "combat".
        Fires any queued step whose scheduled time has arrived.
        """
        if not self.action_queue:
            self.action_pending = False
            return

        now = pygame.time.get_ticks()
        # Collect steps that are ready (trigger_at <= now), preserve order
        ready = [s for s in self.action_queue if s["trigger_at"] <= now]
        self.action_queue = [s for s in self.action_queue if s["trigger_at"] > now]

        for step in ready:
            step["fn"]()

        self.action_pending = bool(self.action_queue)

    def dequeue_result(self):
        """
        Main.py polls this after update_action_queue().
        Returns the final battle result string ("victory", "game_over", etc.)
        or None if the battle is still in progress.
        """
        result = self._queued_result
        self._queued_result = None
        return result

    # =========================================================================
    # Critical Hit Helper
    # =========================================================================

    @staticmethod
    def _roll_crit():
        """Returns True with 1/20 probability."""
        return random.randint(1, 20) == 1

    def _trigger_log_shake(self):
        """Shake only the log panel — used on critical hits."""
        self.log_shake_intensity = 6
        self.log_shake_duration  = 20   # frames

    # =========================================================================
    # Flavor Text Helpers
    # =========================================================================

    def _flavor_enemy(self, enemy_name, player_name, dmg):
        """Pick a random flavor line for an enemy basic attack."""
        key = enemy_name.lower()
        lines = self._enemy_attack_lines.get(key, self._enemy_attack_lines["_generic"])
        template = random.choice(lines)
        return template.format(name=enemy_name, player=player_name, dmg=dmg)

    def _flavor_player(self, skill_id, player_name, enemy_name, dmg):
        """
        Pick a random flavor line for a player attack.
        skill_id should be "_basic" for normal attacks or the skill's .id string.
        """
        lines = self._player_attack_lines.get(
            skill_id,
            self._player_attack_lines.get("_generic_skill", [f"{player_name} attacks for {dmg} damage!"])
        )
        template = random.choice(lines)
        return template.format(player=player_name, name=enemy_name, dmg=dmg)

    def _flavor_crit(self, attacker_name):
        """Pick a random crit announcement line."""
        template = random.choice(self._crit_lines)
        return template.format(attacker=attacker_name)

    # =========================================================================
    # Attack Flash Animation
    # =========================================================================

    def _spawn_flash(self, side):
        """
        Spawn a flash animation on the given side ("player" or "enemy").
        The flash is drawn as a concentric ring burst that expands and fades.
        """
        color = (255, 80, 80) if side == "enemy" else (255, 160, 60)
        self.flash_animations.append({
            "side": side,
            "timer": self._flash_max_timer,
            "color": color,
        })

    def _draw_flashes(self, surface, player_rect, enemy_rect):
        """
        Draw all active flash animations onto surface.
        Each flash is a series of concentric circles that expand as timer falls,
        with alpha fading toward zero.  Uses an SRCALPHA surface so the alpha
        compositing works correctly over the combat background.
        """
        for flash in self.flash_animations:
            t = flash["timer"]
            max_t = self._flash_max_timer
            progress = 1.0 - (t / max_t)   # 0 at start, 1 at end

            # Pick center based on which side is being hit
            if flash["side"] == "enemy":
                cx = enemy_rect.centerx
                cy = enemy_rect.centery
            else:
                cx = player_rect.centerx
                cy = player_rect.centery

            # Radius grows from 10 to 80 over the animation
            radius = int(10 + progress * 70)
            # Alpha fades from 220 down to 0
            alpha = int(220 * (t / max_t))

            r, g, b = flash["color"]

            # Draw two rings for a more interesting burst shape
            for ring_offset in (0, 20):
                ring_radius = max(1, radius - ring_offset)
                ring_alpha  = max(0, alpha - ring_offset * 5)
                flash_surf = pygame.Surface((ring_radius * 2 + 4, ring_radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    flash_surf,
                    (r, g, b, ring_alpha),
                    (ring_radius + 2, ring_radius + 2),
                    ring_radius,
                    max(1, ring_radius // 5)   # ring thickness scales with size
                )
                surface.blit(flash_surf, (cx - ring_radius - 2, cy - ring_radius - 2))

            flash["timer"] -= 1

        # Remove finished flashes
        self.flash_animations = [f for f in self.flash_animations if f["timer"] > 0]

    # =========================================================================
    # Combat Menu Drawing
    # =========================================================================

    def draw_combat_menu(self, screen, player, enemy):
        """
        Renders the static combat screen after the transition completes.
        Everything is drawn onto an off-screen surface first so shake offsets
        can be applied cleanly in one blit.
        """
        # --- Whole-screen shake update ---
        if self.shake_duration > 0:
            self.shake_offset = (
                random.randint(-self.shake_intensity, self.shake_intensity),
                random.randint(-self.shake_intensity, self.shake_intensity)
            )
            self.shake_duration -= 1
        else:
            self.shake_offset = (0, 0)

        # --- Log-box shake update ---
        if self.log_shake_duration > 0:
            self.log_shake_offset = (
                random.randint(-self.log_shake_intensity, self.log_shake_intensity),
                random.randint(-self.log_shake_intensity, self.log_shake_intensity)
            )
            self.log_shake_duration -= 1
        else:
            self.log_shake_offset = (0, 0)

        combat_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

        # --- Background ---
        if self.battle_bg:
            combat_surface.blit(self.battle_bg, (0, 0))
        else:
            for i in range(0, WINDOW_HEIGHT, 10):
                cv = 30 + int((i / WINDOW_HEIGHT) * 40)
                pygame.draw.rect(combat_surface, (cv, max(0,cv-10), max(0,cv-20)), (0, i, WINDOW_WIDTH, 10))

        vignette = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 60))
        combat_surface.blit(vignette, (0, 0))

        # Decorative border
        bm = 10
        pygame.draw.rect(combat_surface, (100, 70, 50),
                         (bm, bm, WINDOW_WIDTH - bm*2, WINDOW_HEIGHT - bm*2), 4, border_radius=8)
        pygame.draw.rect(combat_surface, (60, 40, 30),
                         (bm+2, bm+2, WINDOW_WIDTH - bm*2 - 4, WINDOW_HEIGHT - bm*2 - 4), 2, border_radius=6)

        # --- Player Sprite ---
        player_scaled = pygame.transform.scale(player.image, (TILESIZE * 5, TILESIZE * 5))
        player_rect   = player_scaled.get_rect(midright=(WINDOW_WIDTH // 3, WINDOW_HEIGHT // 2))
        shadow = pygame.Surface(player_scaled.get_size(), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 100))
        combat_surface.blit(shadow, (player_rect.x + 5, player_rect.y + 5))
        combat_surface.blit(player_scaled, player_rect)
 
        # --- Player Status Panel ---
        panel_width, panel_height = 240, 130
        panel_x, panel_y = 20, 20
        panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_bg.fill((20, 15, 25, 220))
        combat_surface.blit(panel_bg, (panel_x, panel_y))
        pygame.draw.rect(combat_surface, (150, 100, 70),
                         (panel_x, panel_y, panel_width, panel_height), 2, border_radius=5)

        combat_surface.blit(self.panel_name_font.render("TENEBRIS", True, (255, 220, 150)),
                            (panel_x + 10, panel_y + 8))
        combat_surface.blit(self.panel_name_font.render(f"Lv.{player.level}", True, (200, 200, 200)),
                            (panel_x + panel_width - 60, panel_y + 8))

        bar_x      = panel_x + 10
        bar_y      = panel_y + 45
        bar_width  = panel_width - 20
        bar_height = 18

        combat_surface.blit(self.skill_button_font.render("HEALTH", True, (200, 180, 150)),
                            (bar_x, bar_y - 18))
        pygame.draw.rect(combat_surface, (40, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        player_max_hp = getattr(player, 'max_health', 100)
        pygame.draw.rect(combat_surface, (220, 60, 60),
                         (bar_x, bar_y, int(bar_width * player.health / player_max_hp), bar_height), border_radius=4)
        pygame.draw.rect(combat_surface, (150, 100, 70), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=4)
        combat_surface.blit(
            self.skill_button_font.render(f"{player.health}/{player_max_hp}", True, (255, 255, 200)),
            (bar_x + bar_width // 2 - self.skill_button_font.size(f"{player.health}/{player_max_hp}")[0] // 2, bar_y + 2)
        )

        energy_y = bar_y + bar_height + 15
        combat_surface.blit(self.skill_button_font.render("ENERGY", True, (150, 180, 220)),
                            (bar_x, energy_y - 18))
                            
        pygame.draw.rect(combat_surface, (20, 30, 40), (bar_x, energy_y, bar_width, bar_height), border_radius=4)
        pygame.draw.rect(combat_surface, (80, 150, 220),
                         (bar_x, energy_y, int(bar_width * player.energy / player.max_energy), bar_height), border_radius=4)
        pygame.draw.rect(combat_surface, (100, 130, 180), (bar_x, energy_y, bar_width, bar_height), 2, border_radius=4)
        combat_surface.blit(
            self.skill_button_font.render(f"{player.energy}/{player.max_energy}", True, (200, 220, 255)),
            (bar_x + bar_width // 2 - self.skill_button_font.size(f"{player.energy}/{player.max_energy}")[0] // 2, energy_y + 2)
        )
        # Weapon display inside player panel
        weapon_text = self.skill_button_font.render(f"Weapon: {player.weapon.name if player.weapon else 'Fists'}", True, (240,200,100))
        combat_surface.blit(weapon_text, (panel_x + 10, panel_y + panel_height - 25))
        # --- Enemy Sprite ---
        if hasattr(enemy, 'combat_image'):
            enemy_surface = enemy.combat_image
        else:
            enemy_surface = pygame.image.load(enemy.initial_image).convert_alpha()
            enemy_surface = pygame.transform.scale(enemy_surface, (TILESIZE * 6, TILESIZE * 6))

        enemy_rect = enemy_surface.get_rect(midleft=(WINDOW_WIDTH * 2 // 3, WINDOW_HEIGHT // 2))
        shadow2 = pygame.Surface(enemy_surface.get_size(), pygame.SRCALPHA)
        shadow2.fill((0, 0, 0, 100))
        combat_surface.blit(shadow2, (enemy_rect.x + 5, enemy_rect.y + 5))
        combat_surface.blit(enemy_surface, enemy_rect)

        # --- Enemy Status Panel ---
        ep_w, ep_h = 240, 130
        ep_x = WINDOW_WIDTH - ep_w - 20
        ep_y = 20
        ep_bg = pygame.Surface((ep_w, ep_h), pygame.SRCALPHA)
        ep_bg.fill((25, 15, 20, 220))
        combat_surface.blit(ep_bg, (ep_x, ep_y))
        pygame.draw.rect(combat_surface, (150, 80, 60), (ep_x, ep_y, ep_w, ep_h), 2, border_radius=5)

        combat_surface.blit(
            self.panel_name_font.render(enemy.__class__.__name__.upper(), True, (255, 200, 150)),
            (ep_x + 10, ep_y + 8)
        )

        eb_x = ep_x + 10
        eb_y = ep_y + 45
        combat_surface.blit(self.skill_button_font.render("HEALTH", True, (200, 160, 130)), (eb_x, eb_y - 18))
        pygame.draw.rect(combat_surface, (40, 20, 20), (eb_x, eb_y, bar_width, bar_height), border_radius=4)
        enemy_hp_pct = enemy.health / enemy.max_health
        pygame.draw.rect(combat_surface, (200, 50, 50),
                         (eb_x, eb_y, int(bar_width * enemy_hp_pct), bar_height), border_radius=4)
        pygame.draw.rect(combat_surface, (150, 80, 60), (eb_x, eb_y, bar_width, bar_height), 2, border_radius=4)
        combat_surface.blit(
            self.skill_button_font.render(f"{enemy.health}/{enemy.max_health}", True, (255, 220, 200)),
            (eb_x + bar_width // 2 - self.skill_button_font.size(f"{enemy.health}/{enemy.max_health}")[0] // 2, eb_y + 2)
        )
        combat_surface.blit(
            self.skill_button_font.render(f"DEF: {enemy.defense}", True, (180, 180, 200)),
            (eb_x, ep_y + ep_h - 30)
        )

        if hasattr(enemy, 'active_statuses') and enemy.active_statuses:
            sx, sy = ep_x + 10, ep_y + ep_h - 55
            for i, effect in enumerate(list(enemy.active_statuses.keys())[:3]):
                combat_surface.blit(
                    self.skill_button_font.render(effect.upper(), True, (255, 150, 100)),
                    (sx + i * 70, sy)
                )

        # --- VS Divider ---
        # Pulsing scale driven by current time so it animates every frame.
        vs_pulse = 1.0 + 0.06 * math.sin(pygame.time.get_ticks() * 0.004)
        vs_size  = int(64 * vs_pulse)
        vs_font  = pygame.font.Font(None, vs_size)
        vs_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)

        # Outer glow — vivid orange-red perimeter, drawn at larger offsets first
        for radius, glow_color in [
            (6, (200, 30, 0)),    # outermost: deep red
            (4, (240, 80, 10)),   # mid: orange-red
            (2, (255, 130, 30)),  # inner: bright orange
        ]:
            for gx in range(-radius, radius + 1, radius):
                for gy in range(-radius, radius + 1, radius):
                    if gx == 0 and gy == 0:
                        continue
                    g = vs_font.render("VS", True, glow_color)
                    combat_surface.blit(g, g.get_rect(center=(vs_center[0] + gx, vs_center[1] + gy)))

        # Core text — pure bright yellow, sits on top of the glow
        vs_surf = vs_font.render("VS", True, (255, 230, 0))
        vs_rect = vs_surf.get_rect(center=vs_center)
        combat_surface.blit(vs_surf, vs_rect)

        # --- Action Buttons ---
        btn_w, btn_h = 130, 65
        btn_gap = 15
        total_w = btn_w * 4 + btn_gap * 3
        btn_x_start = (WINDOW_WIDTH - total_w) // 2
        btn_y = WINDOW_HEIGHT - 100

        btn_colors = {
            "fight":  (180,  60,  60),
            "skills": (180, 120,  60),
            "items":  ( 60, 120,  80),
            "run":    (100,  80,  60),
        }
        button_defs = [
            ("Fight",  btn_colors["fight"],  (255, 100, 100)),
            ("Skills", btn_colors["skills"], (255, 180, 100)),
            ("Items",  btn_colors["items"],  (100, 255, 140)),
            ("Run",    btn_colors["run"],    (255, 160, 100)),
        ]

        # Grey out buttons when action is in progress
        buttons = []
        for i, (text, bg_color, border_color) in enumerate(button_defs):
            bx = btn_x_start + i * (btn_w + btn_gap)
            btn_rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
            buttons.append(btn_rect)

            # Dim while locked
            draw_bg    = (60, 60, 60)     if self.action_pending else bg_color
            draw_border = (120, 120, 120) if self.action_pending else border_color

            for j in range(btn_h):
                rv = max(20, draw_bg[0] - j // 3)
                gv = max(20, draw_bg[1] - j // 3)
                bv = max(20, draw_bg[2] - j // 3)
                pygame.draw.line(combat_surface, (rv, gv, bv), (bx, btn_y + j), (bx + btn_w, btn_y + j))

            pygame.draw.rect(combat_surface, draw_border, btn_rect, 3, border_radius=6)
            pygame.draw.rect(combat_surface, (0, 0, 0), btn_rect, 1, border_radius=6)

            txt_color = (150, 150, 150) if self.action_pending else (255, 255, 220)
            btn_text = self.button_font.render(text, True, txt_color)
            combat_surface.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        self.fight_button, self.skills_button, self.items_button, self.run_button = buttons

        # --- Attack Flashes ---
        # Drawn before floating text so numbers render on top of the burst.
        self._draw_flashes(combat_surface, player_rect, enemy_rect)

        # --- Floating Text ---
        for f in self.floaters:
            surf   = self.float_font.render(f["text"], True, f["color"])
            shadow = self.float_font.render(f["text"], True, (0, 0, 0))
            combat_surface.blit(shadow, (int(f["x"]) + 2, int(f["y"]) + 2))
            combat_surface.blit(surf,   (int(f["x"]),     int(f["y"])))
            f["y"]     -= 0.5
            f["timer"] -= 1
        self.floaters = [f for f in self.floaters if f["timer"] > 0]

        # --- Turn Indicator ---
        # Colour and text change based on whose turn it is.
        if self.current_turn == "player":
            turn_color = (255, 215, 0)    # gold
            turn_label = "YOUR TURN"
        else:
            turn_color = (220, 60, 60)    # red
            turn_label = "ENEMY TURN"

        turn_text = self.turn_font.render(turn_label, True, turn_color)
        combat_surface.blit(turn_text, (WINDOW_WIDTH // 2 - turn_text.get_width() // 2, 10))

        # --- Battle Log ---
        self._draw_battle_log(combat_surface)

        # --- Skill Menu overlay ---
        if self.skill_menu_active:
            self._draw_skill_menu(combat_surface, player, enemy)

        # --- Post-Battle overlay ---
        if self.battle_result is not None:
            self._draw_post_battle(combat_surface)

        screen.blit(combat_surface, self.shake_offset)

    # =========================================================================
    # Click Handler
    # =========================================================================

    def handle_click(self, mouse_pos, player, enemy, inventory):
        # Post-battle screen takes priority
        if self.battle_result is not None:
            return self._handle_post_battle_click(mouse_pos)

        # Skill menu takes priority
        if self.skill_menu_active:
            return self.handle_skill_click(mouse_pos, player, enemy)

        # Block all buttons while a turn sequence is animating
        if self.action_pending:
            return None

        # --- Fight ---
        if self.fight_button and self.fight_button.collidepoint(mouse_pos):
            self._queue_basic_attack(player, enemy)
            return "action_queued"   # main.py can ignore this — outcome arrives via dequeue_result()

        # --- Skills ---
        elif hasattr(self, 'skills_button') and self.skills_button and self.skills_button.collidepoint(mouse_pos):
            self.open_skill_menu()
            return "skill_menu_opened"

        # --- Items ---
        elif self.items_button and self.items_button.collidepoint(mouse_pos):
            return "open_inventory"

        # --- Run ---
        elif self.run_button and self.run_button.collidepoint(mouse_pos):
            self._add_to_log(f"{PLAYER_NAME} ran away!")
            return "run"

        return None

    # =========================================================================
    # Basic Attack — queued sequence
    # =========================================================================

    def _queue_basic_attack(self, player, enemy):
        """
        Breaks a full combat round into four time-separated steps:

          t+300ms  — calculate + show player attack; add log line
          t+800ms  — flip turn indicator to enemy
          t+1300ms — calculate + show enemy attack; add log line
          t+1900ms — restore player turn indicator; signal result
        """
        # Pre-calculate both attacks NOW (before any delays) so the numbers
        # are consistent regardless of timing.
        # Pre-calculate hit chance
        hit_chance = 1.0 - (player.get_miss_modifier() + enemy.evasion)
        is_hit = random.random() <= hit_chance

        # Damage calculation only if hit
        if is_hit:
            player_attack = player.get_attack()
            enemy_defense = getattr(enemy, 'defense', 0)
            raw_damage = max(1, player_attack - enemy_defense)
            is_player_crit = self._roll_crit()
            player_damage = raw_damage * 2 if is_player_crit else raw_damage
        else:
            player_damage = 0
            is_player_crit = False

        enemy_name = enemy.__class__.__name__

        # --- Step 1: Player attack log ---
        def step_player_attack():
            player.regen_energy(player.energy_regen_basic_attack)
            if not is_hit:
                self._add_to_log(f"{PLAYER_NAME} swings and misses!")
                self.floaters.append({
                    "text": "MISS!",
                    "color": (200, 200, 200),
                    "x": WINDOW_WIDTH // 1.5 + 80,
                    "y": WINDOW_HEIGHT // 6.25 - 60,
                    "timer": 30
                })
                return   # no damage, skip to next queued steps

            enemy.health -= player_damage
            self.attack_sound.play()
            self._spawn_flash("enemy")   # flash on enemy side when player hits
            self.floaters.append({
                "text": f"-{player_damage}",
                "color": (255, 215, 0) if is_player_crit else (255, 60, 60),
                "x": WINDOW_WIDTH // 1.5 + 80,
                "y": WINDOW_HEIGHT // 6.25 - 60,
                "timer": 40
            })
            self.floaters.append({
                "text": f"+{player.energy_regen_basic_attack} Energy",
                "color": (80, 180, 255),
                "x": WINDOW_WIDTH // 6 + 40,
                "y": WINDOW_HEIGHT // 3.5 - 80,
                "timer": 30
            })
            if is_player_crit:
                self._add_to_log(self._flavor_crit(PLAYER_NAME))
                self._add_to_log(self._flavor_player("_basic", PLAYER_NAME, enemy_name, player_damage))
                self._trigger_log_shake()
                self.trigger_shake(10, 15)
            else:
                self._add_to_log(self._flavor_player("_basic", PLAYER_NAME, enemy_name, player_damage))
            if player_damage >= 15:
                self.trigger_shake(8, 8)

            # Check victory immediately; if so, skip remaining steps
            if enemy.health <= 0:
                player.gain_exp(enemy.exp_on_kill)
                enemy.kill()
                self._add_to_log(f"{enemy_name} crumbles and falls!")
                self._queued_result = "victory"
                # Drain remaining queued steps so buttons re-enable
                self.action_queue.clear()

        # --- Step 2: Flip to enemy turn ---
        def step_enemy_turn_start():
            if self._queued_result:   # already over
                return
            self.current_turn = "enemy"

        # --- Step 3: Enemy attack ---
        def step_enemy_attack():
            if self._queued_result:
                return
            # Status effects tick before enemy acts
            if hasattr(enemy, 'update_status_effects'):
                enemy.update_status_effects(turn_action=True)
                if enemy.health <= 0:
                    player.gain_exp(enemy.exp_on_kill)
                    enemy.kill()
                    self._add_to_log(f"{enemy_name} succumbs to status!")
                    self._queued_result = "victory"
                    self.action_queue.clear()
                    return

            enemy_attack  = enemy.damage
            player_def    = player.get_defense()
            raw_e_damage  = max(1, enemy_attack - player_def)
            is_enemy_crit = self._roll_crit()
            enemy_damage  = raw_e_damage * 2 if is_enemy_crit else raw_e_damage

            player.take_damage(enemy_damage)
            self.hurt_sound.play()
            self._spawn_flash("player")   # flash on player side when enemy hits
            self.floaters.append({
                "text": f"-{enemy_damage}",
                "color": (255, 215, 0) if is_enemy_crit else (255, 80, 80),
                "x": WINDOW_WIDTH // 6 + 40,
                "y": WINDOW_HEIGHT // 3.5 - 40,
                "timer": 40
            })
            if is_enemy_crit:
                self._add_to_log(self._flavor_crit(enemy_name))
                self._add_to_log(self._flavor_enemy(enemy_name, PLAYER_NAME, enemy_damage))
                self._trigger_log_shake()
                self.trigger_shake(12, 15)
            else:
                self._add_to_log(self._flavor_enemy(enemy_name, PLAYER_NAME, enemy_damage))
            if enemy_damage >= 15:
                self.trigger_shake(8, 8)

            if player.health <= 0:
                self._queued_result = "game_over"
                self.action_queue.clear()

        # --- Step 4: Restore player turn ---
        def step_restore_turn():
            self.current_turn = "player"
            if not self._queued_result:
                self._queued_result = "turn_done"

        self._enqueue(step_player_attack,  DELAY_PLAYER_LOG)
        self._enqueue(step_enemy_turn_start, DELAY_TURN_SWITCH)
        self._enqueue(step_enemy_attack,   DELAY_ENEMY_ATTACK)
        self._enqueue(step_restore_turn,   DELAY_TURN_RESTORE)

    # =========================================================================
    # Skill Menu
    # =========================================================================

    def open_skill_menu(self):
        self.skill_menu_active = True

    def close_skill_menu(self):
        self.skill_menu_active = False
        self.skill_buttons.clear()
        self.back_button = None

    def _draw_skill_menu(self, surface, player, enemy):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        panel_width, panel_height = 500, 400
        panel_x = (WINDOW_WIDTH  - panel_width)  // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2

        pygame.draw.rect(surface, (40, 40, 60),    (panel_x, panel_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(surface, (255, 220, 80),  (panel_x, panel_y, panel_width, panel_height), 3, border_radius=10)

        title_font = pygame.font.Font(None, 40)
        title = title_font.render("Select Skill", True, (255, 220, 80))
        surface.blit(title, (panel_x + panel_width // 2 - title.get_width() // 2, panel_y + 15))

        from skills import get_available_skills
        available_skills  = get_available_skills(player.level)
        unlocked_skills   = [s for s in available_skills if s.id in player.unlocked_skill_ids]

        self.skill_buttons.clear()
        btn_width, btn_height = 200, 70
        start_x = panel_x + 30
        start_y = panel_y + 70
        gap = 20
        mouse_pos = pygame.mouse.get_pos()

        for i, skill in enumerate(unlocked_skills):
            row, col = divmod(i, 2)
            bx = start_x + col * (btn_width + gap)
            by = start_y + row * (btn_height + gap)
            rect = pygame.Rect(bx, by, btn_width, btn_height)
            can_afford = player.energy >= skill.cost
            bg_color = (80, 60, 60) if not can_afford else (60, 60, 80)
            pygame.draw.rect(surface, bg_color, rect, border_radius=5)
            pygame.draw.rect(surface, (255, 220, 80) if can_afford else (180, 100, 100), rect, 2, border_radius=5)
            surface.blit(self.skill_button_font.render(skill.name, True, (255, 255, 255)), (rect.x + 8, rect.y + 8))
            surface.blit(self.skill_button_font.render(f"Cost: {skill.cost} Energy", True, (180, 180, 255)), (rect.x + 8, rect.y + 35))
            if not can_afford:
                surface.blit(self.skill_button_font.render("NOT ENOUGH ENERGY!", True, (255, 100, 100)), (rect.x + 8, rect.y + 50))
            self.skill_buttons.append((skill, rect, can_afford))

        # Back button
        bb_w, bb_h = 120, 40
        bb_x = panel_x + panel_width // 2 - bb_w // 2
        bb_y = panel_y + panel_height - 55
        self.back_button = pygame.Rect(bb_x, bb_y, bb_w, bb_h)
        pygame.draw.rect(surface, (80, 80, 100), self.back_button, border_radius=5)
        pygame.draw.rect(surface, (200, 200, 200), self.back_button, 2, border_radius=5)
        back_text = self.skill_button_font.render("Back", True, (255, 255, 255))
        surface.blit(back_text, back_text.get_rect(center=self.back_button.center))

        # Tooltip
        for skill, rect, _ in self.skill_buttons:
            if rect.collidepoint(mouse_pos):
                lines = [f"Type: {skill.skill_type.upper()}", skill.description, f"Cost: {skill.cost} Energy"]
                if skill.effect:
                    lines.append(f"Effect: {skill.effect} ({skill.effect_duration} turns)")
                lh = 24
                tw, th = 250, len(lines) * lh + 10
                tx = mouse_pos[0] + 15
                ty = mouse_pos[1] + 15
                if tx + tw > WINDOW_WIDTH:  tx = mouse_pos[0] - tw - 15
                if ty + th > WINDOW_HEIGHT: ty = mouse_pos[1] - th - 15
                pygame.draw.rect(surface, (20, 20, 30),  (tx, ty, tw, th), border_radius=5)
                pygame.draw.rect(surface, (255, 220, 80), (tx, ty, tw, th), 2, border_radius=5)
                for j, line in enumerate(lines):
                    surface.blit(self.skill_button_font.render(line, True, (220, 220, 220)), (tx + 8, ty + 5 + j * lh))
                break

    def draw_skill_menu(self, screen, player, enemy):
        self._draw_skill_menu(screen, player, enemy)

    def handle_skill_click(self, mouse_pos, player, enemy):
        if self.back_button and self.back_button.collidepoint(mouse_pos):
            self.close_skill_menu()
            return "close"
        for skill, rect, can_afford in self.skill_buttons:
            if rect.collidepoint(mouse_pos):
                if not can_afford:
                    return "no_energy"
                result = self.use_skill(skill, player, enemy)
                self.close_skill_menu()
                return result
        return None

    def use_skill(self, skill, player, enemy):
        """Execute a skill's effect — skills still resolve immediately (not queued)."""
        if not player.use_energy(skill.cost):
            return "no_energy"

        self.floaters.append({"text": f"-{skill.cost} Energy", "color": (255, 180, 80),
                              "x": WINDOW_WIDTH // 2, "y": WINDOW_HEIGHT // 2, "timer": 25})

        enemy_name = enemy.__class__.__name__
        is_crit = self._roll_crit()

        if skill.skill_type == "damage":
            player_attack = player.get_attack()
            enemy_defense = getattr(enemy, 'defense', 0)
            raw = max(1, int((player_attack * skill.value) - enemy_defense))
            damage = raw * 2 if is_crit else raw
            enemy.health -= damage
            self._spawn_flash("enemy")
            self.floaters.append({"text": f"-{damage}!", "color": (255, 215, 0) if is_crit else (255, 60, 60),
                                  "x": WINDOW_WIDTH // 1.5 + 80, "y": WINDOW_HEIGHT // 6.25 - 60, "timer": 30})
            self.attack_sound.play()
            if is_crit:
                self._add_to_log(self._flavor_crit(PLAYER_NAME))
                self._trigger_log_shake()
                self.trigger_shake(12, 15)
            self._add_to_log(self._flavor_player(skill.id, PLAYER_NAME, enemy_name, damage))
            if damage >= 20:
                self.trigger_shake(12, 12)

        elif skill.skill_type == "heal":
            heal_amount = int(skill.value)
            player.health = min(100, player.health + heal_amount)
            self.floaters.append({"text": f"+{heal_amount} HP", "color": (80, 255, 80),
                                  "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 40, "timer": 30})
            self._add_to_log(f"{PLAYER_NAME} uses {skill.name} and recovers {heal_amount} HP!")

        elif skill.skill_type == "status":
            player_attack = player.get_attack()
            enemy_defense = getattr(enemy, 'defense', 0)
            raw = max(1, int((player_attack * skill.value) - enemy_defense))
            damage = raw * 2 if is_crit else raw
            enemy.health -= damage
            self._spawn_flash("enemy")
            self.floaters.append({"text": f"-{damage}!", "color": (255, 215, 0) if is_crit else (255, 60, 60),
                                  "x": WINDOW_WIDTH // 1.5 + 80, "y": WINDOW_HEIGHT // 6.25 - 60, "timer": 30})
            if is_crit:
                self._add_to_log(self._flavor_crit(PLAYER_NAME))
                self._trigger_log_shake()
                self.trigger_shake(12, 15)
            self._add_to_log(self._flavor_player(skill.id, PLAYER_NAME, enemy_name, damage))
            if skill.effect:
                enemy.set_combat_handler(self)
                enemy.apply_status_effect(skill.effect, skill.effect_duration)
                self._add_to_log(f"{enemy_name} is now {skill.effect}!")
            self.attack_sound.play()

        elif skill.skill_type == "buff":
            if skill.effect == "energy_boost":
                player.regen_energy(int(skill.value))
                self.floaters.append({"text": f"+{int(skill.value)} Energy", "color": (80, 180, 255),
                                      "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 80, "timer": 30})
                self._add_to_log(f"{PLAYER_NAME} uses {skill.name}!")

        if enemy.health <= 0:
            player.gain_exp(enemy.exp_on_kill)
            enemy.kill()
            self._add_to_log(f"{enemy_name} is defeated!")
            return "victory"

        return self.do_enemy_turn(player, enemy)

    def do_enemy_turn(self, player, enemy):
        """Immediate enemy turn — used by skills (not queued)."""
        if hasattr(enemy, 'update_status_effects'):
            enemy.update_status_effects(turn_action=True)
        if enemy.health <= 0:
            player.gain_exp(enemy.exp_on_kill)
            enemy.kill()
            self._add_to_log(f"{enemy.__class__.__name__} succumbs to status effects!")
            return "victory"

        en = enemy.__class__.__name__
        enemy_attack  = enemy.damage
        player_def    = player.get_defense()
        raw           = max(1, enemy_attack - player_def)
        is_crit       = self._roll_crit()
        enemy_damage  = raw * 2 if is_crit else raw
        player.take_damage(enemy_damage)
        self.hurt_sound.play()
        self._spawn_flash("player")

        self.floaters.append({"text": f"-{enemy_damage}", "color": (255, 215, 0) if is_crit else (255, 80, 80),
                              "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 40, "timer": 30})
        if is_crit:
            self._add_to_log(self._flavor_crit(en))
            self._trigger_log_shake()
            self.trigger_shake(12, 15)
        self._add_to_log(self._flavor_enemy(en, PLAYER_NAME, enemy_damage))
        if enemy_damage >= 15:
            self.trigger_shake(8, 8)

        if player.health <= 0:
            return "game_over"
        return "turn_done"

    # =========================================================================
    # Battle Log
    # =========================================================================

    def _add_to_log(self, text):
        self.battle_log.append(text)
        if len(self.battle_log) > self.max_log_lines:
            self.battle_log.pop(0)

    def _draw_battle_log(self, surface):
        if not self.battle_log:
            return

        # Panel sized to hold exactly max_log_lines rows at the current font.
        # line_height = font size + a few pixels padding.
        line_height = 42   # pixels per row (font 17px PressStart2P + padding)
        log_w = 900
        log_h = self.max_log_lines * line_height + 20   # 20px total vertical padding
        log_x = (WINDOW_WIDTH - log_w) // 2
        # Sit just above the action buttons (buttons at WINDOW_HEIGHT - 100, h=65)
        log_y = WINDOW_HEIGHT - 100 - log_h - 12

        # Apply log-specific shake on crits
        ox, oy = self.log_shake_offset
        draw_x = log_x + ox
        draw_y = log_y + oy

        bg = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        surface.blit(bg, (draw_x, draw_y))
        pygame.draw.rect(surface, (100, 70, 50),
                         (draw_x, draw_y, log_w, log_h), 2, border_radius=6)

        # Show the most recent max_log_lines entries; newest at the bottom.
        # Older lines fade toward transparent — line 0 (oldest visible) is most faded.
        # Alpha ramp: oldest = 80, newest = 255.
        visible = self.battle_log[-self.max_log_lines:]
        n = len(visible)
        for i, line in enumerate(visible):
            # Fade factor: 0.0 for oldest, 1.0 for newest
            fade = i / max(n - 1, 1)
            # Alpha: 80 at oldest, 255 at newest
            alpha = int(80 + fade * 175)
            # Colour: grey → bright cream as line ages out
            grey_val = int(160 + fade * 95)
            color = (grey_val, grey_val, int(grey_val * 0.78))  # warm cream tint on newest

            # Render to a temporary SRCALPHA surface so we can apply per-line alpha
            rendered = self.log_font.render(line, True, (255, 255, 255))
            line_surf = pygame.Surface(rendered.get_size(), pygame.SRCALPHA)
            line_surf.blit(rendered, (0, 0))
            # Modulate alpha: multiply each pixel's alpha by our fade factor
            line_surf.fill((color[0], color[1], color[2], alpha), special_flags=pygame.BLEND_RGBA_MULT)

            surface.blit(line_surf, (draw_x + 14, draw_y + 10 + i * line_height))

    # =========================================================================
    # Screen Shake
    # =========================================================================

    def trigger_shake(self, intensity=10, duration=8):
        self.shake_intensity = intensity
        self.shake_duration  = duration

    # =========================================================================
    # Post-Battle Screen
    # =========================================================================

    def show_post_battle(self, xp_gained, items=None):
        if items is None:
            items = []
        self.battle_result = {"xp": xp_gained, "items": items}

    def _draw_post_battle(self, surface):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 400, 250
        panel_x = (WINDOW_WIDTH  - panel_w) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2
        pygame.draw.rect(surface, (20, 20, 40), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surface, (255, 215, 0), (panel_x, panel_y, panel_w, panel_h), 3, border_radius=12)

        title_font = pygame.font.Font(None, 56)
        title = title_font.render("Victory!", True, (255, 215, 0))
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 20))

        info_font = pygame.font.Font(None, 36)
        xp_text = info_font.render(f"+{self.battle_result['xp']} XP", True, (255, 255, 255))
        surface.blit(xp_text, (panel_x + panel_w // 2 - xp_text.get_width() // 2, panel_y + 90))

        if self.battle_result["items"]:
            item_font = pygame.font.Font(None, 28)
            surface.blit(item_font.render("Items found:", True, (200, 200, 200)), (panel_x + 40, panel_y + 140))
            for i, item in enumerate(self.battle_result["items"]):
                surface.blit(item_font.render(f"• {item}", True, (255, 255, 255)), (panel_x + 60, panel_y + 170 + i * 30))

        btn_w, btn_h = 160, 45
        btn_x = panel_x + panel_w // 2 - btn_w // 2
        btn_y = panel_y + panel_h - 70
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(surface, (60, 60, 100), btn_rect, border_radius=6)
        pygame.draw.rect(surface, (150, 150, 200), btn_rect, 2, border_radius=6)
        surface.blit(info_font.render("Continue", True, (255, 255, 255)),
                     info_font.render("Continue", True, (255,255,255)).get_rect(center=btn_rect.center))
        self._post_battle_continue_rect = btn_rect

    def _handle_post_battle_click(self, mouse_pos):
        if hasattr(self, '_post_battle_continue_rect') and self._post_battle_continue_rect.collidepoint(mouse_pos):
            self.battle_result = None
            return "post_battle_continue"
        return None

    def clear_battle(self):
        self.transition_finished = False
        self.battle_result    = None
        self.battle_log       = []
        self.action_queue     = []
        self.action_pending   = False
        self._queued_result   = None
        self.current_turn     = "player"
        self.flash_animations = []
        self._add_to_log("Combat begins!")