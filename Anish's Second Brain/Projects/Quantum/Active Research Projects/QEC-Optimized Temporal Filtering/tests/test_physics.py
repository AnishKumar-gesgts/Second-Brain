from temporal_filter_qec.physics import (
    PhysicalParameters,
    analytic_unfiltered,
    event_table,
    sample_event_frequencies,
)


PARAMS = PhysicalParameters(60.0, 15.0, 1.5, 0.995)


def test_event_table_conserves_probability() -> None:
    for gate in (10.0, 60.0, 200.0, None):
        table = event_table(PARAMS, gate)
        assert abs(table.total - 1.0) < 2e-10
        assert table.accepted_wrong >= 0
        assert table.erasure >= 0


def test_unfiltered_matches_closed_form() -> None:
    numeric = event_table(PARAMS, None)
    exact = analytic_unfiltered(PARAMS)
    assert abs(numeric.accepted_wrong - exact.accepted_wrong) < 1e-12
    assert abs(numeric.accepted_correct - exact.accepted_correct) < 1e-12


def test_ideal_interference_has_no_accepted_error() -> None:
    ideal = PhysicalParameters(60.0, 15.0, 0.0, 1.0)
    for gate in (20.0, 100.0, None):
        assert event_table(ideal, gate).accepted_wrong < 1e-13


def test_temporal_grid_converges() -> None:
    coarse = event_table(PARAMS, 60.0, grid_points=2_001)
    fine = event_table(PARAMS, 60.0, grid_points=20_001)
    assert abs(coarse.accepted_wrong - fine.accepted_wrong) < 2e-8
    assert abs(coarse.erasure - fine.erasure) < 2e-8


def test_spectral_diffusion_matches_unfiltered_closed_form() -> None:
    diffusing = PhysicalParameters(60.0, 15.0, 0.8, 0.995, 0.35)
    numeric = event_table(diffusing, None)
    exact = analytic_unfiltered(diffusing)
    assert abs(numeric.accepted_wrong - exact.accepted_wrong) < 1e-12
    assert numeric.accepted_wrong > event_table(PhysicalParameters(60.0, 15.0, 0.8, 0.995), None).accepted_wrong


def test_monte_carlo_agrees_with_integral() -> None:
    expected = event_table(PARAMS, 60.0)
    observed = sample_event_frequencies(PARAMS, 60.0, shots=300_000, seed=7)
    for key in ("accepted_correct", "accepted_wrong", "rejected", "loss"):
        assert abs(observed[key] - getattr(expected, key)) < 0.003
