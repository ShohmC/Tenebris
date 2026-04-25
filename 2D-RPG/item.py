# item.py — Defines the Item class used for all collectible/usable items.
# Concrete item instances are defined in items.py.
# effect_value is a plain number for simple items (health, max_health, antidote)
# and a dictionary for items with multiple properties (poison, speed_boost, slow).

import pygame

class Item:
    def __init__(self, name, item_type, effect_value):
        self.name = name
        self.item_type = item_type
        # Plain number for simple items, dictionary for status effects —
        # e.g. {"damage": 2, "duration": 10000} for poison
        self.effect_value = effect_value

    # Status effects write into player.status_timers and player.active_statuses;
    # the actual per-frame effect logic lives in player.status().
    def use(self, player):
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