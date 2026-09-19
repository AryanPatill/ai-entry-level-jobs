"""Smoke test: the environment has the right Python and working packages."""
import sys

import numpy as np
import pandas as pd
import pyarrow
import pytest


def test_python_version():
    assert sys.version_info[:2] == (3, 12), f"Expected 3.12, got {sys.version}"


def test_ipumspy_pins_hold():
    # ipumspy 0.8.2 requires these bounds; a silent upgrade would break it.
    assert int(pd.__version__.split(".")[0]) < 3
    assert int(pyarrow.__version__.split(".")[0]) < 24


@pytest.mark.parametrize(
    "module",
    ["scipy", "duckdb", "ipumspy", "pyfixest", "linearmodels",
     "statsmodels", "wildboottest", "matplotlib", "yaml", "dotenv"],
)
def test_imports(module):
    __import__(module)


def test_pyfixest_runs_a_regression():
    # Tiny fake data with a known slope of 2, to confirm the compiled code works.
    import pyfixest as pf

    rng = np.random.default_rng(0)
    n = 500
    df = pd.DataFrame({
        "x": rng.normal(size=n),
        "g": rng.integers(0, 10, size=n),
    })
    df["y"] = 2.0 * df["x"] + df["g"] * 0.5 + rng.normal(scale=0.1, size=n)

    fit = pf.feols("y ~ x | g", data=df, vcov={"CRV1": "g"})
    assert abs(fit.coef()["x"] - 2.0) < 0.05