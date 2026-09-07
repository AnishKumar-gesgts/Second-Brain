import pytest

from temporal_filter_qec.fusion_events import compile_fusion_events
from temporal_filter_qec.fusion_network import (
    build_bulk_component_memory,
    build_bulk_fusion_memory,
    bulk_edges,
    simulate_bulk_component_error,
    simulate_bulk_logical_error,
    six_ring_edge_observable,
)
from temporal_filter_qec.physics import PhysicalParameters, event_table


def _table(detuning: float = 0.0, gate: float | None = None):
    scalar = event_table(PhysicalParameters(60.0, 0.0, detuning, 1.0), gate)
    return compile_fusion_events(scalar)


def test_periodic_bulk_graph_is_12_valent() -> None:
    distance = 3
    edges = bulk_edges(distance)
    degree = {(x, y, z): 0 for x in range(distance) for y in range(distance) for z in range(distance)}
    for start, end, _ in edges:
        degree[start] += 1
        degree[end] += 1
    assert len(edges) == 6 * distance**3
    assert set(degree.values()) == {12}
    assert sum(six_ring_edge_observable(edge[2]) == "xx" for edge in edges) == 3 * distance**3
    assert sum(six_ring_edge_observable(edge[2]) == "zz" for edge in edges) == 3 * distance**3


def test_bulk_circuit_has_two_logical_observables() -> None:
    circuit = build_bulk_fusion_memory(3, _table())
    assert circuit.num_observables == 2
    circuit.detector_error_model(
        decompose_errors=True,
        approximate_disjoint_errors=True,
    )


def test_noiseless_bulk_has_no_failures() -> None:
    estimate = simulate_bulk_logical_error(_table(), 3, 1000, 11)
    assert estimate.failures_any == 0


def test_noiseless_component_has_no_failures() -> None:
    circuit = build_bulk_component_memory(3, _table(), component="xx")
    assert circuit.num_observables == 1
    estimate = simulate_bulk_component_error(_table(), 3, 1000, 21)
    assert estimate.failures == 0


def test_correlated_fusion_channel_runs_with_heralds() -> None:
    scalar = event_table(PhysicalParameters(60.0, 15.0, 1.2, 0.995), 140.0)
    fusion = compile_fusion_events(
        scalar,
        wrong_xx_fraction=0.25,
        wrong_zz_fraction=0.25,
        wrong_xx_zz_fraction=0.5,
    )
    estimate = simulate_bulk_logical_error(fusion, 3, 2000, 12)
    assert 0 <= estimate.logical_error_rate_any <= 1


def test_six_ring_type_ii_channel_runs() -> None:
    scalar = event_table(PhysicalParameters(60.0, 15.0, 0.6, 0.995), 220.0)
    fusion = compile_fusion_events(
        scalar,
        wrong_xx_fraction=0.0,
        wrong_zz_fraction=1.0,
        wrong_xx_zz_fraction=0.0,
    )
    estimate = simulate_bulk_component_error(
        fusion,
        3,
        1000,
        31,
        channel_profile="six_ring_type_ii",
    )
    assert estimate.p_wrong_xx_edges == 0.0
    assert estimate.p_wrong_zz_edges == pytest.approx(scalar.accepted_wrong)
