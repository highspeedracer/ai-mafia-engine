"""Core game engine for the Town of Salem clone."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import litellm

from roles import ALL_ROLES, Role


@dataclass
class Player:
    name: str
    role: Role | None = None


@dataclass
class GameState:
    players: list[Player] = field(default_factory=list)
    day: int = 1
    phase: str = "night"


class GameEngine:
    """Main orchestrator for the Town of Salem clone."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.state = GameState()

    def add_players(self, names: Iterable[str]) -> None:
        self.state.players = [Player(name=name) for name in names]
        self._assign_roles()

    def _assign_roles(self) -> None:
        for player, role in zip(self.state.players, ALL_ROLES, strict=False):
            player.role = role

    def narrate(self, prompt: str) -> str:
        """Generate narration using litellm with the configured model."""
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]

    def run(self) -> None:
        if not self.state.players:
            self.add_players(["Alice", "Ben", "Casey", "Drew", "Emery"])

        intro = self.narrate(
            "Introduce the setting for a Town of Salem style game night in two sentences."
        )
        print(intro)
        print("Assigned roles:")
        for player in self.state.players:
            role_name = player.role.name if player.role else "Unassigned"
            print(f"- {player.name}: {role_name}")
