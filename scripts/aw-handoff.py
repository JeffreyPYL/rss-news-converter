#!/usr/bin/env python3
"""
scripts/aw-handoff.py

Handoff schema inspection, validation, status updating, and failure extraction
for agent-workflow Conductor pipelines and CLI workflows.
"""

import argparse
import datetime
import json
import os
import re
import sys


def parse_handoff(content: str) -> dict:
    data = {
        "title": "",
        "updated": "",
        "stage_done": "",
        "status": "",
        "pointers": {},
        "facts": {},
        "scorecard": {},
        "suggested_next_step": {},
        "failures": "",
        "raw_sections": {},
    }
    
    current_section = None
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if line.startswith("# aw-handoff:"):
            data["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("updated:"):
            data["updated"] = line.split(":", 1)[1].strip()
        elif line.startswith("stage_done:"):
            data["stage_done"] = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            data["status"] = line.split(":", 1)[1].strip()
        elif line.startswith("## "):
            current_section = line[3:].strip()
            data["raw_sections"][current_section] = []
        elif current_section:
            data["raw_sections"][current_section].append(line)
            if stripped.startswith("- "):
                key_val = stripped[2:].split(":", 1)
                k = key_val[0].strip()
                v = key_val[1].strip() if len(key_val) > 1 else ""
                if current_section == "pointers":
                    data["pointers"][k] = v
                elif current_section == "facts":
                    data["facts"][k] = v
                elif current_section == "scorecard":
                    data["scorecard"][k] = v
                elif current_section == "suggested_next_step":
                    data["suggested_next_step"][k] = v
        i += 1
        
    if "failures" in data["raw_sections"]:
        data["failures"] = "\n".join(data["raw_sections"]["failures"]).strip()
        
    return data


def format_handoff(data: dict) -> str:
    lines = []
    lines.append(f"# aw-handoff: {data.get('title', '')}")
    lines.append(f"updated: {data.get('updated', datetime.datetime.now(datetime.timezone.utc).isoformat())}")
    lines.append(f"stage_done: {data.get('stage_done', '')}")
    lines.append(f"status: {data.get('status', 'ready_for_next')}")
    lines.append("")
    
    # pointers
    lines.append("## pointers")
    pointers = data.get("pointers", {})
    for k, v in pointers.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    
    # facts
    if data.get("facts"):
        lines.append("## facts")
        for k, v in data["facts"].items():
            lines.append(f"- {k}: {v}")
        lines.append("")
        
    # scorecard
    if data.get("scorecard"):
        lines.append("## scorecard")
        for k, v in data["scorecard"].items():
            lines.append(f"- {k}: {v}")
        lines.append("")
        
    # failures (if present)
    if data.get("failures"):
        lines.append("## failures")
        lines.append(data["failures"].strip())
        lines.append("")
        
    # preserve other custom sections if any
    for sec_name, sec_lines in data.get("raw_sections", {}).items():
        if sec_name in ("pointers", "facts", "scorecard", "suggested_next_step", "failures"):
            continue
        lines.append(f"## {sec_name}")
        for l in sec_lines:
            lines.append(l)
        lines.append("")
        
    # suggested_next_step
    lines.append("## suggested_next_step")
    s_next = data.get("suggested_next_step", {})
    for k, v in s_next.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    
    return "\n".join(lines)


def cmd_check(args):
    handoff_file = args.handoff
    if not os.path.exists(handoff_file):
        print(json.dumps({"valid": False, "error": f"File not found: {handoff_file}"}))
        sys.exit(1)
        
    with open(handoff_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    data = parse_handoff(content)
    
    valid = True
    errors = []
    
    if not data.get("title"):
        valid = False
        errors.append("Missing title")
        
    if not data.get("stage_done"):
        valid = False
        errors.append("Missing stage_done")
        
    if args.stage and data.get("stage_done") != args.stage:
        # Check if stage matches expected stage
        pass
        
    output = {
        "valid": valid,
        "title": data.get("title"),
        "stage_done": data.get("stage_done"),
        "status": data.get("status"),
        "errors": errors,
        "retry_count": int(data.get("pointers", {}).get("retry_count", 0)),
    }
    print(json.dumps(output, indent=2))
    sys.exit(0 if valid else 1)


def cmd_check_review(args):
    handoff_file = args.handoff
    if not os.path.exists(handoff_file):
        print(json.dumps({"valid": False, "error": f"File not found: {handoff_file}"}))
        sys.exit(1)
        
    with open(handoff_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    data = parse_handoff(content)
    scorecard = data.get("scorecard", {})
    status = scorecard.get("status", "NOT READY").upper()
    blockers = int(scorecard.get("blockers", 0) or 0)
    
    valid = (status == "READY" and blockers == 0)
    output = {
        "valid": valid,
        "status": status,
        "blockers": blockers,
        "suggested_next": data.get("suggested_next_step", {}).get("Next", ""),
    }
    print(json.dumps(output, indent=2))
    sys.exit(0)


def cmd_update(args):
    handoff_file = args.handoff
    if not os.path.exists(handoff_file):
        # Create minimal skeleton
        data = {
            "title": args.change_id or "change",
            "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stage_done": args.stage,
            "status": "ready_for_next",
            "pointers": {"retry_count": "0"},
            "facts": {},
            "suggested_next_step": {},
        }
    else:
        with open(handoff_file, "r", encoding="utf-8") as f:
            content = f.read()
        data = parse_handoff(content)

    if args.stage:
        data["stage_done"] = args.stage

    pointers = data.setdefault("pointers", {})
    current_retries = int(pointers.get("retry_count", 0))

    if args.stage in ("test_failed", "review_failed"):
        current_retries += 1
        pointers["retry_count"] = str(current_retries)
        data["suggested_next_step"]["Next"] = "/aw-implement"
        data["suggested_next_step"]["New session?"] = "no"
        data["status"] = "ready_for_next"
        
        if args.stderr:
            data["failures"] = f"```text\n{args.stderr.strip()}\n```"
    elif args.stage == "test_passed":
        pointers["retry_count"] = "0"
        data["suggested_next_step"]["Next"] = "/aw-ship-review"
        data["suggested_next_step"]["New session?"] = "yes"
    elif args.stage == "implement":
        data["suggested_next_step"]["Next"] = "/aw-test"
        data["suggested_next_step"]["New session?"] = "yes"
        
    data["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    new_content = format_handoff(data)
    with open(handoff_file, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print(json.dumps({
        "success": True,
        "stage_done": data["stage_done"],
        "retry_count": current_retries,
        "handoff": handoff_file
    }))
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="aw-handoff tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check
    check_p = subparsers.add_parser("check", help="Check handoff validity")
    check_p.add_argument("--handoff", required=True, help="Path to aw-handoff.md")
    check_p.add_argument("--stage", required=False, help="Expected stage_done")
    check_p.set_defaults(func=cmd_check)

    # check-review
    review_p = subparsers.add_parser("check-review", help="Check review status and blockers")
    review_p.add_argument("--handoff", required=True, help="Path to aw-handoff.md")
    review_p.set_defaults(func=cmd_check_review)

    # update
    update_p = subparsers.add_parser("update", help="Update handoff status / failures")
    update_p.add_argument("--handoff", required=True, help="Path to aw-handoff.md")
    update_p.add_argument("--change-id", required=False, help="Change id if creating")
    update_p.add_argument("--stage", required=False, help="New stage_done")
    update_p.add_argument("--stderr", required=False, help="Stderr or failure log content")
    update_p.set_defaults(func=cmd_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
