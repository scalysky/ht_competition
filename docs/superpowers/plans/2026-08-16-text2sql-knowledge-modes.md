# Text-to-SQL Knowledge Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit `Full` and `None` knowledge modes to the competition runner, default to the complete knowledge base, show the active mode in the terminal, document both workflows, and locally run the no-knowledge baseline.

**Architecture:** A focused knowledge loader recursively builds deterministic prompt context from `.knowledge/**/*.md`, while the launcher selects the mode and the generator prints and records it. The existing question generation and evaluator remain unchanged; their checkpoint fingerprint naturally changes because the final prompt context changes.

**Tech Stack:** Python 3.9+, Windows PowerShell, `unittest`, PostgreSQL `psql`, OpenAI-compatible Chat Completions.

## Global Constraints

- `Full` is the default mode; `None` must be explicit.
- `Full` loads every non-empty Markdown file under `workspace/skills/at2s/.knowledge` in deterministic relative-path order.
- `None` must not read or include any knowledge-base content.
- The terminal and `run_metadata.json` record the active mode.
- Standard SQL is never sent to the model; database access remains read-only.
- No API key, database password, or `.env` value may be logged or committed.

---

### Task 1: Knowledge loader

**Files:**
- Create: `workspace/standard/text2sql_runner/knowledge.py`
- Create: `workspace/standard/text2sql_runner/tests/test_knowledge.py`

**Interfaces:**
- Produces: `KnowledgeContext(mode: str, files: tuple[str, ...], content: str)`.
- Produces: `load_knowledge_context(mode: str, root: Path) -> KnowledgeContext`.
- Produces: `combine_schema_and_knowledge(schema: str, context: KnowledgeContext) -> str`.

- [ ] Write tests proving `Full` recursively loads and sorts every non-empty Markdown file, `None` does not require the directory, and empty `Full` input fails.
- [ ] Run `python -m unittest workspace.standard.text2sql_runner.tests.test_knowledge -v` and verify the new tests fail because the module does not exist.
- [ ] Implement the minimal loader and prompt combiner.
- [ ] Re-run the focused tests and verify they pass.

### Task 2: Generator and launcher modes

**Files:**
- Modify: `workspace/standard/text2sql_runner/generate.py`
- Modify: `run_text2sql.ps1`
- Modify: `workspace/standard/text2sql_runner/tests/test_generate.py`
- Modify: `workspace/standard/text2sql_runner/tests/test_launcher.py`

**Interfaces:**
- CLI consumes: `--knowledge-mode Full|None`, default `Full`.
- PowerShell consumes: `-KnowledgeMode Full|None`, default `Full`.

- [ ] Add tests for generator default/explicit mode and launcher forwarding.
- [ ] Run the focused tests and verify they fail for the missing options.
- [ ] Wire the loader into the generator, print the selected mode and loaded paths, and forward the PowerShell parameter.
- [ ] Re-run focused tests and verify they pass.

### Task 3: Run metadata

**Files:**
- Modify: `workspace/standard/text2sql_runner/outputs.py`
- Modify: `workspace/standard/text2sql_runner/tests/test_outputs.py`
- Modify: `workspace/standard/text2sql_runner/generate.py`

**Interfaces:**
- Produces: `write_run_metadata(output_dir: Path, *, knowledge_mode: str, knowledge_files: tuple[str, ...], model: str) -> Path`.

- [ ] Add a test that metadata contains only the mode, relative knowledge file list, model and generated timestamp.
- [ ] Run the focused test and verify it fails because the writer does not exist.
- [ ] Implement atomic metadata output and call it before model generation.
- [ ] Re-run focused tests and verify they pass.

### Task 4: Teammate documentation and repository hygiene

**Files:**
- Modify: `README.md`
- Modify: `workspace/standard/text2sql_runner/README.md`
- Modify: `.gitignore`

**Interfaces:**
- Documents CMD and PowerShell commands for `Full`, `None`, one-question, full-run, resume, generation-only and evaluation-only workflows.

- [ ] Update the Chinese README with DeepSeek V4 Flash configuration, the two knowledge modes, terminal markers, output interpretation, and current empty/zero-result caveats.
- [ ] Add a repository-wide Python `__pycache__/` ignore rule without changing secret-file rules.
- [ ] Run `git diff --check` and inspect the documentation diff.

### Task 5: Verification and local no-knowledge run

**Files:**
- Verify all changed files and generated ignored run output.

- [ ] Run the full Text-to-SQL runner unit suite.
- [ ] Run the competition evaluator unit suite.
- [ ] Run the launcher help command through `powershell.exe -ExecutionPolicy Bypass`.
- [ ] Run `-Limit 1 -RunName smoke_no_kb -KnowledgeMode None` against DeepSeek and the read-only PostgreSQL database.
- [ ] If the single-question run succeeds, run `-Full -RunName baseline_no_kb -KnowledgeMode None` and inspect its reports.
- [ ] Confirm `run_metadata.json` says `None` and contains no knowledge files.
- [ ] Commit only source, tests, docs and ignore rules; never commit `.env` or generated runs.

### Task 6: Integrate and push after user review

**Files:**
- Git history only.

- [ ] Present the local no-knowledge result and changed-file summary to the user.
- [ ] After confirmation to finish, update local `main` from `origin/main`, merge `develop_g`, re-run the full verification suite, and push `main` without force.
