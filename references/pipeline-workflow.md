# `/boost` Pipeline & Operational Workflow

This reference details the step-by-step lifecycle, state machine transitions, operational triggers, and decision logic that power the `/boost` deep reasoning workflow.

---

## 1. State Machine & Execution Flow

```text
[ User invokes /boost ]
           │
           ▼
┌─────────────────────────┐
│ State 0: Ingestion &    │  - Isolate <original_task>
│ Scoping                 │  - Map affected components & test harnesses
└──────────┬──────────────┘  - Identify non-negotiable boundaries
           │
           ▼
┌─────────────────────────┐
│ State 0.5: Parallel     │  - Fan out N read-only DeepInvestigator workers,
│ Investigation Fan-Out   │    one per independent question (root cause,
│ (optional)              │    call graph, dependency recon)
└──────────┬──────────────┘  - Safe in shared tree: investigators never write
           │                  - Merge findings into implementation brief
           ▼
┌─────────────────────────┐
│ State 1: Workstream     │  - Coordinator determines subagent roles
│ Orchestration           │  - Spawns DeepCoderWorkerL0 with isolated context
└──────────┬──────────────┘  - Parallel impl workers? → git worktree per worker
           │                  (fallback: provably disjoint file scopes)
           ▼
┌─────────────────────────┐
│ State 2: Implementation │  - Reproduce defect on clean baseline
│ & Local Verification    │  - Implement surgical fix (Minimal Diff)
└──────────┬──────────────┘  - Deep verification with local test suites
           │
           ▼
┌─────────────────────────┐
│ State 3: Skeptical      │  - Worker compiles 5-part completion report
│ Reporting Hand-off      │  - Highlights residual risks and untested edges
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ State 4: Adversarial    │  - Spawns AdversarialVerifier with <original_task> & <prior_attempt>
│ Verification            │  - Boundary testing, fault injection, stress test, tampering audit
└──────────┬──────────────┘  - Records: input → expected → actual → root cause
           │
      [ Flaws found? ]
      ├── YES (Rounds < 3) ──► [ Fix & Re-verify loop ]
      ├── TAMPERING FOUND  ──► [ Revert tampered tests, demand structural fix ]
      └── NO / CONVERGED   ──┐
                             ▼
┌─────────────────────────┐
│ State 5: Full Suite     │  - Coordinator runs full repository regression pass
│ Regression Sweep        │  - Verifies zero collateral regressions
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ State 6: Evidence-Based │  - Synthesize findings, diffs, and verification proofs
│ Final Delivery          │  - Present final delivery to user
└─────────────────────────┘
```

---

## 2. Phase-by-Phase Operational Procedures

### Phase 1: Ingestion & Scoping (Primary Orchestrator)

**Goal**: Transform user intent into an unambiguous, verifiable contract.

1. **Extract Canonical Task**:
   - Enclose the authoritative prompt inside `<original_task>...</original_task>`.
   - Strip out coordinator speculation, premature architectural assumptions, or unverified constraints.
2. **Context Discovery**:
   - Locate test harnesses, build targets, and lint configurations.
   - Map dependencies without performing broad, wasteful scans.
   - Establish baseline reproduction criteria (e.g., specific failing test, reproducer script, or benchmark).
3. **Parallel Investigation Fan-Out**:
   - When the task spans unfamiliar or broad code areas, dispatch one read-only `DeepInvestigator` per independent question (e.g., "what calls `renewLease`", "why does the timeout spike above 2MB payloads").
   - Investigators never write files, so they run safely in the shared workspace and in parallel with each other.
   - Merge their evidence-backed findings into the implementation brief handed to the coding worker.
4. **Guardrail Declaration**:
   - Explicitly declare components that must **not** be modified (regression boundary).

### Phase 2: Implementation & Local Verification (Coding Worker)

**Goal**: Implement the general solution cleanly and prove it works with tests.

1. **Failure Reproduction**:
   - Before writing any implementation code, run the existing test suite or write a targeted reproduction test.
   - Confirm the failure occurs as expected on the clean baseline.
2. **Implementation Under Constraints**:
   - Apply the **Minimal Diff Principle**: only touch lines directly necessary to solve the root cause.
   - Maintain idiomatic codebase style, naming conventions, and typing guarantees.
   - **Prohibited**: Special-casing tests with hardcoded responses, skipping tests, or masking errors.
   - **Parallel implementation**: if the coordinator spawned multiple coding workers, each runs in its own `git worktree` (or a declared disjoint file scope). A worker must never edit files outside its declared scope.
3. **Local Deep Verification**:
   - Execute the test suite against the modified code.
   - Verify both happy path and localized edge cases (null inputs, boundary values, error branches).

### Phase 3: Skeptical Reporting & Handoff (Coding Worker)

**Goal**: Provide an unvarnished audit of the work done and risks remaining.

1. **Strict Messaging Contract**:
   - Never send interim chatter or partial status updates.
   - Send exactly **one** structured final completion message using the standard report format.
2. **Classification of Findings**:
   - Clearly delineate between **Deep Verification** (automated tests actually run) and **Shallow Verification** (manual inspection/syntax check).
   - Honestly disclose all unverified aspects and edge cases.

### Phase 4: Adversarial Verification (AdversarialVerifier)

**Goal**: Attempt to break the solution before it reaches production.

1. **Adversarial Mindset**:
   - The verification worker treats the coding worker's patch with constructive skepticism ("You are not a rubber stamp").
   - Understand the task from `<original_task>` independently BEFORE reading `<prior_attempt>`.
2. **Targeted Red-Teaming**:
   - **Test Tampering Audit**: Did the prior attempt weaken, skip, or delete any test assertions? If so, revert immediately and record the root cause.
   - **Concurrency & Races**: Probe under thread contention, high async loads, or out-of-order execution.
   - **Boundary Conditions**: Empty collections, zero values, maximum integer limits, malformed payloads.
   - **Error Handling & Cleanup**: Do exceptions leak connections, locks, memory, or file descriptors?
   - **Regression Audit**: Run untouched test suites across the repository to catch unexpected collateral damage.
3. **Root Cause Attribution**:
   - Record every flaw as: `input → expected → actual → root cause`.
4. **Fix & Re-verify**:
   - Implement the necessary corrections and re-run all failing scenarios + full test suite.

### Phase 5: Convergence, Circuit Breakers & Regression Sweep (Orchestrator)

**Goal**: Guarantee termination and repo-wide stability.

1. **Convergence Criteria**:
   - Pipeline completes when the adversarial reviewer identifies **zero** `Fatal Functional Bug` and **zero** `Shallow Verification` items.
2. **Circuit Breaker (Max Rounds)**:
   - Limit adversarial iterations to a maximum of 3 rounds. If unresolved issues persist after round 3, the orchestrator halts the loop and presents the exact remaining risks to the user.
3. **Full Regression Sweep**:
   - Execute the complete test suite and linters across the entire workspace.

### Phase 6: Synthesis & Safe Delivery (Primary Orchestrator)

**Goal**: Final validation and transparent delivery to the user.

1. **Evidence Packaging**:
   - Summarize the exact changes made with clickable file links.
   - Attach verification proofs (test outputs, execution logs, diff summaries).
   - Highlight any residual caveats or recommendations for follow-up testing.

---

## 3. Communication & Concurrency Protocol

- **Single Handoff**: Subagents run asynchronously without chatting back and forth. They perform their complete investigation and return a single, comprehensive report.
- **Context Isolation**: Workers operate with clean contexts to prevent prompt degradation, context pollution, or compounding errors.
- **Filesystem Isolation**: Read-only `DeepInvestigator` workers always share the tree safely. Writers (coding workers) are serialized by default; parallel writers require one `git worktree` each or provably disjoint file scopes.
- **Permission Inheritance**: Workers inherit the host workspace's file-access rules and command-approval policies; protected commands surface to the user.
- **Fail-Fast Policy**: If an invariant is violated (e.g., test tampering), the coordinator immediately rejects the patch.
