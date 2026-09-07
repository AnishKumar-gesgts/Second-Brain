import pytest

from photonic_noise_compiler.qec import (
    build_paired_bulk_memory,
    bulk_edges,
    edge_observable,
    fusion_pairs,
    simulate_logical_error,
)
from photonic_noise_compiler.schema import CompiledChannel, OutcomeBranch


def _channel(*branches: OutcomeBranch) -> CompiledChannel:
    return CompiledChannel(
        name="qec_test",
        adapter="test",
        adapter_version="1",
        primitive="type-II",
        branches=branches,
    )


def test_pairing_covers_each_edge_and_swaps_observable_kind() -> None:
    distance = 3
    edges = bulk_edges(distance)
    pairs = fusion_pairs(distance)
    assert len(pairs) == len(edges)
    assert {edge_a for edge_a, _, _, _ in pairs} == set(range(len(edges)))
    assert {edge_b for _, edge_b, _, _ in pairs} == set(range(len(edges)))
    for edge_a, edge_b, target_a, target_b in pairs:
        assert edge_observable(edges[edge_a][2]) == target_a
        assert edge_observable(edges[edge_b][2]) == target_b
        assert target_a != target_b


def test_noiseless_paired_memory_has_no_failures() -> None:
    channel = _channel(OutcomeBranch(1.0, physical_event="correct"))
    circuit = build_paired_bulk_memory(3, channel)
    assert circuit.num_observables == 2
    estimate = simulate_logical_error(channel, 3, 1000, 11)
    assert estimate.failures_any == 0


def test_joint_erasure_channel_compiles_and_decodes() -> None:
    channel = _channel(
        OutcomeBranch(0.85, physical_event="correct"),
        OutcomeBranch(0.05, flips=("ZZ",), physical_event="wrong"),
        OutcomeBranch(
            0.1,
            erasures=("XX", "ZZ"),
            heralds=("erasure:XX", "erasure:ZZ"),
            physical_event="loss",
        ),
    )
    estimate = simulate_logical_error(channel, 3, 1000, 12)
    assert 0.0 <= estimate.logical_error_rate_any <= 1.0


def test_independent_control_is_fixed_point_of_reduction() -> None:
    branches = []
    for xx_state, p_xx in (("correct", 0.9), ("erased", 0.1)):
        for zz_state, p_zz in (("correct", 0.8), ("flipped", 0.1), ("erased", 0.1)):
            branches.append(
                OutcomeBranch(
                    p_xx * p_zz,
                    flips=("ZZ",) if zz_state == "flipped" else (),
                    erasures=tuple(
                        target
                        for target, state in (("XX", xx_state), ("ZZ", zz_state))
                        if state == "erased"
                    ),
                    physical_event="independent_control",
                )
            )
    channel = _channel(*branches)
    reduced = channel.independent_target_approximation()
    assert channel.total_variation_from(reduced) == pytest.approx(0.0, abs=1e-12)


def test_sampler_can_use_frozen_marginal_decoder() -> None:
    full = _channel(
        OutcomeBranch(0.8, physical_event="correct"),
        OutcomeBranch(
            0.2,
            erasures=("XX", "ZZ"),
            physical_event="joint_erasure",
        ),
    )
    marginal = full.independent_target_approximation()
    estimate = simulate_logical_error(
        full,
        3,
        1000,
        22,
        decoder_channel=marginal,
    )
    assert estimate.decoder_channel_name == marginal.name


def test_qec_harness_refuses_unvalidated_leakage_reduction() -> None:
    channel = _channel(
        OutcomeBranch(
            1.0,
            leakages=("XX",),
            physical_event="multiphoton_leakage",
        )
    )
    with pytest.raises(ValueError, match="no validated leakage"):
        build_paired_bulk_memory(3, channel)
