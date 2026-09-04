---
name: repository-working-memory
description: Persistent, incremental repository memory for coding agents. Automatically use for repository coding, debugging, refactoring, testing, code review, and architecture tasks. Maintains compact project state, architecture, repository map, symbol index, dependency/call relationships, file hashes, recent changes, decisions, and next steps so the agent retrieves targeted code instead of rereading the entire repository.
---

# Repository Working Memory

## Mission

Maintain persistent, verified, compact knowledge of the current repository.

For every repository task:

MEMORY → FRESHNESS → TARGETED RETRIEVAL → CHANGE → TEST → MEMORY UPDATE

Do not reread the entire repository by default.

Source code is authoritative. Memory is a cache of verified engineering facts.

## Project memory

Use:

```text
.agent/
├── state.json
├── architecture.md
├── decisions.md
├── repo_map.json
└── index.db
```

Do not store conversations, chain-of-thought, secrets, credentials, API keys, passwords, or tokens.

## Skill tools

From this skill directory, the helper commands are:

```bash
python scripts/init_memory.py --root .
python scripts/index_repo.py --root .
python scripts/check_stale.py --root .
python scripts/query_repo.py --root . --symbol "AuthService.login"
python scripts/query_repo.py --root . --search "authentication login"
python scripts/update_memory.py --root . --task "..." --status implementing
```

When the repository is large, prefer `index_repo.py` + `query_repo.py` over manual repository-wide reading.

The index is SQLite and is incremental.

## First use

If `.agent/` does not exist:

1. Run `init_memory.py`.
2. Run `index_repo.py`.
3. Read the generated map only as needed.
4. Identify project instructions and important architecture.
5. Do not load all source files into context.

## Every coding prompt

For every repository-related request:

1. Locate repository root.
2. Load `.agent/state.json`.
3. Load relevant architecture information.
4. Check stale files.
5. Search the symbol/semantic index.
6. Retrieve only relevant source.
7. Expand dependencies/callers/tests as needed.
8. Make the change.
9. Run relevant checks/tests.
10. Inspect the final diff.
11. Incrementally update the index.
12. Update working memory.

Do not ask the user to activate this skill manually.

## Instruction precedence

Inspect and respect repository instructions such as:

```text
AGENTS.md
CLAUDE.md
GEMINI.md
README.md
CONTRIBUTING.md
```

Local project instructions take precedence over generic assumptions in this skill.

## Retrieval strategy

Start with:

```text
user request
→ state.json
→ project instructions
→ symbol search
→ semantic search
→ exact source ranges
```

Then expand:

```text
target symbol
→ direct dependencies
→ callers
→ related interfaces/types
→ relevant tests
```

Only broaden further when required.

## Symbol-level context

Prefer symbols over arbitrary chunks.

For each relevant symbol, retrieve:

- file
- symbol name
- type
- start/end lines
- signature
- source
- imports
- callers
- callees
- tests when available

Example:

```text
AuthService.login
  file: src/auth/service.py
  lines: 42-78
  calls:
    UserRepository.get_by_email
    create_access_token
  called by:
    POST /auth/login
```

## Incremental SQLite index

`index.db` stores:

```text
files
symbols
imports
references
tests
```

It should be incrementally updated.

Do not delete/rebuild the database merely because one file changed.

Use file hashes to identify changed files.

## Tree-sitter

The indexer supports Tree-sitter when installed.

If Tree-sitter and the appropriate language grammar are available:

- parse the source AST
- extract functions
- classes
- methods
- interfaces
- types
- imports
- calls/references where the grammar permits

If Tree-sitter is unavailable for a language, fall back to lightweight regex extraction.

Never fail the entire memory system because one language lacks a parser.

The index must remain useful in mixed-language repositories.

## Supported parser behavior

Prefer Tree-sitter for common languages such as:

```text
Python
JavaScript
TypeScript
Java
C
C++
Go
Rust
C#
Ruby
PHP
Kotlin
```

The implementation may use installed grammars only. Do not assume every grammar exists.

## File freshness

Run:

```bash
python scripts/check_stale.py --root .
```

before relying heavily on cached information.

If relevant files changed:

1. Re-index only changed files.
2. Remove stale symbols/references for those files.
3. Reinsert current information.
4. Continue.

Current source code always wins over memory.

## Semantic search

Use semantic search when exact symbol search is insufficient.

If embeddings are available, use them.

If embeddings are unavailable, use lexical/FTS search.

The system must work without a paid embedding API.

Never require internet access merely to maintain repository memory.

## Context budget

Do not send the full index database to the LLM.

Do not send the entire repository unless explicitly necessary.

Construct context from:

```text
project rules
+
task state
+
relevant symbols
+
relevant source
+
dependencies
+
tests
+
recent changes
```

Prefer exact source ranges over entire files.

## Broad tasks

Full or broad repository inspection is acceptable when:

- the user explicitly requests architecture analysis
- a global refactor requires it
- dependency relationships cannot otherwise be established
- security/correctness requires broader inspection
- the repository is genuinely small

Even then:

inspect → summarize → persist

Do not repeatedly rediscover the same facts.

## Memory updates

After meaningful changes, update:

```text
state.json
repo_map.json
index.db
```

Update:

```text
architecture.md
decisions.md
```

only when durable architecture or engineering decisions changed.

## Test memory

Record important test commands/results in state.json.

Never claim tests passed unless they actually ran successfully.

## Git

Use Git selectively:

```bash
git status
git diff
git log
```

Inspect relevant history when useful.

Do not put complete Git history into model context.

## Security

Never persist:

- API keys
- passwords
- access tokens
- private keys
- `.env` values
- credentials

Ignore by default:

```text
.git
.agent
node_modules
venv
.venv
dist
build
coverage
.cache
__pycache__
```

and binary/large generated files.

## Compression

Working memory must remain small.

Keep:

- current task
- relevant files
- relevant symbols
- durable decisions
- known issues
- current tests
- next steps

Remove:

- old tool output
- obsolete task state
- duplicated facts
- completed steps
- source code copied into memory

Never store private reasoning.

## Completion

Before finishing:

1. Verify requested behavior.
2. Run relevant tests/checks.
3. Inspect `git diff`.
4. Refresh changed files in the index.
5. Update `state.json`.
6. Update architecture/decisions if needed.

Then mark the task complete.

## Core principle

Do not make the model memorize the repository.

Make the repository cheaply searchable, incrementally indexed, and safely retrievable.
