"""Convert the 10K vocabulary dump into a lemma + Spanish CSV.

The script reads the ``10K`` frequency list, lemmatizes every German
token with spaCy, translates the lemmas to Spanish with the
``Helsinki-NLP/opus-mt-de-es`` model, and writes a CSV matching the
``A1_vokabeln.csv`` structure.

Usage example::

    python format_10k_vocabulary.py

Make sure ``de_core_news_sm`` (or a compatible German spaCy model) and
``transformers`` with a Torch backend are installed before running the
script.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Iterable, Sequence
from pathlib import Path

import spacy
import torch
from transformers import MarianMTModel, MarianTokenizer

DEFAULT_SPACY_MODEL = "de_core_news_sm"
DEFAULT_HELSINKI_MODEL = "Helsinki-NLP/opus-mt-de-es"


def parse_frequency_file(path: Path) -> list[str]:
    """Return word tokens from the ``10K`` frequency dump."""

    content = path.read_text(encoding="utf-8").split()
    words: list[str] = []
    index = 0

    while index + 1 < len(content):
        token = content[index]
        next_token = content[index + 1]

        try:
            int(token)
        except ValueError:
            index += 1
            continue

        words.append(next_token)
        index += 2

    if index < len(content):
        unmatched = content[index]
        raise ValueError(f"Unmatched token at end of file: {unmatched!r}")

    return words


def load_spacy_model(model_name: str) -> spacy.language.Language:
    """Load a German spaCy model with only the pipes needed for lemmas."""

    try:
        nlp = spacy.load(model_name)
    except OSError as exc:
        msg = f"spaCy model '{model_name}' is not installed. Install it with: python -m spacy download {model_name}"
        raise SystemExit(msg) from exc

    for pipe in ("parser", "ner"):
        if pipe in nlp.pipe_names:
            nlp.disable_pipes(pipe)

    return nlp


def lemmatize_words(nlp: spacy.language.Language, words: Sequence[str]) -> list[str]:
    """Return lemmas for each token while preserving order."""

    lemmas: list[str] = []
    for doc in nlp.pipe(words, batch_size=512):
        if not doc:
            lemmas.append("")
            continue
        lemmas.append(doc[0].lemma_.strip())

    return lemmas


class HelsinkiTranslator:
    """Translate German strings to Spanish using Helsinki NLP models."""

    def __init__(self, model_name: str, device: str | None = None) -> None:
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.model = MarianMTModel.from_pretrained(model_name)

        torch_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model.to(torch_device)
        self.device = torch_device

    def translate_batch(self, texts: Sequence[str], batch_size: int = 32) -> list[str]:
        results: list[str] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            encoded = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            with torch.no_grad():
                generated = self.model.generate(**encoded)
            decoded = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
            results.extend(text.strip() for text in decoded)

        return results


def ordered_unique_lemmas(lemmas: Iterable[str]) -> list[str]:
    """Return lemmas without duplicates while preserving order."""

    seen = set()
    unique: list[str] = []
    for lemma in lemmas:
        key = lemma.lower()
        if not lemma or key in seen:
            continue
        seen.add(key)
        unique.append(lemma)

    return unique


def write_csv(path: Path, rows: Sequence[tuple[str, str]]) -> None:
    """Write lemma and translation pairs to disk."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\r\n")
        for lemma, translation in rows:
            writer.writerow([lemma, translation])


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Format the 10K vocabulary dump")
    parser.add_argument(
        "--input",
        default=None,
        help="Path to the raw 10K vocabulary file (default: script_dir/10K)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Destination CSV path (default: script_dir/10K_formatted.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of entries to process",
    )
    parser.add_argument(
        "--spacy-model",
        default=DEFAULT_SPACY_MODEL,
        help="spaCy model name for lemmatization",
    )
    parser.add_argument(
        "--helsinki-model",
        default=DEFAULT_HELSINKI_MODEL,
        help="Helsinki-NLP model used for translation",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for translation requests",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Torch device string (e.g. 'cuda', 'cuda:0', 'cpu')",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    input_path = Path(args.input) if args.input else script_dir / "10K"
    output_path = Path(args.output) if args.output else script_dir / "10K_formatted.csv"

    words = parse_frequency_file(input_path)
    if args.limit is not None:
        words = words[: args.limit]

    nlp = load_spacy_model(args.spacy_model)
    lemmas = lemmatize_words(nlp, words)
    unique_lemmas = ordered_unique_lemmas(lemmas)

    translator = HelsinkiTranslator(args.helsinki_model, device=args.device)
    translations = translator.translate_batch(unique_lemmas, batch_size=args.batch_size)

    rows = list(zip(unique_lemmas, translations, strict=False))
    write_csv(output_path, rows)


if __name__ == "__main__":
    main()
