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


def test_outcome_columns_are_consistent():
    # Accounting identities only; asserts, never prints, so no outcome is seen.
    c = pd.read_parquet(PANEL, columns=["emp_w", "emp_w_men", "emp_w_women", "emp_w_ba", "emp_w_private",
                                        "emp_w_fulltime", "hours_w", "hours_wsum", "unemp_w", "n_unemp"])
    assert (c.emp_w_men + c.emp_w_women - c.emp_w).abs().max() < 1e-6 * c.emp_w.max()
    for sub in ("emp_w_ba", "emp_w_private", "emp_w_fulltime", "hours_w"):
        assert (c[sub] <= c.emp_w + 1e-6).all(), sub
    pos = c.hours_w > 0
    assert ((c.hours_wsum[pos] / c.hours_w[pos]).between(1, 168)).all()
    assert ((c.unemp_w > 0) == (c.n_unemp > 0)).all()


def test_one_quintile_per_occupation(p):
    assert p.groupby("occ2010").quintile.nunique().eq(1).all()
    assert set(p.quintile) == {1, 2, 3, 4, 5}
