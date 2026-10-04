"""Resolves the plan's [verify]: pyfixest fepois handles Poisson with three interacted fixed
effects, with and without weights, matching a dummy-variable GLM (synthetic data only)."""
import numpy as np
import pandas as pd
import pyfixest as pf
import pytest
import statsmodels.api as sm
import statsmodels.formula.api as smf


@pytest.mark.parametrize("weights", [None, "w"])
def test_fepois_three_way_fe_matches_glm(weights):
    rng = np.random.default_rng(0)
    df = pd.MultiIndex.from_product([range(12), range(3), range(10)], names=["o", "a", "t"]).to_frame(index=False)
    df["d"] = ((df.o >= 8) & (df.a == 0) & (df.t >= 5)).astype(int)
    mu = np.exp(1 + 0.3 * df.o / 12 + 0.2 * df.a + 0.05 * df.t + 0.02 * df.o * df.t / 12 - 0.2 * df.d)
    df["y"], df["w"] = rng.poisson(mu * 20), rng.uniform(0.5, 2, len(df))

    fx = pf.fepois("y ~ d | o^a + o^t + a^t", data=df, weights=weights, vcov={"CRV1": "o"})
    glm = smf.glm("y ~ d + C(o):C(a) + C(o):C(t) + C(a):C(t)", data=df, family=sm.families.Poisson(),
                  freq_weights=None if weights is None else df[weights]).fit()
    assert fx.coef()["d"] == pytest.approx(glm.params["d"], abs=1e-6)
