from config import *

def load_enemy_image(path):
    return pygame.transform.scale(
        pygame.image.load(path).convert_alpha(),
        (28, 28)
    )

class Enemies(pygame.sprite.Sprite):
    def __init__(self, screen, initial_x_location, initial_y_location, initial_image, up_img_1, up_img_2,
        down_img_1, down_img_2, left_img_1, left_img_2, right_img_1, right_img_2, health, damage,exp_on_kill):
        super().__init__()
        self.initiate_battle_sequence = False
        self.screen = screen
        self.initial_x_location = initial_x_location
        self.initial_y_location = initial_y_location
        self.initial_image = initial_image

        self.image = load_enemy_image(initial_image)
        self.up_img_1 = load_enemy_image(up_img_1)
        self.up_img_2 = load_enemy_image(up_img_2)
        self.down_img_1 = load_enemy_image(down_img_1)
        self.down_img_2 = load_enemy_image(down_img_2)
        self.left_img_1 = load_enemy_image(left_img_1)
        self.left_img_2 = load_enemy_image(left_img_2)
        self.right_img_1 = load_enemy_image(right_img_1)
        self.right_img_2 = load_enemy_image(right_img_2)

        self.rect = self.image.get_rect(topleft=(initial_x_location, initial_y_location))
        self._layer = ENEMY_LAYER

        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 2

        self.health = health
        self.damage = damage
        self.exp_on_kill = exp_on_kill

        self.previous_x_location = self.rect.x
        self.previous_y_location = self.rect.y

        self.up_counter = 0
        self.down_counter = 0
        self.left_counter = 0
        self.right_counter = 0

    def _animate_direction(self, counter_name, frame_1, frame_2):
        counter = (getattr(self, counter_name) + 1) % 20
        setattr(self, counter_name, counter)
        self.image = frame_1 if counter < 10 else frame_2

    def animation(self):
        if self.rect.y < self.previous_y_location:
            self._animate_direction("up_counter", self.up_img_1, self.up_img_2)
        elif self.rect.y > self.previous_y_location:
            self._animate_direction("down_counter", self.down_img_1, self.down_img_2)
        elif self.rect.x < self.previous_x_location:
            self._animate_direction("left_counter", self.left_img_1, self.left_img_2)
        elif self.rect.x > self.previous_x_location:
            self._animate_direction("right_counter", self.right_img_1, self.right_img_2)

        self.previous_x_location = self.rect.x
        self.previous_y_location = self.rect.y

    def idle_animation(self):
        pass

    def check_collision(self, tile_collision_group, player_collision_group):
        if pygame.sprite.spritecollideany(self, tile_collision_group):
            self.rect.move_ip(-self.velocity.x, -self.velocity.y)
            self.velocity.update(-1, -1)
        if pygame.sprite.spritecollideany(self, player_collision_group):
            self.initiate_battle_sequence = True

    def update_movement(self, player_rect, tile_collision_group, player_collision_group):
        direction = pygame.math.Vector2(
            player_rect.x - self.rect.x,
            player_rect.y - self.rect.y
        )
        distance = direction.length()

        if distance <= TILESIZE * 8:
            if distance > 0:
                direction.normalize_ip()
                self.velocity = direction * self.speed
                self.check_collision(tile_collision_group, player_collision_group)
            else:
                self.idle_animation()

            self.rect.move_ip(self.velocity)
            self.animation()


class Bat(Enemies):
    def __init__(self, screen, initial_x_location, initial_y_location, health):
        super().__init__(screen, initial_x_location, initial_y_location,"Enemy/Bat/left1.png",
                         "Enemy/Bat/left1.png","Enemy/Bat/left2.png",
                         "Enemy/Bat/right1.png","Enemy/Bat/right2.png",
                         "Enemy/Bat/left1.png","Enemy/Bat/left2.png",
                         "Enemy/Bat/right1.png","Enemy/Bat/right2.png",
                         health,1,35
        )