"""Diagnostics for reductions that discard compiled channel structure."""

from __future__ import annotations

from typing import Any

from .schema import CompiledChannel


def compare_with_independent(channel: CompiledChannel) -> dict[str, Any]:
    independent = channel.independent_target_approximation()
    states = independent.state_distribution(("XX", "ZZ"))
    synthetic_partial_erasure = sum(
        states.get(signature, 0.0)
        for signature in (
            ("erased", "correct"),
            ("correct", "erased"),
            ("erased", "flipped"),
            ("flipped", "erased"),
        )
    )
    return {
        "channel": channel.name,
        "full_erasure_probability": channel.state_distribution(("XX", "ZZ")).get(
            ("erased", "erased"), 0.0
        ),
        "zz_flip_probability": channel.marginal("flip", "ZZ"),
        "xx_flip_probability": channel.marginal("flip", "XX"),
        "erasure_mutual_information_bits": channel.mutual_information_bits(
            "erasure", "XX", "ZZ"
        ),
        "total_variation_from_independent": channel.total_variation_from(independent),
        "independent_synthetic_partial_erasure_probability": synthetic_partial_erasure,
    }
