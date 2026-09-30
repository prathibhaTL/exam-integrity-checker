"""Test with short text to verify fallback"""
import sys
import os

# Add project root to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import generate_questions

# Very short text
short_text = """
Python is a programming language. Java is also a language. 
Computer science involves algorithms and data structures.
Software development requires coding skills.
"""

print("Testing with SHORT text...")
print("=" * 60)

mcqs, desc = generate_questions(short_text, mcq_count=6, desc_count=3)

print(f"\nGenerated {len(mcqs)} MCQs")
if len(mcqs) > 0:
    for i, q in enumerate(mcqs[:3], 1):
        print(f"\nMCQ {i}:")
        print(f"Q: {q['question']}")
        print(f"Options: {q['options']}")
        print(f"Answer: {q['answer']}")
else:
    print("âŒ No MCQs generated!")

print(f"\n{len(desc)} Descriptive questions generated")
print("âœ… Test complete!")

