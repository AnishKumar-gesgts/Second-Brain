from temporal_filter_qec.physics import EventTable
from temporal_filter_qec.qec import build_surface_code_memory, simulate_logical_error, wilson_interval


def table(erasure: float, wrong: float) -> EventTable:
    return EventTable(None, 1.0 - erasure - wrong, wrong, erasure, 0.0, wrong / max(1e-15, 1-erasure), 1.0, 0)


def test_compiled_channel_is_valid_stim() -> None:
    circuit = build_surface_code_memory(3, 3, 0.1, 0.02)
    circuit.detector_error_model(decompose_errors=True, approximate_disjoint_errors=True)


def test_noiseless_channel_has_no_failures() -> None:
    estimate = simulate_logical_error(table(0.0, 0.0), 3, 3, 1000, 1)
    assert estimate.failures == 0


def test_heralds_help_for_erasure_dominated_channel() -> None:
    noisy = table(0.2, 0.0)
    aware = simulate_logical_error(noisy, 3, 3, 30_000, 2, heralded_decoder=True)
    blind = simulate_logical_error(noisy, 3, 3, 30_000, 3, heralded_decoder=False)
    assert aware.logical_error_rate < blind.logical_error_rate


def test_wilson_interval_contains_observed_rate() -> None:
    low, high = wilson_interval(12, 1000)
    assert low < 0.012 < high


def test_missing_all_flags_matches_flag_blind_erasure_channel() -> None:
    noisy = table(0.15, 0.01)
    missed = simulate_logical_error(
        noisy, 3, 3, 100_000, 11, missed_erasure_fraction=1.0
    )
    blind = simulate_logical_error(
        noisy, 3, 3, 100_000, 11, heralded_decoder=False
    )
    assert abs(missed.logical_error_rate - blind.logical_error_rate) < 0.005
