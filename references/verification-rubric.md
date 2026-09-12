# Verification Rubric & Quality Standards in `/boost`

In high-stakes software engineering, claims of correctness must be backed by reproducible evidence. The `/boost` pipeline rejects superficial assertions of success and enforces a strict, hierarchical verification rubric.

---

## 1. The Verification Hierarchy

Every claim made by an agent regarding test results or functional stability must be categorized into one of three tiers:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Deep Verification                                        │
│    - Automated tests executed and passed                    │
│    - Defect reproduced prior to patch, confirmed resolved   │
│    - Full test suite passed with zero regressions           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Shallow Verification                                     │
│    - Manual CLI execution or single happy-path curl         │
│    - Static type checking or linter pass only               │
│    - Visual inspection of code without running tests        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Unverified Aspects                                       │
│    - Boundary cases (null, empty, overflows, malformed)     │
│    - Concurrency under high contention                      │
│    - Platform or environmental matrix dependencies          │
└─────────────────────────────────────────────────────────────┘
```

### Tier 1: Deep Verification (Gold Standard)
- **Requirement**: The agent executed real test commands in the environment (e.g., `npm test`, `pytest`, `cargo test`, `go test`) and captured the exit code and output.
- **Criteria**:
  - The bug was reproduced beforehand with a failing test.
  - The modified code makes the failing test pass.
  - All existing, related tests continue to pass without modification.
  - Edge cases explicitly mentioned in the task requirements are tested.

### Tier 2: Shallow Verification (Requires Skepticism)
- **Requirement**: Any check that does not prove correctness across state spaces.
- **Examples**:
  - Running a single manual command on one input (`python script.py "arg"`).
  - Confirming that the compiler/linter succeeded (`tsc --noEmit`, `eslint`).
  - Reading the diff and believing it is correct without execution.
- **Rule**: Shallow verification must never be represented as deep proof. It must be explicitly labeled as shallow in reports.

### Tier 3: Unverified Aspects (Mandatory Disclosure)
- **Requirement**: An exhaustive accounting of everything the agent did *not* or *could not* test.
- **Examples**:
  - Untested race conditions or thread safety under high concurrency.
  - Performance regressions under large datasets.
  - Integration with external third-party services or live APIs.
  - OS-specific behaviors (e.g., Windows vs macOS vs Linux).

---

## 2. Defect Severity Taxonomy

When reporting issues, workers must prefix each known issue or risk with one of three standardized labels:

### `Fatal Functional Bug`
- **Definition**: The code crashes, produces objectively wrong output, corrupts data, or fails to meet explicit task requirements.
- **Action**: Cannot proceed to delivery. Must be fixed immediately.

### `Shallow Verification`
- **Definition**: The implementation appears correct, but could not be definitively proven with automated tests (e.g., missing test framework, environment constraints).
- **Action**: Must be called out clearly in the final deliverable so the user knows manual verification is needed.

### `Minor Robustness Risk`
- **Definition**: Edge cases, unusual boundary inputs, or non-critical performance trade-offs that do not impact standard operation.
- **Action**: Documented in the completion report with recommended remediation steps.

---

## 3. The Five Golden Rules of Verification

1. **Zero Test Weakening**:
   - Never modify an existing test to lower its assertions, increase timeouts, or skip tests (`test.skip()`, `@pytest.mark.xfail`) to make a broken patch look successful. An existing test failure is a direct signal that the patch is flawed.
2. **Zero Special-Casing**:
   - Never write code that checks `if input == "test_case_1"` to pass a specific test. Solutions must solve the general problem structurally.
3. **Reproduction Before Remediation**:
   - Always demonstrate the failure on the unchanged codebase first. If you cannot reproduce the bug, you cannot prove you fixed it.
4. **Clean Baseline Regression Sweeps**:
   - Always run the broader test suite to ensure no collateral damage was introduced into unrelated modules.
5. **Brutal Skepticism Over Flattery**:
   - Reports must never reassure the reader with statements like "Everything works perfectly!". Every report must open with a **Skepticism Disclaimer** acknowledging remaining risks.

---

## 4. Adversarial Red-Teaming Checklist

Improvement workers must run through this checklist before approving any change:

- [ ] **Empty / Nil Inputs**: Does the code handle `null`, `undefined`, `None`, empty strings, empty arrays, or missing dictionary keys without uncaught exceptions?
- [ ] **Numeric Boundaries**: Does the code handle `0`, negative numbers, floating point precision limits, and integer overflows?
- [ ] **Resource Cleanup**: Are file handles, database connections, locks, and network sockets closed in `finally` / `defer` blocks?
- [ ] **Concurrency & Locking**: Are shared states protected by mutexes, atomic operations, or queues? Is there a risk of deadlocks?
- [ ] **Error Propagation**: Are errors caught and logged or re-thrown appropriately? Are errors masked silently?
- [ ] **Idempotency**: What happens if the operation is executed twice with the same arguments?
- [ ] **Performance & Complexity**: Is there an accidental $O(N^2)$ loop or memory leak introduced by caching unbounded data?
