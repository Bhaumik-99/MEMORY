#!/usr/bin/env python3
import argparse
from pathlib import Path
from memory_utils import *

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    args=ap.parse_args()
    root=Path(args.root).resolve()
    db=root/".agent/index.db"
    if not db.exists():
        print("No index.db. Run index_repo.py first."); return
    c=connect(db)
    current={p.relative_to(root).as_posix():sha256(p) for p in iter_files(root)}
    indexed={r["path"]:r["hash"] for r in c.execute("SELECT path,hash FROM files")}
    changed=[p for p,h in current.items() if p in indexed and indexed[p]!=h]
    added=[p for p in current if p not in indexed]
    deleted=[p for p in indexed if p not in current]
    print(f"Changed: {len(changed)}")
    for p in changed[:100]: print("  CHANGED",p)
    print(f"Added: {len(added)}")
    for p in added[:100]: print("  ADDED  ",p)
    print(f"Deleted: {len(deleted)}")
    for p in deleted[:100]: print("  DELETED",p)
    if not changed and not added and not deleted: print("Index is fresh.")

if __name__=="__main__": main()
