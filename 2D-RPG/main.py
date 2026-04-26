# main.py — Entry point. The Game class runs the game loop and owns the state machine.
#
# Game states:
#   "playing"   — player/enemy updates run; world is drawn
#   "inventory" — inventory panel overlaid on frozen world
#   "combat"    — circle-wipe transition, then combat menu
#   "dialogue"  — NPC dialogue box shown; world is frozen
#
# Bootstrap order matters: pygame.init() and display.set_mode() must run before
# any image loads, so Game() is created before TilemapHandler().
import pickle

from combat_handler import CombatHandler
from tilemap_handler import *
from tiles import TransitionTile
from camera import *
from inventory import *
from save_manager import SaveManager

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SCALED)

class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        # dt scales player velocity so speed is frame-rate independent
        self.dt = self.clock.tick(FPS) / 100
        self.running = True
        self.current_enemy_image = None
        self.camera = Camera()
        self.inventory = Inventory()
        self.combat = CombatHandler()
        self.game_state = "playing"
        self.save_manager = SaveManager(".save", "SaveData")

        # NPC dialogue tracking
        self.active_npc = None  # The NPC currently being talked to

    # Handles QUIT, I key (toggle inventory), E key (NPC interact),
    # F key (map transition), and left-click slot selection
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                # --- Dialogue state: E advances / closes dialogue ---
                if self.game_state == "dialogue":
                    if event.key == pygame.K_e:
                        if self.active_npc:
                            still_talking = self.active_npc.interact()
                            if not still_talking:
                                self.active_npc = None
                                self.game_state = "playing"
                    continue  # Block all other keys during dialogue

                if event.key == pygame.K_i:
                    if self.game_state == "playing":
                        self.game_state = "inventory"
                    elif self.game_state == "inventory":
                        self.game_state = "playing"

                # --- E key: interact with nearby NPC ---
                if event.key == pygame.K_e and self.game_state == "playing":
                    for npc in tilemap_handler.npc_sprite_group.sprites():
                        if npc.is_player_in_range(tilemap_handler.player_character.rect):
                            npc.interact()
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

                if event.key == pygame.K_F5:
                    self.save_manager.save_data(self.get_save_data(), "slot1")

                if event.key == pygame.K_F9:
                    self.load_save_data()

            if self.game_state == "inventory":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.inventory.select_inventory_slot(tilemap_handler.player_character)

    # Advances logic for the active state only; inactive states are frozen.
    # "playing": moves player/camera/enemies, checks for combat trigger.
    # "combat": currently a stub after the transition finishes (TODO: combat logic).
    def update(self):
        if self.game_state == "playing":
            tilemap_handler.player_sprite_group.update(
                tilemap_handler.collision_tile_sprite_group,
                tilemap_handler.collision_enemy_sprite_group, self.dt
            )

            self.camera.update(tilemap_handler.player_sprite_group)

            for chest in tilemap_handler.chest_sprite_group.sprites():
                chest.on_chest_open(tilemap_handler.player_character)

            for enemy in tilemap_handler.enemy_sprite_group.sprites():
                enemy.update_movement(
                    tilemap_handler.player_character.rect,
                    tilemap_handler.collision_tile_sprite_group,
                    tilemap_handler.player_sprite_group
                )

                if enemy.initiate_battle_sequence:
                    self.game_state = "combat"
                    self.current_enemy_image = pygame.image.load(enemy.initial_image)
                    self.combat.start_transition()

            for npc in tilemap_handler.npc_sprite_group.sprites():
                npc.update()

        elif self.game_state == "inventory":
            self.inventory.update_menu()

        elif self.game_state == "combat":
            if self.combat.transition_finished:
                pass

    # Draws tiles/player/enemies using camera-offset positions.
    # Health bar is drawn in screen space (no camera offset).
    # Also draws NPC interact prompts and transition prompts.
    def draw_world(self):
        for tile in tilemap_handler.tile_sprite_group.sprites():
            screen.blit(tile.image, self.camera.apply(tile))
        for player in tilemap_handler.player_sprite_group.sprites():
            screen.blit(player.image, self.camera.apply(player))
            player.draw_player_health_bar(screen)
            player.draw_player_status_effects(screen)
        for enemy in tilemap_handler.enemy_sprite_group.sprites():
            screen.blit(enemy.image, self.camera.apply(enemy))

        # NPC interaction prompts (shown when player is nearby)
        for npc in tilemap_handler.npc_sprite_group.sprites():
            if npc.is_player_in_range(tilemap_handler.player_character.rect):
                npc.draw_interact_prompt(screen, self.camera.offset)

        # Transition tile prompts (shown when player stands on one)
        for t_tile in tilemap_handler.transition_sprite_group.sprites():
            if t_tile.is_player_on_tile(tilemap_handler.player_character.rect):
                t_tile.draw_prompt(screen, self.camera.offset)

    # Dispatches rendering based on game_state.
    # display.flip() swaps the back buffer; clock.tick() caps the frame rate.
    def draw(self):
        screen.fill(RED)
        if self.game_state == "playing":
            self.draw_world()
        elif self.game_state == "dialogue":
            self.draw_world()
            if self.active_npc:
                self.active_npc.draw_dialogue_box(screen)
        elif self.game_state == "inventory":
            self.draw_world()
            self.inventory.draw_inventory_menu(screen)
        elif self.game_state == "combat":
            if not self.combat.transition_finished:
                self.draw_world()
                self.combat.draw_transition(screen)
            else: # Waits for the transition to finish THEN blits the menu
                self.combat.draw_combat_menu(screen, player_image_right_1, self.current_enemy_image)

        pygame.display.flip()
        self.clock.tick(FPS)

    # Collects current player state into a dictionary for serialization.
    # Called by events() on F5 and can be reused for autosave or save-on-quit.
    def get_save_data(self):
        return {
            "health": tilemap_handler.player_character.health,
            "exp": tilemap_handler.player_character.exp,
            "x": tilemap_handler.player_character.rect.x,
            "y": tilemap_handler.player_character.rect.y,
            "map": tilemap_handler.current_map,
        }

    # Loads save file and restores player state from the stored dictionary.
    # Handles missing files and corrupted/incompatible pickle data gracefully.
    def load_save_data(self):
        try:
            data = self.save_manager.load_data("slot1")
            # Restore map if saved (backwards compatible with old saves)
            saved_map = data.get("map", tilemap_handler.current_map)
            if saved_map and saved_map != tilemap_handler.current_map:
                tilemap_handler.transition_to_map(saved_map, data["x"], data["y"])
            tilemap_handler.player_character.health = data["health"]
            tilemap_handler.player_character.exp = data["exp"]
            tilemap_handler.player_character.rect.x = data["x"]
            tilemap_handler.player_character.rect.y = data["y"]
        except (pickle.UnpicklingError, EOFError, AttributeError, ImportError) as e:
            print(f"Failed to load corrupted or incompatible pickle file: {e}")
        except FileNotFoundError:
            print("No save file found")

    def main(self):
        tilemap_handler.create_test_tilemap()
        while self.running:
            self.events()
            self.update()
            self.draw()


g = Game()
tilemap_handler = TilemapHandler(screen)
g.main()
pygame.quit()