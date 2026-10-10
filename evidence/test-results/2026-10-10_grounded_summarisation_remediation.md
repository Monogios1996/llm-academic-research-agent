# Grounded summarisation remediation

Date: 2026-10-10

## Live finding

A repeat live fallback run passed relevance filtering and sentence-safe
truncation, but review identified a grounding defect in one LLM-generated
summary. The generated summary introduced named benchmark acronyms that were
not present in the retrieved source evidence.

A second weaker case also inferred likely benchmark content from a title when
the record had no abstract.

Because the system is intended to produce traceable academic evidence, these
were treated as genuine output-quality defects rather than acceptable model
variation.

## Remediation

The evidence summariser now applies three safeguards:

1. **No-abstract deterministic path.** When a retrieved record has no abstract,
   the LLM is not called. The system returns a deterministic limitation
   statement explaining that specific methods, metrics, datasets, findings,
   and conclusions cannot be established from the retrieved evidence.

2. **Stronger grounding instruction.** For records with abstracts, the prompt
   explicitly forbids introducing named benchmarks, datasets, models,
   organisations, acronyms, metric names, or numeric values unless they are
   present in the supplied bibliographic evidence.

3. **High-confidence deterministic guard.** Generated summaries are checked for
   acronyms and numeric claims that do not occur in the retrieved record. If an
   unsupported high-risk term is detected, the generated text is discarded and
   replaced by a bounded extractive summary from the source abstract.

The guard is intentionally conservative rather than attempting to solve general
semantic hallucination detection. This keeps the behaviour inspectable and
testable while directly addressing the observed failure mode.

## Automated verification

New tests cover:

- bypassing the LLM and returning a limitation statement when no abstract is
  available;
- rejecting generated summaries that introduce unsupported benchmark acronyms;
- rejecting generated summaries that introduce unsupported numeric claims;
- the strengthened grounding constraints in the summarisation prompt.

Latest verified GitHub Actions result after the substantive change:

```
70 passed in 0.49s
```

A repeat live fallback run is required to confirm the behaviour under local
Qwen3 inference before this remediation is considered fully verified.


## First live verification failure after grounding change

The first live fallback verification after this remediation did not complete.
Automated tests passed locally (`70 passed`), but the live summarisation stage
raised:

```
TypeError: sequence item 4: expected str instance, HttpUrl found
```

The failure occurred in the new grounding guard while building a searchable
metadata string. Pydantic stores `AcademicRecord.url` as an `HttpUrl`
object, and the new guard attempted to join it directly with ordinary strings.

This was a genuine integration defect that the existing unit fixtures had not
exercised because they did not include a populated URL on the guarded path.

## HttpUrl remediation

The grounding guard now normalises each metadata component with `str(...)`
before joining it. A regression test was added with a real Pydantic
`HttpUrl` value to ensure the guarded summarisation path handles URL metadata
without failure.

Latest GitHub Actions result:

```
71 passed in 0.67s
```

The live fallback verification should now be repeated. The grounding
remediation remains unverified end-to-end until that run completes.


## Successful live verification

After the HttpUrl regression fix, the repeat controlled fallback workflow
completed successfully and reached the human-approval boundary.

Observed result:

- workflow status: `awaiting_approval`;
- local fallback enabled with `qwen3:4b`;
- six fallback calls in total;
- two Planner subtasks;
- five final evidence items after cross-subtask deduplication;
- three low-relevance records filtered from each subtask before summarisation;
- both validation stages passed;
- no export was performed.

The lower fallback-call count is expected because the FlowBench record had no
abstract and therefore used the deterministic no-abstract path without calling
the local LLM.

The live output confirmed the grounding safeguards:

- FlowBench produced an explicit limitation statement rather than inferred
  metrics or findings;
- the survey summary no longer introduced unsupported benchmark acronyms such
  as the previously observed LARC/RBLA examples;
- one generated summary triggered the high-confidence grounding guard and was
  replaced with a source-grounded abstract extract.

A preceding local run timed out while waiting for Ollama during the Planner
call. A direct `ollama run qwen3:4b` invocation succeeded, and the immediate
repeat workflow then completed. This is retained as an observed local-runtime
limitation rather than treated as a grounding-code defect.
