import pytest

from temporal_filter_qec.fock import balanced_beamsplitter_validation


@pytest.mark.parametrize("cutoff", [3, 4])
def test_hong_ou_mandel_limit_and_cutoff(cutoff: int) -> None:
    result = balanced_beamsplitter_validation(cutoff)
    assert result.p_20 == pytest.approx(0.5, abs=1e-9)
    assert result.p_02 == pytest.approx(0.5, abs=1e-9)
    assert result.p_11 == pytest.approx(0.0, abs=1e-9)
    assert result.probability_sum == pytest.approx(1.0, abs=1e-9)

