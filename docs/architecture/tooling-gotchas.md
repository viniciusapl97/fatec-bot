# Editor/tooling gotchas

Quirks of the development tooling itself, not of the app's architecture —
kept separate so they don't get mixed into "how the code works".

## File-write tool preserves on-disk encoding

The file-write tool preserves an existing file's on-disk encoding when
overwriting it — editing `requirements.txt` (historically UTF-16, likely
from `pip freeze` on Windows PowerShell) through it silently re-wrote UTF-16
even with UTF-8 content, which breaks `pip` (`Invalid requirement` with
literal `\x00` bytes in the error). It was converted to plain UTF-8 when
Alembic was added (git history has both versions if you need to compare). If
a similar non-UTF-8 file ever needs an encoding fix, overwrite it via a shell
heredoc (`cat > file << 'EOF' ... EOF`) instead of the normal edit path, then
verify with `file <path>`.
