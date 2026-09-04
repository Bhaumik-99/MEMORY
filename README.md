# Repository Working Memory — Antigravity v2

This version adds an incremental SQLite index, optional Tree-sitter AST parsing, symbol search, file hashes, stale detection, and memory management.

## Install in a project

Copy this folder to:

    .agents/skills/repository-working-memory/

## Recommended first run

From the repository root:

    python .agents/skills/repository-working-memory/scripts/init_memory.py --root .
    python .agents/skills/repository-working-memory/scripts/index_repo.py --root .

Optional AST upgrade:

    pip install tree-sitter tree-sitter-language-pack

Then re-index:

    python .agents/skills/repository-working-memory/scripts/index_repo.py --root .

## Query

Exact symbol:

    python .agents/skills/repository-working-memory/scripts/query_repo.py --root . --symbol AuthService.login

Semantic-style lexical search:

    python .agents/skills/repository-working-memory/scripts/query_repo.py --root . --search "payment retry timeout"

Freshness:

    python .agents/skills/repository-working-memory/scripts/check_stale.py --root .

Update memory:

    python .agents/skills/repository-working-memory/scripts/update_memory.py --root . --task "Add retry logic" --status implementing

The Antigravity agent should use the skill automatically for repository coding tasks.
