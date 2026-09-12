# Subagent Setup

`/boost` requires real subagent infrastructure: isolated workers the orchestrator can spawn, each with a clean context and a dedicated system prompt. Not every harness ships suitable subagents out of the box — this guide installs the `/boost` worker roster so the skill works as designed.

Currently covered: **OpenCode**. (Contributions for other harnesses welcome — each needs an isolated-context subagent with a custom system prompt and per-role tool restrictions.)

---

## OpenCode

### Roster

| File in `resources/agents/opencode/` | Agent name | Mode | Writes? |
| :--- | :--- | :--- | :--- |
| `deep-investigator.md` | `deep-investigator` | subagent | **Never** — `edit: deny`, curated bash allowlist |
| `deepcoder-worker-l0.md` | `deepcoder-worker-l0` | subagent | Yes — scoped to its task |
| `adversarial-verifier.md` | `adversarial-verifier` | subagent | Yes — fixes what it breaks |
| `boost-orchestrator.md` *(optional)* | `boost-orchestrator` | **primary** | No — delegates everything |

Install the three workers for a minimal working pipeline. The optional `boost-orchestrator` primary agent is for users who want to **Tab into a dedicated orchestration session** — it denies its own file edits and restricts `task` invocations to the `/boost` roster. Without it, the normal primary agent acts as orchestrator (it reads this skill and dispatches the workers itself).

### Install

Global (available in every project):

```bash
cp ~/.agents/skills/boost/resources/agents/opencode/deep-investigator.md \
   ~/.agents/skills/boost/resources/agents/opencode/deepcoder-worker-l0.md \
   ~/.agents/skills/boost/resources/agents/opencode/adversarial-verifier.md \
   ~/.config/opencode/agents/

# optional: dedicated orchestrator primary agent
cp ~/.agents/skills/boost/resources/agents/opencode/boost-orchestrator.md \
   ~/.config/opencode/agents/
```

Per-project (ships with the repo for teammates):

```bash
mkdir -p .opencode/agents
cp <skill-path>/resources/agents/opencode/*.md .opencode/agents/
```

### How dispatch works

- The orchestrator invokes workers via OpenCode's **`task` tool**, e.g. `task(subagent_type="deep-investigator", ...)`. Users can also `@`-mention any worker manually (`@deep-investigator why does X time out?`).
- Worker permissions gate tool use at the platform level, not just by prompt:
  - `deep-investigator` has `edit: deny` (write/edit/apply_patch all blocked) plus a bash allowlist for read-only commands and test runners; everything else asks.
  - All workers have `task: deny` — only the orchestrator may spawn subagents. This prevents uncontrolled nesting.
  - The optional `boost-orchestrator` inverts this: `edit: deny` for itself, `task` allowlist limited to the `/boost` roster.
- Permission values (`allow` / `ask` / `deny`, plus glob patterns for `bash` and `task`) follow the last-match-wins rule — tighten or loosen in the frontmatter to taste.

### Tuning

- **Model**: unset by default so workers inherit the session model. Pin per-role with `model: provider/model` in frontmatter (e.g., a cheaper model for `deep-investigator`, strongest for `adversarial-verifier`).
- **Temperature**: shipped at 0.1 for the deterministic roles (investigator, verifier) and 0.2 for the coder.
- **`max_steps`**: if a worker is being cut off mid-investigation on huge codebases, raise it in its frontmatter.
- **Bash allowlist for `deep-investigator`**: extend with your repo's test commands (e.g., `"pnpm test*": allow`).

### Verify the install

1. Restart OpenCode (or reload config) so it discovers the new agent files.
2. `@`-mention `@deep-investigator` with a scoped question — it should answer without ever writing files.
3. Run a small `/boost` task and confirm the primary agent dispatches `deepcoder-worker-l0` then `adversarial-verifier` via the task tool.

---

## Porting to another harness

Any harness can host `/boost` if it supports subagents with:

1. **Isolated context** — the worker starts clean, no inherited conversation history.
2. **Custom system prompts** — paste the role templates from `resources/prompts.md`.
3. **Tool/permission restrictions** — at minimum, a way to make `deep-investigator` read-only and to block workers from spawning their own subagents.
4. **Single-shot dispatch** — one prompt in, one report out (no interactive back-and-forth channel required).

Filesystem isolation (git worktrees) is a bonus: if the harness supports a `worktree`/`branch` workspace option per subagent, parallel coding workers become safe; otherwise keep writers serial or enforce disjoint file scopes.
