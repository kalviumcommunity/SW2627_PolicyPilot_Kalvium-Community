"""Fix Python 3.14 SyntaxError in all src Python service files.

Python 3.14 is stricter about escape sequences in strings. 
Replace problematic patterns in docstrings.
"""
from pathlib import Path

files = list(Path("src").rglob("*.py"))

replacements = [
    # model's -> models (remove apostrophe from docstrings to be safe)
    (b"model's", b"models"),
    (b"user's", b"users"),
    (b"it's", b"its"),
    (b"don't", b"do not"),
    (b"doesn't", b"does not"),
    (b"can't", b"cannot"),
    (b"won't", b"will not"),
    (b"isn't", b"is not"),
    (b"aren't", b"are not"),
    (b"wasn't", b"was not"),
    (b"weren't", b"were not"),
    (b"hasn't", b"has not"),
    (b"haven't", b"have not"),
    (b"hadn't", b"had not"),
    (b"wouldn't", b"would not"),
    (b"couldn't", b"could not"),
    (b"shouldn't", b"should not"),
    (b"that's", b"that is"),
    (b"there's", b"there is"),
    (b"what's", b"what is"),
    (b"who's", b"who is"),
]

total = 0
for path in files:
    data = path.read_bytes()
    original = data
    for old, new in replacements:
        data = data.replace(old, new)
    if data != original:
        path.write_bytes(data)
        count = sum(original.count(old) for old, _ in replacements)
        print(f"Fixed {path.name}: {count} replacements")
        total += count

print(f"\nTotal: {total} replacements across {len(files)} files")
