# =============================================================================
# main.py — Entry Point & Game Loop
# =============================================================================
# Game states:
#   "playing"   — world runs; player, enemies, NPCs, and items update
#   "inventory" — inventory panel overlaid; world is frozen
#   "combat"    — circle-wipe transition, then turn-based combat menu
#   "dialogue"  — NPC dialogue box shown; world is frozen
#
# State transitions:
#   playing → combat    : enemy.initiate_battle_sequence fires
#   playing → dialogue  : E key near NPC
#   dialogue → playing  : E key on last dialogue line
#   combat  → playing   : victory (enemy.kill()) clears the enemy
#   combat  → inventory : player clicks Items button
#   inventory → *       : Back button or I restores previous_state
#   playing → inventory : I key
#
# Bootstrap order: pygame.init() + display.set_mode() must run before any
# image load, so Game() is created before TilemapHandler().
# =============================================================================
import pickle

from combat_handler  import CombatHandler
from tilemap_handler import *   # also pulls in NPC, WorldItem, items via handler
from camera          import *
from inventory       import *
from save_manager    import SaveManager

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SCALED)


class Game:
    def __init__(self):
        self.clock        = pygame.time.Clock()
        self.dt           = self.clock.tick(FPS) / 100
        self.running      = True
        self.camera       = Camera()
        self.inventory    = Inventory()
        self.combat       = CombatHandler()
        self.game_state   = "playing"
        # previous_state lets inventory return to either "playing" or "combat"
        self.previous_state      = None
        # current_enemy is set when combat begins; cleared on victory
        self.current_enemy       = None
        self.current_enemy_image = None
        self.save_manager = SaveManager(".save", "SaveData")

        # NPC dialogue tracking
        self.active_npc = None  # The NPC currently being talked to

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:

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
                        self.game_state = "playing"
                        self.combat.transition_finished = False
                        self.current_enemy = None
                    elif result == "game_over":
                        print("Game Over")
                        self.running = False
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

    def draw_dialogue_overlays(self):
        """
        Renders open NPC dialogue boxes on top of everything else.
        Must be called after draw_world() so panels composite above world sprites.
        """
        for npc in tilemap_handler.npc_sprite_group.sprites():
            npc.draw_dialogue(screen)

    def draw(self):
        screen.fill(RED)

        if self.game_state == "playing":
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

    def load_save_data(self):
        try:
            data = self.save_manager.load_data("slot1")
            # Restore map if saved (backwards compatible with old saves)
            saved_map = data.get("map", tilemap_handler.current_map)
            if saved_map and saved_map != tilemap_handler.current_map:
                tilemap_handler.transition_to_map(saved_map, data["x"], data["y"])
            tilemap_handler.player_character.health = data["health"]
            tilemap_handler.player_character.exp    = data["exp"]
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
        # Start on the tutorial map.
        # To switch maps, replace this with:
        #   tilemap_handler.create_test_tilemap()      — original combat test map
        #   tilemap_handler.create_tutorial_tilemap()  — old diamond-path layout
        tilemap_handler.create_tutorial_map()

        while self.running:
            self.events()
            self.update()
            self.draw()


# --- Bootstrap ---
g = Game()
tilemap_handler = TilemapHandler(screen)
g.main()
pygame.quit()
