#!/usr/bin/env bash
# Blocks Bash commands invoking the system `python`/`python3` interpreter,
# per .claude/rules/general.md ("Use .venv, not global python environment").
#
# A bare interpreter name (python, python3, python3.11, py, ...) is always
# blocked, since PATH resolution of a bare name can never be verified from
# the command text alone. A path-qualified invocation is allowed only if
# the path resolves into a real venv: the directory holding the executable
# (or that directory's parent, to cover both the standard <venv>/bin/python
# layout and a flat <venv>/python layout) must contain a pyvenv.cfg marker
# (PEP 405), which every real venv (stdlib venv, virtualenv, uv) writes and
# a bare symlink-into-a-directory-named-.venv does not. This also means a
# path straight at the system interpreter (e.g. /usr/bin/python3) is
# blocked with no special-casing: there's no pyvenv.cfg sitting next to it.
#
# Segments are split on unquoted ; & | ( ) only (an operator character
# inside a quoted argument isn't a real command separator), then walked
# past the same leading forms Claude Code's own Bash permission matcher
# strips before comparing against a deny rule (see "Compound commands" /
# "Wrappers" at code.claude.com/docs/en/permissions): env assignments,
# bare `xargs`, and the wrapper commands `timeout`, `time`, `nice`,
# `nohup`, `stdbuf`, `env`, `command`, `builtin`, `noglob`.
set -euo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || COMMAND=""
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null) || CWD=""
[ -z "$CWD" ] && CWD="$PWD"

# Split $1 into one subcommand per line on unquoted ; & | ( ), preserving
# quoted spans (including a backslash-escaped quote inside a "..." span)
# verbatim so operator characters inside them aren't treated as separators.
split_unquoted() {
  awk '
    BEGIN { q = "" }
    {
      n = length($0)
      # A record (original input line) that already started inside an open quote
      # is pure continuation of a multi-line quoted argument (e.g. a git commit
      # -m message spanning several lines) -- not a new shell command, so its
      # first word must never be checked below. Mark it with a leading SOH
      # sentinel the consumer strips and skips on sight, without analysis.
      out = (q != "") ? "\001" : ""
      for (i = 1; i <= n; i++) {
        c = substr($0, i, 1)
        if (q == "\"" && c == "\\" && i < n) {
          out = out c substr($0, i + 1, 1)
          i++
          continue
        }
        if (q != "") {
          out = out c
          if (c == q) q = ""
        } else if (c == "\x27" || c == "\"") {
          q = c
          out = out c
        } else if (index(";&|()", c) > 0) {
          out = out "\n"
        } else {
          out = out c
        }
      }
      print out
    }
  '
}

is_env_assignment() { [[ "$1" =~ ^[A-Za-z_][A-Za-z0-9_]*=.*$ ]]; }

is_noarg_wrapper() {
  case "$1" in
    nohup | command | builtin | noglob | time) return 0 ;;
    *) return 1 ;;
  esac
}

is_witharg_wrapper() {
  case "$1" in
    timeout | nice | stdbuf | env) return 0 ;;
    *) return 1 ;;
  esac
}

is_flag_or_duration() {
  [[ "$1" =~ ^- ]] && return 0
  [[ "$1" =~ ^[0-9]+[A-Za-z]*$ ]] && return 0
  return 1
}

is_bare_interpreter_name() {
  [[ "$1" =~ ^(python[0-9]*(\.[0-9]+)?|py)$ ]]
}

resolve_path() {
  local raw="$1"
  if [[ "$raw" == "~" || "$raw" == '~'/* ]]; then
    raw="${HOME}${raw:1}"
  fi
  if [[ "$raw" != /* ]]; then
    raw="$CWD/$raw"
  fi
  printf '%s' "$raw"
}

is_real_venv_python() {
  local exe_path bindir parent
  exe_path="$(resolve_path "$1")"
  bindir="$(cd "$(dirname "$exe_path")" 2>/dev/null && pwd)" || return 1
  [ -f "$bindir/pyvenv.cfg" ] && return 0
  parent="$(dirname "$bindir")"
  [ -f "$parent/pyvenv.cfg" ] && return 0
  return 1
}

blocked=0
while IFS= read -r seg; do
  if [[ "$seg" == $'\001'* ]]; then
    continue
  fi
  seg="$(printf '%s' "$seg" | sed -e 's/^[[:space:]]*//')"
  [ -z "$seg" ] && continue

  words=()
  read -ra words <<< "$seg" || true
  [ "${#words[@]}" -eq 0 ] && continue

  idx=0
  guard=0
  while [ "$idx" -lt "${#words[@]}" ] && [ "$guard" -lt 10 ]; do
    guard=$((guard + 1))
    tok="${words[$idx]}"

    if is_env_assignment "$tok"; then
      idx=$((idx + 1))
      continue
    fi

    if [ "$tok" = "xargs" ]; then
      next="${words[$((idx + 1))]:-}"
      if [[ ! "$next" =~ ^- ]]; then
        idx=$((idx + 1))
        continue
      fi
      break
    fi

    if is_noarg_wrapper "$tok"; then
      idx=$((idx + 1))
      continue
    fi

    if is_witharg_wrapper "$tok"; then
      idx=$((idx + 1))
      while [ "$idx" -lt "${#words[@]}" ] && is_flag_or_duration "${words[$idx]}"; do
        idx=$((idx + 1))
      done
      continue
    fi

    break
  done

  first="${words[$idx]:-}"
  if [[ "$first" == */* ]]; then
    if ! is_real_venv_python "$first"; then
      blocked=1
      break
    fi
  elif is_bare_interpreter_name "$first"; then
    blocked=1
    break
  fi
done < <(printf '%s\n' "$COMMAND" | split_unquoted)

if [ "$blocked" = "1" ]; then
  printf '%s\n' '{
    "hookSpecificOutput":{
      "hookEventName":"PreToolUse",
      "permissionDecision":"deny",
      "permissionDecisionReason":"Rule Violation"
      },
    "reason":"Pay attention to the rules and try that command again"
  }'
fi
exit 0
