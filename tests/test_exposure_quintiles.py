"""Pins the weighted-quintile rule (Section 5) on synthetic data; needs no raw files."""
import pandas as pd

from src.crosswalks.exposure_quintiles import assign, cutoffs


def test_equal_weights_ten_occupations():
    score = pd.Series([float(i) for i in range(10, 0, -1)])   # unsorted on purpose
    cuts = cutoffs(score, pd.Series([1.0] * 10))
    assert cuts == [2.0, 4.0, 6.0, 8.0]                        # 2 occupations per quintile
    assert list(assign(pd.Series([1.0, 2.0, 2.1, 8.0, 10.0]), cuts)) == [1, 1, 2, 4, 5]


def test_weights_not_counts_set_the_cutoffs():
    # One heavy occupation holds 60% of employment: it fills Q1-Q3 by itself.
    score, w = pd.Series([1.0, 2.0, 3.0]), pd.Series([60.0, 20.0, 20.0])
    cuts = cutoffs(score, w)
    assert cuts == [1.0, 1.0, 1.0, 2.0]
    assert list(assign(score, cuts)) == [1, 4, 5]
