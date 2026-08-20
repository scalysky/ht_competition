# minimax_m3 isolated at2s run

This directory is intentionally isolated from the evaluator, gold SQL, Q&A.xlsx, historical runs, and the other model.

## Run

1. Start OpenCode from this exact directory.
2. Send the full contents of prompts/01_build_knowledge.txt.
3. After it finishes, start a new OpenCode session from this directory.
4. Send the full contents of prompts/02_generate_sql.txt.
5. Close the generation session before evaluation.

Expected outputs:

- workspace/skills/at2s/.knowledge/architecture/
- generated/predictions.txt
- generated/generation_notes.md

## Evaluate from the main repository

~~~powershell
cd C:\Code\Fin_tech_match\ht_competition
.\run_text2sql.ps1 -Predictions "C:\Code\Fin_tech_match\at2s_runs\minimax_m3\generated\predictions.txt" -OutputRoot .\workspace\standard\eval_runs\competition\model_comparison\0818 -RunName minimax_m3
~~~
