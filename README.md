# Multi-Agent Skill: `/boost` Deep Reasoning Pipeline

The **`/boost`** skill implements an on-demand, multi-agent deep reasoning pipeline for complex software engineering problems. It is installed and available across all AI coding agents on this machine.

---

## Directory Layout

```text
boost/
├── SKILL.md                          # Main entry point with YAML frontmatter & progressive disclosure
├── README.md                         # Overview, installation paths & CLI usage
├── references/
│   ├── pipeline-workflow.md          # 6-state execution machine, circuit breakers & convergence
│   ├── agent-roles.md                # Orchestrator, Investigator, Worker L0, Verifier roles & invariants
│   ├── verification-rubric.md        # Deep vs Shallow verification & defect severity taxonomy
│   └── subagent-setup.md             # Installing the /boost worker roster per harness (OpenCode, ...)
├── resources/
│   ├── prompts.md                    # Canonical system prompts and completion report templates
│   └── agents/
│       └── opencode/                 # Copy-ready OpenCode subagent definitions
│           ├── deep-investigator.md      # Read-only investigation worker (edit: deny)
│           ├── deepcoder-worker-l0.md    # Layer 0 implementation worker
│           ├── adversarial-verifier.md   # Adversarial patch reviewer / fixer
│           └── boost-orchestrator.md     # Optional dedicated primary orchestrator
├── templates/
│   └── prompts.md                    # Mirrored templates for backward compatibility
├── examples/
│   └── workflow-walkthrough.md       # Real-world concurrency race condition walkthrough
└── scripts/
    └── verify_report.py              # Executable CLI tool to validate reports against rubric
```

---

## Multi-Agent Discovery Paths

The skill is canonically hosted in the universal agent skills repository and linked across all installed coding agents:

1. **Canonical Universal Agent Skills Repository**:
   - `~/.agents/skills/boost/`
2. **Claude Code**:
   - `~/.claude/skills/boost`
3. **OpenAI Codex**:
   - `~/.codex/skills/boost`
4. **OpenCode**:
   - `~/.config/opencode/skills/boost`
   - `~/.opencode/skills/boost`
5. **Qwen Code**:
   - `~/.qwen/skills/boost`
6. **Grok**:
   - `~/.grok/skills/boost`
7. **Junie**:
   - `~/.junie/skills/boost`
8. **KiloCode & Kilo CLI**:
   - `~/.kilocode/skills/boost`
   - `~/.config/kilo/skills/boost`
9. **OpenClaw**:
   - `~/.openclaw/skills/boost`
10. **Command Code**:
    - `~/.commandcode/skills/boost`
11. **Pi Coding Agent**:
    - `~/.pi/agent/skills/boost`
    - `~/.pi/skills/boost`
12. **GitHub Copilot**:
    - `~/.copilot/skills/boost`
13. **Cline**:
    - `~/.cline/skills/boost`
14. **OpenCodex**:
    - `~/.opencodex/skills/boost`
15. **Gemini & Antigravity**:
    - `~/.gemini/config/skills/boost/`
    - `~/.gemini/antigravity/skills/boost/`
    - `~/.gemini/skills/boost/`
    - Manifest: `~/.gemini/config/skills.json`

---

## How to Use

### In Any Agent's Chat Canvas, CLI, or TUI
Simply invoke:
```text
/boost <task description or problem statement>
```
or request "boost mode" / deep reasoning. The active agent discovers the skill via progressive disclosure, parses the authoritative `<original_task>`, and orchestrates the isolated coding and adversarial verification workers.

### Validating Completion Reports Programmatically
```bash
# Universal command (executable from any directory):
python3 ~/.agents/skills/boost/scripts/verify_report.py path/to/report.md --role worker
python3 ~/.agents/skills/boost/scripts/verify_report.py path/to/report.md --role reviewer

# Or from within the skill directory:
python3 scripts/verify_report.py path/to/report.md --role worker
python3 scripts/verify_report.py path/to/report.md --role reviewer
```
