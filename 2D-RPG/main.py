# main.py — Entry point. The Game class runs the game loop and owns the state machine.
#
# Game states:
#   "playing"   — player/enemy updates run; world is drawn
#   "inventory" — inventory panel overlaid on frozen world
#   "combat"    — circle-wipe transition, then combat menu
#
# Bootstrap order matters: pygame.init() and display.set_mode() must run before
# any image loads, so Game() is created before TilemapHandler().

from combat_handler import CombatHandler
from tilemap_handler import *
from camera import *
from inventory import *

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

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

    # Handles QUIT, I key (toggle inventory), and left-click slot selection
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    if self.game_state == "playing":
                        self.game_state = "inventory"
                    else:
                        self.game_state = "playing"

            if self.game_state == "inventory":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.inventory.select_inventory_slot()

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
    def draw_world(self):
        for tile in tilemap_handler.tile_sprite_group.sprites():
            screen.blit(tile.image, self.camera.apply(tile))
        for player in tilemap_handler.player_sprite_group.sprites():
            screen.blit(player.image, self.camera.apply(player))
            player.draw_player_health_bar(screen)
        for enemy in tilemap_handler.enemy_sprite_group.sprites():
            screen.blit(enemy.image, self.camera.apply(enemy))

    # Dispatches rendering based on game_state.
    # display.flip() swaps the back buffer; clock.tick() caps the frame rate.
    def draw(self):
        screen.fill(RED)
        if self.game_state == "playing":
            self.draw_world()
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