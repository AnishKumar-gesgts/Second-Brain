import pytest

from photonic_noise_compiler.schema import CompiledChannel, OutcomeBranch


def _correlated_erasure_channel() -> CompiledChannel:
    return CompiledChannel(
        name="test",
        adapter="test_adapter",
        adapter_version="1",
        primitive="two-outcome primitive",
        branches=(
            OutcomeBranch(0.7, physical_event="correct"),
            OutcomeBranch(0.1, flips=("ZZ",), physical_event="wrong"),
            OutcomeBranch(
                0.2,
                erasures=("XX", "ZZ"),
                heralds=("erasure:XX", "erasure:ZZ"),
                physical_event="loss",
                latent_tags=("hidden_photon_number",),
            ),
        ),
    )


def test_channel_conserves_probability() -> None:
    assert _correlated_erasure_channel().total_probability == pytest.approx(1.0)
    with pytest.raises(ValueError, match="sum"):
        CompiledChannel(
            name="bad",
            adapter="bad",
            adapter_version="1",
            primitive="bad",
            branches=(OutcomeBranch(0.5),),
        )


def test_decoder_view_does_not_leak_fault_truth_or_hidden_labels() -> None:
    exported = _correlated_erasure_channel().decoder_distribution()
    serialized = str(exported)
    assert "physical_event" not in serialized
    assert "latent" not in serialized
    assert "hidden_photon_number" not in serialized
    assert "flips" not in serialized
    assert "leakages" not in serialized


def test_unheralded_erasure_is_hidden_from_decoder() -> None:
    branch = OutcomeBranch(
        1.0,
        erasures=("signal",),
        heralds=("idler_one_count",),
        physical_event="vacuum_despite_valid_source_herald",
    )
    assert branch.simulation_view()["erasures"] == ["signal"]
    assert branch.decoder_view()["erasures"] == []


def test_leakage_is_preserved_in_truth_but_hidden_from_decoder() -> None:
    branch = OutcomeBranch(
        1.0,
        leakages=("signal",),
        heralds=("idler_one_count",),
        physical_event="multiphoton_despite_valid_source_herald",
    )
    assert branch.target_state("signal") == "leaked"
    assert branch.simulation_view()["leakages"] == ["signal"]
    assert "leakages" not in branch.decoder_view()


def test_independent_approximation_preserves_marginals_but_removes_correlation() -> None:
    channel = _correlated_erasure_channel()
    independent = channel.independent_target_approximation()
    for target in ("XX", "ZZ"):
        assert independent.marginal("erasure", target) == pytest.approx(
            channel.marginal("erasure", target)
        )
        assert independent.marginal("flip", target) == pytest.approx(
            channel.marginal("flip", target)
        )
    assert channel.mutual_information_bits("erasure", "XX", "ZZ") > 0
    assert independent.mutual_information_bits(
        "erasure", "XX", "ZZ"
    ) == pytest.approx(0.0, abs=1e-12)
    assert channel.total_variation_from(independent) > 0


def test_round_trip_preserves_channel() -> None:
    channel = _correlated_erasure_channel()
    restored = CompiledChannel.from_dict(channel.to_dict())
    assert restored == channel
