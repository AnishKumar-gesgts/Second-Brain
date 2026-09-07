import pytest

from temporal_filter_qec.fusion_events import (
    compile_fusion_events,
    compile_type_ii_detuning_events,
)
from temporal_filter_qec.physics import PhysicalParameters, event_table


PARAMS = PhysicalParameters(60.0, 15.0, 1.2, 0.995)


def test_fusion_event_schema_conserves_probability() -> None:
    scalar = event_table(PARAMS, 140.0)
    fusion = compile_fusion_events(
        scalar,
        wrong_xx_fraction=0.2,
        wrong_zz_fraction=0.3,
        wrong_xx_zz_fraction=0.5,
        intrinsic_failure_probability=0.1,
    )
    assert fusion.total == pytest.approx(1.0)
    assert fusion.accepted_wrong == pytest.approx(0.9 * scalar.accepted_wrong)
    assert fusion.erasure_xx == pytest.approx(0.05 * scalar.acceptance)
    assert fusion.erasure_zz == pytest.approx(0.05 * scalar.acceptance)
    assert fusion.full_erasure == pytest.approx(scalar.erasure)


def test_invalid_wrong_outcome_split_is_rejected() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        compile_fusion_events(
            event_table(PARAMS, None),
            wrong_xx_fraction=0.5,
            wrong_zz_fraction=0.5,
            wrong_xx_zz_fraction=0.5,
        )


def test_type_ii_detuning_is_zz_only() -> None:
    scalar = event_table(PARAMS, 140.0)
    fusion = compile_type_ii_detuning_events(scalar)
    assert fusion.wrong_xx == 0.0
    assert fusion.wrong_zz == pytest.approx(scalar.accepted_wrong)
    assert fusion.wrong_xx_zz == 0.0
    assert fusion.full_erasure == pytest.approx(scalar.erasure)
