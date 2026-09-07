"""Architecture-aware bulk fusion-network proxy.

This implements the published local syndrome semantics of the six-ring FBQC
bulk: two 12-valent syndrome graphs and one XX/ZZ outcome pair per fusion.
The finite model is a periodic triangulated-cubic graph.  It is intentionally
called a proxy because the exact resource-state placement, half-cell shift,
physical edge crossing, and planar logical-block boundaries are not yet
constructed from the six-ring stabilizer complex.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt

import numpy as np
import pymatching
import stim

from .fusion_events import FusionEventTable


Coord = tuple[int, int, int]
Edge = tuple[Coord, Coord, tuple[int, int, int]]


def six_ring_edge_observable(direction: tuple[int, int, int]) -> str:
    """Return the Bell outcome represented by a six-ring bulk edge.

    Cubic-axis edges carry XX outcomes and face-diagonal edges carry ZZ
    outcomes in each of the two half-cell-shifted syndrome graphs.
    """
    nonzero = sum(value != 0 for value in direction)
    if nonzero == 1:
        return "xx"
    if nonzero == 2:
        return "zz"
    raise ValueError(f"not a six-ring bulk direction: {direction}")


@dataclass(frozen=True)
class BulkLogicalEstimate:
    distance: int
    shots: int
    failures_any: int
    failures_xx: int
    failures_zz: int
    logical_error_rate_any: float
    logical_error_rate_xx: float
    logical_error_rate_zz: float
    ci_low: float
    ci_high: float
    missed_erasure_fraction: float
    seed: int
    syndrome_vertices_per_component: int
    edges_per_component: int
    vertex_degree: int
    model_label: str

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


@dataclass(frozen=True)
class ComponentLogicalEstimate:
    distance: int
    component: str
    shots: int
    failures: int
    logical_error_rate: float
    ci_low: float
    ci_high: float
    p_wrong: float
    p_erasure: float
    p_wrong_xx_edges: float
    p_wrong_zz_edges: float
    p_erasure_xx_edges: float
    p_erasure_zz_edges: float
    missed_erasure_fraction: float
    seed: int
    syndrome_vertices: int
    edges: int
    vertex_degree: int
    model_label: str

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def wilson_interval(
    failures: int, shots: int, z: float = 1.959963984540054
) -> tuple[float, float]:
    if shots <= 0 or not 0 <= failures <= shots:
        raise ValueError("invalid binomial counts")
    p = failures / shots
    denominator = 1.0 + z * z / shots
    center = (p + z * z / (2.0 * shots)) / denominator
    radius = z * sqrt(
        (p * (1.0 - p) + z * z / (4.0 * shots)) / shots
    ) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def bulk_edges(distance: int) -> list[Edge]:
    """Return a periodic 12-valent cubic-with-diagonals graph.

    Six positive directions give twelve incident edges at each vertex.  The
    representation is simple, deterministic, and has three toric homology
    classes, which makes it useful for testing bulk distance scaling.
    """
    if distance < 3 or distance % 2 == 0:
        raise ValueError("distance must be an odd integer >= 3")
    directions = (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 1, 0),
        (1, 0, 1),
        (0, 1, 1),
    )
    result: list[Edge] = []
    for x in range(distance):
        for y in range(distance):
            for z in range(distance):
                start = (x, y, z)
                for dx, dy, dz in directions:
                    end = (
                        (x + dx) % distance,
                        (y + dy) % distance,
                        (z + dz) % distance,
                    )
                    result.append((start, end, (dx, dy, dz)))
    return result


def _event_branches(
    table: FusionEventTable,
    *,
    xx_qubit: int,
    zz_qubit: int,
    xx_flag_qubit: int,
    zz_flag_qubit: int,
    hidden_qubit: int,
    missed_erasure_fraction: float,
) -> list[tuple[float, list[stim.GateTarget]]]:
    """Enumerate an exact mutually exclusive channel for one fusion."""
    if not 0 <= missed_erasure_fraction <= 1:
        raise ValueError("missed_erasure_fraction must lie in [0, 1]")
    branches: list[tuple[float, list[stim.GateTarget]]] = []

    def add(probability: float, qubits: tuple[int, ...]) -> None:
        if probability > 0:
            branches.append((probability, [stim.target_x(q) for q in qubits]))

    add(table.wrong_xx, (xx_qubit,))
    add(table.wrong_zz, (zz_qubit,))
    add(table.wrong_xx_zz, (xx_qubit, zz_qubit))

    def partial(probability: float, data: int, flag: int) -> None:
        flagged = probability * (1.0 - missed_erasure_fraction)
        missed = probability * missed_erasure_fraction
        add(flagged / 2.0, (flag,))
        add(flagged / 2.0, (data, flag))
        # The hidden target makes the no-flip missed-erasure branch a real
        # branch in Stim's mutually exclusive ELSE_CORRELATED_ERROR chain.
        add(missed / 2.0, (hidden_qubit,))
        add(missed / 2.0, (data, hidden_qubit))

    partial(table.erasure_xx, xx_qubit, xx_flag_qubit)
    partial(table.erasure_zz, zz_qubit, zz_flag_qubit)

    full = table.full_erasure
    flagged = full * (1.0 - missed_erasure_fraction)
    missed = full * missed_erasure_fraction
    for probability, flag_targets in (
        (flagged, (xx_flag_qubit, zz_flag_qubit)),
        (missed, (hidden_qubit,)),
    ):
        for flip_xx, flip_zz in ((0, 0), (1, 0), (0, 1), (1, 1)):
            targets = list(flag_targets)
            if flip_xx:
                targets.append(xx_qubit)
            if flip_zz:
                targets.append(zz_qubit)
            add(probability / 4.0, tuple(targets))
    return branches


def _append_disjoint_channel(
    circuit: stim.Circuit,
    branches: list[tuple[float, list[stim.GateTarget]]],
) -> None:
    consumed = 0.0
    for index, (unconditional_probability, targets) in enumerate(branches):
        remaining = 1.0 - consumed
        conditional_probability = unconditional_probability / remaining
        name = "CORRELATED_ERROR" if index == 0 else "ELSE_CORRELATED_ERROR"
        circuit.append(name, targets, conditional_probability)
        consumed += unconditional_probability


def build_bulk_fusion_memory(
    distance: int,
    table: FusionEventTable,
    *,
    missed_erasure_fraction: float = 0.0,
) -> stim.Circuit:
    """Construct the paired primal/dual bulk measurement circuit."""
    edges = bulk_edges(distance)
    circuit = stim.Circuit()
    measured: list[int] = []
    for edge_index in range(len(edges)):
        base = 5 * edge_index
        xx, zz, flag_xx, flag_zz, hidden = range(base, base + 5)
        branches = _event_branches(
            table,
            xx_qubit=xx,
            zz_qubit=zz,
            xx_flag_qubit=flag_xx,
            zz_flag_qubit=flag_zz,
            hidden_qubit=hidden,
            missed_erasure_fraction=missed_erasure_fraction,
        )
        if branches:
            _append_disjoint_channel(circuit, branches)
        measured.extend((xx, zz, flag_xx, flag_zz))

    circuit.append("M", measured)
    record_index = {qubit: index for index, qubit in enumerate(measured)}
    record_count = len(measured)

    def rec(qubit: int) -> stim.GateTarget:
        return stim.target_rec(record_index[qubit] - record_count)

    incident: dict[Coord, list[int]] = {
        (x, y, z): []
        for x in range(distance)
        for y in range(distance)
        for z in range(distance)
    }
    for edge_index, (start, end, _) in enumerate(edges):
        incident[start].append(edge_index)
        incident[end].append(edge_index)
    if any(len(edge_indices) != 12 for edge_indices in incident.values()):
        raise RuntimeError("bulk graph is not 12-valent")

    for outcome_offset in (0, 1):
        for coord in sorted(incident):
            circuit.append(
                "DETECTOR",
                [rec(5 * edge_index + outcome_offset) for edge_index in incident[coord]],
            )
    for edge_index in range(len(edges)):
        circuit.append("DETECTOR", [rec(5 * edge_index + 2)])
        circuit.append("DETECTOR", [rec(5 * edge_index + 3)])

    # A seam-crossing cocycle detects x-winding error cycles.  The two copies
    # give separate XX- and ZZ-component logical observables.
    seam_edges = [
        edge_index
        for edge_index, ((x, _, _), _, (dx, _, _)) in enumerate(edges)
        if dx and x + dx >= distance
    ]
    circuit.append("OBSERVABLE_INCLUDE", [rec(5 * i) for i in seam_edges], 0)
    circuit.append("OBSERVABLE_INCLUDE", [rec(5 * i + 1) for i in seam_edges], 1)
    return circuit


def build_bulk_component_memory(
    distance: int,
    table: FusionEventTable,
    *,
    component: str = "xx",
    missed_erasure_fraction: float = 0.0,
    channel_profile: str = "uniform_marginal",
) -> stim.Circuit:
    """Build one primal/dual component using the exact marginal channel.

    The published hardware-agnostic decoder treats the two syndrome graphs as
    separate matching problems.  This reduced circuit is therefore the main
    scalable benchmark; ``build_bulk_fusion_memory`` remains available for
    smaller paired-correlation checks.
    """
    if component not in {"xx", "zz"}:
        raise ValueError("component must be 'xx' or 'zz'")
    if channel_profile not in {"uniform_marginal", "six_ring_type_ii"}:
        raise ValueError("unknown channel_profile")
    if not 0 <= missed_erasure_fraction <= 1:
        raise ValueError("missed_erasure_fraction must lie in [0, 1]")
    uniform_wrong = table.xx_wrong_marginal if component == "xx" else table.zz_wrong_marginal
    uniform_erasure = table.xx_erasure_marginal if component == "xx" else table.zz_erasure_marginal

    graph_edges = bulk_edges(distance)
    circuit = stim.Circuit()
    measured: list[int] = []
    for edge_index, (_, _, direction) in enumerate(graph_edges):
        if channel_profile == "six_ring_type_ii":
            observable = six_ring_edge_observable(direction)
            if observable == "xx":
                p_wrong = table.xx_wrong_marginal
                p_erasure = table.xx_erasure_marginal
            else:
                p_wrong = table.zz_wrong_marginal
                p_erasure = table.zz_erasure_marginal
        else:
            p_wrong = uniform_wrong
            p_erasure = uniform_erasure
        if p_wrong + p_erasure > 1 + 1e-12:
            raise ValueError("component edge probabilities are inconsistent")
        outcome, flag, hidden = range(3 * edge_index, 3 * edge_index + 3)
        branches: list[tuple[float, list[stim.GateTarget]]] = []

        def add(probability: float, qubits: tuple[int, ...]) -> None:
            if probability > 0:
                branches.append((probability, [stim.target_x(q) for q in qubits]))

        add(p_wrong, (outcome,))
        flagged = p_erasure * (1.0 - missed_erasure_fraction)
        missed = p_erasure * missed_erasure_fraction
        add(flagged / 2.0, (flag,))
        add(flagged / 2.0, (outcome, flag))
        add(missed / 2.0, (hidden,))
        add(missed / 2.0, (outcome, hidden))
        if branches:
            _append_disjoint_channel(circuit, branches)
        measured.extend((outcome, flag))

    circuit.append("M", measured)
    record_index = {qubit: index for index, qubit in enumerate(measured)}
    record_count = len(measured)

    def rec(qubit: int) -> stim.GateTarget:
        return stim.target_rec(record_index[qubit] - record_count)

    incident: dict[Coord, list[int]] = {
        (x, y, z): []
        for x in range(distance)
        for y in range(distance)
        for z in range(distance)
    }
    for edge_index, (start, end, _) in enumerate(graph_edges):
        incident[start].append(edge_index)
        incident[end].append(edge_index)
    for coord in sorted(incident):
        circuit.append(
            "DETECTOR",
            [rec(3 * edge_index) for edge_index in incident[coord]],
        )
    for edge_index in range(len(graph_edges)):
        circuit.append("DETECTOR", [rec(3 * edge_index + 1)])
    seam_edges = [
        edge_index
        for edge_index, ((x, _, _), _, (dx, _, _)) in enumerate(graph_edges)
        if dx and x + dx >= distance
    ]
    circuit.append("OBSERVABLE_INCLUDE", [rec(3 * i) for i in seam_edges], 0)
    return circuit


def simulate_bulk_component_error(
    table: FusionEventTable,
    distance: int,
    shots: int,
    seed: int,
    *,
    component: str = "xx",
    missed_erasure_fraction: float = 0.0,
    channel_profile: str = "uniform_marginal",
) -> ComponentLogicalEstimate:
    if shots <= 0:
        raise ValueError("shots must be positive")
    circuit = build_bulk_component_memory(
        distance,
        table,
        component=component,
        missed_erasure_fraction=missed_erasure_fraction,
        channel_profile=channel_profile,
    )
    dem = circuit.detector_error_model(
        decompose_errors=True,
        approximate_disjoint_errors=True,
        ignore_decomposition_failures=False,
    )
    matching = pymatching.Matching.from_detector_error_model(
        dem, enable_correlations=True
    )
    detectors, observables = circuit.compile_detector_sampler(seed=seed).sample(
        shots,
        separate_observables=True,
        bit_packed=True,
    )
    predictions = matching.decode_batch(
        detectors,
        bit_packed_shots=True,
        bit_packed_predictions=True,
        enable_correlations=True,
    )
    failures = int(
        np.count_nonzero(
            np.unpackbits(predictions, axis=1, count=1, bitorder="little")
            != np.unpackbits(observables, axis=1, count=1, bitorder="little")
        )
    )
    low, high = wilson_interval(failures, shots)
    if channel_profile == "six_ring_type_ii":
        p_wrong_xx = table.xx_wrong_marginal
        p_wrong_zz = table.zz_wrong_marginal
        p_erasure_xx = table.xx_erasure_marginal
        p_erasure_zz = table.zz_erasure_marginal
        p_wrong = (p_wrong_xx + p_wrong_zz) / 2.0
        p_erasure = (p_erasure_xx + p_erasure_zz) / 2.0
        model_label = "periodic six-ring bulk graph with XX-axis/ZZ-diagonal channels"
    else:
        p_wrong = table.xx_wrong_marginal if component == "xx" else table.zz_wrong_marginal
        p_erasure = table.xx_erasure_marginal if component == "xx" else table.zz_erasure_marginal
        p_wrong_xx = p_wrong_zz = p_wrong
        p_erasure_xx = p_erasure_zz = p_erasure
        model_label = "periodic 12-valent six-ring bulk syndrome-graph proxy"
    return ComponentLogicalEstimate(
        distance=distance,
        component=component,
        shots=shots,
        failures=failures,
        logical_error_rate=failures / shots,
        ci_low=low,
        ci_high=high,
        p_wrong=p_wrong,
        p_erasure=p_erasure,
        p_wrong_xx_edges=p_wrong_xx,
        p_wrong_zz_edges=p_wrong_zz,
        p_erasure_xx_edges=p_erasure_xx,
        p_erasure_zz_edges=p_erasure_zz,
        missed_erasure_fraction=missed_erasure_fraction,
        seed=seed,
        syndrome_vertices=distance**3,
        edges=len(bulk_edges(distance)),
        vertex_degree=12,
        model_label=model_label,
    )


def simulate_bulk_logical_error(
    table: FusionEventTable,
    distance: int,
    shots: int,
    seed: int,
    *,
    missed_erasure_fraction: float = 0.0,
) -> BulkLogicalEstimate:
    if shots <= 0:
        raise ValueError("shots must be positive")
    circuit = build_bulk_fusion_memory(
        distance,
        table,
        missed_erasure_fraction=missed_erasure_fraction,
    )
    dem = circuit.detector_error_model(
        decompose_errors=True,
        approximate_disjoint_errors=True,
        ignore_decomposition_failures=False,
    )
    matching = pymatching.Matching.from_detector_error_model(
        dem, enable_correlations=True
    )
    detectors, observables = circuit.compile_detector_sampler(seed=seed).sample(
        shots,
        separate_observables=True,
        bit_packed=True,
    )
    predictions = matching.decode_batch(
        detectors,
        bit_packed_shots=True,
        bit_packed_predictions=True,
        enable_correlations=True,
    )
    predicted_bits = np.unpackbits(
        predictions, axis=1, count=2, bitorder="little"
    ).astype(bool)
    observed_bits = np.unpackbits(
        observables, axis=1, count=2, bitorder="little"
    ).astype(bool)
    disagreements = predicted_bits != observed_bits
    failures_xx = int(np.count_nonzero(disagreements[:, 0]))
    failures_zz = int(np.count_nonzero(disagreements[:, 1]))
    failures_any = int(np.count_nonzero(np.any(disagreements, axis=1)))
    low, high = wilson_interval(failures_any, shots)
    edge_count = len(bulk_edges(distance))
    return BulkLogicalEstimate(
        distance=distance,
        shots=shots,
        failures_any=failures_any,
        failures_xx=failures_xx,
        failures_zz=failures_zz,
        logical_error_rate_any=failures_any / shots,
        logical_error_rate_xx=failures_xx / shots,
        logical_error_rate_zz=failures_zz / shots,
        ci_low=low,
        ci_high=high,
        missed_erasure_fraction=missed_erasure_fraction,
        seed=seed,
        syndrome_vertices_per_component=distance**3,
        edges_per_component=edge_count,
        vertex_degree=12,
        model_label="periodic 12-valent six-ring bulk syndrome-graph proxy",
    )
