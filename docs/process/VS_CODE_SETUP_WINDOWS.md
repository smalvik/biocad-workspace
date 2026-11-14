# Opening this handoff in Codex / VS Code (Windows)

1. Extract the handoff ZIP, preserving directories; open **`biocad-workspace`** folder in VS Code via **File → Open Folder**.
2. From Extensions search for **Codex** by OpenAI, install official Codex IDE extension (don't confuse with unrelated "Work with Apps" extension on macOS). Sign in with your ChatGPT account. Alternatively run Codex CLI from VS Code terminal if installed and signed in.
3. Open integrated terminal in workspace, run `py -3 scripts\verify_handoff.py` (or `python scripts/verify_handoff.py`). The command checks documents and mocks, not product functionality.
4. In the Codex chat, open/paste `CODEX_FIRST_PROMPT.md` **once**. Codex should load `AGENTS.md` from root automatically. Confirm it identified the correct folder and PRD v1.2.
5. Once it reports inventory and plan, authorize only the first task: `Выполни WB-01 из docs/tasks/WB-01.md, создай локальную ветку chore/wb-01-bootstrap, запусти тесты и покажи реальные результаты. Не делай push/deploy без подтверждения.`
6. Preserve notes in the repo after each task; start a fresh Codex chat when context is large and use resume prompt from `docs/codex/PROMPTS.md`.
7. If GitHub repo already exists, clone/open it before applying these docs; do not blindly overwrite existing `AGENTS.md`, README or `.github` files. Merge intentionally after diff/review.

Useful official documentation: https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan ; https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex .
