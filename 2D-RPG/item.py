# item.py — Defines the Item class used for all collectible/usable items.
# Concrete item instances are defined in items.py.
# effect_value is a plain number for simple items (health, max_health, antidote)
# and a dictionary for items with multiple properties (poison, speed_boost, slow).

import pygame
from config import *

class Item:
    def __init__(self, name, item_type, effect_value, image_path = None, consumable = True , miss_modifier=0.0):
        self.name = name
        self.item_type = item_type
        # Plain number for simple items, dictionary for status effects —
        # e.g. {"damage": 2, "duration": 10000} for poison
        self.effect_value = effect_value
        # Store the path instead of loading immediately — convert_alpha()
        # requires pygame.display.set_mode() to have been called first.
        # The image Surface is built on first access via the property below.
        self._image_path = image_path
        self._image = None          # loaded lazily on first use
        self.consumable = consumable
        self.miss_modifier = miss_modifier
    @property
    def image(self):
        """Load and cache the image Surface on first access."""
        if self._image is None and self._image_path is not None:
            self._image = pygame.transform.scale(
                pygame.image.load(self._image_path).convert_alpha(),
                (TILESIZE * 2 - 8, TILESIZE * 2 - 8)
            )
        return self._image

    @image.setter
    def image(self, value):
        """Allow external code to assign self.image directly if needed."""
        self._image = value

    # Status effects write into player.status_timers and player.active_statuses;
    # the actual per-frame effect logic lives in player.status().
    def use(self, player):
        if self.item_type == "weapon":
            player.weapon = self
            return
        current_time = pygame.time.get_ticks()

        if self.item_type == "health":
            player.health = min(100, player.health + self.effect_value)

        elif self.item_type == "max_health":
            player.health = 100

        elif self.item_type == "poison":
            player.active_statuses.add("poison")
            player.status_timers["poison"]["damage"] = self.effect_value["damage"]
            player.status_timers["poison"]["last_tick"] = current_time
            player.status_timers["poison"]["end"] = current_time + self.effect_value["duration"]

        elif self.item_type == "antidote":
            player.active_statuses.discard("poison")

        elif self.item_type == "speed_boost":
            player.active_statuses.add("speed_boost")
            player.status_timers["speed_boost"]["multiplier"] = self.effect_value["multiplier"]
            player.status_timers["speed_boost"]["end"] = current_time + self.effect_value["duration"]

        elif self.item_type == "slow":
            player.active_statuses.add("slow")
            player.status_timers["slow"]["multiplier"] = self.effect_value["multiplier"]
            player.status_timers["slow"]["end"] = current_time + self.effect_value["duration"]