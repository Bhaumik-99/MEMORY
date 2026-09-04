import hashlib, json, os, re, sqlite3
from pathlib import Path
from datetime import datetime, timezone

IGNORE_DIRS={".git",".agent","node_modules","venv",".venv","dist","build","coverage",".cache","__pycache__",".idea",".vscode","target","vendor"}
IGNORE_EXT={".png",".jpg",".jpeg",".gif",".webp",".ico",".pdf",".zip",".gz",".tar",".exe",".dll",".so",".dylib",".pyc",".class",".jar",".lock"}
MAX_SIZE=3_000_000

def now(): return datetime.now(timezone.utc).isoformat()
def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def should_skip(p,root):
    rel=p.relative_to(root)
    if any(x in IGNORE_DIRS for x in rel.parts): return True
    if p.suffix.lower() in IGNORE_EXT: return True
    try: return p.stat().st_size>MAX_SIZE
    except OSError: return True

def iter_files(root):
    root=Path(root).resolve()
    for p in root.rglob("*"):
        if p.is_file() and not should_skip(p,root): yield p

def load_json(path,default):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception: return default

def save_json(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def connect(db):
    Path(db).parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(db)
    c.row_factory=sqlite3.Row
    c.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS files(
      path TEXT PRIMARY KEY, hash TEXT NOT NULL, size INTEGER,
      language TEXT, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS symbols(
      id INTEGER PRIMARY KEY, path TEXT NOT NULL, name TEXT NOT NULL,
      kind TEXT, start_line INTEGER, end_line INTEGER,
      signature TEXT, source TEXT,
      UNIQUE(path,name,start_line)
    );
    CREATE TABLE IF NOT EXISTS imports(
      path TEXT, value TEXT
    );
    CREATE TABLE IF NOT EXISTS references(
      path TEXT, symbol TEXT, reference TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
    CREATE INDEX IF NOT EXISTS idx_symbols_path ON symbols(path);
    CREATE INDEX IF NOT EXISTS idx_imports_path ON imports(path);
    CREATE INDEX IF NOT EXISTS idx_refs_symbol ON references(symbol);
    """)
    return c

def language(path):
    m={
      ".py":"python",".js":"javascript",".jsx":"javascript",
      ".ts":"typescript",".tsx":"typescript",".java":"java",
      ".go":"go",".rs":"rust",".c":"c",".h":"c",
      ".cpp":"cpp",".cc":"cpp",".hpp":"cpp",".cs":"csharp",
      ".rb":"ruby",".php":"php",".kt":"kotlin",".kts":"kotlin",
      ".swift":"swift",".sql":"sql",".md":"markdown"
    }
    return m.get(path.suffix.lower(),"text")
