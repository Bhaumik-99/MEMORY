#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from memory_utils import save_json, now

STATE={
 "task":"","status":"idle","goal":"",
 "relevant_files":[],"relevant_symbols":[],"recent_changes":[],
 "decisions":[],"known_issues":[],"next_steps":[],
 "tests":{"status":"unknown","command":"","failures":[]}
}
ARCH="""# Architecture

This file stores durable project architecture facts.

## Project
- Type: unknown
- Entry point: unknown

## Structure
- Add important modules and relationships here.

## Conventions
- Add durable conventions here.

## Constraints
- Add architectural constraints here.
"""
DECISIONS="# Engineering Decisions\n\nRecord durable engineering decisions here.\n"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); args=ap.parse_args()
    root=Path(args.root).resolve(); a=root/".agent"; a.mkdir(exist_ok=True)
    if not (a/"state.json").exists(): save_json(a/"state.json",STATE)
    if not (a/"architecture.md").exists(): (a/"architecture.md").write_text(ARCH,encoding="utf-8")
    if not (a/"decisions.md").exists(): (a/"decisions.md").write_text(DECISIONS,encoding="utf-8")
    if not (a/"repo_map.json").exists(): save_json(a/"repo_map.json",{"generated_at":now(),"root":str(root),"files":{}})
    print(f"Initialized {a}")
if __name__=="__main__": main()
