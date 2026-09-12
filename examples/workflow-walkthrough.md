# `/boost` End-to-End Workflow Walkthrough

This walkthrough illustrates how the `/boost` multi-agent pipeline operates in practice on a complex, high-concurrency engineering problem.

---

## The Scenario

A distributed background task queue (`TaskWorkerQueue`) is experiencing intermittent phantom failures in production: tasks that are actively running are periodically marked as timed-out and re-assigned to secondary workers, resulting in duplicate job execution and database transaction conflicts.

Standard single-agent attempts failed because the race condition occurs only under high async event-loop pressure when lease renewal and heartbeat acknowledgment overlap.

---

## Step 1: Ingestion & Boundary Scoping (Orchestrator)

The user runs:
```text
/boost Fix phantom timeouts and race conditions in TaskWorkerQueue lease renewal under concurrent heartbeat acknowledgments.
```

The **Primary Orchestrator** parses the request and constructs the authoritative contract:

```markdown
<original_task>
Fix phantom timeouts and race conditions in TaskWorkerQueue lease renewal under concurrent heartbeat acknowledgments.
</original_task>
```

The Orchestrator identifies:
- Target module: `src/queue/worker_queue.ts`
- Test suite: `test/queue/worker_queue.test.ts`
- Constraint: Must not alter public queue API or weaken existing test timeouts.

Before dispatching implementation, the Orchestrator fans out **two parallel read-only `DeepInvestigator` workers** (safe in the shared tree — they never write files):
- Investigator A: "Which code paths write `leaseExpiresAt`, and under what interleavings?"
- Investigator B: "Does anything outside `worker_queue.ts` (e.g., the reaper, retry scheduler) read stale lease state?"

Both return evidence-backed reports; their findings are merged into the implementation brief.

The Orchestrator invokes the worker:
`invoke_subagent` with Role `Layer 0 Coding Worker` (`DeepCoderWorkerL0`), passing `<original_task>`, the merged investigator findings, and the declared file scope.

---

## Step 2: Problem Localization & Reproduction (Coding Worker)

The **Layer 0 Coding Worker** receives the task in an isolated context:

1. **Investigate Codebase**:
   - Locates `heartbeat()` and `renewLease()` in `src/queue/worker_queue.ts`.
   - Discovers that `heartbeat()` reads `this.leaseExpiresAt`, performs an asynchronous ping, and then writes the updated expiration timestamp.
   - **Root Cause Identified**: A classic Time-of-Check to Time-of-Use (TOCTOU) race condition. If a parallel lease renewal completes during the `await ping()`, the subsequent timestamp assignment overwrites the renewed lease with a stale earlier time.

2. **Write Pre-Fix Reproduction Test**:
   - In `test/queue/worker_queue.test.ts`, the worker writes `testConcurrentHeartbeatAndRenewalRace()`.
   - Runs `npm test`: The reproduction test reliably reproduces the failure (`FAIL: task lease overwritten by stale heartbeat`).

3. **Implement Minimal Fix**:
   - Uses an atomic monotonic check:
     ```typescript
     // Ensure lease expiration only advances forward monotonically
     const newExpiration = Date.now() + this.leaseDurationMs;
     if (newExpiration > this.leaseExpiresAt) {
       this.leaseExpiresAt = newExpiration;
     }
     ```
   - Matches the codebase conventions and keeps the diff to exactly 8 lines.

4. **Deep Verification**:
   - Runs `npm test test/queue/worker_queue.test.ts`: Both existing tests and the new reproduction test pass.

5. **Submit Brutally Honest Report**:
   The worker calls `send_message` with the standard completion report:

   ```markdown
   > [!WARNING] **Skepticism Disclaimer**
   > While the monotonic lease check resolves concurrent heartbeat overwrites, this was tested in a single-process Node.js runtime and has not been verified against distributed NTP clock skew.

   ## 1. What I changed
   - `src/queue/worker_queue.ts`: Added monotonic timestamp guard in `heartbeat()` and `renewLease()` to prevent stale lease expiration overwrites.
   - `test/queue/worker_queue.test.ts`: Added concurrency test simulating interleaved heartbeat and manual renewal.

   ## 2. Why
   Directly resolves the TOCTOU race condition identified in the task.

   ## 3. Verification Record
   - **Deep Verification (ran actual tests):** Ran `npm test test/queue/worker_queue.test.ts` (14 passed, 0 failed).
   - **Shallow Verification (manual run only):** None.
   - **Unverified aspects:** Behavior when server clock jumps backward due to NTP synchronization.

   ## 4. Known Issues
   - `Minor Robustness Risk`: System relies on `Date.now()` rather than monotonic process uptime (`performance.now()`).

   ## 5. Untested Edge Cases & Next Step
   Reviewer should test backward clock drift during active lease renewal.
   ```

---

## Step 3: Adversarial Verification (AdversarialVerifier)

The **Primary Orchestrator** reads the worker's report and immediately assigns the adversarial review to the **Adversarial Verification Worker** (`AdversarialVerifier`), passing `<original_task>` and the worker's report as `<prior_attempt>`.

1. **Adversarial Red-Teaming**:
   - The AdversarialVerifier reads `<original_task>` independently FIRST.
   - Attacks the worker's admitted vulnerability: NTP clock skew.
   - Writes an adversarial stress test mocking clock skew:
     `Date.now = () => stalePastTimestamp`.
   - **Flaw Confirmed**: If the system clock steps backward by even 50ms, lease renewals are rejected as "stale", immediately triggering an unearned task timeout!

2. **Root Cause Attribution & Fix**:
   - The AdversarialVerifier records:
     - `input`: Simulated NTP backward time synchronization during active renewal.
     - `expected`: Monotonic lease extension based on elapsed monotonic interval.
     - `actual`: Lease expiration rejected as past timestamp.
     - `root cause`: Dependency on wall-clock `Date.now()` which is not guaranteed monotonic across NTP syncs.
   - Migrates lease duration tracking to monotonic time (`process.hrtime.bigint()`).

3. **Re-Verification & Reviewer Report**:
   - Re-runs unit test suite and clock-skew stress test. Both pass.
   - Submits completion report with `input → expected → actual → root cause` breakdown.

---

## Step 4: Regression Sweep & Final Synthesis (Orchestrator)

1. The Orchestrator triggers the global repository test pass:
   `npm test` (all 284 test suites across the repository pass).
2. Linter pass confirms zero lint errors.
3. The Orchestrator delivers the comprehensive final resolution to the user, including the root-cause diagnosis, diff summary, adversarial test proofs, and confidence assessment.

