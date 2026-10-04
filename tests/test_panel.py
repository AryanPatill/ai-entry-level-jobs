"""Structure of the analysis panel (Phase 5). Reads only keys and flags, never the outcome.
Skipped where the panel has not been built (data/ is never committed)."""
import pandas as pd
import pytest

from src.utils.config import load_settings

PANEL = load_settings()["paths"]["processed"] / "panel_occ_age_month.parquet"
pytestmark = pytest.mark.skipif(not PANEL.exists(), reason="panel not built")


@pytest.fixture(scope="module")
def p():
    return pd.read_parquet(PANEL, columns=["occ2010", "age_group", "ym", "quintile", "pandemic", "main_sample", "post"])


def test_balanced_and_unique(p):
    assert not p.duplicated(["occ2010", "age_group", "ym"]).any()
    assert len(p) == p.occ2010.nunique() * p.age_group.nunique() * p.ym.nunique()
    assert set(p.age_group) == {"22-25", "26-34", "35-49", "50-64"}
    assert p.ym.nunique() == 187 and 202510 not in set(p.ym)


def test_flags_follow_settings(p):
    assert not (p.main_sample & p.pandemic).any()
    assert p.loc[p.main_sample, "ym"].min() == 201501
    assert p.loc[p.pandemic, "ym"].agg(["min", "max"]).tolist() == [202003, 202112]
    assert p.loc[p.post, "ym"].min() == 202212


def test_one_quintile_per_occupation(p):
    assert p.groupby("occ2010").quintile.nunique().eq(1).all()
    assert set(p.quintile) == {1, 2, 3, 4, 5}
