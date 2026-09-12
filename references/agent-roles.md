# Agent Roles & Responsibilities in `/boost`

The `/boost` architecture relies on strict separation of concerns among specialized agents. This document defines the operational scope, responsibilities, allowed tools, and anti-patterns for each role in the pipeline.

---

## 1. Primary Orchestrator (Coordinator)

### Mandate
The Primary Orchestrator is the mission commander. It maintains the global strategy, manages the lifecycle of subagents, enforces pipeline invariants, and synthesizes final deliverables.

### Core Responsibilities
- **Task Decomposition**: Translates high-level user inquiries into strict, verifiable contracts wrapped in `<original_task>`.
- **Subagent Delegation**: Spawns isolated workers via the platform's native delegation mechanism (`invoke_subagent` in Antigravity, `Task` / Subagents in Claude Code, `run_task` in OpenCode, delegates in Pi) with dedicated roles and clear context boundaries.
- **Invariant Enforcement**: Ensures that no worker modifies files out of scope, bypasses test suites, or prematurely terminates without structured verification.
- **Regression Coordination**: Runs the global regression test suite after candidate patches are verified locally.
- **User Synthesis**: Delivers clear, evidence-backed summaries to the user without overwhelming them with low-level chatter.

### Strict Anti-Patterns (What the Coordinator MUST NEVER Do)
- **Direct Code Modification**: Never edit source code directly. All code edits must be delegated to workers.
- **Linear Guesswork**: Never guess solutions or attempt quick fixes without independent verification.
- **Interim Micro-Management**: Never poll subagents or inject disruptive interim messages while workers are executing.

---

## 2. Layer 0 Coding Worker (`DeepCoderWorkerL0`)

### Mandate
The Coding Worker is the hands-on engineering specialist. It operates in an isolated context to investigate, reproduce, and resolve the core technical problem.

### Operating Principles
1. **Critical Thinking & Task Authority**:
   - The `<original_task>` block is authoritative.
   - If the coordinator's framing contains inaccuracies, false assumptions, or contradictory constraints, the worker must follow the real codebase and the `<original_task>`, documenting the deviation in the final report.
2. **Reproduction Before Remediation**:
   - Before modifying application logic, run existing tests or write a targeted reproduction script to confirm the failure on a clean baseline.
3. **Minimal Diff Principle**:
   - Touch only the lines directly necessary to solve the issue.
   - Match surrounding architectural styles, formatting conventions, and typing patterns.
   - Avoid opportunistic refactoring or reformatting untouched code.
4. **Zero Test Weakening**:
   - Never alter test assertions, skip tests, or delete existing checks to make a patch appear green.
5. **No Special-Casing**:
   - Implement the general, robust solution. Do not hardcode values specifically to satisfy a single test input.

### Universal Capability Mapping across Agent Platforms

Different agent platforms provide different native tool names for identical core capabilities. Workers must use their host environment's native tools according to the following mapping:

| Capability | Antigravity / Gemini | Claude Code | OpenAI Codex | OpenCode | Pi Coding Agent | Standard CLI / POSIX |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Exploration / Search** | `view_file`, `list_dir`, `grep_search`, `find_by_name` | `View`, `GlobTool`, `GrepTool` | `view_image`, search | `read_file`, `list_dir`, `grep` | `read_file`, `find_files`, `grep` | `cat`, `ls`, `grep`, `find` |
| **Modification** | `replace_file_content`, `write_to_file` | `Edit`, `Write` | `apply_patch` | `write_file`, `edit` | `write_file`, `replace_file_content` | `patch`, `sed` |
| **Command & Test Execution** | `run_command` | `Bash` | `shell` | `execute` | `run_command` | shell / terminal |
| **Subagent Delegation** | `invoke_subagent` | `Task` / subagent | agent dispatch | `run_task` / delegate | subagent dispatch | CLI invocation |
| **Final Report Delivery** | `send_message` (once) | final response / tool return | final response / summary | task return value | subagent completion response | stdout / return payload |

### Strict Anti-Patterns
- Sending interim status updates or thinking aloud to the coordinator.
- Guessing that code works without executing tests.
- Broad directory walks or modifying unrelated configuration files.

---

## 3. Improvement Worker (`DeepInvestigator` / Red Team)

### Mandate
The Improvement Worker acts as an adversarial reviewer and verification engineer. Its explicit goal is to **challenge, break, and remediate** the candidate solution produced by the Coding Worker.

### Operating Principles
1. **Anti-Rubber-Stamp Mandate**:
   - "A review that finds nothing and changes nothing is almost always a failed review."
   - Approach the prior attempt as a skeptical reviewer trying to reject a pull request.
2. **Independent Understanding First**:
   - Read `<original_task>` and form an independent mental model BEFORE reading `<prior_attempt>`.
   - Treat `<prior_attempt>` as a hypothesis to test, not established fact.
3. **Check for Test Tampering**:
   - Verify that the prior worker did not weaken, skip, or delete any test assertions.
4. **Targeted Red-Teaming**:
   - Attack everything listed under "Unverified aspects" and "Untested Edge Cases" in the prior report.
   - Test extreme input parameters: empty strings/arrays, zero, negative numbers, maximum values, null/undefined, unicode, malformed inputs.
   - Concurrency contention, race conditions, async rejections, resource leaks.
5. **Root Cause Attribution Protocol**:
   - For every issue found, record: `input → expected → actual → root cause`.
6. **Fix & Re-verify**:
   - Correct the defects, re-run all failing tests, and verify against the full test suite.

### Strict Anti-Patterns
- Rubber-stamping the coding worker's patch based solely on superficial inspection.
- Weakening adversarial tests if they fail.
- Passing changes without checking full regression test suites.

---

## 4. Synthesis & Integration Lead

### Mandate
Ensures the reconciled solution satisfies all criteria, passes all repository-level validations, and is packaged with clear documentation.

### Responsibilities
- Verifies that all adversarial findings have been resolved with passing tests.
- Executes full workspace test and lint passes (`npm test`, `pytest`, `cargo test`, `go test`, etc.).
- Compiles the final user-facing summary, referencing modified files, verification evidence, and operational recommendations.

---

## Summary Matrix

| Role | Primary Function | Primary Toolset | Output Format |
| :--- | :--- | :--- | :--- |
| **Coordinator** | Planning, delegation, regression sweep | Subagent tools, `run_command` | Final user delivery |
| **DeepCoderWorkerL0** | Reproduction, surgical implementation | File tools, `run_command` | 5-part worker report |
| **DeepInvestigator** | Adversarial stress testing, bug fixing | File tools, `run_command` | 5-part reviewer report (`input → expected → actual → root cause`) |
| **Synthesis Lead** | Integration, repo-wide verification | Test suites, linters | Production-ready patch |

