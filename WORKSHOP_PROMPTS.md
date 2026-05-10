# Claude Code Prompts

## Understand the project

```text
Read this project and explain how data flows from live scan or SQLite into the UI.
Do not change code yet. Point me to the smallest files/functions I need to edit for a small product improvement.
```

## Add a feature safely

```text
We are in a workshop. Keep the change small and working.
Add [MISSION NAME].

Constraints:
- Do not rewrite the app.
- Keep the live scan flow working.
- Prefer changing app.py and static/app.js only.
- After the change, tell me how to test it in the browser.
```

## Debug

```text
The app changed and something broke.
Find the smallest fix. Do not refactor unrelated code.
First inspect the browser/API error, then patch only the necessary file.
```
