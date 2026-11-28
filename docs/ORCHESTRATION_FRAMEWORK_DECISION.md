# Orchestration Framework Evaluation and Decision

**Decision date:** 12 November 2026  
**Status:** Accepted for the current development phase; reconsider only against a reproducible prototype and explicit acceptance criteria.  
**Production branch:** `feature/four-round-mdt-and-performance`  
**Current production orchestration:** Project-owned Python/FastAPI orchestration with Ollama inference.

## 1. Decision

**Retain the existing custom orchestration for the current product. Do not add AutoGen or CrewAI as a production dependency.**

Evaluate Microsoft Agent Framework only in a separate, non-production prototype if it demonstrates a concrete advantage. Do not replace the current runtime based on framework popularity, agent count, API convenience or a demo.

This is not a claim that the current orchestration is complete or clinically validated. The current architecture still requires current-head live model quality validation, a complete 136-contribution audit, security review and qualified clinical review.

## 2. What the current application needs from orchestration

The architecture is not a free-form agent group chat. It is a fixed, auditable state machine:

1. **R1:** 45 independent specialist assessments. Each role sees the permitted case data and its own profile, not peer assessments.
2. **R2:** 45 specialist debate contributions using bounded, source-labelled R1 peer context.
3. **R3:** 45 adversarial reviews of actual saved R2 records and attributed source opinions. Peer IDs must come from the actual supplied-peer allowlist; a server-bound quote must come from that peer's source-specific response for the same CASE source.
4. **R4:** one Chair synthesis from the actual saved R1–R3 contributions.

The application, not a framework or an LLM, must own:
- round order, execution state, persistence and resume;
- role identity and the allowed peer/source set for each call;
- deterministic counts and source-reference validation;
- immutable case snapshots, hashes, run IDs and audit history;
- failed/missing contribution visibility;
- consensus and dissent constraints;
- report reconciliation and output validation.

The LLM may interpret and draft. It must not be authoritative for source identity, contribution counts, state transitions or factual integrity.

## 3. Framework comparison

| Option | Current status / capabilities | Project assessment |
|---|---|---|
| Existing custom orchestration | Already implements the fixed four-round workflow, Ollama calls, SQLite persistence, resume, source allowlists, deterministic Chair reconciliation and regression suite. | **Retain.** Avoid introducing an abstraction that duplicates existing state and provenance controls. Continue improving the known live-quality gaps. |
| AutoGen | Microsoft's official repository currently states that AutoGen is archived and no longer maintained by Microsoft, and advises against production use. It remains useful as historical architecture/reference material. | **Do not adopt.** A new production dependency on an archived framework would add maintenance and security risk without resolving our current failures. |
| CrewAI | Multi-agent role/task orchestration can be useful for more dynamic delegated workflows. | **No demonstrated need.** The current process has explicit fixed rounds and deterministic server-owned workflow state. A framework migration would add complexity without a concrete requirement or proven quality improvement. |
| Microsoft Agent Framework | Microsoft's stated successor to AutoGen and Semantic Kernel. It offers agents, explicit workflows, session/state management, middleware/filters, telemetry, type support and model integrations, including Ollama. | **Candidate for isolated prototype only.** Its workflow and state abstractions may be worth benchmarking, but do not delegate provenance or clinical-safety controls to it. |

Official references (reviewed 12 November 2026):
- [Microsoft AutoGen repository and archived-project warning](https://github.com/microsoft/autogen)
- [Microsoft Agent Framework overview](https://learn.microsoft.com/en-us/agent-framework/overview/)
- [Microsoft Agent Framework Ollama integration](https://learn.microsoft.com/en-us/agent-framework/integrations/by-provider/ollama)
- [Microsoft Agent Framework migration guide from AutoGen](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)

## 4. Why AutoGen is not selected

The official AutoGen repository reports that the project is archived and no longer actively maintained by Microsoft, with no Microsoft bug fixes, security fixes, new features or support. It recommends Microsoft Agent Framework for new projects.

For a local application that handles potentially sensitive case narratives and requires long-term support, adopting an archived orchestration dependency is not justified. AutoGen's historical multi-agent patterns may inform design, but they are not a reason to replace functioning application-owned state and provenance logic.

## 5. Conditions for a Microsoft Agent Framework prototype

A prototype must be implemented outside the production branch or in a separately isolated experiment. It must not alter PR #1, the user's installed application or current databases.

Use the exact same:
- Ollama runtime version and model digest;
- prompts, schemas, case fixtures and source-peer allowlists;
- model parameters and context budgets;
- concurrency setting (1);
- six-call R2/R3 quality fixture and its expected results.

Measure:
1. exact R1/R2/R3/R4 separation and no cross-round data leakage;
2. deterministic role and round accounting;
3. source attribution and CASE-to-peer evidence binding;
4. exact persistence, idempotent retries, process restart and resume;
5. failure visibility and no fabricated replacement responses;
6. Chair report reconciliation and preservation of conditional support/dissent;
7. prompt injection and untrusted-output boundaries;
8. local Ollama compatibility and whether model inputs stay local;
9. latency, CPU/GPU placement and memory at concurrency 1;
10. dependency footprint, licence, maintenance, security advisories and packaging impact.

A higher-level framework must not increase inference calls, hide failures, mutate application state outside the repository's persistence layer or weaken any deterministic validation. Model output and framework orchestration events remain untrusted inputs to server-owned validation.

## 6. Acceptance rule

No production migration unless the prototype:
- passes the same deterministic regression suite;
- passes the same live R2/R3 quality gate on the same model and fixtures;
- demonstrates better maintainability or reliability with measurable evidence;
- adds no unacceptable dependency, privacy, security or packaging risk;
- has a documented rollback path; and
- is independently reviewed before a separate, explicit production-change decision.

**Current result:** no framework change. Existing custom orchestration remains the control implementation. AutoGen is not selected; Microsoft Agent Framework is an optional future benchmark, not a roadmap dependency.
