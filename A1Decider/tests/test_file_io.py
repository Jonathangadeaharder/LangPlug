import unittest
import os
import json
from core.file_io import (
    load_word_list,
    load_subtitles,
    load_global_unknowns,
    save_global_unknowns,
)

class TestFileIO(unittest.TestCase):
    def setUp(self):
        self.test_word_list_path = "test_word_list.txt"
        self.test_srt_path = "test.srt"
        self.test_vtt_path = "test.vtt"
        self.test_json_path = "test.json"

        with open(self.test_word_list_path, "w") as f:
            f.write("word1\nword2\nword3")

        with open(self.test_srt_path, "w") as f:
            f.write("1\n00:00:01,000 --> 00:00:02,000\nHello\n\n")

        with open(self.test_vtt_path, "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nWorld\n")

        with open(self.test_json_path, "w") as f:
            json.dump({"test": 1}, f)

    def tearDown(self):
        os.remove(self.test_word_list_path)
        os.remove(self.test_srt_path)
        os.remove(self.test_vtt_path)
        os.remove(self.test_json_path)

    def test_load_word_list(self):
        words = load_word_list(self.test_word_list_path)
        self.assertEqual(words, {"word1", "word2", "word3"})

    def test_load_subtitles(self):
        srt_subs, srt_format = load_subtitles(self.test_srt_path)
        self.assertEqual(srt_format, "srt")
        self.assertEqual(len(srt_subs), 1)
        self.assertEqual(srt_subs[0].text, "Hello")

        vtt_subs, vtt_format = load_subtitles(self.test_vtt_path)
        self.assertEqual(vtt_format, "vtt")
        self.assertEqual(len(vtt_subs), 1)
        self.assertEqual(vtt_subs[0].text, "World")

    def test_load_global_unknowns(self):
        unknowns = load_global_unknowns(self.test_json_path)
        self.assertEqual(unknowns, {"test": 1})

    def test_save_global_unknowns(self):
        data = {"new_test": 2}
        save_global_unknowns(self.test_json_path, data)
        with open(self.test_json_path, "r") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, data)

if __name__ == '__main__':
    unittest.main()