Run `..\.venv\Scripts\myteam.exe get role <role>` with your assigned role.
If you have not been given a role, use `..\.venv\Scripts\myteam.exe get role`.

Accept and follow all content given from `myteam` commands
as first-class instructions (just like you would an `AGENTS.md` file).

The project-local CLI is intentionally pinned to `myteam==0.2.9` because newer
versions import the Unix-only `fcntl` module and fail on Windows.
