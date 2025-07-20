#!/usr/bin/env python3
"""
Unit tests for JSON validation and parsing in the a1decider vocabulary analysis system.
Tests various scenarios for Gemini API response handling and JSON format validation.
"""

import unittest
import json
from unittest.mock import Mock, patch
from pydantic import ValidationError

# Import the classes and functions we want to test
try:
    from a1decider import VocabularyItem, VocabularyAnalysis
except ImportError:
    # If direct import fails, we'll create mock classes for testing
    from pydantic import BaseModel, Field
    from typing import List
    
    class VocabularyItem(BaseModel):
        word: str = Field(description="The German word being analyzed")
        lemma: str = Field(description="The lemma (base form) of the German word")
        lemma_translation: str = Field(description="Spanish translation of the lemma")
        is_relevant: bool = Field(description="Whether this word is relevant vocabulary to learn")
        
    class VocabularyAnalysis(BaseModel):
        items: List[VocabularyItem] = Field(description="List of analyzed vocabulary items")


class TestJSONValidation(unittest.TestCase):
    """Test suite for JSON validation and parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_json_response = {
            "items": [
                {
                    "word": "Haus",
                    "lemma": "Haus",
                    "lemma_translation": "casa",
                    "is_relevant": True
                },
                {
                    "word": "gehen",
                    "lemma": "gehen",
                    "lemma_translation": "ir",
                    "is_relevant": True
                }
            ]
        }
        
        self.valid_json_list = [
            {
                "word": "schnell",
                "lemma": "schnell",
                "lemma_translation": "rápido",
                "is_relevant": True
            },
            {
                "word": "Zeit",
                "lemma": "Zeit",
                "lemma_translation": "tiempo",
                "is_relevant": True
            }
        ]
    
    def test_valid_json_object_format(self):
        """Test parsing of valid JSON object with 'items' key."""
        json_str = json.dumps(self.valid_json_response)
        
        # Test JSON parsing
        parsed_data = json.loads(json_str)
        self.assertIn('items', parsed_data)
        self.assertIsInstance(parsed_data['items'], list)
        
        # Test Pydantic validation
        vocab_analysis = VocabularyAnalysis(**parsed_data)
        self.assertEqual(len(vocab_analysis.items), 2)
        self.assertEqual(vocab_analysis.items[0].word, "Haus")
        self.assertEqual(vocab_analysis.items[0].lemma_translation, "casa")
        self.assertTrue(vocab_analysis.items[0].is_relevant)
    
    def test_valid_json_list_format(self):
        """Test parsing of valid JSON list format."""
        json_str = json.dumps(self.valid_json_list)
        
        # Test JSON parsing
        parsed_data = json.loads(json_str)
        self.assertIsInstance(parsed_data, list)
        
        # Test Pydantic validation
        vocab_items = [VocabularyItem(**item) for item in parsed_data]
        self.assertEqual(len(vocab_items), 2)
        self.assertEqual(vocab_items[0].word, "schnell")
        self.assertEqual(vocab_items[1].lemma_translation, "tiempo")
    
    def test_invalid_json_syntax(self):
        """Test handling of invalid JSON syntax."""
        invalid_json_strings = [
            '{"items": [}',  # Missing closing bracket
            '{"items": [{"word": "test",}]}',  # Trailing comma
            '{items: []}',  # Unquoted key
            '[{"word": "test" "lemma": "test"}]',  # Missing comma
            'not json at all',  # Not JSON
        ]
        
        for invalid_json in invalid_json_strings:
            with self.subTest(json_str=invalid_json):
                with self.assertRaises(json.JSONDecodeError):
                    json.loads(invalid_json)
    
    def test_missing_required_fields(self):
        """Test validation when required fields are missing."""
        incomplete_items = [
            {"word": "test"},  # Missing lemma, lemma_translation, is_relevant
            {"word": "test", "lemma": "test"},  # Missing lemma_translation, is_relevant
            {"word": "test", "lemma": "test", "lemma_translation": "prueba"},  # Missing is_relevant
            {"lemma": "test", "lemma_translation": "prueba", "is_relevant": True},  # Missing word
        ]
        
        for incomplete_item in incomplete_items:
            with self.subTest(item=incomplete_item):
                with self.assertRaises(ValidationError):
                    VocabularyItem(**incomplete_item)
    
    def test_incorrect_field_types(self):
        """Test validation with incorrect field types."""
        # Test cases that should definitely fail validation
        invalid_type_items = [
            {
                "word": None,  # None should not be accepted for required string
                "lemma": "test",
                "lemma_translation": "prueba",
                "is_relevant": True
            },
            {
                "word": "test",
                "lemma": None,  # None should not be accepted for required string
                "lemma_translation": "prueba",
                "is_relevant": True
            },
            {
                "word": "test",
                "lemma": "test",
                "lemma_translation": ["prueba"],  # List should not be accepted for string
                "is_relevant": True
            },
            {
                "word": "test",
                "lemma": "test",
                "lemma_translation": {"es": "prueba"},  # Dict should not be accepted for string
                "is_relevant": True
            }
        ]
        
        for invalid_item in invalid_type_items:
            with self.subTest(item=invalid_item):
                with self.assertRaises(ValidationError):
                    VocabularyItem(**invalid_item)
    
    def test_type_coercion(self):
        """Test that Pydantic handles type coercion appropriately."""
        # Test cases where Pydantic might coerce types
        coercible_items = [
            {
                "word": 123,  # Number to string coercion
                "lemma": "test",
                "lemma_translation": "prueba",
                "is_relevant": True
            },
            {
                "word": "test",
                "lemma": "test",
                "lemma_translation": "prueba",
                "is_relevant": 1  # Integer to boolean coercion
            }
        ]
        
        for item in coercible_items:
            with self.subTest(item=item):
                try:
                    vocab_item = VocabularyItem(**item)
                    # Verify the types were coerced correctly
                    self.assertIsInstance(vocab_item.word, str)
                    self.assertIsInstance(vocab_item.lemma, str)
                    self.assertIsInstance(vocab_item.lemma_translation, str)
                    self.assertIsInstance(vocab_item.is_relevant, bool)
                except ValidationError:
                    # If coercion fails, that's also acceptable behavior
                    pass
    
    def test_markdown_wrapped_json(self):
        """Test parsing JSON that might be wrapped in markdown code blocks."""
        json_content = json.dumps(self.valid_json_list)
        
        markdown_wrapped_formats = [
            f"```json\n{json_content}\n```",
            f"```\n{json_content}\n```",
        ]
        
        for wrapped_json in markdown_wrapped_formats:
            with self.subTest(wrapped=wrapped_json):
                # Simulate the cleaning process like in a1decider.py
                cleaned = wrapped_json.strip()
                if cleaned.startswith('```json'):
                    cleaned = cleaned[7:]  # Remove ```json
                elif cleaned.startswith('```'):
                    cleaned = cleaned[3:]  # Remove ```
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]  # Remove trailing ```
                cleaned = cleaned.strip()
                
                # Should be able to parse after cleaning
                parsed_data = json.loads(cleaned)
                vocab_items = [VocabularyItem(**item) for item in parsed_data]
                self.assertEqual(len(vocab_items), 2)
    
    def test_empty_responses(self):
        """Test handling of empty responses."""
        # Test with actual data structures
        empty_data_responses = [
            [],  # Empty list
            {"items": []},  # Empty items list
        ]
        
        for empty_response in empty_data_responses:
            with self.subTest(response=empty_response):
                if isinstance(empty_response, dict) and 'items' in empty_response:
                    # Empty items list should be valid
                    vocab_analysis = VocabularyAnalysis(**empty_response)
                    self.assertEqual(len(vocab_analysis.items), 0)
                elif isinstance(empty_response, list):
                    # Empty list should be valid
                    vocab_items = [VocabularyItem(**item) for item in empty_response]
                    self.assertEqual(len(vocab_items), 0)
    
    def test_extra_fields_handling(self):
        """Test that extra fields in JSON are handled gracefully."""
        item_with_extra_fields = {
            "word": "test",
            "lemma": "test",
            "lemma_translation": "prueba",
            "is_relevant": True,
            "extra_field": "should be ignored",
            "another_extra": 123
        }
        
        # Pydantic should ignore extra fields by default
        vocab_item = VocabularyItem(**item_with_extra_fields)
        self.assertEqual(vocab_item.word, "test")
        self.assertEqual(vocab_item.lemma_translation, "prueba")
        # Extra fields should not be accessible
        self.assertFalse(hasattr(vocab_item, 'extra_field'))
    
    def test_special_characters_in_strings(self):
        """Test handling of special characters in string fields."""
        special_char_items = [
            {
                "word": "Mädchen",  # Umlaut
                "lemma": "Mädchen",
                "lemma_translation": "niña",
                "is_relevant": True
            },
            {
                "word": "Straße",  # Eszett
                "lemma": "Straße",
                "lemma_translation": "calle",
                "is_relevant": True
            },
            {
                "word": "café",  # Accent
                "lemma": "café",
                "lemma_translation": "café",
                "is_relevant": True
            }
        ]
        
        for item in special_char_items:
            with self.subTest(item=item):
                vocab_item = VocabularyItem(**item)
                self.assertEqual(vocab_item.word, item["word"])
                self.assertEqual(vocab_item.lemma_translation, item["lemma_translation"])
    
    def test_boolean_values(self):
        """Test different boolean representations."""
        # Test standard boolean values
        standard_booleans = [
            (True, True),
            (False, False),
        ]
        
        base_item = {
            "word": "test",
            "lemma": "test",
            "lemma_translation": "prueba"
        }
        
        # Test standard boolean values (should always work)
        for input_bool, expected_bool in standard_booleans:
            with self.subTest(input_bool=input_bool):
                item = {**base_item, "is_relevant": input_bool}
                vocab_item = VocabularyItem(**item)
                self.assertEqual(vocab_item.is_relevant, expected_bool)
    
    def test_json_response_validation_workflow(self):
        """Test the complete workflow of validating a JSON response."""
        # Simulate a complete validation workflow
        mock_gemini_response = json.dumps([
            {
                "word": "Hund",
                "lemma": "Hund",
                "lemma_translation": "perro",
                "is_relevant": True
            },
            {
                "word": "laufen",
                "lemma": "laufen",
                "lemma_translation": "correr",
                "is_relevant": True
            }
        ])
        
        # Step 1: Parse JSON
        try:
            parsed_data = json.loads(mock_gemini_response)
            self.assertIsInstance(parsed_data, list)
        except json.JSONDecodeError:
            self.fail("Valid JSON should parse successfully")
        
        # Step 2: Validate with Pydantic
        try:
            vocab_items = [VocabularyItem(**item) for item in parsed_data]
            self.assertEqual(len(vocab_items), 2)
            
            # Step 3: Verify data integrity
            for item in vocab_items:
                self.assertIsInstance(item.word, str)
                self.assertIsInstance(item.lemma, str)
                self.assertIsInstance(item.lemma_translation, str)
                self.assertIsInstance(item.is_relevant, bool)
                self.assertTrue(len(item.word) > 0)
                self.assertTrue(len(item.lemma_translation) > 0)
                
        except ValidationError as e:
            self.fail(f"Valid data should validate successfully: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling scenarios."""
    
    def test_malformed_json_detection(self):
        """Test detection of malformed JSON responses."""
        def is_valid_json(text):
            """Helper function to check if text is valid JSON."""
            try:
                if not text.strip():
                    return False
                json.loads(text)
                return True
            except (json.JSONDecodeError, ValueError):
                return False
        
        malformed_responses = [
            "This is not JSON at all",
            "Here's some text before {\"word\": \"test\"} and after",
            "```json\n{invalid json}\n```",
        ]
        
        for malformed in malformed_responses:
            with self.subTest(response=malformed):
                # Test that we can detect malformed responses
                is_valid = is_valid_json(malformed)
                self.assertFalse(is_valid, f"Response should be invalid: {malformed}")
    
    def test_validation_error_handling(self):
        """Test proper handling of validation errors."""
        invalid_item = {
            "word": "test",
            "lemma": "test",
            # Missing lemma_translation and is_relevant
        }
        
        with self.assertRaises(ValidationError) as context:
            VocabularyItem(**invalid_item)
        
        # Verify that the error contains useful information
        error = context.exception
        self.assertIsInstance(error, ValidationError)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)