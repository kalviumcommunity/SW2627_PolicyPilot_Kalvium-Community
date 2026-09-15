from src.api import load_default_chunks, run_server
chunks = load_default_chunks()
print("OK -", len(chunks), "chunks loaded")
print("First chunk section:", chunks[0]["section"])
print("First chunk source:", chunks[0]["source"])
