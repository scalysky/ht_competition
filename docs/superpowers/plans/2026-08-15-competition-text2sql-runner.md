# Competition Text-to-SQL One-Click Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows one-click workflow that sends only the seven competition questions and PostgreSQL schema to an OpenAI-compatible model, saves resumable predictions plus a 40-hyphen text export, and runs the existing competition EM/EX/R-VES evaluator.

**Architecture:** A thin root PowerShell launcher validates mutually exclusive run flags and delegates generation to focused Python modules under `workspace/standard/text2sql_runner`. The Python layer reuses the existing read-only PostgreSQL configuration and SQL safety validator, separates question-only prompt data from gold SQL, checkpoints every completed request, and writes evaluator-compatible JSON. After generation, PowerShell invokes the existing `competition_eval/evaluate.py` against either the full gold file or an aligned limited gold subset.

**Tech Stack:** Python 3.11+ standard library, PowerShell 5.1+, PostgreSQL `psql`, existing `competition_eval` modules, `unittest`.

## Global Constraints

- Only the competition PostgreSQL questions are generated and evaluated; Spider and BIRD are out of scope.
- The model uses a non-streaming OpenAI-compatible Chat Completions endpoint configured by `.env`.
- The prompt must never contain gold SQL.
- Only one read-only PostgreSQL `SELECT` or `WITH` query whose final operation is `SELECT` is accepted per answer.
- Every successful answer is checkpointed before moving to the next question.
- `predictions.txt` separates answers with exactly `----------------------------------------` and has no trailing separator.
- A run must explicitly select either `-Limit N` or `-Full`.
- API keys and database passwords must never be logged, reported, or committed.

---

### Task 1: Competition question and schema loader

**Files:**
- Create: `workspace/standard/text2sql_runner/__init__.py`
- Create: `workspace/standard/text2sql_runner/competition_data.py`
- Create: `workspace/standard/text2sql_runner/tests/__init__.py`
- Create: `workspace/standard/text2sql_runner/tests/test_competition_data.py`
- Modify: `workspace/standard/competition_eval/psql_runner.py`
- Create: `workspace/standard/competition_eval/tests/test_psql_runner.py`

**Interfaces:**
- Produces: `CompetitionQuestion(id: int, question: str)`.
- Produces: `load_questions(path: Path) -> list[CompetitionQuestion]`, which never exposes the source `sql` field.
- Produces: `PsqlRunner.public_schema_metadata() -> dict[str, object]` using fixed read-only catalog SQL.
- Produces: `format_schema(metadata: dict[str, object]) -> str`.

- [ ] **Step 1: Write failing tests for question isolation and schema formatting**

```python
def test_load_questions_discards_gold_sql(self):
    source = self.tmp_path / "gold.json"
    source.write_text(
        json.dumps([{"id": 1, "question": "客户数量", "sql": "SELECT secret"}]),
        encoding="utf-8",
    )
    questions = load_questions(source)
    self.assertEqual(questions, [CompetitionQuestion(id=1, question="客户数量")])
    self.assertFalse(hasattr(questions[0], "sql"))

def test_format_schema_lists_columns_keys_and_foreign_keys(self):
    metadata = {
        "tables": [{"name": "orders", "columns": [
            {"name": "id", "type": "bigint", "nullable": False},
            {"name": "customer_id", "type": "bigint", "nullable": False},
        ], "primary_key": ["id"]}],
        "foreign_keys": [{"table": "orders", "column": "customer_id",
                          "references_table": "customer", "references_column": "id"}],
    }
    text = format_schema(metadata)
    self.assertIn("orders(id bigint NOT NULL, customer_id bigint NOT NULL)", text)
    self.assertIn("PRIMARY KEY: orders.id", text)
    self.assertIn("orders.customer_id -> customer.id", text)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_competition_data -v
```

Expected: import failure because `competition_data.py` does not exist.

- [ ] **Step 3: Implement the immutable question model and fixed catalog query**

Implement `CompetitionQuestion` as a frozen dataclass. `load_questions` validates unique positive integer IDs and non-empty questions, and constructs only those two fields. Add `PsqlRunner.public_schema_metadata()` with fixed `information_schema.columns`, `table_constraints`, `key_column_usage`, and `constraint_column_usage` queries restricted to `public`; parse its JSON output into tables, columns, primary keys, and foreign keys. Do not accept table names or SQL from callers.

- [ ] **Step 4: Implement deterministic schema text formatting**

Sort tables, columns by ordinal position, primary keys, and foreign keys. Include data type, nullability, primary keys, and foreign-key arrows. Empty schema raises `RuntimeError("未读取到 public schema")`.

- [ ] **Step 5: Run focused and existing evaluator tests**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_competition_data -v
python -m unittest discover -s workspace/standard/competition_eval/tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add workspace/standard/text2sql_runner workspace/standard/competition_eval/psql_runner.py workspace/standard/competition_eval/tests/test_metrics.py
git commit -m "feat: 加载比赛题目和PostgreSQL结构"
```

---

### Task 2: Prompt construction and SQL response validation

**Files:**
- Create: `workspace/standard/text2sql_runner/prompts.py`
- Create: `workspace/standard/text2sql_runner/tests/test_prompts.py`

**Interfaces:**
- Consumes: `CompetitionQuestion` and formatted schema text from Task 1.
- Produces: `build_messages(question: CompetitionQuestion, schema: str) -> list[dict[str, str]]`.
- Produces: `clean_model_sql(content: str) -> str`, validated by the existing `validate_read_only_sql`.

- [ ] **Step 1: Write failing prompt and cleaning tests**

```python
def test_prompt_contains_question_and_schema_but_not_gold_sql(self):
    question = CompetitionQuestion(1, "客户数量")
    messages = build_messages(question, "customer(id bigint)")
    rendered = json.dumps(messages, ensure_ascii=False)
    self.assertIn("客户数量", rendered)
    self.assertIn("customer(id bigint)", rendered)
    self.assertNotIn("gold", rendered.lower())
    self.assertNotIn("标准 SQL", rendered)

def test_clean_model_sql_removes_single_markdown_fence(self):
    self.assertEqual(clean_model_sql("```sql\nSELECT 1;\n```"), "SELECT 1;")

def test_clean_model_sql_rejects_multiple_statements(self):
    with self.assertRaises(SqlSafetyError):
        clean_model_sql("SELECT 1; DROP TABLE customer;")
```

- [ ] **Step 2: Run tests and verify RED**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_prompts -v
```

Expected: import failure because `prompts.py` does not exist.

- [ ] **Step 3: Implement fixed PostgreSQL prompt messages**

The system message requires one read-only PostgreSQL statement, no prose or Markdown, only supplied tables/columns, explicit JOINs based on listed relationships, and faithful aggregation/date/NULL semantics. The user message contains only `question.question` and the formatted schema.

- [ ] **Step 4: Implement conservative response cleaning**

Strip surrounding whitespace and one complete Markdown SQL fence. Reject empty content, text before/after a fenced block, multiple statements, DML, DDL, `COPY`, `CALL`, `DO`, and `SELECT INTO` by calling `validate_read_only_sql` from `competition_eval/sql_tools.py`. Do not rewrite aliases, predicates, or SQL logic.

- [ ] **Step 5: Run tests**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_prompts -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add workspace/standard/text2sql_runner/prompts.py workspace/standard/text2sql_runner/tests/test_prompts.py
git commit -m "feat: 构建比赛SQL生成提示词"
```

---

### Task 3: OpenAI-compatible model client

**Files:**
- Create: `workspace/standard/text2sql_runner/llm_client.py`
- Create: `workspace/standard/text2sql_runner/tests/test_llm_client.py`

**Interfaces:**
- Produces: `LlmConfig.from_env() -> LlmConfig` for `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and `LLM_TIMEOUT_SECONDS`.
- Produces: `OpenAICompatibleClient.complete(messages: list[dict[str, str]]) -> str`.

- [ ] **Step 1: Write a failing real-HTTP test**

Start a local `http.server.ThreadingHTTPServer` on an ephemeral port. Its handler records the JSON request and returns:

```json
{"choices":[{"message":{"content":"SELECT 1"}}]}
```

Assert that `complete` returns `SELECT 1`, posts to `/v1/chat/completions`, sends the configured model and `temperature: 0`, and uses `Authorization: Bearer test-key`. Add tests that a 400 response is not retried and a 429 response succeeds on the second real HTTP request.

- [ ] **Step 2: Run tests and verify RED**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_llm_client -v
```

Expected: import failure because `llm_client.py` does not exist.

- [ ] **Step 3: Implement configuration validation and endpoint joining**

Reject missing variables before any request. Normalize `LLM_BASE_URL` so either `https://host/v1` or `https://host/v1/` becomes `https://host/v1/chat/completions`. Parse timeout as a positive float. Never include the key in exception messages or object `repr`.

- [ ] **Step 4: Implement request, response parsing, and retry policy**

Use `urllib.request.Request` and `urlopen`, non-streaming JSON, and UTF-8. Retry connection errors, timeouts, HTTP 429, and HTTP 5xx up to 3 total attempts with waits of 1 and 2 seconds. Do not retry other HTTP 4xx errors. Validate `choices[0].message.content` as a string and return it.

- [ ] **Step 5: Run tests**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_llm_client -v
```

Expected: all tests pass with no external network access.

- [ ] **Step 6: Commit**

```powershell
git add workspace/standard/text2sql_runner/llm_client.py workspace/standard/text2sql_runner/tests/test_llm_client.py
git commit -m "feat: 添加OpenAI兼容模型客户端"
```

---

### Task 4: Checkpoints and evaluator-compatible outputs

**Files:**
- Create: `workspace/standard/text2sql_runner/outputs.py`
- Create: `workspace/standard/text2sql_runner/tests/test_outputs.py`

**Interfaces:**
- Produces: `PredictionRecord(id, sql, fingerprint, status, error)` frozen dataclass.
- Produces: `input_fingerprint(question, schema, model, messages) -> str` using SHA-256.
- Produces: `append_checkpoint(path: Path, record: PredictionRecord) -> None`.
- Produces: `load_successful_checkpoints(path: Path) -> dict[tuple[int, str], PredictionRecord]`.
- Produces: `write_prediction_files(output_dir, records, source_gold_path, selected_ids) -> OutputPaths`.

- [ ] **Step 1: Write failing output tests**

```python
def test_text_output_uses_exact_separator_without_trailing_separator(self):
    records = [
        PredictionRecord(id=1, sql="SELECT 1", fingerprint="fp-1",
                         status="success", error=None),
        PredictionRecord(id=2, sql="SELECT 2", fingerprint="fp-2",
                         status="success", error=None),
    ]
    paths = write_prediction_files(
        self.tmp_path,
        records,
        self.gold_path,
        [1, 2],
    )
    self.assertEqual(
        paths.text.read_text(encoding="utf-8"),
        "SELECT 1\n----------------------------------------\nSELECT 2\n",
    )

def test_resume_requires_matching_fingerprint(self):
    record = PredictionRecord(id=1, sql="SELECT 1", fingerprint="old",
                              status="success", error=None)
    append_checkpoint(self.path, record)
    loaded = load_successful_checkpoints(self.path)
    self.assertIn((1, "old"), loaded)
    self.assertNotIn((1, "new"), loaded)

def test_gold_subset_contains_only_selected_ids(self):
    records = [PredictionRecord(id=2, sql="SELECT 2", fingerprint="fp-2",
                                status="success", error=None)]
    paths = write_prediction_files(
        self.tmp_path, records, self.gold_path, selected_ids=[2]
    )
    gold = json.loads(paths.gold.read_text(encoding="utf-8"))
    self.assertEqual([item["id"] for item in gold], [2])
```

- [ ] **Step 2: Run tests and verify RED**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_outputs -v
```

Expected: import failure because `outputs.py` does not exist.

- [ ] **Step 3: Implement append-only checkpoint records**

Write one UTF-8 JSON object per line, flush, and `os.fsync` before returning. Loading ignores failed records and keeps the latest successful record for each `(id, fingerprint)`. Malformed checkpoint lines raise a path-and-line-number error instead of silently losing work.

- [ ] **Step 4: Implement atomic final outputs**

Write `predictions.json`, `predictions.txt`, `gold_subset.json`, and `errors.json` to sibling temporary files and replace their final paths with `Path.replace`. Sort records by numeric ID. JSON predictions contain only `id` and `sql`. TXT contains only successful SQL separated by exactly 40 hyphens. Failed IDs are listed in `errors.json` and omitted from TXT but represented as missing predictions for scoring.

- [ ] **Step 5: Run tests**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_outputs -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add workspace/standard/text2sql_runner/outputs.py workspace/standard/text2sql_runner/tests/test_outputs.py
git commit -m "feat: 保存可恢复的SQL预测结果"
```

---

### Task 5: Generation CLI and one-click PowerShell launcher

**Files:**
- Create: `workspace/standard/text2sql_runner/generate.py`
- Create: `workspace/standard/text2sql_runner/tests/test_generate.py`
- Create: `run_text2sql.ps1`
- Modify: `.env.example`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: `generate.py --limit N|--full --output-dir PATH [--no-resume] [--psql-path PATH]`.
- Produces: `run_text2sql.ps1 -Limit N|-Full [-GenerateOnly|-EvaluateOnly] [-NoResume] [-RunName NAME] [-PsqlPath PATH]`.

- [ ] **Step 1: Write failing orchestration tests**

Use fake `QuestionSource`, `SchemaSource`, and `ModelClient` implementations passed to `run_generation`. Assert that it sends seven question-only prompts in full mode, sends only the first N in limit mode, immediately appends each successful checkpoint, resumes matching fingerprints without calling the client again, and continues after a failed question. Assert that standard SQL text placed in the source fixture never appears in the captured model messages.

- [ ] **Step 2: Run tests and verify RED**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_generate -v
```

Expected: import failure because `generate.py` does not exist.

- [ ] **Step 3: Implement `run_generation` and CLI validation**

Load `.env` through the existing `db_config.load_env_file`, validate model config, create `DatabaseConfig` and `PsqlRunner`, assert `default_transaction_read_only=on`, fetch schema once, and iterate questions in ID order. For every question: build messages, calculate the fingerprint, reuse a matching checkpoint when allowed, otherwise call the model, clean/validate SQL, and append success or error. Always write final prediction and gold-subset files. Return exit code 2 when any item failed, while leaving valid outputs available.

- [ ] **Step 4: Implement the thin PowerShell launcher**

Use `[CmdletBinding(DefaultParameterSetName='Limited')]` and parameter-set validation so exactly one of `-Limit` or `-Full`, and at most one of `-GenerateOnly` or `-EvaluateOnly`, is accepted. Resolve all paths from `$PSScriptRoot`. Default `-RunName` to `latest`; `-NoResume` without an explicit name uses a timestamped name. Call Python generation unless `-EvaluateOnly`, then call:

```powershell
python workspace/standard/competition_eval/evaluate.py `
  --gold <run-dir>/gold_subset.json `
  --predictions <run-dir>/predictions.json `
  --metrics em,ex,rves `
  --output <run-dir>/evaluation.json
```

Propagate nonzero exit codes and print the absolute report directory. Never echo `.env` contents.

- [ ] **Step 5: Add safe model placeholders**

Append to `.env.example`:

```dotenv
LLM_BASE_URL=https://your-openai-compatible-host/v1
LLM_API_KEY=replace-with-local-api-key
LLM_MODEL=replace-with-model-name
LLM_TIMEOUT_SECONDS=120
```

- [ ] **Step 6: Run focused tests and PowerShell syntax/help checks**

```powershell
python -m unittest workspace.standard.text2sql_runner.tests.test_generate -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -?
```

Expected: Python tests pass and PowerShell prints parameter help without starting generation.

- [ ] **Step 7: Commit**

```powershell
git add run_text2sql.ps1 .env.example workspace/standard/text2sql_runner/generate.py workspace/standard/text2sql_runner/tests/test_generate.py
git commit -m "feat: 添加比赛SQL一键生成评测入口"
```

---

### Task 6: Documentation and complete verification

**Files:**
- Create: `workspace/standard/text2sql_runner/README.md`
- Modify: `workspace/standard/README.md`
- Modify: `README.md`

**Interfaces:**
- Documents the environment variables, first `-Limit 1` smoke test, full run, resume, generate-only, evaluate-only, output files, cost warning, and failure recovery.

- [ ] **Step 1: Add command examples and safety notes**

Document these exact starter commands:

```powershell
Copy-Item .env.example .env
# Edit only the local .env, then run one paid request first.
.\run_text2sql.ps1 -Limit 1 -RunName smoke
.\run_text2sql.ps1 -Full -RunName baseline
```

Explain that Spider/BIRD are intentionally excluded from this launcher, gold SQL is not sent to the model, and `predictions.txt` is the 40-hyphen human-readable export.

- [ ] **Step 2: Run the complete offline test suite**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s workspace/standard/text2sql_runner/tests -v
python -m unittest discover -s workspace/standard/competition_eval/tests -v
```

Expected: all tests pass with no warnings or network requests.

- [ ] **Step 3: Verify repository hygiene and CLI behavior**

```powershell
git diff --check
git status --short
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -?
```

Expected: no whitespace errors, only intended files changed, and CLI help succeeds without secrets.

- [ ] **Step 4: Run a real `-Limit 1` smoke test only after user confirms API settings and cost**

```powershell
.\run_text2sql.ps1 -Limit 1 -RunName smoke
```

Expected: one model request, one prediction in JSON/TXT, and EM/EX/R-VES reports in the smoke run directory. If no usable API credentials are available, report this single external verification as pending rather than fabricating success.

- [ ] **Step 5: Commit documentation**

```powershell
git add README.md workspace/standard/README.md workspace/standard/text2sql_runner/README.md
git commit -m "docs: 添加比赛一键评测使用说明"
```
