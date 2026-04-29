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
        self.float_font   = pygame.font.Font(None, 40)
        self.fight_button = None
        self.items_button = None
        self.run_button   = None

        self.skills_button = None
        self.skill_menu_active = False
        self.skill_buttons = []  # List of (skill, rect) for current menu
        self.back_button = None
        self.skill_button_font = pygame.font.Font(None, 32)

        self.attack_sound = pygame.mixer.Sound("Music/punch2.mp3")
        self.attack_sound.set_volume(0.5)
        self.hurt_sound = pygame.mixer.Sound("Music/punch1.mp3")
        self.hurt_sound.set_volume(0.6)
        

        # Floating text system — list of {"text", "color", "x", "y", "timer"}
        self.floaters = []
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
        """
        # --- Background with gradient effect ---
        for i in range(0, WINDOW_HEIGHT, 10):
            color_value = 30 + int((i / WINDOW_HEIGHT) * 40)
            pygame.draw.rect(screen, (color_value, color_value - 10, color_value - 20),
                             (0, i, WINDOW_WIDTH, 10))

        # Simple vignette effect
        vignette = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 60))
        screen.blit(vignette, (0, 0))

        # --- Decorative border/frame ---
        border_margin = 10
        pygame.draw.rect(screen, (100, 70, 50), (border_margin, border_margin,
                                                 WINDOW_WIDTH - border_margin * 2, WINDOW_HEIGHT - border_margin * 2),
                         4, border_radius=8)
        pygame.draw.rect(screen, (60, 40, 30), (border_margin + 2, border_margin + 2,
                                                WINDOW_WIDTH - border_margin * 2 - 4,
                                                WINDOW_HEIGHT - border_margin * 2 - 4), 2, border_radius=6)

        # --- Player Sprite (Left Side) ---
        player_scaled = pygame.transform.scale(player.image, (TILESIZE * 5, TILESIZE * 5))
        player_rect = player_scaled.get_rect(midright=(WINDOW_WIDTH // 3, WINDOW_HEIGHT // 2))
        shadow_surf = pygame.Surface((player_scaled.get_width(), player_scaled.get_height()), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        screen.blit(shadow_surf, (player_rect.x + 5, player_rect.y + 5))
        screen.blit(player_scaled, player_rect)

        # --- Player Status Panel (Left) ---
        panel_width = 240
        panel_height = 130
        panel_x = 20
        panel_y = 20

        panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_bg.fill((20, 15, 25, 220))
        screen.blit(panel_bg, (panel_x, panel_y))
        pygame.draw.rect(screen, (150, 100, 70), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=5)

        name_font = pygame.font.Font(None, 28)
        name_text = name_font.render("TENEBRIS", True, (255, 220, 150))
        screen.blit(name_text, (panel_x + 10, panel_y + 8))

        level_text = name_font.render(f"Lv.{player.level}", True, (200, 200, 200))
        screen.blit(level_text, (panel_x + panel_width - 60, panel_y + 8))

        # Health Bar
        bar_x = panel_x + 10
        bar_y = panel_y + 45
        bar_width = panel_width - 20
        bar_height = 18

        health_label = self.skill_button_font.render("HEALTH", True, (200, 180, 150))
        screen.blit(health_label, (bar_x, bar_y - 18))

        pygame.draw.rect(screen, (40, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        player_max_health = getattr(player, 'max_health', 100)
        health_percent = player.health / player_max_health
        pygame.draw.rect(screen, (220, 60, 60), (bar_x, bar_y, bar_width * health_percent, bar_height), border_radius=4)
        pygame.draw.rect(screen, (150, 100, 70), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=4)
        health_text = self.skill_button_font.render(f"{player.health}/{player_max_health}", True, (255, 255, 200))
        screen.blit(health_text, (bar_x + bar_width // 2 - health_text.get_width() // 2, bar_y + 2))

        # Energy Bar
        energy_y = bar_y + bar_height + 15

        energy_label = self.skill_button_font.render("ENERGY", True, (150, 180, 220))
        screen.blit(energy_label, (bar_x, energy_y - 18))

        pygame.draw.rect(screen, (20, 30, 40), (bar_x, energy_y, bar_width, bar_height), border_radius=4)
        energy_percent = player.energy / player.max_energy
        pygame.draw.rect(screen, (80, 150, 220), (bar_x, energy_y, bar_width * energy_percent, bar_height),
                         border_radius=4)
        pygame.draw.rect(screen, (100, 130, 180), (bar_x, energy_y, bar_width, bar_height), 2, border_radius=4)
        energy_text = self.skill_button_font.render(f"{player.energy}/{player.max_energy}", True, (200, 220, 255))
        screen.blit(energy_text, (bar_x + bar_width // 2 - energy_text.get_width() // 2, energy_y + 2))

        # =========================================================================
        # ENEMY SPRITE - Defined ONCE here (after both panels, before VS divider)
        # =========================================================================
        # Load the enemy combat sprite
        if hasattr(enemy, 'combat_image'):
            enemy_surface = enemy.combat_image
        else:
            enemy_surface = pygame.image.load(enemy.initial_image).convert_alpha()
            enemy_surface = pygame.transform.scale(enemy_surface, (TILESIZE * 6, TILESIZE * 6))

        enemy_rect = enemy_surface.get_rect(midleft=(WINDOW_WIDTH * 2 // 3, WINDOW_HEIGHT // 2))
        # Add shadow under enemy
        shadow_surf = pygame.Surface((enemy_surface.get_width(), enemy_surface.get_height()), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        screen.blit(shadow_surf, (enemy_rect.x + 5, enemy_rect.y + 5))
        screen.blit(enemy_surface, enemy_rect)

        # --- Enemy Status Panel (Right) ---
        enemy_panel_width = 240
        enemy_panel_height = 130
        enemy_panel_x = WINDOW_WIDTH - enemy_panel_width - 20
        enemy_panel_y = 20

        panel_bg = pygame.Surface((enemy_panel_width, enemy_panel_height), pygame.SRCALPHA)
        panel_bg.fill((25, 15, 20, 220))
        screen.blit(panel_bg, (enemy_panel_x, enemy_panel_y))
        pygame.draw.rect(screen, (150, 80, 60), (enemy_panel_x, enemy_panel_y, enemy_panel_width, enemy_panel_height),
                         2, border_radius=5)

        enemy_name = enemy.__class__.__name__.upper()
        enemy_name_text = name_font.render(enemy_name, True, (255, 200, 150))
        screen.blit(enemy_name_text, (enemy_panel_x + 10, enemy_panel_y + 8))

        # Health Bar (Enemy)
        bar_x = enemy_panel_x + 10
        bar_y = enemy_panel_y + 45

        enemy_health_label = self.skill_button_font.render("HEALTH", True, (200, 160, 130))
        screen.blit(enemy_health_label, (bar_x, bar_y - 18))

        pygame.draw.rect(screen, (40, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        enemy_health_percent = enemy.health / enemy.max_health
        pygame.draw.rect(screen, (200, 50, 50), (bar_x, bar_y, bar_width * enemy_health_percent, bar_height),
                         border_radius=4)
        pygame.draw.rect(screen, (150, 80, 60), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=4)

        enemy_health_text = self.skill_button_font.render(f"{enemy.health}/{enemy.max_health}", True, (255, 220, 200))
        screen.blit(enemy_health_text, (bar_x + bar_width // 2 - enemy_health_text.get_width() // 2, bar_y + 2))

        # Enemy Defense info
        defense_label = self.skill_button_font.render(f"DEF: {enemy.defense}", True, (180, 180, 200))
        screen.blit(defense_label, (bar_x, enemy_panel_y + enemy_panel_height - 30))

        # Status effects display on enemy panel
        if hasattr(enemy, 'active_statuses') and enemy.active_statuses:
            status_x = enemy_panel_x + 10
            status_y = enemy_panel_y + enemy_panel_height - 55
            for i, effect in enumerate(list(enemy.active_statuses.keys())[:3]):
                effect_text = self.skill_button_font.render(effect.upper(), True, (255, 150, 100))
                screen.blit(effect_text, (status_x + i * 70, status_y))

        # --- VS Divider ---
        vs_font = pygame.font.Font(None, 48)
        vs_text = vs_font.render("VS", True, (200, 150, 100))
        vs_rect = vs_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        for offset in [-2, -1, 0, 1, 2]:
            glow_text = vs_font.render("VS", True, (100, 70, 50))
            screen.blit(glow_text, (vs_rect.x + offset, vs_rect.y + offset))
        screen.blit(vs_text, vs_rect)

        # --- Action Buttons (Bottom) ---
        btn_w = 130
        btn_h = 65
        btn_gap = 15
        total_w = btn_w * 4 + btn_gap * 3
        btn_x_start = (WINDOW_WIDTH - total_w) // 2
        btn_y = WINDOW_HEIGHT - 100

        btn_colors = {
            "fight": (180, 60, 60),
            "skills": (180, 120, 60),
            "items": (60, 120, 80),
            "run": (100, 80, 60)
        }

        button_defs = [
            ("Fight", btn_colors["fight"], (255, 100, 100)),
            ("Skills", btn_colors["skills"], (255, 180, 100)),
            ("Items", btn_colors["items"], (100, 255, 140)),
            ("Run", btn_colors["run"], (255, 160, 100))
        ]

        buttons = []
        for i, (text, bg_color, border_color) in enumerate(button_defs):
            btn_x = btn_x_start + i * (btn_w + btn_gap)
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            buttons.append(btn_rect)

            for j in range(btn_h):
                color_val = max(20, bg_color[0] - j // 3), max(20, bg_color[1] - j // 3), max(20, bg_color[2] - j // 3)
                pygame.draw.line(screen, color_val, (btn_x, btn_y + j), (btn_x + btn_w, btn_y + j))

            pygame.draw.rect(screen, border_color, btn_rect, 3, border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), btn_rect, 1, border_radius=6)

            btn_text = self.button_font.render(text, True, (255, 255, 220))
            screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        self.fight_button, self.skills_button, self.items_button, self.run_button = buttons

        # --- Floating Text ---
        for f in self.floaters:
            surf = self.float_font.render(f["text"], True, f["color"])
            shadow_surf = self.float_font.render(f["text"], True, (0, 0, 0))
            screen.blit(shadow_surf, (int(f["x"]) + 2, int(f["y"]) + 2))
            screen.blit(surf, (int(f["x"]), int(f["y"])))
            f["y"] -= 0.5
            f["timer"] -= 1
        self.floaters = [f for f in self.floaters if f["timer"] > 0]

        # --- Turn Indicator ---
        turn_text = self.skill_button_font.render("YOUR TURN", True, (255, 220, 100))
        turn_rect = turn_text.get_rect(center=(WINDOW_WIDTH // 2, 15))
        screen.blit(turn_text, turn_rect)

    def handle_click(self, mouse_pos, player, enemy, inventory):
        # If skill menu is active, handle skill selection
        if self.skill_menu_active:
            return self.handle_skill_click(mouse_pos, player, enemy)

        # Normal combat menu
        if self.fight_button and self.fight_button.collidepoint(mouse_pos):
            # Basic attack (free, builds energy)
            player_attack = player.get_attack()
            self.attack_sound.play()
            enemy_defense = getattr(enemy, 'defense', 0)
            damage = max(1, player_attack - enemy_defense)
            enemy.health -= damage

            # Regenerate energy on basic attack
            player.regen_energy(player.energy_regen_basic_attack)

            # Damage floater
            self.floaters.append({"text": f"-{damage}", "color": (255, 60, 60),
                                  "x": WINDOW_WIDTH // 1.5 + 80, "y": WINDOW_HEIGHT // 6.25 - 60, "timer": 30})

            # Energy gain floater
            self.floaters.append({"text": f"+{player.energy_regen_basic_attack} Energy", "color": (80, 180, 255),
                                  "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 80, "timer": 25})

            if enemy.health <= 0:
                player.exp += enemy.exp_on_kill
                enemy.kill()
                return "victory"
            else:
                # Enemy turn
                enemy_attack = enemy.damage
                player_defense = player.get_defense()
                enemy_damage = max(1, enemy_attack - player_defense)
                player.take_damage(enemy_damage)
                self.hurt_sound.play()
                self.floaters.append({"text": f"-{enemy_damage}", "color": (255, 80, 80),
                                      "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 40, "timer": 30})
                if player.health <= 0:
                    return "game_over"
                return "turn_done"

        elif hasattr(self, 'skills_button') and self.skills_button and self.skills_button.collidepoint(mouse_pos):
            # Open skill menu
            self.open_skill_menu()
            return "skill_menu_opened"

        elif self.items_button and self.items_button.collidepoint(mouse_pos):
            return "open_inventory"

        elif self.run_button and self.run_button.collidepoint(mouse_pos):
            return "run"

        return None

    # -------------------------------------------------------------------------
    # Skill Menu
    # -------------------------------------------------------------------------

    def open_skill_menu(self):
        """Open the skill selection menu."""
        self.skill_menu_active = True

    def close_skill_menu(self):
        """Close the skill selection menu."""
        self.skill_menu_active = False
        self.skill_buttons.clear()
        self.back_button = None

    def draw_skill_menu(self, screen, player, enemy):
        """
        Draws the skill selection menu overlay on top of combat screen.
        Optimized for performance.
        """
        # Simple dark overlay (much faster than per-pixel vignette)
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Skill menu panel
        panel_width = 500
        panel_height = 400
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2

        # Draw panel (no per-pixel operations)
        pygame.draw.rect(screen, (40, 40, 60), (panel_x, panel_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(screen, (255, 220, 80), (panel_x, panel_y, panel_width, panel_height), 3, border_radius=10)

        # Title
        title_font = pygame.font.Font(None, 40)
        title = title_font.render("Select Skill", True, (255, 220, 80))
        screen.blit(title, (panel_x + panel_width // 2 - title.get_width() // 2, panel_y + 15))

        # Get available skills (cache this if possible)
        from skills import get_available_skills
        available_skills = get_available_skills(player.level)

        # Filter to unlocked skills
        unlocked_skills = [s for s in available_skills if s.id in player.unlocked_skill_ids]

        # Create skill buttons (reused, not recreated every frame unnecessarily)
        self.skill_buttons.clear()
        btn_width = 200
        btn_height = 70
        start_x = panel_x + 30
        start_y = panel_y + 70
        gap = 20

        # Get mouse position once per frame
        mouse_pos = pygame.mouse.get_pos()

        for i, skill in enumerate(unlocked_skills):
            row = i // 2
            col = i % 2
            btn_x = start_x + col * (btn_width + gap)
            btn_y = start_y + row * (btn_height + gap)
            rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)

            # Button background color (red if not enough energy)
            can_afford = player.energy >= skill.cost
            bg_color = (80, 60, 60) if not can_afford else (60, 60, 80)
            pygame.draw.rect(screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(screen, (255, 220, 80) if can_afford else (180, 100, 100), rect, 2, border_radius=5)

            # Skill name and cost
            name_text = self.skill_button_font.render(skill.name, True, (255, 255, 255))
            cost_text = self.skill_button_font.render(f"Cost: {skill.cost} Energy", True, (180, 180, 255))
            screen.blit(name_text, (rect.x + 8, rect.y + 8))
            screen.blit(cost_text, (rect.x + 8, rect.y + 35))

            # Low energy warning
            if not can_afford:
                warning = self.skill_button_font.render("NOT ENOUGH ENERGY!", True, (255, 100, 100))
                screen.blit(warning, (rect.x + 8, rect.y + 50))

            self.skill_buttons.append((skill, rect, can_afford))

        # Back button
        back_btn_width = 120
        back_btn_height = 40
        back_btn_x = panel_x + panel_width // 2 - back_btn_width // 2
        back_btn_y = panel_y + panel_height - 55
        self.back_button = pygame.Rect(back_btn_x, back_btn_y, back_btn_width, back_btn_height)
        pygame.draw.rect(screen, (80, 80, 100), self.back_button, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.back_button, 2, border_radius=5)
        back_text = self.skill_button_font.render("Back", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button.center))

        # Tooltip for hovered skill (only draw if mouse is over a skill)
        for skill, rect, _ in self.skill_buttons:
            if rect.collidepoint(mouse_pos):
                # Draw tooltip
                tooltip_lines = [
                    f"Type: {skill.skill_type.upper()}",
                    skill.description,
                    f"Cost: {skill.cost} Energy"
                ]
                if skill.effect:
                    tooltip_lines.append(f"Effect: {skill.effect} ({skill.effect_duration} turns)")

                # Calculate tooltip size
                line_height = 24
                tooltip_width = 250
                tooltip_height = len(tooltip_lines) * line_height + 10
                tooltip_x = mouse_pos[0] + 15
                tooltip_y = mouse_pos[1] + 15

                # Make sure tooltip stays on screen
                if tooltip_x + tooltip_width > WINDOW_WIDTH:
                    tooltip_x = mouse_pos[0] - tooltip_width - 15
                if tooltip_y + tooltip_height > WINDOW_HEIGHT:
                    tooltip_y = mouse_pos[1] - tooltip_height - 15

                # Draw tooltip background
                pygame.draw.rect(screen, (20, 20, 30), (tooltip_x, tooltip_y, tooltip_width, tooltip_height),
                                 border_radius=5)
                pygame.draw.rect(screen, (255, 220, 80), (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 2,
                                 border_radius=5)

                # Draw tooltip text
                for j, line in enumerate(tooltip_lines):
                    text = self.skill_button_font.render(line, True, (220, 220, 220))
                    screen.blit(text, (tooltip_x + 8, tooltip_y + 5 + j * line_height))
                break  # Only show tooltip for first hovered skill

    def handle_skill_click(self, mouse_pos, player, enemy):
        """
        Handle clicks on the skill menu.
        Returns:
            "skill_used" - Skill was used successfully
            "no_energy" - Not enough energy
            None - No skill clicked (check back button)
        """
        # Check back button
        if self.back_button and self.back_button.collidepoint(mouse_pos):
            self.close_skill_menu()
            return "close"

        # Check skill buttons
        for skill, rect, can_afford in self.skill_buttons:
            if rect.collidepoint(mouse_pos):
                if not can_afford:
                    return "no_energy"

                # Use the skill
                result = self.use_skill(skill, player, enemy)
                self.close_skill_menu()
                return result

        return None

    def use_skill(self, skill, player, enemy):
        """
        Execute a skill's effect.
        Returns:
            "victory" - Enemy defeated
            "game_over" - Player died
            "turn_done" - Turn completed, enemy will attack
        """
        # Deduct energy cost
        if not player.use_energy(skill.cost):
            return "no_energy"

        # Show energy cost floater
        self.floaters.append({"text": f"-{skill.cost} Energy", "color": (255, 180, 80),
                              "x": WINDOW_WIDTH // 2, "y": WINDOW_HEIGHT // 2, "timer": 25})

        # Execute based on skill type
        if skill.skill_type == "damage":
            # Calculate damage
            player_attack = player.get_attack()
            enemy_defense = getattr(enemy, 'defense', 0)
            damage = max(1, int((player_attack * skill.value) - enemy_defense))
            enemy.health -= damage

            # Damage floater
            self.floaters.append({"text": f"-{damage}!", "color": (255, 60, 60),
                                  "x": WINDOW_WIDTH // 1.5 + 80, "y": WINDOW_HEIGHT // 6.25 - 60, "timer": 30})

            self.attack_sound.play()

        elif skill.skill_type == "heal":
            # Heal player
            heal_amount = int(skill.value)
            player.health = min(100, player.health + heal_amount)
            self.floaters.append({"text": f"+{heal_amount} HP", "color": (80, 255, 80),
                                  "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 40, "timer": 30})

            # No damage, just heal (enemy won't attack this turn? depends on design)

        elif skill.skill_type == "status":
            # Damage + status effect
            player_attack = player.get_attack()
            enemy_defense = getattr(enemy, 'defense', 0)
            damage = max(1, int((player_attack * skill.value) - enemy_defense))
            enemy.health -= damage

            self.floaters.append({"text": f"-{damage}!", "color": (255, 60, 60),
                                  "x": WINDOW_WIDTH // 1.5 + 80, "y": WINDOW_HEIGHT // 6.25 - 60, "timer": 30})

            # Apply status effect to enemy
            if skill.effect:
                enemy.set_combat_handler(self)  # Set reference for floaters
                enemy.apply_status_effect(skill.effect, skill.effect_duration)

            self.attack_sound.play()

        # Check for victory
        if enemy.health <= 0:
            player.exp += enemy.exp_on_kill
            enemy.kill()
            return "victory"

        # Enemy turn (will be expanded later with enemy skills)
        return self.do_enemy_turn(player, enemy)

    def do_enemy_turn(self, player, enemy):
        """Handle enemy's turn (basic attack for now)."""

        # Process enemy status effects FIRST (poison/burn damage)
        status_result = enemy.update_status_effects(turn_action=True)

        # Check if status effects killed the enemy
        if enemy.health <= 0:
            player.exp += enemy.exp_on_kill
            enemy.kill()
            return "victory"

        # Enemy attacks
        enemy_attack = enemy.damage
        player_defense = player.get_defense()
        enemy_damage = max(1, enemy_attack - player_defense)
        player.take_damage(enemy_damage)
        self.hurt_sound.play()

        self.floaters.append({"text": f"-{enemy_damage}", "color": (255, 80, 80),
                              "x": WINDOW_WIDTH // 6 + 40, "y": WINDOW_HEIGHT // 3.5 - 40, "timer": 30})

        if player.health <= 0:
            return "game_over"
        return "turn_done"