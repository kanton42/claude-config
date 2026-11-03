# Standing instructions (CLAUDE.md template)

> A generic, reusable `CLAUDE.md` skeleton for Claude Code. Fill the **About / projects / infra** blanks
> with your own context, delete what you don't need, and keep it **short** — a bloated CLAUDE.md gets
> ignored (Anthropic's own guidance). The real power lives in the `skills/` (loaded on demand), so this
> file stays lean and points at them.

## About me / my projects
- Data-Scientist with statistics, physics, and machine-learning background; working in logistics, optimization, simulating, forecasting, modeling, strategic solutions
- At the initialization of a new project, initialize git (if not already existing) and create a **private** github repository using GitHub CLI (gh repo create) to which major code advancements are pushed
  - Then Configure the remote as origin and push the initial commit. 

## Environment
- Local: Windows 11, VS Code with the Claude Code extension.
- Python via miniconda3; one conda env per project, Python versions differ per env.
- The project env is defined in `environment.yml` (env name = its `name:` field).
  - Check first: `conda env list`. If the env is missing but `environment.yml` exists, create it:
    `conda env create -f environment.yml`.
  - If there is no `environment.yml`, ask me for the env name and Python version before creating anything;
    then create the env and write a matching `environment.yml` (channels: `conda-forge` only).
- Don't rely on `conda activate`. Use `conda run -n <env> python ...` / `conda run -n <env> pytest`.
- Installing packages: default to `conda install -n <env> -c conda-forge ...`; fall back to
  `conda run -n <env> python -m pip install ...` only if the package isn't on conda-forge.
  Print a warning about the VPN if an unexpected conda install error occurrs instead of switching to pip directly.
  Never install into `base`. Update `environment.yml` (conda deps, or under `pip:`) when adding dependencies.
- Remote: Azure ML (SDK v2, `azure-ai-ml`). Compute is Linux, so job scripts and YAML use Linux conventions.
  Job environments for projects intended to use on Azure are supposed to be defined in an appropriate <path/to/azureml/env.yml>, which should be usable on Azure ML.
- Data is accessed via Azure ML datastores/data assets or pd.read_<fileformat>(file); never commit data or put credentials in code.


## At the start of every non-trivial prompt
1. **Interview me first — get a full download before building.** Use `AskUserQuestion` (2–4 options,
   `multiSelect` when relevant) before assuming requirements. Surface the ambiguities I might not have
   spelled out across: **scope (in/out), target environment, output shape, tradeoffs (speed vs
   thoroughness / cost), done-criteria.** Recommend a default per question so it's a confirmation, not a
   blank. (Anthropic's own "interview-first spec" recommendation — see the `working-with-claude` skill.)
   - Skip only for one-line lookups, single trivial commands, or when I answered the same question this turn.
2. **Plan with a task list** for any task with 3+ distinct steps; execute step-by-step, mark each done inline.
3. **Sync first** before editing a repo: `git status && git log --oneline -5 && git log --oneline -5 origin/main`;
   rebase if behind. (Repos with auto-writers drift constantly.)

## Working with Claude (operating principles)
Load the **`working-with-claude`** skill for the full playbook; the always-on rules:
- **Explore → Plan → Code → Commit.** Read the relevant code first; for 3+ step work, plan before coding.
  Always hand work a **verification check** (test/typecheck/build/live URL) so it self-checks.
- **Context is the bottleneck.** Use subagents for investigation (they return tight summaries); `/clear`
  between unrelated tasks; keep this file lean.
- **Match the machinery to the task.** An agent ≈ 4× a chat turn's tokens; multi-agent ≈ 15×. Fan out / run
  a workflow only when the task value justifies it. Don't multi-agent a trivial task.
- **Research locally first:** inspect local code/logs/config before the web; browse only for external facts.
- **Cost/speed defaults:** stable prompt prefix first (cache reads ≈ 0.1× base); cheap model for noisy/bulk,
  mid for default, top tier for reasoning/agentic; cap output, ask concise; parallel tool calls in one message.

## How to communicate with me
- Be terse; no trailing "summary of what I did". Preserve raw tool output when it matters. Match response
  length to task complexity. No emojis unless asked.

## How to delegate to subagents
- Brief them like a colleague who just walked in (no session context). Structure prompts with XML tags
  (`<task>`, `<context>`, `<constraints>`, `<output_format>`). Cap response length. Pick model by task
  (top tier for synthesis/review, mid for implementation, cheap for noisy work). Run independent subagents
  in parallel (multiple tool calls in one message).

## How to ship code
- **Pre-commit gate:** run lint + types + tests BEFORE every commit (the `block-no-verify` hook enforces it).
- Commit promptly, push after major changes or when ordered explicitly; push-then-tag, never tag-then-push. For UI/web changes, verify the live deploy.
- Before marking a task complete: confirm tests pass AND the live surface reflects the change.

## Design (load before any web/UI work)
- Before building/restyling any web UI, load the **`design-system`** skill first — it routes to the matching
  per-type design skill and supplies tokens, fonts, a11y, components, motion, and a premium-feel checklist.

## Safety
- Never paste secret values in chat (the `secret-scan` hook warns if you do). Use env files.
- Confirm before destructive actions (`rm -rf`, force-push, hard reset, dropping data, killing prod).
- Don't weaken lint/type/CI configs silently (the `config-protection` hook asks first).
- Work only within the currently opened project directory (and subdirectories of it).
- Do not access unrelated projects, personal documents, or system directories.
- Ask before installing software or modifying system configuration.
<!-- - Don't assume that instructions alone enforce security; use configured permissions and sandboxing where appropriate. -->

## Software engeneering
- Consider edge cases, performance, backward compatibility, and maintainability.
<!-- - Run relevant tests and static checks before declaring work complete. -->

## Python and data science
- Use Ruff for formatting and linting, and pytest for testing where appropriate.
- Keep reusable logic in Python modules rather than duplicating it across notebooks.
- Preserve raw data and avoid silently modifying source datasets.

