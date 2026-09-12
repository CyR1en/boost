#!/usr/bin/env python3
"""
verify_report.py - CLI tool to validate /boost worker and reviewer completion reports.

Usage:
  python3 verify_report.py <path_to_report.md> [--role worker|reviewer]
  python3 verify_report.py --role <worker|reviewer> <path_to_report.md>
  python3 verify_report.py - [--role worker|reviewer]  # read from stdin
"""

import argparse
import os
import re
import sys

ALLOWED_ISSUE_PREFIXES = (
    "Fatal Functional Bug",
    "Shallow Verification",
    "Minor Robustness Risk",
    "None",
)


def _parse_report_sections(content: str) -> dict[int, tuple[str, str]]:
    """
    Parses top-level numbered sections (## 1. to ## 5.) from markdown content,
    ignoring any headers that appear within fenced code blocks.
    Returns a dict mapping section number (1-5) to (title, body).
    """
    code_spans = [m.span() for m in re.finditer(r"```.*?```", content, re.DOTALL)]

    def in_code_block(pos: int) -> bool:
        return any(start <= pos < end for start, end in code_spans)

    pattern = re.compile(r"^##\s*([1-5])[\.:]\s*(.+)$", re.MULTILINE)
    matches = [m for m in pattern.finditer(content) if not in_code_block(m.start())]

    sections: dict[int, tuple[str, str]] = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end].strip()
        sections[num] = (title, body)

    return sections


def validate_report(content: str, role: str = "worker") -> tuple[bool, list[str]]:
    errors = []

    # 1. Check Skepticism Disclaimer
    if not re.search(
        r">\s*\[!(?:WARNING|CAUTION)\]\s*\*\*Skepticism Disclaimer\*\*",
        content,
        re.IGNORECASE,
    ):
        errors.append("Missing required header: '> [!WARNING] **Skepticism Disclaimer**'")

    sections = _parse_report_sections(content)

    # 2. Check Role-Specific Section 1 & 2
    if role == "reviewer":
        if 1 not in sections or not re.match(
            r"^what\s+the\s+prior\s+attempt\s+got\s+wrong",
            sections[1][0],
            re.IGNORECASE,
        ):
            errors.append("Missing required section: '## 1. What the prior attempt got wrong'")
        else:
            substance = sections[1][1]
            sub_lower = substance.lower()
            nothing_wrong = (
                "genuinely nothing was wrong" in sub_lower
                or substance.strip().lower().rstrip(".") in ("none", "n/a", "no defects", "no issues", "no bugs found")
            )
            if not nothing_wrong:
                required_tokens = ["input", "expected", "actual", "root cause"]
                missing_tokens = []
                if "input" not in sub_lower:
                    missing_tokens.append("input")
                if "expected" not in sub_lower:
                    missing_tokens.append("expected")
                if "actual" not in sub_lower:
                    missing_tokens.append("actual")
                if not re.search(r"root[-_\s]cause", sub_lower):
                    missing_tokens.append("root cause")
                if missing_tokens:
                    errors.append(
                        f"Reviewer defect section missing required root-cause tokens: {missing_tokens}"
                    )

        if 2 not in sections or not re.match(
            r"^what\s+i\s+changed",
            sections[2][0],
            re.IGNORECASE,
        ):
            errors.append("Missing required section: '## 2. What I changed'")
    else:  # worker
        if 1 not in sections or not re.match(
            r"^what\s+i\s+changed",
            sections[1][0],
            re.IGNORECASE,
        ):
            errors.append("Missing required section: '## 1. What I changed'")

        if 2 not in sections or not re.match(
            r"^why\b",
            sections[2][0],
            re.IGNORECASE,
        ):
            errors.append("Missing required section: '## 2. Why'")

    # 3. Check Verification Record
    if 3 not in sections or not re.match(
        r"^verification\s+record",
        sections[3][0],
        re.IGNORECASE,
    ):
        errors.append("Missing required section: '## 3. Verification Record'")
    else:
        verif_section = sections[3][1]
        if not re.search(r"deep\s+verification", verif_section, re.IGNORECASE):
            errors.append("Verification Record missing '**Deep Verification**' entry")
        if not re.search(r"shallow\s+verification", verif_section, re.IGNORECASE):
            errors.append("Verification Record missing '**Shallow Verification**' entry")
        if not re.search(r"unverified\s+aspects", verif_section, re.IGNORECASE):
            errors.append("Verification Record missing '**Unverified aspects**' entry")

    # 4. Check Known Issues & Severity Prefixes
    if 4 not in sections or not re.match(
        r"^known\s+issues",
        sections[4][0],
        re.IGNORECASE,
    ):
        errors.append("Missing required section: '## 4. Known Issues'")
    else:
        issues_section = sections[4][1]
        raw_lines = [line.strip() for line in issues_section.splitlines() if line.strip()]

        # Filter out known instruction template lines
        filtered_lines = []
        for line in raw_lines:
            low = line.lower()
            if (
                low.startswith("prefix each with one of:")
                or low.startswith("prefixed `fatal functional bug`")
                or low.startswith("prefix each issue with:")
                or low.startswith("- `fatal functional bug` — core logic does not work")
                or low.startswith("- `fatal functional bug` — it does not work")
                or low.startswith("- `shallow verification` — plausibly works")
                or low.startswith("- `minor robustness risk` — edge case")
                or low.startswith("- `minor robustness risk` — low-probability")
            ):
                continue
            filtered_lines.append(line)

        if not filtered_lines:
            errors.append("Section '## 4. Known Issues' is empty or contains only unedited template placeholder text.")
        else:
            bullet_lines = [l for l in filtered_lines if re.match(r"^(?:[-*]|\d+[\.)])\s+", l)]
            if bullet_lines:
                for line in bullet_lines:
                    clean_line = re.sub(r"^(?:[-*]|\d+[\.)])\s*[`*\[(]*", "", line).strip()
                    has_valid_prefix = any(
                        clean_line.lower().startswith(prefix.lower())
                        for prefix in ALLOWED_ISSUE_PREFIXES
                    )
                    if not has_valid_prefix:
                        errors.append(
                            f"Known Issue '{line}' does not start with one of: {ALLOWED_ISSUE_PREFIXES}"
                        )
            else:
                # No bullet lines. Check if content is None / N/A
                non_none = [
                    l
                    for l in filtered_lines
                    if l.lower().rstrip(".") not in ("none", "n/a", "no known issues", "no issues")
                ]
                if not non_none:
                    pass  # Explicitly 'None'
                else:
                    for line in non_none:
                        clean_line = re.sub(r"^[`*\[(]*", "", line).strip()
                        has_valid_prefix = any(
                            clean_line.lower().startswith(prefix.lower())
                            for prefix in ALLOWED_ISSUE_PREFIXES
                        )
                        if not has_valid_prefix:
                            errors.append(
                                f"Known Issue '{line}' does not start with one of: {ALLOWED_ISSUE_PREFIXES}"
                            )

    # 5. Check Section 5 (Next steps / Untested Edge Cases)
    if role == "reviewer":
        if 5 not in sections or not (
            re.match(r"^remaining\s+risks?\s+&\s+next\s+steps?", sections[5][0], re.IGNORECASE)
            or re.match(r"^untested\s+edge\s+cases", sections[5][0], re.IGNORECASE)
        ):
            errors.append("Missing required section: '## 5. Remaining risk & next step'")
    else:
        if 5 not in sections or not re.match(
            r"^untested\s+edge\s+cases\s+&\s+next\s+steps?",
            sections[5][0],
            re.IGNORECASE,
        ):
            errors.append("Missing required section: '## 5. Untested Edge Cases & Next Step'")

    return len(errors) == 0, errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate /boost worker and reviewer completion reports against the verification rubric."
    )
    parser.add_argument(
        "report_path",
        metavar="path_to_report.md",
        help="Path to markdown report file to validate (use '-' for standard input)",
    )
    parser.add_argument(
        "--role",
        "-r",
        choices=["worker", "reviewer"],
        default="worker",
        type=str.lower,
        help="Report author role: 'worker' (default) or 'reviewer'",
    )

    args = parser.parse_args(argv)

    report_path = args.report_path
    role = args.role

    if report_path == "-":
        try:
            content = sys.stdin.read()
        except Exception as e:
            print(f"Error reading from stdin: {e}")
            sys.exit(1)
    else:
        if not os.path.exists(report_path):
            print(f"Error: File '{report_path}' not found.")
            sys.exit(1)

        if os.path.isdir(report_path):
            print(f"Error: '{report_path}' is a directory.")
            sys.exit(1)

        try:
            with open(report_path, "rb") as f:
                raw = f.read()
            for enc in ("utf-8-sig", "utf-16", "latin-1"):
                try:
                    content = raw.decode(enc)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                content = raw.decode("utf-8", errors="replace")
        except Exception as e:
            print(f"Error reading file '{report_path}': {e}")
            sys.exit(1)

    passed, errors = validate_report(content, role)
    if passed:
        print(f"✓ Report at '{report_path}' conforms to /boost verification rubric (role: {role}).")
        sys.exit(0)
    else:
        print(f"✗ Report at '{report_path}' failed /boost verification rubric (role: {role}):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
