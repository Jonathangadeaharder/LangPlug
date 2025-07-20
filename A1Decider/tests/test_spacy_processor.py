import unittest
from unittest.mock import MagicMock
import spacy

# Mock the Rich console to avoid printing during tests
from rich.console import Console
console = MagicMock()

from core.spacy_processor import SpacyProcessor

class TestSpacyProcessor(unittest.TestCase):
    def setUp(self):
        # Load a real model for testing, but a small one
        self.nlp = spacy.load("de_core_news_sm")
        self.processor = SpacyProcessor(model="de_core_news_sm")
        self.processor.nlp = self.nlp

    def test_filter_tokens(self):
        text = "Anna und Peter gehen nach Berlin. Das ist eine tolle Stadt."
        
        # Expected lemmas after filtering
        expected_lemmas = ["toll", "stadt"]
        
        tokens = self.processor.filter_tokens(text)
        lemmas = [token.lemma_.lower() for token in tokens]
        
        self.assertEqual(lemmas, expected_lemmas)

    def test_filter_with_no_matches(self):
        text = "PER LOC ORG PROPN INTJ X SYM 123 ."
        tokens = self.processor.filter_tokens(text)
        self.assertEqual(len(tokens), 0)

if __name__ == '__main__':
    unittest.main()