#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path
from memory_utils import *

def treesitter_extract(text, lang):
    try:
        from tree_sitter import Parser
    except Exception:
        return None
    # Grammar loading varies across tree-sitter versions and installations.
    # Use tree-sitter-language-pack when available.
    try:
        from tree_sitter_language_pack import get_parser
        parser=get_parser(lang)
    except Exception:
        return None

    tree=parser.parse(text.encode("utf-8","ignore"))
    root=tree.root_node
    names={"function_definition","function_declaration","method_definition",
           "class_definition","class_declaration","interface_declaration",
           "struct_item","impl_item","function_item","type_declaration",
           "method_declaration","constructor_declaration"}
    out=[]
    def walk(n):
        if n.type in names:
            snippet=text.splitlines()[n.start_point[0]:n.end_point[0]+1]
            src="\n".join(snippet)
            name=""
            for ch in n.children:
                if ch.type in ("identifier","type_identifier","property_identifier"):
                    name=text[ch.start_byte:ch.end_byte]
                    break
            if name:
                first=snippet[0].strip() if snippet else name
                out.append((name,n.type,n.start_point[0]+1,n.end_point[0]+1,first,src))
        for ch in n.children: walk(ch)
    walk(root)
    return out

REGEX={
"python":[
(re.compile(r'^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\((.*?)\)\s*(?:->\s*(.*?))?:'),"function"),
(re.compile(r'^\s*class\s+([A-Za-z_]\w*)'),"class")],
"javascript":[
(re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)'),"function"),
(re.compile(r'^\s*(?:export\s+)?class\s+([A-Za-z_]\w*)'),"class")],
"typescript":[
(re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)'),"function"),
(re.compile(r'^\s*(?:export\s+)?class\s+([A-Za-z_]\w*)'),"class"),
(re.compile(r'^\s*(?:export\s+)?interface\s+([A-Za-z_]\w*)'),"interface")],
"java":[
(re.compile(r'^\s*(?:public|private|protected|static|final|abstract|\s)+class\s+([A-Za-z_]\w*)'),"class"),
(re.compile(r'^\s*(?:public|private|protected|static|final|abstract|\s)+[\w<>\[\]]+\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:throws [^{]+)?\{'),"method")],
"go":[
(re.compile(r'^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\('),"function"),
(re.compile(r'^\s*type\s+([A-Za-z_]\w*)\s+struct'),"struct")],
"rust":[
(re.compile(r'^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)'),"function"),
(re.compile(r'^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)'),"struct"),
(re.compile(r'^\s*(?:pub\s+)?enum\s+([A-Za-z_]\w*)'),"enum")],
"c":[
(re.compile(r'^\s*(?:[\w\*\s]+)\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{'),"function")],
"cpp":[
(re.compile(r'^\s*(?:[\w:\<\>\*&\s]+)\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{'),"function"),
(re.compile(r'^\s*class\s+([A-Za-z_]\w*)'),"class")],
"csharp":[
(re.compile(r'^\s*(?:public|private|protected|internal|abstract|sealed|\s)+class\s+([A-Za-z_]\w*)'),"class"),
(re.compile(r'^\s*(?:public|private|protected|internal|static|async|\s)+[\w<>\[\]?]+\s+([A-Za-z_]\w*)\s*\('),"method")]
}

def regex_extract(text,lang):
    out=[]; lines=text.splitlines()
    for i,line in enumerate(lines,1):
        for pat,kind in REGEX.get(lang,[]):
            m=pat.match(line)
            if m:
                out.append((m.group(1),kind,i,min(len(lines),i+100),line.strip(),line.strip()))
                break
    return out

def imports(text,lang):
    pats={
      "python":[r'^\s*(?:from\s+.+\s+)?import\s+.+'],
      "javascript":[r'^\s*import\s+.+',r'^\s*(?:const|let|var).+require\(.+\)'],
      "typescript":[r'^\s*import\s+.+'],
      "java":[r'^\s*import\s+.+;'],
      "go":[r'^\s*"[^"]+"',r'^\s*import\s+'],
      "rust":[r'^\s*(?:pub\s+)?use\s+.+;'],
      "c":[r'^\s*#include\s+[<"].+[>"]'],
      "cpp":[r'^\s*#include\s+[<"].+[>"]'],
      "csharp":[r'^\s*using\s+.+;'],
      "ruby":[r'^\s*(?:require|load)\s+.+'],
      "php":[r'^\s*(?:use|require|include).+;']
    }
    result=[]
    for line in text.splitlines():
        if any(re.match(p,line) for p in pats.get(lang,[])): result.append(line.strip())
    return result[:200]

def calls(text):
    # Lightweight reference extraction; Tree-sitter remains the preferred parser.
    return re.findall(r'\b([A-Za-z_]\w*)\s*\(',text)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--full",action="store_true")
    args=ap.parse_args()
    root=Path(args.root).resolve()
    agent=root/".agent"; agent.mkdir(exist_ok=True)
    db=agent/"index.db"
    con=connect(db)

    if args.full:
        con.execute("DELETE FROM symbols"); con.execute("DELETE FROM imports"); con.execute("DELETE FROM references"); con.execute("DELETE FROM files")
        con.commit()

    current={}
    for p in iter_files(root):
        rel=p.relative_to(root).as_posix()
        try: h=sha256(p); size=p.stat().st_size; text=p.read_text(encoding="utf-8",errors="ignore")
        except Exception: continue
        current[rel]=h
        old=con.execute("SELECT hash FROM files WHERE path=?",(rel,)).fetchone()
        if old and old["hash"]==h: continue

        con.execute("DELETE FROM symbols WHERE path=?",(rel,))
        con.execute("DELETE FROM imports WHERE path=?",(rel,))
        con.execute("DELETE FROM references WHERE path=?",(rel,))

        lang=language(p)
        extracted=treesitter_extract(text,lang)
        if extracted is None: extracted=regex_extract(text,lang)

        for name,kind,start,end,sig,src in extracted:
            con.execute("""INSERT OR REPLACE INTO symbols
              (path,name,kind,start_line,end_line,signature,source)
              VALUES (?,?,?,?,?,?,?)""",(rel,name,kind,start,end,sig,src[:20000]))
        for imp in imports(text,lang):
            con.execute("INSERT INTO imports(path,value) VALUES(?,?)",(rel,imp))
        for ref in calls(text)[:2000]:
            con.execute("INSERT INTO references(path,symbol,reference) VALUES(?,?,?)",(rel,"",ref))
        con.execute("""INSERT OR REPLACE INTO files(path,hash,size,language,updated_at)
                       VALUES(?,?,?,?,?)""",(rel,h,size,lang,now()))
        con.commit()

    # Remove deleted files.
    indexed=[r["path"] for r in con.execute("SELECT path FROM files").fetchall()]
    for rel in indexed:
        if rel not in current:
            con.execute("DELETE FROM files WHERE path=?",(rel,))
            con.execute("DELETE FROM symbols WHERE path=?",(rel,))
            con.execute("DELETE FROM imports WHERE path=?",(rel,))
            con.execute("DELETE FROM references WHERE path=?",(rel,))
    con.commit()

    # Human-readable repo map.
    files={}
    for r in con.execute("SELECT * FROM files ORDER BY path"):
        syms=[dict(x) for x in con.execute("SELECT name,kind,start_line,end_line,signature FROM symbols WHERE path=? ORDER BY start_line",(r["path"],))]
        files[r["path"]]={"hash":r["hash"],"size":r["size"],"language":r["language"],"symbols":syms}
    save_json(agent/"repo_map.json",{"generated_at":now(),"root":str(root),"files":files})
    print(f"Indexed/verified {len(files)} files. Database: {db}")

if __name__=="__main__": main()
