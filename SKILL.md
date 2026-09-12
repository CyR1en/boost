---
name: boost
description: >-
  Executes the /boost multi-agent deep reasoning pipeline for complex software engineering tasks.
  Activate this skill whenever the user invokes /boost, asks for boost mode, or requests deep
  multi-agent reasoning, hierarchical orchestration, isolated coding workers, adversarial
  verification, or skeptical reporting for intricate bugs, race conditions, or large refactors.
---

# `/boost` Deep Reasoning & Multi-Agent Orchestration Skill

The `/boost` skill packages the on-demand, multi-agent deep reasoning pipeline. It is engineered for high-complexity, high-stakes coding problems that exceed the reliable cognitive horizon of single-turn agents across any agentic environment (Antigravity, Claude Code, OpenAI Codex, OpenCode, Qwen, Grok, etc.).

Instead of relying on a single agent to plan, code, and self-validate in one continuous stream, `/boost` decouples high-level strategy from isolated execution and independent adversarial verification.

---

## Quick Navigation

- **Pipeline & State Workflow**: [references/pipeline-workflow.md](references/pipeline-workflow.md)
- **Agent Roles & Mandates**: [references/agent-roles.md](references/agent-roles.md)
- **Verification Rubric & Standards**: [references/verification-rubric.md](references/verification-rubric.md)
- **Prompt & Report Templates**: [resources/prompts.md](resources/prompts.md)
- **End-to-End Walkthrough**: [examples/workflow-walkthrough.md](examples/workflow-walkthrough.md)
- **Report Verification Helper**: [scripts/verify_report.py](scripts/verify_report.py)

---

## 1. When to Use `/boost`

| Use Standard Agent Mode | Use `/boost` Deep Reasoning Mode |
| :--- | :--- |
| Single-file bug fixes with clear stack traces | Intermittent, concurrency, or distributed race conditions |
| Straightforward feature additions and boilerplate | Multi-file architectural refactoring or subsystem redesigns |
| Documentation updates and localized edits | Algorithmic optimization with tight performance constraints |
| Adding test cases to existing well-defined suites | Obscure regressions where previous attempts introduced side effects |
| Direct questions about codebase structure | High-uncertainty tasks with conflicting requirements or sparse repros |

---

## 2. Core Architecture & Multi-Agent Hierarchy

The `/boost` pipeline employs a three-tier hierarchical division of labor:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Primary Orchestrator                     │
│  - Parses <original_task> & isolates workspace boundaries    │
│  - Fans out parallel read-only investigators at scoping      │
│  - Delegates implementation to isolated coding worker(s)     │
│  - Synthesizes findings & runs final regression sweep       │
└──────┬───────────────┬──────────────────────────▲───────────┘
       │               │                          │
       │ 0a. Parallel  │ 0b. Spawn Coding Worker  │ 4. Single Final Report
       │     read-only │    (isolated context)    │
       ▼     investigators (no writes)            │
┌──────────────┐      │                           │
│ DeepInvest-  │      ▼                           │
│ igator x N   │ ┌───────────────────────────────┐│
│ (read-only)  │ │   Layer 0 Coding Worker       ││
│ - root cause │ │   (DeepCoderWorkerL0)         ││
│ - call graph │ │  - Targeted code modification ││
│   tracing    │ │  - Reproduces bug with tests  │├───────────┤
│ - dep recon  │ │  - Adheres to minimal diff    ││           │
└──────────────┘ └──────────────┬────────────────┘│           │
                                │                 │           │
                                │ 2. Candidate Patch          │
                                ▼                 │           │
                     ┌───────────────────────────────┐        │
                     │ Adversarial Verification      │        │
                     │ Worker (AdversarialVerifier)  │────────┘
                     │  - Actively tries to break fix│ 3. Adversarial Feedback
                     │  - Tests boundary conditions  │    & Regression Audit
                     │  - Edge-case stress testing   │
                     └───────────────────────────────┘
```

### Workspace Isolation Model

Workers get **context isolation** by default (clean context windows, no inherited history). For **filesystem isolation**, follow this ladder:

1. **Preferred — git worktrees**: When multiple implementation workers run in parallel, or when candidate patches must not contaminate the user's working tree, spawn each worker in an ephemeral `git worktree` (or the host platform's equivalent — e.g., `invoke_subagent` workspace `branch` in Antigravity). The orchestrator merges verified results afterward.
2. **Fallback — disjoint file scopes**: If worktrees are unavailable, parallel workers are permitted only when their file scopes are provably disjoint. Declare each worker's allowed paths in its dispatch prompt and forbid edits outside them.
3. **Read-only investigators are always safe** in the shared tree — they never write files, so `DeepInvestigator` fan-out needs no isolation beyond context.

All workers inherit the host agent's permission policies (file access rules, command approvals). Protected commands still surface to the user for approval.

### Agent Roles

1. **Primary Orchestrator (Coordinator)**:
   - Holds the master plan and coordinates execution phases.
   - **Never** attempts manual code modifications or guesswork directly.
   - Fans out parallel read-only investigators during scoping when the task spans unfamiliar or broad code areas.
   - Holds subagents to strict verification and reporting contracts.
   - Coordinates regression testing before delivering the final resolution.

2. **Investigation Worker (`DeepInvestigator`)** — *read-only*:
   - Runs in parallel with other investigators during scoping; may be spawned any time a focused root-cause question exists.
   - Traces execution call graphs, analyzes unfamiliar dependencies, and localizes defects.
   - **Must never modify files.** Output is analysis only: findings, suspected root cause, and a recommended verification path.

3. **Layer 0 Coding Worker (`DeepCoderWorkerL0`)**:
   - Operates in an isolated subagent context to focus solely on implementation.
   - Treats `<original_task>` as authoritative over coordinator interpretations.
   - Reproduces the defect with automated tests prior to making modifications.
   - Adheres to the **Minimal Diff Principle** and matches surrounding codebase conventions.
   - Submits a brutally honest, single final completion report.

4. **Adversarial Verification Worker (`AdversarialVerifier`)**:
   - Follows the coding worker with an explicit adversarial mindset ("break the patch").
   - Hunts for regressions, edge cases (empty inputs, concurrency contention, resource leaks), and test cheating.
   - Generates counter-example tests to expose latent defects.
   - Unlike `DeepInvestigator`, this worker **does** modify code to fix what it breaks.

---

## 3. Four-Phase Lifecycle

### Phase 1: Architectural Scoping & Task Ingestion
- Extract the raw, authoritative task from `<original_task>`.
- Identify affected modules, dependency graphs, and existing test suites.
- **Fan out parallel `DeepInvestigator` workers** (read-only) for any task spanning unfamiliar or broad code areas — one per independent question (root cause, call graph, dependency recon). Merge their findings before dispatching implementation.
- Establish an isolated reproduction harness.
- Formulate acceptance criteria and boundary constraints.

### Phase 2: Targeted Implementation (Coding Worker)
- Reproduce failure on clean baseline before applying edits.
- Implement the general solution without special-casing tests.
- Verify locally by executing real unit and integration test suites.
- Package diff with a structured verification record.
- When multiple implementation workstreams run in parallel, place each in an ephemeral `git worktree` (or enforce disjoint file scopes — see Workspace Isolation Model).

### Phase 3: Adversarial Verification (AdversarialVerifier)
- Subject the candidate patch to stress testing and adversarial edge cases.
- Verify untouched components to ensure zero collateral regressions.
- Audit test suites to guarantee no existing assertions were weakened or bypassed.

### Phase 4: Synthesis & Safe Integration (Orchestrator)
- Resolve any defects uncovered by the adversarial worker.
- Execute full repository regression test suite.
- Deliver evidence-based completion report with reproduction proofs and artifacts.

---

## 4. Engineering Invariants & Guardrails

The `/boost` pipeline enforces six non-negotiable engineering rules:

1. **Authoritative Task Rule**: The `<original_task>` block is ground truth. Subagents must challenge and reject any coordinator assumptions that contradict the actual codebase or original request.
2. **Never Weaken Tests (Zero Test Tampering)**: Under no circumstances may an agent delete, skip, or soften assertions in existing test suites to make a patch appear successful.
3. **No Special-Casing**: Solutions must solve the general problem structurally. Hardcoding return values to satisfy specific test parameters is treated as a fatal failure.
4. **Minimal Diff Principle**: Edits must be surgical. Unrelated refactoring, stylistic reformatting, or speculative cleanups add regression surface and are prohibited.
5. **No Interim Conversational Noise**: Workers must never send chatter or interim status messages. Exactly **one** final completion report is delivered upon task finish.
6. **Mandatory Root Cause Attribution**: Every defect identified by an adversarial worker must be documented as `input → expected → actual → root cause`. A symptom without a root cause is not understood.

---

## 5. Standard Completion Reports

### Coding Worker Report Schema
```markdown
> [!WARNING] **Skepticism Disclaimer**
> [One honest sentence assessing confidence and residual risks. No reassuring fluff.]

## 1. What I changed
[Files modified and exact functional nature of each change.]

## 2. Why
[Rationale directly mapped to task requirements.]

## 3. Verification Record
- **Deep Verification (ran actual tests):** [Commands executed, output summary, tests passed]
- **Shallow Verification (manual run only):** [Manually inspected or syntax checked only]
- **Unverified aspects:** [Exhaustive list of what was NOT verified]

## 4. Known Issues
Prefix each issue with:
- `Fatal Functional Bug` — Core logic does not work
- `Shallow Verification` — Plausibly works, but automated proof is missing
- `Minor Robustness Risk` — Low-probability edge case or performance risk

## 5. Untested Edge Cases & Next Step
[High-priority attack surfaces for the adversarial verification worker.]
```

### Adversarial / Reviewer Worker Report Schema
```markdown
> [!WARNING] **Skepticism Disclaimer**
> [Honest one-liner on your confidence. No reassurance.]

## 1. What the prior attempt got wrong
[Each issue: input → expected → actual → root cause. If genuinely nothing was wrong, present the evidence that proves it — which tests you ran and their output.]

## 2. What I changed
[Files and substance.]

## 3. Verification Record
- **Deep Verification (ran actual tests):** [commands and results]
- **Shallow Verification (manual only):** [...]
- **Unverified aspects:** [exhaustive and honest]

## 4. Known Issues
Prefixed `Fatal Functional Bug` / `Shallow Verification` / `Minor Robustness Risk`. Do not sugarcoat.

## 5. Remaining risk & next step
[What the next round should attack, or an explicit statement that the task is complete and why you believe that.]
```

---

## 6. Automated Validation Helper

To validate any completion report against the `/boost` rubric programmatically, run:

```bash
# Universal command (executable from any directory):
python3 ~/.agents/skills/boost/scripts/verify_report.py path/to/report.md --role worker
# or for reviewer/adversarial reports:
python3 ~/.agents/skills/boost/scripts/verify_report.py path/to/report.md --role reviewer

# Or within the skill directory:
python3 scripts/verify_report.py path/to/report.md --role worker
```

