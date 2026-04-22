import math
from config import *


class CombatHandler(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.max_radius = int(math.hypot(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.transition_radius = self.max_radius
        self.transition_speed = 20
        self.transition_active = False
        self.transition_finished = False

        self.button_font = pygame.font.Font(None, 48)

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

        pygame.draw.circle(
            overlay,
            (0, 0, 0, 0),
            center,
            max(0, int(self.transition_radius))
        )

        screen.blit(overlay, (0, 0))

        self.transition_radius -= self.transition_speed

        if self.transition_radius <= 0:
            self.transition_radius = 0
            self.transition_active = False
            self.transition_finished = True

    def draw_combat_menu(self, screen, player, enemy):
        screen.fill((255, 255, 255))
        screen.blit(
            pygame.transform.scale(player, (TILESIZE * 5, TILESIZE * 5)),
            (WINDOW_WIDTH // 6, WINDOW_HEIGHT // 3.5)
        )
        screen.blit(
            pygame.transform.scale(enemy, (TILESIZE * 6, TILESIZE * 6)),
            (WINDOW_WIDTH // 1.5, WINDOW_HEIGHT // 6.25)
        )

        fight_button = pygame.Rect(WINDOW_WIDTH // 3.5, WINDOW_HEIGHT // 1.6, 250, 100)
        items_button = pygame.Rect(WINDOW_WIDTH // 2 + WINDOW_WIDTH // 40, WINDOW_HEIGHT // 1.6,  250, 100)

        pygame.draw.rect(screen, BLACK, fight_button)
        pygame.draw.rect(screen, BLACK, items_button)

        pygame.draw.rect(screen, GREEN, fight_button, 4)
        pygame.draw.rect(screen, BLUE, items_button, 4)

        fight_text = self.button_font.render("Fight", True, (255, 0, 0))
        items_text = self.button_font.render("Items", True, (0, 255, 0))

        fight_text_rect = fight_text.get_rect(center=fight_button.center)
        items_text_rect = items_text.get_rect(center=items_button.center)

        screen.blit(fight_text, fight_text_rect)
        screen.blit(items_text, items_text_rect)