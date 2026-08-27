"""Demonstration script for Sprint 2 Concept 10 Document Processing.

Loads documents from the data/ folder using DocumentService and prints output logs.
"""

import os
import sys

# Ensure src/ is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.document_service import DocumentService


def main():
    print("=" * 60)
    print("PolicyPilot Document Processing - Intake Verification")
    print("=" * 60)
    print("Initializing DocumentService and loading corpus...")
    print()
    
    service = DocumentService()
    docs = service.load_documents(data_dir="data")
    
    print()
    print("=" * 60)
    print(f"Intake summary: successfully loaded {len(docs)} documents.")
    print("=" * 60)


if __name__ == "__main__":
    main()
