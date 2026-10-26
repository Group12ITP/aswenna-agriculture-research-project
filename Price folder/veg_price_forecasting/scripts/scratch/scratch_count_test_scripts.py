import re
from pathlib import Path

py_files = sorted(Path(".").glob("*.py")) + sorted(Path("src").glob("*.py"))
test_reading_scripts = []

patterns = [
    r"test_mask",
    r"predictions_test\.csv",
    r"test_preds",
    r"split\s*==\s*['\"]test['\"]",
    r"y_test"
]

for p in py_files:
    # Skip temporary scratch files if desired, or include them to be exhaustive
    text = p.read_text(encoding="utf-8", errors="ignore")
    matches = []
    for pat in patterns:
        if re.search(pat, text):
            matches.append(pat)
    if matches:
        test_reading_scripts.append((str(p), matches))

print(f"Total Python scripts accessing test split or test data: {len(test_reading_scripts)}")
for p, m in test_reading_scripts:
    print(f"  - {p} (matched: {len(m)} patterns)")
