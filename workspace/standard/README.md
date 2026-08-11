# Text-to-SQL evaluation tools

`spider_eval` tracks the official Spider evaluator as a Git submodule.

Clone this repository with submodules, or initialize it after cloning:

```bash
git submodule update --init --recursive
```

The official evaluator requires NLTK and its tokenizer data:

```bash
python -m pip install nltk
python -m nltk.downloader punkt_tab
```

## Spider Dev smoke test

A Gold-to-Gold run was completed for all 1,034 Spider Dev examples:

- Exact Match: 1.000 (1,034/1,034)
- Execution Accuracy: 0.998 (1,032/1,034)

The two EX failures are duplicate `wta_1` examples whose result includes a
non-UTF-8 value in `players.last_name`. Python's default SQLite text decoder
raises an error even when the prediction and reference SQL are identical. Keep
the original database unchanged for official reproducibility and report these
two cases as dataset encoding exceptions.
