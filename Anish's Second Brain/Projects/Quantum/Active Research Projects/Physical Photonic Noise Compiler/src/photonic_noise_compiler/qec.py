"""Fixed paired-component QEC harness for compiled fusion channels.

The graph preserves the local six-ring bulk facts used by this project: each
component is a periodic 12-valent cubic-with-face-diagonals graph, axis edges
carry XX outcomes, diagonal edges carry ZZ outcomes, and each physical fusion
pairs one XX edge with one ZZ edge across the two components.  The exact
half-cell geometric crossing map and planar logical boundaries are not modeled.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import product
from math import sqrt

import numpy as np
import pymatching
import stim

from .schema import CompiledChannel, OutcomeBranch


Coord = tuple[int, int, int]
Direction = tuple[int, int, int]
Edge = tuple[Coord, Coord, Direction]
FusionPair = tuple[int, int, str, str]


@dataclass(frozen=True)
class LogicalEstimate:
    distance: int
    shots: int
    failures_any: int
    failures_a: int
    failures_b: int
    failures_both: int
    logical_error_rate_any: float
    logical_error_rate_a: float
    logical_error_rate_b: float
    logical_error_rate_both: float
    any_ci_low: float
    any_ci_high: float
    failure_phi: float
    seed: int
    channel_name: str
    decoder_channel_name: str
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
    edges: list[Edge] = []
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
                    edges.append((start, end, (dx, dy, dz)))
    return edges


def edge_observable(direction: Direction) -> str:
    nonzero = sum(value != 0 for value in direction)
    if nonzero == 1:
        return "XX"
    if nonzero == 2:
        return "ZZ"
    raise ValueError(f"invalid six-ring edge direction {direction}")


def fusion_pairs(distance: int) -> list[FusionPair]:
    """Pair every edge across components with the opposite observable kind.

    Each tuple is ``(edge_a, edge_b, target_on_a, target_on_b)``.  The pairing
    is a deterministic bulk proxy, not the published half-cell crossing map.
    """
    edges = bulk_edges(distance)
    axes = [i for i, edge in enumerate(edges) if edge_observable(edge[2]) == "XX"]
    diagonals = [i for i, edge in enumerate(edges) if edge_observable(edge[2]) == "ZZ"]
    if len(axes) != len(diagonals):
        raise RuntimeError("six-ring bulk edge classes are unbalanced")
    pairs = [
        (axis, diagonal, "XX", "ZZ")
        for axis, diagonal in zip(axes, diagonals, strict=True)
    ]
    pairs.extend(
        (diagonal, axis, "ZZ", "XX")
        for diagonal, axis in zip(diagonals, axes, strict=True)
    )
    return pairs


def _expand_branch(
    branch: OutcomeBranch,
    outcome_qubits: dict[str, int],
    flag_qubits: dict[str, int],
) -> list[tuple[float, list[stim.GateTarget]]]:
    if branch.leakages:
        raise ValueError(
            "paired type-II harness has no validated leakage-to-Pauli reduction"
        )
    if any(target not in {"XX", "ZZ"} for target in (*branch.flips, *branch.erasures)):
        raise ValueError("paired type-II harness supports only XX and ZZ targets")
    erased = tuple(branch.erasures)
    randomizations = product((0, 1), repeat=len(erased))
    expanded: list[tuple[float, list[stim.GateTarget]]] = []
    for random_bits in randomizations:
        qubits = [outcome_qubits[target] for target in branch.flips]
        qubits.extend(flag_qubits[target] for target in erased)
        qubits.extend(
            outcome_qubits[target]
            for target, bit in zip(erased, random_bits, strict=True)
            if bit
        )
        probability = branch.probability / (2 ** len(erased))
        if probability > 0.0 and qubits:
            expanded.append((probability, [stim.target_x(qubit) for qubit in qubits]))
    return expanded


def _append_disjoint_channel(
    circuit: stim.Circuit,
    branches: list[tuple[float, list[stim.GateTarget]]],
) -> None:
    consumed = 0.0
    for index, (probability, targets) in enumerate(branches):
        remaining = 1.0 - consumed
        if remaining <= 0.0:
            raise ValueError("nontrivial event branches consume all probability")
        conditional = probability / remaining
        circuit.append(
            "CORRELATED_ERROR" if index == 0 else "ELSE_CORRELATED_ERROR",
            targets,
            conditional,
        )
        consumed += probability


def _independent_target_branches(
    channel: CompiledChannel,
    target: str,
    outcome_qubit: int,
    flag_qubit: int,
) -> list[tuple[float, list[stim.GateTarget]]]:
    """Compile one categorical correct/flip/erasure target independently."""
    p_flip = channel.marginal("flip", target)
    p_erasure = channel.marginal("erasure", target)
    if p_flip + p_erasure > 1.0 + 1e-12:
        raise ValueError(f"invalid independent marginal for {target}")
    result: list[tuple[float, list[stim.GateTarget]]] = []
    if p_flip > 0.0:
        result.append((p_flip, [stim.target_x(outcome_qubit)]))
    if p_erasure > 0.0:
        result.append((p_erasure / 2.0, [stim.target_x(flag_qubit)]))
        result.append(
            (
                p_erasure / 2.0,
                [stim.target_x(outcome_qubit), stim.target_x(flag_qubit)],
            )
        )
    return result


def build_paired_bulk_memory(distance: int, channel: CompiledChannel) -> stim.Circuit:
    """Compile a channel into two paired periodic syndrome components."""
    edges = bulk_edges(distance)
    pairs = fusion_pairs(distance)
    circuit = stim.Circuit()
    measured: list[int] = []
    edge_records: dict[str, dict[int, tuple[int, int]]] = {"a": {}, "b": {}}

    for fusion_index, (edge_a, edge_b, target_a, target_b) in enumerate(pairs):
        base = 4 * fusion_index
        outcome_xx, outcome_zz, flag_xx, flag_zz = range(base, base + 4)
        outcome_qubits = {"XX": outcome_xx, "ZZ": outcome_zz}
        flag_qubits = {"XX": flag_xx, "ZZ": flag_zz}
        is_independent = channel.correlations == (
            "all cross-target correlations removed",
        )
        if is_independent:
            for target in ("XX", "ZZ"):
                target_branches = _independent_target_branches(
                    channel,
                    target,
                    outcome_qubits[target],
                    flag_qubits[target],
                )
                if target_branches:
                    _append_disjoint_channel(circuit, target_branches)
        else:
            expanded: list[tuple[float, list[stim.GateTarget]]] = []
            for branch in channel.branches:
                expanded.extend(_expand_branch(branch, outcome_qubits, flag_qubits))
            if expanded:
                _append_disjoint_channel(circuit, expanded)
        measured.extend((outcome_xx, outcome_zz, flag_xx, flag_zz))
        edge_records["a"][edge_a] = (
            outcome_qubits[target_a],
            flag_qubits[target_a],
        )
        edge_records["b"][edge_b] = (
            outcome_qubits[target_b],
            flag_qubits[target_b],
        )

    if any(len(edge_records[component]) != len(edges) for component in ("a", "b")):
        raise RuntimeError("fusion pairing did not cover every component edge exactly once")

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
    if set(map(len, incident.values())) != {12}:
        raise RuntimeError("bulk component is not 12-valent")

    for component in ("a", "b"):
        for coord in sorted(incident):
            circuit.append(
                "DETECTOR",
                [
                    rec(edge_records[component][edge_index][0])
                    for edge_index in incident[coord]
                ],
            )
        for edge_index in range(len(edges)):
            circuit.append("DETECTOR", [rec(edge_records[component][edge_index][1])])

    seam_edges = [
        edge_index
        for edge_index, ((x, _, _), _, (dx, _, _)) in enumerate(edges)
        if dx and x + dx >= distance
    ]
    for observable, component in enumerate(("a", "b")):
        circuit.append(
            "OBSERVABLE_INCLUDE",
            [rec(edge_records[component][edge_index][0]) for edge_index in seam_edges],
            observable,
        )
    return circuit


def simulate_logical_error(
    channel: CompiledChannel,
    distance: int,
    shots: int,
    seed: int,
    *,
    decoder_channel: CompiledChannel | None = None,
) -> LogicalEstimate:
    if shots <= 0:
        raise ValueError("shots must be positive")
    circuit = build_paired_bulk_memory(distance, channel)
    decoder_channel = decoder_channel or channel
    decoder_circuit = build_paired_bulk_memory(distance, decoder_channel)
    if (
        circuit.num_detectors != decoder_circuit.num_detectors
        or circuit.num_observables != decoder_circuit.num_observables
    ):
        raise ValueError("sampler and decoder channels produced incompatible circuits")
    dem = decoder_circuit.detector_error_model(
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
    actual = np.unpackbits(observables, axis=1, count=2, bitorder="little")
    predicted = np.unpackbits(predictions, axis=1, count=2, bitorder="little")
    failures = predicted != actual
    failed_a = failures[:, 0]
    failed_b = failures[:, 1]
    failed_any = failed_a | failed_b
    failed_both = failed_a & failed_b
    count_a = int(np.count_nonzero(failed_a))
    count_b = int(np.count_nonzero(failed_b))
    count_any = int(np.count_nonzero(failed_any))
    count_both = int(np.count_nonzero(failed_both))
    low, high = wilson_interval(count_any, shots)
    variance_a = float(np.var(failed_a))
    variance_b = float(np.var(failed_b))
    phi = (
        float(np.cov(failed_a, failed_b, ddof=0)[0, 1] / sqrt(variance_a * variance_b))
        if variance_a > 0.0 and variance_b > 0.0
        else 0.0
    )
    return LogicalEstimate(
        distance=distance,
        shots=shots,
        failures_any=count_any,
        failures_a=count_a,
        failures_b=count_b,
        failures_both=count_both,
        logical_error_rate_any=count_any / shots,
        logical_error_rate_a=count_a / shots,
        logical_error_rate_b=count_b / shots,
        logical_error_rate_both=count_both / shots,
        any_ci_low=low,
        any_ci_high=high,
        failure_phi=phi,
        seed=seed,
        channel_name=channel.name,
        decoder_channel_name=decoder_channel.name,
        model_label=(
            "paired periodic 12-valent six-ring bulk proxy; local XX/ZZ edge "
            "semantics exact, cross-component edge pairing approximate"
        ),
    )
