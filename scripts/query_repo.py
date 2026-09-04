#!/usr/bin/env python3
import argparse, sqlite3
from pathlib import Path
from memory_utils import connect

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--symbol")
    ap.add_argument("--search")
    ap.add_argument("--limit",type=int,default=10)
    args=ap.parse_args()
    db=Path(args.root).resolve()/".agent/index.db"
    if not db.exists():
        print("No index.db. Run: python scripts/index_repo.py --root .")
        return 2
    c=connect(db)

    if args.symbol:
        q=args.symbol.split(".")[-1]
        rows=c.execute("""SELECT path,name,kind,start_line,end_line,signature,source
                          FROM symbols WHERE name LIKE ? ORDER BY path LIMIT ?""",(q,args.limit)).fetchall()
        for r in rows:
            print(f"\n{r['path']}:{r['start_line']}-{r['end_line']}  {r['kind']} {r['name']}")
            print(r['signature'])
            if r["source"]: print(r["source"][:8000])

    elif args.search:
        terms=[x for x in args.search.lower().split() if x]
        rows=[]
        for r in c.execute("SELECT path,name,kind,start_line,end_line,signature,source FROM symbols").fetchall():
            blob=(" ".join(str(r[k] or "") for k in ["path","name","kind","signature","source"])).lower()
            score=sum(1 for t in terms if t in blob)
            if score: rows.append((score,r))
        rows.sort(key=lambda x:(-x[0],x[1]["path"],x[1]["start_line"]))
        for score,r in rows[:args.limit]:
            print(f"\n[{score}] {r['path']}:{r['start_line']}-{r['end_line']} {r['kind']} {r['name']}")
            print(r["signature"])
            if r["source"]: print(r["source"][:5000])
    else:
        print("Use --symbol NAME or --search WORDS")
        return 1

if __name__=="__main__": raise SystemExit(main())
