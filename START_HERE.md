# Start working in Codex

**This folder is the persistent memory transferred from our ChatGPT design/planning conversation.** Use the current files as context instead of asking Codex to "remember" the old chat. ChatGPT chat history and Codex conversation history do **not** automatically synchronize.

- Open this folder in VS Code; ensure Codex sees `AGENTS.md` in the workspace root.
- Verify: `python scripts/verify_handoff.py`.
- Paste the content of `CODEX_FIRST_PROMPT.md` in Codex.
- Let Codex inspect the files and report a plan before it edits the repository.
- Then request WB-01, WB-02, etc. individually. Tell Codex to check real dependencies before installing and use lean, minimal modules.
- To resume a later chat: use the prompt "Resume current task" in `docs/codex/PROMPTS.md`; `docs/context/PROGRESS.md` and task notes persist.

**Priority:** original interview assignment P0 over P1/P2. Runtime budget/time 3 days, use tokens sparingly, work in small increments.
