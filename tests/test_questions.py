"""Test script to verify MCQ generation is working"""
import sys
import os

# Add project root to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import generate_questions

# Sample text
sample_text = """
Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.

Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. Machine learning algorithms build mathematical models based on sample data, known as training data, to make predictions or decisions.

Deep Learning is a subset of machine learning based on artificial neural networks with multiple layers. Deep learning is particularly effective for tasks such as image recognition, natural language processing, and speech recognition.

Natural Language Processing (NLP) focuses on the interaction between computers and humans using natural language. NLP enables computers to understand, interpret, and generate human language in valuable ways.

Computer Vision is an interdisciplinary field that enables computers to gain high-level understanding from digital images or videos. Computer vision tasks include image recognition, object detection, and image segmentation.
"""

print("Testing MCQ Generation...")
print("=" * 60)

# Test with different counts
for count in [3, 6, 10]:
    print(f"\nGenerating {count} MCQs:")
    mcqs, descriptives = generate_questions(sample_text, mcq_count=count, desc_count=3)
    
    print(f"Generated {len(mcqs)} MCQs")
    
    if len(mcqs) > 0:
        print("\nFirst MCQ:")
        print(f"Q: {mcqs[0]['question']}")
        print(f"Options: {mcqs[0]['options']}")
        print(f"Answer: {mcqs[0]['answer']}")
        print(f"Difficulty: {mcqs[0]['difficulty']}")
        print("âœ… MCQs are generating successfully!")
    else:
        print("âŒ No MCQs generated!")
    
    print(f"\nGenerated {len(descriptives)} Descriptive Questions")
    if len(descriptives) > 0:
        print(f"First: {descriptives[0]['question']}")
    
    print("-" * 60)

print("\nâœ… Test complete!")

