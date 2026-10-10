# Design and implementation documentation

This directory contains the design-to-implementation notes for the final
prototype.

- `final-system-overview.md` — final architecture, workflow, responsibilities,
  persistence, interface, and design-to-implementation mapping.
- `critical-evaluation.md` — design trade-offs, observed failures,
  remediation decisions, limitations, and future work.
- `orchestration-implementation.md` — bounded LangGraph control flow and
  validation/re-planning behaviour.
- `local-fallback.md` — hosted-to-local LLM failover design and live
  integration findings.
- `approval-export.md` — human approval boundary and guarded export design.

Execution evidence and chronological remediation records are kept separately
under `evidence/test-results/`.
