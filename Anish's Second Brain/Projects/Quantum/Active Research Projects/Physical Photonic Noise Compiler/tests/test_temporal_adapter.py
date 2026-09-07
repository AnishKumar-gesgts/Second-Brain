import pytest

from photonic_noise_compiler.adapters import ScalarTemporalTable, compile_temporal_type_ii
from photonic_noise_compiler.diagnostics import compare_with_independent


def _channel():
    return compile_temporal_type_ii(
        ScalarTemporalTable(0.7, 0.1, 0.15, 0.05),
        name="temporal",
        parameters={"gate_width_ps": 140},
        source_provenance=("test fixture",),
    )


def test_type_ii_mapping_is_zz_biased_with_joint_erasures() -> None:
    channel = _channel()
    assert channel.marginal("flip", "XX") == 0.0
    assert channel.marginal("flip", "ZZ") == pytest.approx(0.1)
    assert channel.marginal("erasure", "XX") == pytest.approx(0.2)
    assert channel.marginal("erasure", "ZZ") == pytest.approx(0.2)
    states = channel.state_distribution(("XX", "ZZ"))
    assert states[("erased", "erased")] == pytest.approx(0.2)
    assert ("erased", "correct") not in states


def test_scalarization_diagnostic_detects_synthetic_partial_erasures() -> None:
    diagnostic = compare_with_independent(_channel())
    assert diagnostic["total_variation_from_independent"] > 0
    assert diagnostic["independent_synthetic_partial_erasure_probability"] > 0
