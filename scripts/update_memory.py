#!/usr/bin/env python3
import argparse
from pathlib import Path
from memory_utils import load_json,save_json

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="."); ap.add_argument("--task"); ap.add_argument("--status"); ap.add_argument("--goal")
    for n in ["file","symbol","change","decision","issue","next"]: ap.add_argument("--add-"+n,action="append",default=[])
    ap.add_argument("--test-status"); ap.add_argument("--test-command"); ap.add_argument("--test-failure",action="append",default=[])
    args=ap.parse_args(); root=Path(args.root).resolve(); p=root/".agent/state.json"
    s=load_json(p,{"task":"","status":"idle","goal":"","relevant_files":[],"relevant_symbols":[],"recent_changes":[],"decisions":[],"known_issues":[],"next_steps":[],"tests":{"status":"unknown","command":"","failures":[]}})
    for k in ["task","status","goal"]:
        v=getattr(args,k)
        if v is not None: s[k]=v
    for key,arg in [("relevant_files","file"),("relevant_symbols","symbol"),("recent_changes","change"),("decisions","decision"),("known_issues","issue"),("next_steps","next")]:
        for v in getattr(args,"add_"+arg):
            if v not in s[key]: s[key].append(v)
    if args.test_status is not None: s["tests"]["status"]=args.test_status
    if args.test_command is not None: s["tests"]["command"]=args.test_command
    s["tests"]["failures"]=(s["tests"].get("failures",[])+args.test_failure)[-20:]
    for k in ["recent_changes","decisions","known_issues","next_steps"]: s[k]=s[k][-20:]
    s["relevant_files"]=s["relevant_files"][-30:]; s["relevant_symbols"]=s["relevant_symbols"][-50:]
    save_json(p,s); print("Memory updated.")
if __name__=="__main__": main()
