"""Fix response_service.py by re-reading with cp1252 encoding and rewriting as UTF-8."""
from pathlib import Path

path = Path("src/services/response_service.py")

# Read raw bytes and try to decode
raw = path.read_bytes()

# Find the problem area around line 969
lines = raw.split(b"\n")
print(f"Total lines: {len(lines)}")

# Show lines 965-974 with raw byte inspection
for i in range(964, min(975, len(lines))):
    line = lines[i]
    suspicious = [(j, b) for j, b in enumerate(line) if b > 127]
    if suspicious:
        print(f"Line {i+1} has non-ASCII bytes: {suspicious}")
    # Check for lone carriage returns or other control chars
    for j, b in enumerate(line):
        if b == 0x0D:  # CR
            print(f"  Line {i+1} col {j}: CR (0x0D)")

# Try decoding with different encodings
for enc in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
    try:
        text = raw.decode(enc)
        print(f"\nDecodes OK as {enc}")
        break
    except Exception as e:
        print(f"Cannot decode as {enc}: {e}")

# Count triple-quote pairs to find imbalance
content = raw.decode('latin-1')
tq_count = content.count('"""')
print(f"\nTriple-quote count: {tq_count} ({'even - balanced' if tq_count % 2 == 0 else 'ODD - IMBALANCED'})")
