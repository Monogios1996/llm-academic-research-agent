# LLM Academic Research Agent

An LLM-powered academic research and information-gathering planning agent developed for the University of Essex Online Intelligent Agents module.

## Project status

This repository currently contains the initial project foundation. Implementation will be developed incrementally so that the Git history records design, implementation, testing, remediation, and refinement over the lifetime of the project.

## Proposed system

The system is based on the Unit 6 design proposal. It will accept a high-level academic research goal and coordinate a bounded planning workflow with six logical roles: Orchestrator/Supervisor, Planner, Academic Retrieval, Processing/Ranking, Evidence Validator, and Storage/Export.

The prototype is intended to use Python 3.11+, LangGraph, Pydantic, Crossref and OpenAlex, with SQLite for local state and structured logging for execution evidence.

## Planned repository structure

- `src/` - application source code
- `tests/` - unit and functional tests
- `docs/` - design and architecture material
- `evidence/` - test outputs, example runs, logs and screenshots

## Development approach

The project will be implemented incrementally. Major functional changes will be committed separately so development progress and remediation can be demonstrated during assessment.

## Running the project

The runnable application has not yet been implemented. Installation and execution instructions will be expanded as functionality is added.

## Academic integrity and acknowledgements

External libraries, frameworks, models, APIs and academic sources used by the implementation will be acknowledged here and, where appropriate, in code commentary. Design-oriented comments will explain why implementation choices were made rather than merely restating what the code does.
