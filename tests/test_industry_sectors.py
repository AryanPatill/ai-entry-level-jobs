"""Pins the preregistered sector mapping (Section 15, Rule A) so it cannot drift."""
import pytest

from src.crosswalks.industry_sectors import TECH_AND_FINANCE_SECTORS, sector_for


@pytest.mark.parametrize("code, expected", [
    (0, None),                                      # NIU
    (732, 1), (441, 1), (882, 1), (892, 1),         # core sector 1
    (171, 1), (800, 1), (852, 1), (12, 1),          # Rule A moves into sector 1
    (841, 1),                                       # legal: inside 812-871 but sector 1
    (700, 2), (712, 2),
    (172, 3), (351, 3), (392, 3),                   # 172 is mixed, stays manufacturing
    (500, 4), (601, 4), (691, 4), (600, 4),         # 600 exists only before 2020
    (641, 6),                                       # restaurants: Rule A, not retail
    (812, 5), (831, 5), (842, 5), (871, 5),
    (60, 6), (410, 6), (731, 6), (872, 6), (910, 6), (952, 6),
])
def test_sector_for(code, expected):
    assert sector_for(code) == expected


def test_tech_and_finance_is_sectors_1_and_2():
    assert TECH_AND_FINANCE_SECTORS == {1, 2}