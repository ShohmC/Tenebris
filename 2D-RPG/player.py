from config import *

class Player(pygame.sprite.Sprite):
    def __init__(self, screen, initial_x_location, initial_y_location):
        super().__init__()

        self.screen = screen
        self.velocity = pygame.math.Vector2(0, 0)

        self.image = pygame.transform.scale(
            pygame.image.load("Player/right1.png").convert_alpha(),
            (TILESIZE - 4, TILESIZE - 4)
        )
        self.rect = self.image.get_rect(topleft=(initial_x_location, initial_y_location))
        self._layer = PLAYER_LAYER

        self.cooldown = 0
        self.cooldown_time = 200

        self.up_counter = 0
        self.left_counter = 0
        self.down_counter = 0
        self.right_counter = 0

        self.health = 100
        self.exp = 0
        self.level = 1
        self.upgrade_points = 0

        self.health_label_font = pygame.font.Font(None, 48)
        self.health_value_font = pygame.font.Font(None, 36)

        self.up_frames = (
            pygame.transform.scale(player_image_up_1, (28, 28)),
            pygame.transform.scale(player_image_up_2, (28, 28))
        )
        self.left_frames = (
            pygame.transform.scale(player_image_left_1, (28, 28)),
            pygame.transform.scale(player_image_left_2, (28, 28))
        )
        self.down_frames = (
            pygame.transform.scale(player_image_down_1, (28, 28)),
            pygame.transform.scale(player_image_down_2, (28, 28))
        )
        self.right_frames = (
            pygame.transform.scale(player_image_right_1, (28, 28)),
            pygame.transform.scale(player_image_right_2, (28, 28))
        )

    def draw_player_health_bar(self, screen):
        screen.blit(self.health_label_font.render("Health", True, BLACK), (50, 50))
        pygame.draw.rect(screen, RED, (175, 55, 150, 25))
        pygame.draw.rect(screen, GREEN, (175, 55, 150 * (self.health / 100), 25))
        screen.blit(self.health_value_font.render(str(self.health), True, BLACK), (230, 56))

    def check_collision(self, tile_collision_group):
        self.rect.move_ip(self.velocity)
        if pygame.sprite.spritecollideany(self, tile_collision_group):
            self.rect.move_ip(-self.velocity.x, -self.velocity.y)

    def animate(self, counter_name, frames):
        counter = (getattr(self, counter_name) + 1) % 20
        setattr(self, counter_name, counter)
        self.image = frames[0] if counter < 10 else frames[1]

    def movement(self, dt):
        keys = pygame.key.get_pressed()
        self.velocity.update(0, 0)
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

    def update(self, tile_collision_group, enemy_collision_group, dt):
        self.movement(dt)
        self.check_collision(tile_collision_group)