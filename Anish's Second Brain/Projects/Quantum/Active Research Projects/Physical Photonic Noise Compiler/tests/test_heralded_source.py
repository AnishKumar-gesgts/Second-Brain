import pytest

from photonic_noise_compiler.adapters.heralded_source import (
    HeraldedSourceParameters,
    compile_heralded_source,
    conditional_signal_probability,
    one_count_herald_probability,
)


def test_perfect_idler_selects_one_generated_pair() -> None:
    parameters = HeraldedSourceParameters(0.1, 0.8, 1.0)
    assert conditional_signal_probability(0, parameters) == pytest.approx(0.2)
    assert conditional_signal_probability(1, parameters) == pytest.approx(0.8)
    assert conditional_signal_probability(2, parameters) == 0.0


def test_closed_form_distribution_normalizes_with_small_tail() -> None:
    parameters = HeraldedSourceParameters(0.2, 0.91, 0.87)
    total = sum(conditional_signal_probability(n, parameters) for n in range(30))
    assert total == pytest.approx(1.0, abs=1e-12)


def test_herald_probability_matches_direct_pair_sum() -> None:
    parameters = HeraldedSourceParameters(0.15, 0.9, 0.82)
    mu = parameters.pair_probability
    eta = parameters.idler_efficiency
    direct = sum(
        (1 - mu) * mu**k * k * eta * (1 - eta) ** (k - 1)
        for k in range(1, 100)
    )
    assert one_count_herald_probability(parameters) == pytest.approx(direct)


def test_compiler_hides_false_herald_histories() -> None:
    channel = compile_heralded_source(
        HeraldedSourceParameters(0.2, 0.9, 0.8),
        name="source_test",
    )
    decoder_records = channel.decoder_distribution()
    assert decoder_records == [
        {
            "probability": pytest.approx(1.0),
            "erasures": [],
            "heralds": ["source_idler_one_count"],
        }
    ]
    assert channel.marginal("erasure", "source_signal") > 0.0
    assert channel.marginal("leakage", "source_signal") > 0.0


def test_cutoff_tail_is_retained_as_leakage() -> None:
    channel = compile_heralded_source(
        HeraldedSourceParameters(0.4, 0.8, 0.7),
        name="tail_test",
        photon_cutoff=2,
    )
    assert channel.total_probability == pytest.approx(1.0)
    assert any(
        any("cutoff_tail" in tag for tag in branch.latent_tags)
        for branch in channel.branches
    )
