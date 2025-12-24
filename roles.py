"""Role definitions for the Town of Salem clone."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    name: str
    alignment: str
    goal: str


TOWN_ROLES = (
    Role(name="Sheriff", alignment="Town", goal="Identify threats to the town."),
    Role(name="Doctor", alignment="Town", goal="Protect townsfolk from attacks."),
    Role(name="Investigator", alignment="Town", goal="Gather clues about suspects."),
)

MAFIA_ROLES = (
    Role(name="Godfather", alignment="Mafia", goal="Eliminate the town."),
    Role(name="Consigliere", alignment="Mafia", goal="Gather intel for the mafia."),
)

NEUTRAL_ROLES = (
    Role(name="Jester", alignment="Neutral", goal="Get executed by the town."),
    Role(name="Executioner", alignment="Neutral", goal="Have your target lynched."),
)

ALL_ROLES = TOWN_ROLES + MAFIA_ROLES + NEUTRAL_ROLES
