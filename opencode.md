# Vibecode Guiding Principles

## 1. Workspace & Directory Guardrails
- All coding projects, experiments, assets, and artifacts MUST be contained strictly within the folder path: `~/lab/aiprojects`
- Do not initialize projects or create files outside of this directory tree under any circumstances.

## 2. Initialization Workflow (Every Session / First Run)
Before writing or modifying any application code, execute the following sequence:
1. **Locate and Read `README.md`**: Read the root `README.md` to gain a comprehensive understanding of the current workspace state and project catalog.
2. **Handle Missing README**: If `README.md` does not exist, create it immediately. Structure it with a high-level title: `# Experimental AI Apps Portfolio`.
3. **Locate and Read `opencode.md`**: Read this rules file to reinforce your operational constraints. If this file was initialized dynamically, ensure these core rules are preserved explicitly within it.

## 3. Directory Cataloging & Alignment
- On the first run, or whenever a change, addition, or deletion is detected in the subfolders or files within `~/lab/aiprojects`, automatically scan the directory.
- Catalogue the functionality of each sub-project/experimental app directly into the root `README.md`. Keep descriptions concise, technical, and focused on the app's core AI capability.

## 4. Strict Changelog Enforcement
Every single time a code modification, creation, or deletion is performed, document it.
- **File Target**: `changelog.md` (Create it in the root if it does not exist).
- **Format**: Append changes to a clean Markdown table using the following structure:

| Date & Time | Component/File | What Was Changed? | Why Was It Changed? |
| :--- | :--- | :--- | :--- |
| [YYYY-MM-DD HH:MM] | `path/to/file` | Brief description of the precise code modification. | The architectural or functional reason for the change. |

- **Timestamp Rule**: All timestamps MUST be read from the live server clock using `date '+%Y-%m-%d %H:%M'`. The reference timezone is Indian Standard Time (IST, UTC+5:30). Do not hardcode or assume timestamps. Always run the `date` command to capture the current server time for every changelog entry.
- **Append-Only Rule**: Never modify, correct, or delete past changelog entries. The changelog is an immutable audit log. New changes are always appended as new rows at the bottom of the table. Even if timestamps, formatting, or descriptions of past entries appear incorrect, leave them untouched and only add new entries moving forward.
