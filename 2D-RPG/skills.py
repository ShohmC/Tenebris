# =============================================================================
# skills.py — Skill System for Turn-Based Combat
# =============================================================================
# Manages player skills, costs, effects, and unlocking.
#
# Skill types:
#   - damage    : Direct damage with multiplier
#   - heal      : Restore health
#   - status    : Apply status effect to enemy
#   - buff      : Apply buff to player
# =============================================================================

from config import *


class Skill:
    """Base class for all skills."""

    def __init__(self, skill_id, name, description, cost, skill_type,
                 value=0, effect=None, effect_duration=0, unlocked_at_level=1):
        """
        Parameters:
        -----------
        skill_id : str — Unique identifier (e.g., "slash")
        name : str — Display name
        description : str — Tooltip description
        cost : int — Energy cost to use
        skill_type : str — "damage", "heal", "status", "buff"
        value : float — Damage multiplier or heal amount
        effect : str — For status/buff skills (e.g., "poison", "energy_boost")
        effect_duration : int — Turns the effect lasts
        unlocked_at_level : int — Minimum player level to unlock
        """
        self.id = skill_id
        self.name = name
        self.description = description
        self.cost = cost
        self.skill_type = skill_type
        self.value = value
        self.effect = effect
        self.effect_duration = effect_duration
        self.unlocked_at_level = unlocked_at_level
        self.unlocked = False  # Will be set based on player level

    def is_available(self, player_level):
        """Check if skill is unlocked at this level."""
        return player_level >= self.unlocked_at_level


# =============================================================================
# Starting Skills (Level 1)
# =============================================================================

STARTING_SKILLS = [
    Skill("slash", "Slash", "A quick slash dealing 1.5x damage",
          cost=15, skill_type="damage", value=1.5, unlocked_at_level=1),

    Skill("heavy_strike", "Heavy Strike", "A powerful blow dealing 2.2x damage",
          cost=30, skill_type="damage", value=2.2, unlocked_at_level=1),

    Skill("poison_strike", "Poison Strike", "Deals 1.2x damage and poisons enemy",
          cost=25, skill_type="status", value=1.2, effect="poison", effect_duration=3, unlocked_at_level=1),

    Skill("quick_slash", "Quick Slash", "Low damage but builds energy",
          cost=10, skill_type="damage", value=0.8, unlocked_at_level=1),
]

# =============================================================================
# Unlockable Skills (Higher Levels)
# =============================================================================

ADVANCED_SKILLS = [
    Skill("healing_light", "Healing Light", "Restores 40 HP",
          cost=25, skill_type="heal", value=40, unlocked_at_level=3),

    Skill("energy_boost", "Energy Boost", "Grants 30 bonus energy",
          cost=15, skill_type="buff", value=30, effect="energy_boost", effect_duration=1, unlocked_at_level=3),

    Skill("cleave", "Cleave", "Deals 1.8x damage to all enemies",
          cost=35, skill_type="damage", value=1.8, unlocked_at_level=5),

    Skill("focus", "Focus", "Next skill deals 2x damage",
          cost=20, skill_type="buff", value=2.0, effect="next_skill_boost", effect_duration=1, unlocked_at_level=4),

    Skill("life_steal", "Life Steal", "Deals 1.5x damage and heals for 50% of damage",
          cost=35, skill_type="damage", value=1.5, effect="life_steal", unlocked_at_level=6),
]


def get_available_skills(player_level):
    """Return list of skills available at given player level."""
    all_skills = STARTING_SKILLS + ADVANCED_SKILLS
    return [skill for skill in all_skills if skill.is_available(player_level)]


def get_skill_by_id(skill_id):
    """Retrieve a skill by its ID."""
    all_skills = STARTING_SKILLS + ADVANCED_SKILLS
    for skill in all_skills:
        if skill.id == skill_id:
            return skill
    return None