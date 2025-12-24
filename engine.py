"""Core game engine for the Town of Salem clone."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
import random

from roles import (
    INVESTIGATOR_RESULTS,
    MAFIA_ROLES,
    NEUTRAL_ROLES,
    SHERIFF_SUSPICIOUS_ALIGNMENTS,
    TOWN_ROLES,
    Role,
)


@dataclass
class Player:
    name: str
    role: Role | None = None
    alive: bool = True
    persona: str = "analytical"
    notes: list[str] = field(default_factory=list)
    cleaned: bool = False


@dataclass
class GameState:
    players: list[Player] = field(default_factory=list)
    day: int = 1
    phase: str = "night"
    winners: list[str] = field(default_factory=list)


class LiteLLMClient:
    """Wrapper around litellm to allow swapping in mocks during simulation."""

    def __init__(self, model: str) -> None:
        self.model = model

    def complete(self, prompt: str) -> str:
        import litellm

        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]


class DialogueGenerator:
    """Generate day chat lines with claims and logs."""

    def __init__(self, llm_client: LiteLLMClient | None = None) -> None:
        self.llm_client = llm_client

    def generate(self, player: Player, day: int, context: str) -> str:
        claim_role = self._claimed_role(player)
        if self.llm_client is None:
            return self._rule_based_line(player, day, context, claim_role)
        prompt = (
            "You are a Town of Salem player. Generate a short day chat line with a "
            f"{player.persona} persona. Claim as a {claim_role}. Include a claim or log. "
            f"Context: {context}"
        )
        return self.llm_client.complete(prompt)

    def _rule_based_line(
        self, player: Player, day: int, context: str, claim: str
    ) -> str:
        log = self._log_line(player)
        base = {
            "aggressive": (
                f"Day {day}: {claim} here. {context} {log} Post will or get voted."
            ),
            "defensive": (
                f"Day {day}: I'm {claim}. {context} {log} Please don't push me."
            ),
            "analytical": (
                f"Day {day}: Claiming {claim}. {context} {log} Here's my log."
            ),
        }
        return base.get(player.persona, base["analytical"])

    def _claimed_role(self, player: Player) -> str:
        if not player.role:
            return "Town"
        if player.role.faction == "Town":
            return player.role.name
        return player.role.fake_claim

    def _log_line(self, player: Player) -> str:
        if not player.notes:
            return "No new info yet."
        if not player.role or player.role.faction == "Town":
            return player.notes[-1]
        return "No new info yet."


class GameEngine:
    """Main orchestrator for the Town of Salem clone."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        rng: random.Random | None = None,
        llm_client: LiteLLMClient | None = None,
    ) -> None:
        self.rng = rng or random.Random()
        self.llm_client = llm_client or LiteLLMClient(model)
        self.dialogue = DialogueGenerator(self.llm_client)
        self.state = GameState()
        self.jailor_executions = 1
        self.janitor_cleans = 2

    def add_players(self, names: Iterable[str]) -> None:
        personas = ["aggressive", "defensive", "analytical"]
        self.state.players = [
            Player(name=name, persona=self.rng.choice(personas)) for name in names
        ]
        self._assign_roles()

    def _assign_roles(self) -> None:
        player_count = len(self.state.players)
        mafia_count = 3 if player_count <= 12 else 4
        neutral_count = 1 if player_count <= 12 else 2
        town_count = max(player_count - mafia_count - neutral_count, 0)

        mafia_roles = list(MAFIA_ROLES)
        neutral_roles = list(NEUTRAL_ROLES)
        town_roles = list(TOWN_ROLES)
        self.rng.shuffle(mafia_roles)
        self.rng.shuffle(neutral_roles)
        self.rng.shuffle(town_roles)

        if len(town_roles) < town_count:
            filler = TOWN_ROLES[-1]
            town_roles.extend([filler] * (town_count - len(town_roles)))

        roles = (
            mafia_roles[:mafia_count]
            + neutral_roles[:neutral_count]
            + town_roles[:town_count]
        )
        self.rng.shuffle(roles)
        for player, role in zip(self.state.players, roles, strict=False):
            player.role = role

    def narrate(self, prompt: str) -> str:
        return self.llm_client.complete(prompt)

    def run(self) -> None:
        if not self.state.players:
            names = [
                "Alice",
                "Ben",
                "Casey",
                "Drew",
                "Emery",
                "Flynn",
                "Gray",
                "Harper",
                "Indigo",
                "Jude",
                "Kai",
                "Logan",
            ]
            self.add_players(names)

        intro = self.narrate(
            "Introduce the setting for a Town of Salem style game night in two sentences."
        )
        print(intro)
        while not self.state.winners:
            self._run_night()
            if self._check_win_conditions():
                break
            self._run_day()
        print(f"Winners: {', '.join(self.state.winners)}")

    def _alive_players(self) -> list[Player]:
        return [player for player in self.state.players if player.alive]

    def _alive_players_by_faction(self, faction: str) -> list[Player]:
        return [
            player
            for player in self._alive_players()
            if player.role and player.role.faction == faction
        ]

    def _run_night(self) -> None:
        self.state.phase = "night"
        actions: dict[str, tuple[Player, Player | None]] = {}
        jailed: Player | None = None
        jailor: Player | None = None
        roleblocked: set[str] = set()
        mafia_targets = [
            player for player in self._alive_players() if player.role.faction != "Mafia"
        ]
        mafia = self._alive_players_by_faction("Mafia")

        for player in self._alive_players():
            if not player.role:
                continue
            if player.role.name == "Jailor":
                target = self._select_jail_target(player)
                jailor = player
                jailed = target
                actions["jail"] = (player, target)
            elif player.role.name == "Escort":
                target = self._random_target(player)
                if target:
                    roleblocked.add(target.name)
                    actions["roleblock"] = (player, target)
            elif player.role.name == "Doctor":
                target = self._random_target(player, allow_self=True)
                actions["heal"] = (player, target)
            elif player.role.name == "Lookout":
                target = self._random_target(player)
                actions["watch"] = (player, target)
            elif player.role.name == "Sheriff":
                target = self._select_sheriff_target(player)
                actions[f"sheriff-{player.name}"] = (player, target)
            elif player.role.name == "Investigator":
                target = self._random_target(player)
                actions[f"investigator-{player.name}"] = (player, target)
            elif player.role.name == "Consigliere":
                target = self._random_target(player)
                actions[f"consigliere-{player.name}"] = (player, target)

        mafia_target = None
        if mafia and mafia_targets:
            mafia_target = self.rng.choice(mafia_targets)
            actions["mafia_kill"] = (mafia[0], mafia_target)
        if mafia_target and any(p.role.name == "Janitor" for p in mafia):
            if self.janitor_cleans > 0:
                actions["janitor_clean"] = (mafia[0], mafia_target)
                self.janitor_cleans -= 1

        if jailed:
            roleblocked.add(jailed.name)

        deaths: list[Player] = []
        heal_target = actions.get("heal", (None, None))[1]

        if jailor and jailed:
            self._jail_chat(jailor, jailed)

        if "mafia_kill" in actions:
            _, target = actions["mafia_kill"]
            if target and target.name not in roleblocked:
                if target != heal_target and target != jailed:
                    deaths.append(target)

        if jailed and self.jailor_executions > 0 and jailed.role.faction != "Town":
            deaths.append(jailed)
            self.jailor_executions -= 1

        if "janitor_clean" in actions and deaths:
            _, target = actions["janitor_clean"]
            if target in deaths:
                target.cleaned = True

        for player in deaths:
            player.alive = False

        self._resolve_investigations(actions)
        self._validate_night(actions)
        self._announce_deaths(deaths)
        self.state.day += 1

    def _resolve_investigations(
        self, actions: dict[str, tuple[Player, Player | None]]
    ) -> None:
        for key, (actor, target) in actions.items():
            if not target or not actor.role:
                continue
            if key.startswith("sheriff"):
                suspicion = (
                    "suspicious"
                    if target.role.alignment in SHERIFF_SUSPICIOUS_ALIGNMENTS
                    else "innocent"
                )
                actor.notes.append(
                    f"Sheriff result on {target.name}: {suspicion}."
                )
            if key.startswith("investigator"):
                result = INVESTIGATOR_RESULTS.get(
                    target.role.investigator_group,
                    "Your target's role is unclear.",
                )
                actor.notes.append(f"Investigator on {target.name}: {result}")
            if key.startswith("consigliere"):
                actor.notes.append(
                    f"Consigliere learns {target.name} is {target.role.name}."
                )

    def _run_day(self) -> None:
        self.state.phase = "day"
        context = "Share claims, post logs, and call out suspicious behavior."
        for player in self._alive_players():
            line = self.dialogue.generate(player, self.state.day, context)
            print(f"{player.name}: {line}")
        self._trial_and_lynch()
        self._check_win_conditions()

    def _trial_and_lynch(self) -> None:
        alive = self._alive_players()
        if len(alive) < 3:
            return
        suspect_counts = self._suspicion_counts()
        eligible = [player for player in alive if player.name in suspect_counts]
        if not eligible:
            return
        suspect = max(eligible, key=lambda player: suspect_counts[player.name])
        suspect.alive = False
        print(f"{suspect.name} was lynched by the town.")

    def _check_win_conditions(self) -> bool:
        town = self._alive_players_by_faction("Town")
        mafia = self._alive_players_by_faction("Mafia")
        if not mafia:
            self.state.winners = ["Town"]
            return True
        if len(mafia) >= len(town):
            self.state.winners = ["Mafia"]
            return True
        return False

    def _random_target(self, actor: Player, allow_self: bool = False) -> Player | None:
        candidates = [p for p in self._alive_players() if p.alive]
        if not allow_self:
            candidates = [p for p in candidates if p.name != actor.name]
        if not candidates:
            return None
        return self.rng.choice(candidates)

    def _validate_night(self, actions: dict[str, tuple[Player, Player | None]]) -> None:
        roster = {p.name for p in self.state.players}
        for key, (actor, target) in actions.items():
            if key == "mafia_kill" and target and target.role.faction == "Mafia":
                raise ValueError("Illegal move: Mafia attempted to kill Mafia.")
            if target and target.name not in roster:
                raise ValueError("Role hallucination: Target name not in roster.")
            if actor.name not in roster:
                raise ValueError("Role hallucination: Actor name not in roster.")

    def _extract_suspect_name(self, note: str) -> str | None:
        if "suspicious" not in note:
            return None
        if "Sheriff result on " in note:
            return note.split("Sheriff result on ", 1)[1].split(":", 1)[0]
        return None

    def _suspicion_counts(self) -> dict[str, int]:
        town_members = self._alive_players_by_faction("Town")
        suspect_counts: dict[str, int] = {}
        for player in town_members:
            for note in player.notes:
                suspect_name = self._extract_suspect_name(note)
                if suspect_name:
                    suspect_counts[suspect_name] = suspect_counts.get(suspect_name, 0) + 1
        return suspect_counts

    def _select_jail_target(self, jailor: Player) -> Player | None:
        suspect_counts = self._suspicion_counts()
        alive = [player for player in self._alive_players() if player.name != jailor.name]
        eligible = [player for player in alive if player.name in suspect_counts]
        if eligible:
            return max(eligible, key=lambda player: suspect_counts[player.name])
        return self._random_target(jailor)

    def _select_sheriff_target(self, sheriff: Player) -> Player | None:
        candidates = [p for p in self._alive_players() if p.name != sheriff.name]
        if not candidates:
            return None
        non_town = [
            player for player in candidates if player.role and player.role.faction != "Town"
        ]
        if non_town and self.rng.random() < 0.7:
            return self.rng.choice(non_town)
        return self.rng.choice(candidates)

    def _announce_deaths(self, deaths: list[Player]) -> None:
        if not deaths:
            print("No one died last night.")
            return
        for player in deaths:
            status = "Cleaned" if player.cleaned else "Uncleaned"
            print(f"{player.name} died last night. ({status})")

    def _jail_chat(self, jailor: Player, prisoner: Player) -> None:
        jailor_line = f"Jailor: State your claim, {prisoner.name}."
        prisoner_line = self.dialogue.generate(
            prisoner,
            self.state.day,
            "You are jailed. Provide a concise claim and defense.",
        )
        print(jailor_line)
        print(f"{prisoner.name}: {prisoner_line}")
