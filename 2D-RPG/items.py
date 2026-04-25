from item import Item

health_potion = Item("Health Potion", "health", 50)
max_potion = Item("Max Potion", "max_health", None)
poison_item = Item("Poison", "poison", {"damage": 2, "duration": 10000})
antidote = Item("Antidote", "antidote", None)
speed_boost_item = Item("Speed Boost", "speed_boost", {"multiplier": 2, "duration": 5000})
slow_item = Item("Slow", "slow", {"multiplier": 0.5, "duration": 5000})