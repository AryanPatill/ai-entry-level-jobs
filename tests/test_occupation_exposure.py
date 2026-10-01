"""Pins the 2010 Census -> SOC 2018 crosswalk (Phase 4). Needs the three raw source files;
skipped where they are absent (they are never committed)."""
import itertools

import pytest

from src.crosswalks.occupation_exposure import build, read_structure, source_path

pytestmark = pytest.mark.skipif(
    not all(source_path(n)[0].exists() for n in ("occ_crosswalk", "soc_structure")),
    reason="raw crosswalk files not present (data/ is never committed)",
)

# Disagreements between Census title parentheticals and the structural expansion, reported
# in design_notes.md (2026-09-30) and awaiting Aryan's decision. Pinned so a NEW mismatch
# fails; none is patched. 2018 Census code -> (title-only codes, expansion-only codes).
KNOWN_TITLE_MISMATCHES = {
    "8865": ((), ("51-9199",)),
    "8990": (("51-9199",), ()),
    "9570": (("53-7065",), ()),
}


@pytest.fixture(scope="module")
def b():
    return build()


def test_residual_groups_disjoint_and_covered(b):
    fails = []
    for code, soc in b["census_soc"].items():
        if "X" not in soc.upper():
            continue
        prefix = soc.upper().split("X")[0]
        region = {d for d in b["detailed"] if d.startswith(prefix)}
        owners = {c: s & region for c, s in b["census_detail"].items() if s & region}
        overlaps = [(x, y) for x, y in itertools.combinations(owners, 2) if owners[x] & owners[y]]
        uncovered = region - set().union(*owners.values())
        if overlaps or uncovered:
            fails.append((code, soc, overlaps, sorted(uncovered)))
    assert not fails, f"residual groups failing: {fails}"


def test_title_parentheticals_match_expansion(b):
    _, groups = read_structure()
    found = {}
    for code, named in b["title_codes"].items():
        named = set().union(*(groups.get(s, {s}) for s in named))   # a title may cite a broad group
        got = b["census_detail"].get(code, set())
        if named != got:
            found[code] = (tuple(sorted(named - got)), tuple(sorted(got - named)))
    assert found == KNOWN_TITLE_MISMATCHES


def test_main_sheet_half_rows_are_in_code_changes(b):
    main, ch = b["main"], b["changes"]
    b_only = set(main.loc[main.census2010.isna() & main.census2018.notna(), "census2018"])
    a_only = set(main.loc[main.census2010.notna() & main.census2018.isna(), "census2010"])
    assert b_only <= set(ch.census2018)
    assert a_only <= set(ch.census2010)


def test_merge_continuations_named_in_note(b):
    mc = b["changes"][b["changes"].merge_continuation]
    assert len(mc) == 28
    assert all(c in note for c, note in zip(mc.census2010, mc.note))


@pytest.mark.parametrize("census2010, census2018, soc", [
    ("1010", "1010", "15-1251"),                    # computer programmers, unchanged
    ("1020", "1021 1022", "15-1252 15-1253"),       # software developers: split
    ("0050", "0051 0052", "11-2021 11-2022"),       # marketing and sales managers: split
    ("3850", "3870", "33-3051 33-3052"),            # police: merge into broad group 33-3050
    ("0740", "0705 0750", "13-1082 13-1199"),       # business ops specialists: split
])
def test_hand_checked_codes(b, census2010, census2018, soc):
    row = b["occ_map"].set_index("census2010").loc[census2010]
    assert (row.census2018, row.soc2018) == (census2018, soc)


def test_only_military_and_never_worked_unresolved(b):
    assert b["unresolved"] == {"9830": "none", "9920": "none"}
