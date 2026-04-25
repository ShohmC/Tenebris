from item import Item

health_potion = Item("Health Potion", "health", 50, "Items/Potions/healthpotion.png")
max_potion = Item("Max Potion", "max_health", None, "Items/Potions/maxhealthpotion.png")
poison_item = Item("Poison", "poison", {"damage": 2, "duration": 30000}, "Items/Potions/poisonpotion.png")
antidote = Item("Antidote", "antidote", None, "Items/Potions/antidotepotion.png", consumable=False)
speed_boost_item = Item("Speed Boost", "speed_boost", {"multiplier": 2, "duration": 15000}, "Items/Potions/speedpotion.png")
slow_item = Item("Slow", "slow", {"multiplier": 0.5, "duration": 15000}, "Items/Potions/slowpotion.png")