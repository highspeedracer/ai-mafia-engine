"""Role definitions and investigative results for the Town of Salem clone."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    name: str
    alignment: str
    faction: str
    investigator_group: str
    fake_claim: str


TOWN_ROLES = (
    Role(
        name="Jailor",
        alignment="Town",
        faction="Town",
        investigator_group="Leader",
        fake_claim="Jailor",
    ),
    Role(
        name="Sheriff",
        alignment="Town",
        faction="Town",
        investigator_group="Investigator",
        fake_claim="Sheriff",
    ),
    Role(
        name="Investigator",
        alignment="Town",
        faction="Town",
        investigator_group="Investigator",
        fake_claim="Investigator",
    ),
    Role(
        name="Doctor",
        alignment="Town",
        faction="Town",
        investigator_group="Protector",
        fake_claim="Doctor",
    ),
    Role(
        name="Escort",
        alignment="Town",
        faction="Town",
        investigator_group="Escort",
        fake_claim="Escort",
    ),
    Role(
        name="Lookout",
        alignment="Town",
        faction="Town",
        investigator_group="Watcher",
        fake_claim="Lookout",
    ),
    Role(
        name="Townie",
        alignment="Town",
        faction="Town",
        investigator_group="Support",
        fake_claim="Townie",
    ),
)

MAFIA_ROLES = (
    Role(
        name="Godfather",
        alignment="Mafia",
        faction="Mafia",
        investigator_group="Leader",
        fake_claim="Investigator",
    ),
    Role(
        name="Mafioso",
        alignment="Mafia",
        faction="Mafia",
        investigator_group="Killing",
        fake_claim="Townie",
    ),
    Role(
        name="Consigliere",
        alignment="Mafia",
        faction="Mafia",
        investigator_group="Investigator",
        fake_claim="Sheriff",
    ),
    Role(
        name="Janitor",
        alignment="Mafia",
        faction="Mafia",
        investigator_group="Support",
        fake_claim="Doctor",
    ),
)

NEUTRAL_ROLES = (
    Role(
        name="Jester",
        alignment="Neutral",
        faction="Neutral",
        investigator_group="Deception",
        fake_claim="Townie",
    ),
    Role(
        name="Executioner",
        alignment="Neutral",
        faction="Neutral",
        investigator_group="Deception",
        fake_claim="Sheriff",
    ),
)

ALL_ROLES = TOWN_ROLES + MAFIA_ROLES + NEUTRAL_ROLES

INVESTIGATOR_RESULTS = {
    "Leader": "Your target could be a Jailor or Godfather.",
    "Investigator": "Your target could be a Sheriff, Investigator, or Consigliere.",
    "Protector": "Your target could be a Doctor.",
    "Escort": "Your target could be an Escort.",
    "Watcher": "Your target could be a Lookout.",
    "Support": "Your target could be a Townie or Janitor.",
    "Killing": "Your target could be a Mafioso.",
    "Deception": "Your target could be a Jester or Executioner.",
}

SHERIFF_SUSPICIOUS_ALIGNMENTS = {"Mafia", "Neutral"}
