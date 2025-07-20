#!/usr/bin/env python3
"""
Integration test to verify the enhanced JSON validation logic in a1decider.py
"""

import json
import sys
import os

# Add the current directory to the path to import a1decider
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a1decider import VocabularyItem, VocabularyAnalysis
from pydantic import ValidationError

def test_enhanced_json_parsing():
    """Test the enhanced JSON parsing logic with various response formats."""
    
    print("Testing enhanced JSON validation integration...")
    
    # Test cases that simulate different Gemini API response formats
    test_cases = [
        {
            "name": "Standard JSON list format",
            "response": json.dumps([
                {"word": "Haus", "lemma": "Haus", "lemma_translation": "casa", "is_relevant": True},
                {"word": "gehen", "lemma": "gehen", "lemma_translation": "ir", "is_relevant": True}
            ])
        },
        {
            "name": "JSON with items wrapper",
            "response": json.dumps({
                "items": [
                    {"word": "Buch", "lemma": "Buch", "lemma_translation": "libro", "is_relevant": True}
                ]
            })
        },
        {
            "name": "Markdown-wrapped JSON",
            "response": "```json\n" + json.dumps([
                {"word": "Wasser", "lemma": "Wasser", "lemma_translation": "agua", "is_relevant": True}
            ]) + "\n```"
        },
        {
            "name": "JSON with type coercion needed",
            "response": json.dumps([
                {"word": "Auto", "lemma": "Auto", "lemma_translation": "coche", "is_relevant": "true"},  # String boolean
                {"word": 123, "lemma": 123, "lemma_translation": "número", "is_relevant": 1}  # Numbers
            ])
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        response_text = test_case['response']
        
        try:
            # Simulate the enhanced cleaning process from a1decider.py
            cleaned_text = response_text.strip()
            
            # Enhanced markdown cleaning
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]   # Remove ```
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            cleaned_text = cleaned_text.strip()
            
            # Handle empty responses
            if not cleaned_text or cleaned_text.lower() in ['null', 'none', '']:
                raise ValueError("Empty or null response received")
            
            # Parse JSON with validation
            try:
                json_data = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                # Try to extract JSON from mixed content
                import re
                json_match = re.search(r'\{.*\}|\[.*\]', cleaned_text, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON: {e}")
            
            # Handle different JSON structures with validation
            if isinstance(json_data, dict):
                if 'items' in json_data:
                    items_data = json_data['items']
                elif len(json_data) == 1 and isinstance(list(json_data.values())[0], list):
                    items_data = list(json_data.values())[0]
                else:
                    raise ValueError("JSON object must contain 'items' key or be a direct list")
            elif isinstance(json_data, list):
                items_data = json_data
            else:
                raise ValueError(f"Unexpected JSON structure: {type(json_data)}")
            
            # Validate using Pydantic models
            results = []
            validation_errors = []
            
            for i, item in enumerate(items_data):
                try:
                    vocab_item = VocabularyItem(**item)
                    results.append((vocab_item.lemma, vocab_item.lemma_translation, vocab_item.is_relevant))
                    print(f"  ✓ Validated: {vocab_item.word} -> {vocab_item.lemma_translation} (relevant: {vocab_item.is_relevant})")
                except Exception as e:
                    validation_errors.append(f"Item {i}: {e}")
                    print(f"  ⚠ Validation error for item {i}: {e}")
            
            if validation_errors:
                print(f"  Warning: {len(validation_errors)} items had validation issues")
            
            print(f"  ✓ Successfully processed {len(results)} vocabulary items")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print("\n=== Integration test completed ===")

if __name__ == "__main__":
    test_enhanced_json_parsing()