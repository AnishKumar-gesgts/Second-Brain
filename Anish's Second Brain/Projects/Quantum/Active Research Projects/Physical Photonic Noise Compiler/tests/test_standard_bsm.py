import numpy as np
import pytest

from photonic_noise_compiler.adapters.heralded_source import HeraldedSourceParameters
from photonic_noise_compiler.adapters.standard_bsm import (
    _two_mode_bs_amplitudes,
    compile_standard_bsm,
    remote_density_for_record,
)


def test_hong_ou_mandel_cancels_split_output() -> None:
    amplitudes = _two_mode_bs_amplitudes(1, 1)
    assert (1, 1) not in amplitudes
    assert sum(abs(value) ** 2 for value in amplitudes.values()) == pytest.approx(1.0)


def test_remote_record_density_is_positive_semidefinite() -> None:
    density = remote_density_for_record(2, 1, 0.85, (1, 0, 0, 1))
    assert np.trace(density).real >= 0.0
    assert np.min(np.linalg.eigvalsh(density)) >= -1e-12


def test_ideal_standard_bsm_has_half_full_and_half_partial_outcomes() -> None:
    result = compile_standard_bsm(
        HeraldedSourceParameters(0.1, 1.0, 1.0),
        detector_efficiency=1.0,
        name="ideal_bsm",
    )
    assert result.probability_full_success == pytest.approx(0.5)
    assert result.probability_partial_failure == pytest.approx(0.5)
    assert result.probability_count_rejection == pytest.approx(0.0, abs=1e-12)
    assert result.full_success_hidden_error_probability == pytest.approx(0.0, abs=1e-12)


def test_multiphoton_loss_creates_hidden_full_bsm_error() -> None:
    result = compile_standard_bsm(
        HeraldedSourceParameters(0.2, 0.99, 0.85),
        detector_efficiency=0.85,
        name="nonideal_bsm",
    )
    assert result.accepted_error_given_full_success > 0.0
    assert result.channel.marginal("flip", "XX") > 0.0
    assert result.channel.marginal("flip", "ZZ") > 0.0
    assert result.channel.total_probability == pytest.approx(1.0)
    assert result.max_full_bell_coherence == pytest.approx(0.0, abs=1e-12)


def test_decoder_export_hides_source_number_history() -> None:
    result = compile_standard_bsm(
        HeraldedSourceParameters(0.2, 0.99, 0.85),
        detector_efficiency=0.85,
        name="privacy_bsm",
    )
    assert "hidden_source_number_history" not in str(
        result.channel.decoder_distribution()
    )
