"""Canonical physical-event to QEC-channel contract."""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product
from math import log2
from typing import Any, Iterable


def _canonical(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(sorted(set(values)))
    if any(not value or not isinstance(value, str) for value in result):
        raise ValueError("channel labels must be non-empty strings")
    return result


@dataclass(frozen=True)
class OutcomeBranch:
    """One mutually exclusive physical event and its compiled consequences.

    ``flips`` and ``erasures`` are simulator truth. ``heralds`` are legitimately
    decoder-visible side information. ``physical_event`` and ``latent_tags``
    exist only for validation and provenance and are removed by decoder export.
    """

    probability: float
    flips: tuple[str, ...] = ()
    erasures: tuple[str, ...] = ()
    leakages: tuple[str, ...] = ()
    heralds: tuple[str, ...] = ()
    physical_event: str = "unspecified"
    latent_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("branch probability must lie in [0, 1]")
        if not self.physical_event:
            raise ValueError("physical_event must be non-empty")
        object.__setattr__(self, "flips", _canonical(self.flips))
        object.__setattr__(self, "erasures", _canonical(self.erasures))
        object.__setattr__(self, "leakages", _canonical(self.leakages))
        object.__setattr__(self, "heralds", _canonical(self.heralds))
        object.__setattr__(self, "latent_tags", _canonical(self.latent_tags))
        effect_sets = (set(self.flips), set(self.erasures), set(self.leakages))
        if any(effect_sets[i] & effect_sets[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError(
                "one target cannot be flipped, erased, or leaked simultaneously"
            )

    def target_state(self, target: str) -> str:
        if target in self.erasures:
            return "erased"
        if target in self.leakages:
            return "leaked"
        if target in self.flips:
            return "flipped"
        return "correct"

    def simulation_view(self) -> dict[str, Any]:
        """Return sampler input, including fault truth but no latent tags."""
        return {
            "probability": self.probability,
            "flips": list(self.flips),
            "erasures": list(self.erasures),
            "leakages": list(self.leakages),
            "heralds": list(self.heralds),
        }

    def decoder_view(self) -> dict[str, Any]:
        """Return only information a decoder may legitimately receive."""
        visible_erasures = tuple(
            target for target in self.erasures if f"erasure:{target}" in self.heralds
        )
        return {
            "probability": self.probability,
            "erasures": list(visible_erasures),
            "heralds": list(self.heralds),
        }

    def to_dict(self, *, include_hidden: bool = True) -> dict[str, Any]:
        result = self.simulation_view()
        if include_hidden:
            result["physical_event"] = self.physical_event
            result["latent_tags"] = list(self.latent_tags)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutcomeBranch":
        return cls(
            probability=float(data["probability"]),
            flips=tuple(data.get("flips", ())),
            erasures=tuple(data.get("erasures", ())),
            leakages=tuple(data.get("leakages", ())),
            heralds=tuple(data.get("heralds", ())),
            physical_event=str(data.get("physical_event", "unspecified")),
            latent_tags=tuple(data.get("latent_tags", ())),
        )


@dataclass(frozen=True)
class CompiledChannel:
    """Normalized event channel produced by one physical adapter."""

    name: str
    adapter: str
    adapter_version: str
    primitive: str
    branches: tuple[OutcomeBranch, ...]
    parameters: tuple[tuple[str, Any], ...] = ()
    assumptions: tuple[str, ...] = ()
    correlations: tuple[str, ...] = ()
    source_provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("name", "adapter", "adapter_version", "primitive"):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must be non-empty")
        if not self.branches:
            raise ValueError("compiled channel must contain at least one branch")
        object.__setattr__(self, "assumptions", _canonical(self.assumptions))
        object.__setattr__(self, "correlations", _canonical(self.correlations))
        object.__setattr__(self, "source_provenance", _canonical(self.source_provenance))
        self.validate()

    @property
    def total_probability(self) -> float:
        return sum(branch.probability for branch in self.branches)

    @property
    def targets(self) -> tuple[str, ...]:
        return _canonical(
            target
            for branch in self.branches
            for target in (*branch.flips, *branch.erasures, *branch.leakages)
        )

    def validate(self, atol: float = 1e-10) -> None:
        if abs(self.total_probability - 1.0) > atol:
            raise ValueError(
                f"channel probabilities sum to {self.total_probability}, not 1"
            )

    def marginal(self, effect: str, target: str) -> float:
        if effect not in {"flip", "erasure", "leakage", "herald"}:
            raise ValueError("effect must be flip, erasure, leakage, or herald")
        attribute = {
            "flip": "flips",
            "erasure": "erasures",
            "leakage": "leakages",
            "herald": "heralds",
        }[effect]
        return sum(
            branch.probability
            for branch in self.branches
            if target in getattr(branch, attribute)
        )

    def state_distribution(
        self, targets: Iterable[str] | None = None
    ) -> dict[tuple[str, ...], float]:
        ordered = tuple(targets) if targets is not None else self.targets
        result: dict[tuple[str, ...], float] = {}
        for branch in self.branches:
            signature = tuple(branch.target_state(target) for target in ordered)
            result[signature] = result.get(signature, 0.0) + branch.probability
        return result

    def decoder_distribution(self) -> list[dict[str, Any]]:
        """Aggregate visible records without exposing fault truth or labels."""
        grouped: dict[tuple[tuple[str, ...], tuple[str, ...]], float] = {}
        for branch in self.branches:
            visible = branch.decoder_view()
            key = (tuple(visible["erasures"]), branch.heralds)
            grouped[key] = grouped.get(key, 0.0) + branch.probability
        return [
            {
                "probability": probability,
                "erasures": list(key[0]),
                "heralds": list(key[1]),
            }
            for key, probability in sorted(grouped.items())
        ]

    def independent_target_approximation(self) -> "CompiledChannel":
        """Match target marginals while removing cross-target correlations."""
        targets = self.targets
        per_target: list[tuple[tuple[str, float], ...]] = []
        for target in targets:
            p_erasure = self.marginal("erasure", target)
            p_flip = sum(
                branch.probability
                for branch in self.branches
                if target in branch.flips and target not in branch.erasures
            )
            p_leakage = self.marginal("leakage", target)
            p_correct = 1.0 - p_erasure - p_flip - p_leakage
            if p_correct < -1e-12:
                raise ValueError(f"inconsistent marginal channel for {target}")
            per_target.append(
                tuple(
                    (state, probability)
                    for state, probability in (
                        ("correct", max(0.0, p_correct)),
                        ("flipped", p_flip),
                        ("erased", p_erasure),
                        ("leaked", p_leakage),
                    )
                    if probability > 0.0
                )
            )
        branches: list[OutcomeBranch] = []
        for states in product(*per_target):
            probability = 1.0
            flips: list[str] = []
            erasures: list[str] = []
            leakages: list[str] = []
            heralds: list[str] = []
            for target, (state, state_probability) in zip(targets, states, strict=True):
                probability *= state_probability
                if state == "flipped":
                    flips.append(target)
                elif state == "erased":
                    erasures.append(target)
                    heralds.append(f"erasure:{target}")
                elif state == "leaked":
                    leakages.append(target)
            branches.append(
                OutcomeBranch(
                    probability=probability,
                    flips=tuple(flips),
                    erasures=tuple(erasures),
                    leakages=tuple(leakages),
                    heralds=tuple(heralds),
                    physical_event="matched_independent_approximation",
                )
            )
        return replace(
            self,
            name=f"{self.name}__independent",
            branches=tuple(branches),
            assumptions=(*self.assumptions, "target states treated as independent"),
            correlations=("all cross-target correlations removed",),
        )

    def total_variation_from(self, other: "CompiledChannel") -> float:
        targets = _canonical((*self.targets, *other.targets))
        left = self.state_distribution(targets)
        right = other.state_distribution(targets)
        keys = set(left) | set(right)
        return 0.5 * sum(
            abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in keys
        )

    def mutual_information_bits(
        self, effect: str, target_a: str, target_b: str
    ) -> float:
        if effect not in {"flip", "erasure"}:
            raise ValueError("effect must be flip or erasure")
        attribute = "flips" if effect == "flip" else "erasures"
        joint = {(a, b): 0.0 for a in (0, 1) for b in (0, 1)}
        for branch in self.branches:
            values = getattr(branch, attribute)
            joint[(int(target_a in values), int(target_b in values))] += branch.probability
        marginal_a = {a: sum(joint[(a, b)] for b in (0, 1)) for a in (0, 1)}
        marginal_b = {b: sum(joint[(a, b)] for a in (0, 1)) for b in (0, 1)}
        return sum(
            probability * log2(probability / (marginal_a[a] * marginal_b[b]))
            for (a, b), probability in joint.items()
            if probability > 0.0
        )

    def to_dict(self, *, include_hidden: bool = True) -> dict[str, Any]:
        return {
            "schema_version": "0.1",
            "name": self.name,
            "adapter": self.adapter,
            "adapter_version": self.adapter_version,
            "primitive": self.primitive,
            "parameters": dict(self.parameters),
            "assumptions": list(self.assumptions),
            "correlations": list(self.correlations),
            "source_provenance": list(self.source_provenance),
            "branches": [
                branch.to_dict(include_hidden=include_hidden)
                for branch in self.branches
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompiledChannel":
        return cls(
            name=str(data["name"]),
            adapter=str(data["adapter"]),
            adapter_version=str(data["adapter_version"]),
            primitive=str(data["primitive"]),
            parameters=tuple(sorted(dict(data.get("parameters", {})).items())),
            assumptions=tuple(data.get("assumptions", ())),
            correlations=tuple(data.get("correlations", ())),
            source_provenance=tuple(data.get("source_provenance", ())),
            branches=tuple(
                OutcomeBranch.from_dict(branch) for branch in data["branches"]
            ),
        )
