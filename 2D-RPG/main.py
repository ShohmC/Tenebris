# =============================================================================
# main.py — Entry Point & Game Loop
# =============================================================================
# Game states:
#   "title"     — title screen with Play / Options
#   "play_menu" — New Game / Load Game selection
#   "playing"   — world runs; player, enemies, NPCs, and items update
#   "paused"    — pause overlay; world is frozen
#   "inventory" — inventory panel overlaid; world is frozen
#   "combat"    — circle-wipe transition, then turn-based combat menu
#   "dialogue"  — NPC dialogue box shown; world is frozen
#
# State transitions:
#   title → play_menu   : click Play
#   play_menu → playing  : click New Game (creates tutorial map)
#   play_menu → title    : click Back
#   playing → paused     : ESC key
#   paused → playing     : click Resume / ESC key
#   playing → combat     : enemy.initiate_battle_sequence fires
#   playing → dialogue   : E key near NPC
#   dialogue → playing   : E key on last dialogue line
#   combat  → playing    : victory (enemy.kill()) clears the enemy
#   combat  → inventory  : player clicks Items button
#   inventory → *        : Back button or I restores previous_state
#   playing → inventory  : I key
#
# Bootstrap order: pygame.init() + display.set_mode() must run before any
# image load, so Game() is created before TilemapHandler().
# =============================================================================
import pickle
import math

from combat_handler  import CombatHandler
from tilemap_handler import *   # also pulls in NPC, WorldItem, items via handler
from camera          import *
from inventory       import *
from save_manager    import SaveManager

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SCALED)
# ----- BACKGROUND MUSIC -----
pygame.mixer.music.load("Music/Theme.mp3")   
pygame.mixer.music.set_volume(0.5)                      
pygame.mixer.music.play(-1)     

class Game:
    def __init__(self):
        self.clock        = pygame.time.Clock()
        self.dt           = self.clock.tick(FPS) / 100
        self.running      = True
        self.camera       = Camera()
        self.inventory    = Inventory()
        self.combat       = CombatHandler()
        self.game_state   = "title"   # Start on the title screen
        self.world_loaded = False     # True after New Game / Load Game creates the map
        # previous_state lets inventory return to either "playing" or "combat"
        self.previous_state      = None
        # current_enemy is set when combat begins; cleared on victory
        self.current_enemy       = None
        self.current_enemy_image = None
        self.save_manager = SaveManager(".save", "SaveData")

        # NPC dialogue tracking
        self.active_npc = None  # The NPC currently being talked to

        # Map name label — shown briefly after map transitions
        self.map_label_timer = 180  # frames to show (3 sec at 60 FPS); starts on first map
        self._map_label_font = pygame.font.Font(None, 32)

        # XP popup — shown briefly after winning combat
        self.xp_popup_timer = 0
        self.xp_popup_text  = ""
        self._xp_popup_font = pygame.font.Font(None, 36)

        # ----- Menu fonts and buttons -----
        self._title_font    = pygame.font.Font(None, 80)
        self._subtitle_font = pygame.font.Font(None, 36)
        self._menu_font     = pygame.font.Font(None, 52)
        self._small_font    = pygame.font.Font(None, 32)

        # Title screen buttons (built once in draw, hit-tested in events)
        self.title_play_btn    = None
        self.title_options_btn = None
        self.title_exit_btn    = None

        # Play-menu buttons
        self.pm_new_btn  = None
        self.pm_load_btn = None
        self.pm_back_btn = None

        # Pause menu buttons
        self.pause_resume_btn  = None
        self.pause_options_btn = None
        self.pause_save_btn    = None
        self.pause_exit_btn    = None

        # Slot selection buttons (shared by save_select and load_select)
        self.slot_btns = [None, None, None]  # 3 slots
        self.slot_back_btn = None
        self.save_slots = ["slot1", "slot2", "slot3"]

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # ========== TITLE SCREEN ==========
            if self.game_state == "title":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mp = pygame.mouse.get_pos()
                    if self.title_play_btn and self.title_play_btn.collidepoint(mp):
                        self.game_state = "play_menu"
                    elif self.title_options_btn and self.title_options_btn.collidepoint(mp):
                        pass  # Placeholder
                    elif self.title_exit_btn and self.title_exit_btn.collidepoint(mp):
                        self.running = False
                continue

            # ========== PLAY MENU ==========
            if self.game_state == "play_menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mp = pygame.mouse.get_pos()
                    if self.pm_new_btn and self.pm_new_btn.collidepoint(mp):
                        tilemap_handler.create_tutorial_map()
                        self.world_loaded = True
                        self.map_label_timer = 180
                        self.game_state = "playing"
                        pygame.mixer.music.set_volume(0.2)
                    elif self.pm_load_btn and self.pm_load_btn.collidepoint(mp):
                        self.game_state = "load_select"
                    elif self.pm_back_btn and self.pm_back_btn.collidepoint(mp):
                        self.game_state = "title"
                continue

            # ========== LOAD SLOT SELECT ==========
            if self.game_state == "load_select":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mp = pygame.mouse.get_pos()
                    for i, btn in enumerate(self.slot_btns):
                        if btn and btn.collidepoint(mp):
                            if not self.world_loaded:
                                tilemap_handler.create_tutorial_map()
                                self.world_loaded = True
                            self.load_save_data(self.save_slots[i])
                            self.map_label_timer = 180
                            self.game_state = "playing"
                            pygame.mixer.music.set_volume(0.2)
                            break
                    if self.slot_back_btn and self.slot_back_btn.collidepoint(mp):
                        self.game_state = "play_menu"
                continue

            # ========== SAVE SLOT SELECT ==========
            if self.game_state == "save_select":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mp = pygame.mouse.get_pos()
                    for i, btn in enumerate(self.slot_btns):
                        if btn and btn.collidepoint(mp):
                            self.save_manager.save_data(self.get_save_data(), self.save_slots[i])
                            self.game_state = "paused"
                            break
                    if self.slot_back_btn and self.slot_back_btn.collidepoint(mp):
                        self.game_state = "paused"
                continue

            # ========== PAUSE MENU ==========
            if self.game_state == "paused":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game_state = "playing"
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mp = pygame.mouse.get_pos()
                    if self.pause_resume_btn and self.pause_resume_btn.collidepoint(mp):
                        self.game_state = "playing"
                    elif self.pause_options_btn and self.pause_options_btn.collidepoint(mp):
                        pass  # Placeholder
                    elif self.pause_save_btn and self.pause_save_btn.collidepoint(mp):
                        self.game_state = "save_select"
                    elif self.pause_exit_btn and self.pause_exit_btn.collidepoint(mp):
                        self.game_state = "title"
                continue

            # ========== IN-GAME STATES ==========
            if event.type == pygame.KEYDOWN:

                # --- ESC: open pause menu from playing ---
                if event.key == pygame.K_ESCAPE and self.game_state == "playing":
                    self.game_state = "paused"
                    continue

                # --- Dialogue state: E advances / closes dialogue ---
                if self.game_state == "dialogue":
                    if event.key == pygame.K_e:
                        if self.active_npc:
                            still_talking = self.active_npc.advance_dialogue()
                            if not still_talking:
                                self.active_npc = None
                                self.game_state = "playing"
                    continue  # Block all other keys during dialogue

                # --- Inventory toggle ---
                # I opens inventory from playing or combat;
                # pressing I again restores the previous state.
                if event.key == pygame.K_i:
                    if self.game_state == "playing":
                        self.previous_state = self.game_state
                        self.game_state = "inventory"
                    elif self.game_state == "combat":
                        self.previous_state = self.game_state
                        self.game_state = "inventory"
                    elif self.game_state == "inventory":
                        self.game_state = (self.previous_state
                                           if self.previous_state is not None
                                           else "playing")

                # --- E key: interact with nearby NPC ---
                if event.key == pygame.K_e and self.game_state == "playing":
                    for npc in tilemap_handler.npc_sprite_group.sprites():
                        if npc.is_near_player(tilemap_handler.player_character):
                            npc.open_dialogue()
                            self.active_npc = npc
                            self.game_state = "dialogue"
                            break

                # --- F key: activate map transition ---
                if event.key == pygame.K_f and self.game_state == "playing":
                    for t_tile in tilemap_handler.transition_sprite_group.sprites():
                        if t_tile.is_player_on_tile(tilemap_handler.player_character.rect):
                            tilemap_handler.transition_to_map(
                                t_tile.target_map, t_tile.dest_x, t_tile.dest_y
                            )
                            self.map_label_timer = 180
                            break

                # --- Save / Load ---
                if event.key == pygame.K_F5:
                    self.save_manager.save_data(self.get_save_data(), "slot1")
                if event.key == pygame.K_F9:
                    self.load_save_data()

            # --- Inventory: slot clicks and Back button ---
            if self.game_state == "inventory":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self.inventory.select_inventory_slot(
                        tilemap_handler.player_character
                    )
                    if result == "close":
                        self.game_state = (self.previous_state
                                           if self.previous_state is not None
                                           else "playing")
                        self.previous_state = None

            # --- Combat: button clicks (only active after transition finishes) ---
            if self.game_state == "combat" and self.combat.transition_finished:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self.combat.handle_click(
                        pygame.mouse.get_pos(),
                        tilemap_handler.player_character,
                        self.current_enemy,
                        self.inventory,
                    )
                    if result == "victory":
                        # Enemy is already killed inside handle_click (enemy.kill())
                        xp_gained = self.current_enemy.exp_on_kill if self.current_enemy else 0
                        tilemap_handler.player_character.gain_exp(xp_gained)
                        self.xp_popup_text = f"+{xp_gained} XP"
                        self.xp_popup_timer = 120  # 2 seconds at 60 FPS
                        self.game_state = "playing"
                        self.combat.transition_finished = False
                        self.combat.floaters.clear()
                        self.current_enemy = None
                    elif result == "game_over":
                        print("Game Over")
                        self.running = False
                    elif result == "run":
                        self.current_enemy.reset_to_spawn()
                        self.game_state = "playing"
                        self.combat.transition_finished = False
                        self.combat.floaters.clear()
                        self.current_enemy = None
                    elif result == "open_inventory":
                        self.previous_state = "combat"
                        self.game_state = "inventory"

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    def update(self):
        if self.game_state == "playing":
            tilemap_handler.player_sprite_group.update(
                tilemap_handler.collision_tile_sprite_group,
                tilemap_handler.collision_enemy_sprite_group,
                self.dt,
            )

            self.camera.update(tilemap_handler.player_sprite_group)

            # Chests — inactive until chest_sprite_group is populated with
            # Chest objects (see TODO in tilemap_handler.create_tutorial_map)
            for chest in tilemap_handler.chest_sprite_group.sprites():
                chest.on_chest_open(tilemap_handler.player_character)

            # Enemy AI + combat trigger
            for enemy in tilemap_handler.enemy_sprite_group.sprites():
                enemy.update_movement(
                    tilemap_handler.player_character.rect,
                    tilemap_handler.collision_tile_sprite_group,
                    tilemap_handler.player_sprite_group,
                )
                if enemy.initiate_battle_sequence:
                    self.current_enemy       = enemy
                    self.current_enemy_image = pygame.image.load(enemy.initial_image)
                    self.game_state          = "combat"
                    self.combat.start_transition()

            # NPC per-frame update (reserved for patrol / idle animation)
            for npc in tilemap_handler.npc_sprite_group.sprites():
                npc.update()

            # WorldItem pickup — walk-over collection
            for world_item in tilemap_handler.item_sprite_group.sprites():
                world_item.check_pickup(tilemap_handler.player_character)

        elif self.game_state == "inventory":
            self.inventory.update_menu()

        elif self.game_state == "combat":
            if self.combat.transition_finished:
                pass   # Turn logic is driven by mouse clicks in events()

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def draw_world(self):
        """
        Renders the game world in layer order (back → front):
          1. All tiles (grass, dirt, trees, chests)
          2. World items (glowing pickups + name labels)
          3. Player sprite + HUD (health bar, status icons) — screen-space
          4. Enemies
          5. NPC sprites + [E] interact prompts
          6. Transition tile prompts
        """
        # 1 — Tiles
        for tile in tilemap_handler.tile_sprite_group.sprites():
            screen.blit(tile.image, self.camera.apply(tile))

        # 2 — World items (below player so player renders on top)
        for world_item in tilemap_handler.item_sprite_group.sprites():
            screen.blit(world_item.image, self.camera.apply(world_item))
            world_item.draw_label(screen, self.camera)

        # 3 — Player + HUD
        for player in tilemap_handler.player_sprite_group.sprites():
            screen.blit(player.image, self.camera.apply(player))
            player.draw_player_health_bar(screen)
            player.draw_player_status_effects(screen)

        # 4 — Enemies
        for enemy in tilemap_handler.enemy_sprite_group.sprites():
            screen.blit(enemy.image, self.camera.apply(enemy))

        # 5 — NPCs + interact prompts
        for npc in tilemap_handler.npc_sprite_group.sprites():
            screen.blit(npc.image, self.camera.apply(npc))
            npc.draw_interact_prompt(screen, tilemap_handler.player_character, self.camera)

        # 6 — Transition tile prompts (shown when player stands on one)
        for t_tile in tilemap_handler.transition_sprite_group.sprites():
            if t_tile.is_player_on_tile(tilemap_handler.player_character.rect):
                t_tile.draw_prompt(screen, self.camera.offset)

        # 7 — Map name label (top-right, fades after a few seconds)
        if self.map_label_timer > 0:
            map_name = tilemap_handler.current_map.replace('_', ' ').title()
            label = self._map_label_font.render(map_name, True, (255, 220, 80))
            screen.blit(label, (WINDOW_WIDTH - label.get_width() - 12, 12))
            self.map_label_timer -= 1

        # 8 — XP popup (gold text, center-top, after combat victory)
        if self.xp_popup_timer > 0:
            xp_surf = self._xp_popup_font.render(self.xp_popup_text, True, (255, 215, 0))
            screen.blit(xp_surf, (WINDOW_WIDTH // 2 - xp_surf.get_width() // 2, 120))
            self.xp_popup_timer -= 1

    def draw_dialogue_overlays(self):
        """
        Renders open NPC dialogue boxes on top of everything else.
        Must be called after draw_world() so panels composite above world sprites.
        """
        for npc in tilemap_handler.npc_sprite_group.sprites():
            npc.draw_dialogue(screen)

    # -------------------------------------------------------------------------
    # Menu Drawing Helpers
    # -------------------------------------------------------------------------

    def _draw_menu_button(self, text, rect, border_color=(255, 220, 80), small=False):
        """Draw a styled menu button and return its Rect for hit-testing."""
        pygame.draw.rect(screen, (30, 30, 50), rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, 3, border_radius=8)
        font = self._small_font if small else self._menu_font
        label = font.render(text, True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=rect.center))
        return rect

    def draw_title_screen(self):
        """Title screen: game name + Play / Options buttons."""
        screen.fill((15, 10, 30))

        # Title
        title_surf = self._title_font.render("Tenebris", True, (255, 220, 80))
        screen.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 180))

        sub_surf = self._subtitle_font.render("A 2D RPG Adventure", True, (180, 180, 200))
        screen.blit(sub_surf, (WINDOW_WIDTH // 2 - sub_surf.get_width() // 2, 260))

        # Buttons
        btn_w, btn_h = 260, 60
        cx = WINDOW_WIDTH // 2 - btn_w // 2
        self.title_play_btn    = self._draw_menu_button("Play",    pygame.Rect(cx, 380, btn_w, btn_h))
        self.title_options_btn = self._draw_menu_button("Options", pygame.Rect(cx, 470, btn_w, btn_h), (120, 120, 140))
        self.title_exit_btn    = self._draw_menu_button("Exit",    pygame.Rect(cx, 560, btn_w, btn_h), (200, 60, 60))

    def draw_play_menu(self):
        """Play sub-menu: New Game / Load Game / Back."""
        screen.fill((15, 10, 30))

        header = self._title_font.render("Select Mode", True, (255, 220, 80))
        screen.blit(header, (WINDOW_WIDTH // 2 - header.get_width() // 2, 180))

        btn_w, btn_h = 280, 60
        cx = WINDOW_WIDTH // 2 - btn_w // 2
        self.pm_new_btn  = self._draw_menu_button("New Game",  pygame.Rect(cx, 340, btn_w, btn_h))
        self.pm_load_btn = self._draw_menu_button("Load Game", pygame.Rect(cx, 430, btn_w, btn_h))
        self.pm_back_btn = self._draw_menu_button("Back",      pygame.Rect(cx, 520, btn_w, btn_h), (120, 120, 140))


    def draw_pause_menu(self):
        """Pause overlay drawn on top of the frozen world."""
        # Draw world underneath (frozen)
        self.draw_world()

        # Semi-transparent dark overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        header = self._title_font.render("Paused", True, (255, 220, 80))
        screen.blit(header, (WINDOW_WIDTH // 2 - header.get_width() // 2, 160))

        btn_w, btn_h = 260, 55
        cx = WINDOW_WIDTH // 2 - btn_w // 2
        self.pause_resume_btn  = self._draw_menu_button("Resume",  pygame.Rect(cx, 300, btn_w, btn_h))
        self.pause_options_btn = self._draw_menu_button("Options", pygame.Rect(cx, 380, btn_w, btn_h), (120, 120, 140))
        self.pause_save_btn    = self._draw_menu_button("Save",    pygame.Rect(cx, 460, btn_w, btn_h))
        self.pause_exit_btn    = self._draw_menu_button("Exit",    pygame.Rect(cx, 540, btn_w, btn_h), (200, 60, 60))

    def _get_slot_info(self, slot_name):
        """Return a short description string for a save slot."""
        try:
            data = self.save_manager.load_data(slot_name)
            from player import Player
            exp = data.get('exp', 0)
            level = 1
            while exp >= Player.total_xp_for_level(level + 1):
                level += 1
            map_name = data.get("map", "unknown").replace('_', ' ').title()
            return f"Lv.{level}  HP:{data.get('health', '?')}  {map_name}"
        except Exception:
            return "— Empty —"

    def draw_slot_select(self, title_text):
        """Shared slot selection screen for Save and Load."""
        # If saving, show world underneath with overlay
        if self.game_state == "save_select":
            self.draw_world()
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((15, 10, 30))

        header = self._title_font.render(title_text, True, (255, 220, 80))
        screen.blit(header, (WINDOW_WIDTH // 2 - header.get_width() // 2, 140))

        btn_w, btn_h = 340, 65
        cx = WINDOW_WIDTH // 2 - btn_w // 2
        for i in range(3):
            info = self._get_slot_info(self.save_slots[i])
            label = f"Slot {i + 1}:  {info}"
            self.slot_btns[i] = self._draw_menu_button(label, pygame.Rect(cx, 260 + i * 90, btn_w, btn_h), small=True)

        self.slot_back_btn = self._draw_menu_button("Back", pygame.Rect(cx, 260 + 3 * 90, btn_w, btn_h), (120, 120, 140))

    def draw(self):
        screen.fill(RED)

        if self.game_state == "title":
            self.draw_title_screen()

        elif self.game_state == "play_menu":
            self.draw_play_menu()

        elif self.game_state == "load_select":
            self.draw_slot_select("Load Game")

        elif self.game_state == "save_select":
            self.draw_slot_select("Save Game")

        elif self.game_state == "paused":
            self.draw_pause_menu()

        elif self.game_state == "playing":
            self.draw_world()
            self.draw_dialogue_overlays()

        elif self.game_state == "dialogue":
            self.draw_world()
            if self.active_npc:
                self.active_npc.draw_dialogue(screen)

        elif self.game_state == "inventory":
            self.draw_world()
            self.draw_dialogue_overlays()
            self.inventory.draw_inventory_menu(screen)

        elif self.game_state == "combat":
            if not self.combat.transition_finished:
                # Circle-wipe animation still playing — show world underneath
                self.draw_world()
                self.combat.draw_transition(screen)
            else:
                # Transition done — show the full combat menu
                self.combat.draw_combat_menu(
                    screen,
                    tilemap_handler.player_character,
                    self.current_enemy,
                )
        # Low health red blink effect
        if hasattr(tilemap_handler, 'player_character') and tilemap_handler.player_character is not None:
            player = tilemap_handler.player_character
            if 0 < player.health <= LOW_HEALTH_THRESHOLD:
                t = pygame.time.get_ticks() * 0.006   # speed of pulse
                alpha = int(75 + 75 * math.sin(t))    
                if alpha > 0:
                    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((255, 0, 0, alpha))
                    screen.blit(overlay, (0, 0))
                

        pygame.display.flip()
        self.clock.tick(FPS)

    # -------------------------------------------------------------------------
    # Save / Load
    # -------------------------------------------------------------------------

    def get_save_data(self):
        return {
            "health": tilemap_handler.player_character.health,
            "exp":    tilemap_handler.player_character.exp,
            "x":      tilemap_handler.player_character.rect.x,
            "y":      tilemap_handler.player_character.rect.y,
            "map":    tilemap_handler.current_map,
        }

    def load_save_data(self, slot_name="slot1"):
        try:
            data = self.save_manager.load_data(slot_name)
            # Restore map if saved (backwards compatible with old saves)
            saved_map = data.get("map", tilemap_handler.current_map)
            if saved_map and saved_map != tilemap_handler.current_map:
                tilemap_handler.transition_to_map(saved_map, data["x"], data["y"])
            tilemap_handler.player_character.health = data["health"]
            tilemap_handler.player_character.exp    = data["exp"]
            level = 1
            while data["exp"] >= tilemap_handler.player_character.total_xp_for_level(level + 1):
                level += 1
            tilemap_handler.player_character.level = level
            tilemap_handler.player_character.rect.x = data["x"]
            tilemap_handler.player_character.rect.y = data["y"]
        except (pickle.UnpicklingError, EOFError, AttributeError, ImportError) as e:
            print(f"Failed to load corrupted or incompatible pickle file: {e}")
        except FileNotFoundError:
            print("No save file found")

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    def main(self):
        # Map creation is now deferred to New Game / Load Game button click.
        while self.running:
            self.events()
            self.update()
            self.draw()


# --- Bootstrap ---
g = Game()
tilemap_handler = TilemapHandler(screen)
g.main()
pygame.quit()
