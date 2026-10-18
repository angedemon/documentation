"""Goal check: the rebuild must pass the tests and each of the 3 mutants must fail them.

Usage: python3 run_checks.py   (exit code 0 only when the goal is met)
"""
import os
import subprocess
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "iban.py"
MUTANTS = ["m1.py", "m2.py", "m3.py"]


def run_tests(module_path):
    """Run the test suite against `module_path` (copied as iban.py). Return True if tests pass."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(module_path, os.path.join(tmp, MODULE))
        shutil.copytree(os.path.join(HERE, "tests"), os.path.join(tmp, "tests"))
        proc = subprocess.run(
            [sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=tmp, capture_output=True, text=True,
        )
        return proc.returncode == 0, proc.stderr.strip().splitlines()[-1:] or [""]


def main():
    ok = True
    passed, tail = run_tests(os.path.join(HERE, MODULE))
    print(f"rebuild  : {'PASS' if passed else 'FAIL'}  ({tail[0]})")
    ok &= passed
    for name in MUTANTS:
        path = os.path.join(HERE, "mutants", name)
        if not os.path.exists(path):
            print(f"{name:9}: MISSING")
            ok = False
            continue
        passed, tail = run_tests(path)
        print(f"{name:9}: {'survived (BAD)' if passed else 'killed (good)'}  ({tail[0]})")
        ok &= not passed
    print("GOAL MET" if ok else "GOAL NOT MET")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
