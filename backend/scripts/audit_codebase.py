"""Comprehensive vibe-coding audit script."""
import sys, os, re, json, ast

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(ROOT, "backend", "app")
FRONTEND_DIR = os.path.join(ROOT, "frontend", "src")
SCRIPTS_DIR = os.path.join(ROOT, "backend", "scripts")

issues = []

def add(category, filepath, line_no, detail):
    issues.append({"cat": category, "file": filepath.replace(ROOT + "\\", "").replace(ROOT + "/", ""), "line": line_no, "detail": detail})

# ──────────────── BACKEND ANALYSIS ────────────────
for root, dirs, files in os.walk(BACKEND_DIR):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        if not f.endswith(".py"):
            continue
        fp = os.path.join(root, f)
        rel = fp.replace(ROOT + os.sep, "")
        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
            src = fh.read()
        lines = src.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 1. Bare except (swallows all exceptions silently)
            if re.match(r"except\s*:", stripped) or stripped == "except:":
                add("BARE_EXCEPT", rel, i, stripped[:80])

            # 2. Broad except Exception with only pass / logger.debug
            if re.match(r"except Exception\s*:", stripped) or re.match(r"except Exception as \w+\s*:", stripped):
                # Peek ahead for body
                body = "\n".join(lines[i:i+3])
                if re.search(r"^\s*(pass|logger\.debug|continue)\s*$", body, re.M):
                    add("SWALLOWED_EXC", rel, i, stripped[:80])

            # 3. Fragile locals() check - indicates variable might not be defined
            if '"passages" in locals()' in line or "'passages' in locals()" in line:
                add("FRAGILE_LOCALS", rel, i, stripped[:80])

            # 4. f-strings in logger calls (performance: lazy eval not used)
            if re.match(r"\s*logger\.\w+\(f[\"']", line):
                add("FSTRING_LOGGER", rel, i, stripped[:80])

            # 5. TODO/FIXME/HACK comments
            if re.search(r"#\s*(TODO|FIXME|HACK|XXX)", line, re.I):
                add("TODO_MARKER", rel, i, stripped[:80])

            # 6. Hardcoded magic numbers / strings that should be constants
            if re.search(r"\"127\.0\.0\.1\"", line) and "config" not in f:
                add("HARDCODED_HOST", rel, i, stripped[:80])
            if re.search(r"port\s*=\s*11434", line) and "config" not in f:
                add("HARDCODED_PORT", rel, i, stripped[:80])

            # 7. any() used as truthiness check on list comprehensions (subtle bug)
            # 8. Import inside function body (slow)
            if re.match(r"\s+from app\.", line) or re.match(r"\s+import app", line):
                # Only flag if inside a function (indented)
                if line.startswith("        "):
                    add("DEFERRED_IMPORT", rel, i, stripped[:80])

            # 9. Missing HTTPException status_code for server errors (using 500 string)
            if "status_code=500" in line:
                add("HTTP_500", rel, i, stripped[:80])

            # 10. SQL interpolation risk
            if re.search(r'f"(SELECT|INSERT|UPDATE|DELETE)', line, re.I):
                add("SQL_INJECTION_RISK", rel, i, stripped[:80])

            # 11. Mutable default arg
            if re.match(r"def \w+\(.*=\[\]", stripped) or re.match(r"def \w+\(.*=\{\}", stripped):
                add("MUTABLE_DEFAULT", rel, i, stripped[:80])

            # 12. Missing validation on run_id / patient_id path params
            if "run_id: str" in line and "pattern" not in line:
                # just note, not necessarily a bug
                pass

# ──────────────── FRONTEND ANALYSIS ────────────────
def audit_frontend_file(fp):
    rel = fp.replace(ROOT + os.sep, "")
    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
        src = fh.read()
    lines = src.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 1. Console.log left in production code
        if "console.log(" in line and "// debug" not in line.lower():
            add("CONSOLE_LOG", rel, i, stripped[:80])

        # 2. Missing key prop in .map()
        if ".map(" in line and "key=" not in line and "key =" not in line and i < len(lines):
            # Only flag JSX lines
            next3 = "\n".join(lines[i:i+3])
            if "<" in next3 and "key=" not in next3:
                add("MISSING_KEY_PROP", rel, i, stripped[:60])

        # 3. Direct mutation of state
        if re.search(r"\bstate\.\w+\s*=", line) and "setState" not in line:
            add("STATE_MUTATION", rel, i, stripped[:80])

        # 4. Hardcoded API base URL
        if re.search(r'"http://127\.0\.0\.1:8000"', line) or re.search(r'"http://localhost:8000"', line):
            add("HARDCODED_API_URL", rel, i, stripped[:80])

        # 5. any / unknown typed as any in .ts files
        if fp.endswith(".tsx") or fp.endswith(".ts"):
            if ": any" in line and "// eslint" not in line:
                add("TS_ANY_TYPE", rel, i, stripped[:80])

        # 6. Unhandled promise - .then() without .catch()
        if ".then(" in line and ".catch(" not in line and "await" not in line:
            if i < len(lines) and ".catch(" not in lines[i]:
                add("UNHANDLED_PROMISE", rel, i, stripped[:80])

        # 7. setTimeout / setInterval without cleanup (memory leak)
        if "setTimeout(" in line or "setInterval(" in line:
            if "clearTimeout" not in src and "clearInterval" not in src:
                add("TIMER_LEAK", rel, i, stripped[:60])

        # 8. fetch without error handling
        if "fetch(" in line and "catch" not in line:
            if i < len(lines) and ".catch" not in "\n".join(lines[i:i+5]):
                add("FETCH_NO_CATCH", rel, i, stripped[:80])

        # 9. Magic numbers in JSX (polling intervals, retries)
        if re.search(r"setTimeout\([^,]+,\s*[0-9]{4,}\)", line):
            add("MAGIC_NUMBER_TIMEOUT", rel, i, stripped[:80])

for root, dirs, files in os.walk(FRONTEND_DIR):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules")]
    for f in files:
        if f.endswith((".tsx", ".ts", ".js")) and "test" not in f and "d.ts" not in f:
            audit_frontend_file(os.path.join(root, f))

# ──────────────── REPORT ────────────────
by_cat = {}
for iss in issues:
    by_cat.setdefault(iss["cat"], []).append(iss)

print(f"\n{'='*60}")
print(f"TOTAL ISSUES: {len(issues)}")
print(f"{'='*60}\n")

priority = [
    "BARE_EXCEPT", "SWALLOWED_EXC", "SQL_INJECTION_RISK", "STATE_MUTATION",
    "HARDCODED_API_URL", "FRAGILE_LOCALS", "TIMER_LEAK", "FETCH_NO_CATCH",
    "DEFERRED_IMPORT", "FSTRING_LOGGER", "CONSOLE_LOG", "MISSING_KEY_PROP",
    "UNHANDLED_PROMISE", "HTTP_500", "HARDCODED_HOST", "HARDCODED_PORT",
    "MAGIC_NUMBER_TIMEOUT", "MUTABLE_DEFAULT", "TS_ANY_TYPE", "TODO_MARKER"
]
for cat in priority:
    if cat not in by_cat:
        continue
    print(f"[{cat}] ({len(by_cat[cat])} issues)")
    for iss in by_cat[cat]:
        print(f"  {iss['file']}:{iss['line']}  {iss['detail']}")
    print()

# Output JSON for supervisor use
with open(os.path.join(SCRIPTS_DIR, "audit_results.json"), "w") as f:
    json.dump(issues, f, indent=2)

print(f"\nAudit JSON written to backend/scripts/audit_results.json")
