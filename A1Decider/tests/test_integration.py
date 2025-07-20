import unittest
import os
import json
from core.spacy_processor import SpacyProcessor
from core.file_io import (
    load_word_list,
    load_subtitles,
    load_global_unknowns,
    save_global_unknowns,
)
from core.subtitle_processing import (
    process_subtitles,
    generate_filtered_subtitles,
)

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_word_list_path = "test_word_list.txt"
        self.test_srt_path = "test.srt"
        self.test_json_path = "test.json"
        self.test_output_path = "test_filtered.srt"

        with open(self.test_word_list_path, "w") as f:
            f.write("gehen\nStadt\n")

        with open(self.test_srt_path, "w") as f:
            f.write("1\n00:00:01,000 --> 00:00:02,000\nAnna und Peter gehen nach Berlin.\n\n")
            f.write("2\n00:00:03,000 --> 00:00:04,000\nDas ist eine tolle Stadt.\n\n")

        with open(self.test_json_path, "w") as f:
            json.dump({}, f)

        self.spacy_processor = SpacyProcessor(model="de_core_news_sm")

    def tearDown(self):
        os.remove(self.test_word_list_path)
        os.remove(self.test_srt_path)
        os.remove(self.test_json_path)
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)

    def test_full_pipeline(self):
        known_words = load_word_list(self.test_word_list_path)
        subs, sub_format = load_subtitles(self.test_srt_path)

        subs, word_counts, total_subtitles, skipped_subtitles, skipped_hard, word_to_subtitles, subtitle_format = process_subtitles(
            subs, sub_format, self.spacy_processor, known_words
        )

        self.assertEqual(total_subtitles, 2)
        self.assertEqual(skipped_subtitles, 1)
        self.assertEqual(skipped_hard, 1)
        self.assertEqual(word_counts, {"toll": 1})

        generate_filtered_subtitles(subs, known_words, self.test_output_path, sub_format, self.spacy_processor)

        self.assertTrue(os.path.exists(self.test_output_path))

        with open(self.test_output_path, "r") as f:
            content = f.read()
            self.assertIn("tolle Stadt", content)
            self.assertNotIn("Anna und Peter", content)

if __name__ == '__main__':
    unittest.main()