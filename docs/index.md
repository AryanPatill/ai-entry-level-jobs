# Documentation index

Every fact has one home. Before writing something down, find its file here.
If a fact would fit two files, it belongs in the one higher in this list, and the
other file links to it.

| File | Holds | Does not hold |
|---|---|---|
| `preregistration.md` | The research design: sample, outcomes, estimators, robustness checks, decision rules. Written before results. Numbered Sections 1-19. | Anything learned after the design was fixed |
| `deviations.md` | Every departure from the preregistration, with date and reason | Facts that are not departures |
| `design_notes.md` | Facts learned from the data or the sources, and interpretations that the preregistration left open | Design changes (those are deviations) |
| `decisions.md` | Choices made about how to build the project: tools, versions, formats, conventions | Research design choices (preregistration) |
| `architecture.md` | Repository layout, data flow, module responsibilities, how to run each stage | Results, or why a design choice was made |
| `plan.md` | Phase list, current position, next step | Detail about how any phase works |
| `data_dictionary.md` | Every variable in the analysis data: source, universe, codes, how it is used | Analysis results |

## Rules

1. `preregistration.md` changes only to fill blanks it told us to fill (for example the
   data pull date). Every other change is a deviation and needs a row in `deviations.md`
   and a row in the preregistration's own Section 19 change log.
2. `plan.md` is updated at the end of every phase step, before the commit.
3. Results (numbers, tables, figures) live in `results/`, never in these documents.
   These documents may describe what was run, not what it showed, until the analysis
   phases begin.
4. Anything unverified is marked `[verify]`. Anything undecided is marked `TBD` and is
   decided by Aryan, never filled in by an assistant.
