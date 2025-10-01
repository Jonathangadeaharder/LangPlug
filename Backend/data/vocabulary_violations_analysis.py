#!/usr/bin/env python3
"""
Analyze German vocabulary CSV files for inappropriate entries.

This script identifies proper names, technical terms, and other non-vocabulary
words that shouldn't be in a language learning vocabulary list.
"""

import csv
import os
import re
from dataclasses import dataclass


@dataclass
class Violation:
    file_name: str
    line_number: int
    german_word: str
    spanish_translation: str
    violation_type: str
    reason: str
    suggested_action: str


class VocabularyAnalyzer:
    def __init__(self):
        # Known proper names (personal names)
        self.personal_names = {
            "hans",
            "maria",
            "wolfgang",
            "peter",
            "anna",
            "klaus",
            "brigitte",
            "thomas",
            "ursula",
            "michael",
            "sabine",
            "andreas",
            "katrin",
            "stefan",
            "petra",
            "alexander",
            "elisabeth",
            "christian",
            "susanne",
            "markus",
            "andrea",
            "frank",
            "barbara",
            "daniel",
            "martina",
            "alex",
            "abby",
            "adams",
            "aeryn",
            "dad",
            "mom",
            "mama",
            "papa",
        }

        # Known place names
        self.place_names = {
            "berlin",
            "münchen",
            "hamburg",
            "köln",
            "frankfurt",
            "stuttgart",
            "düsseldorf",
            "dortmund",
            "essen",
            "leipzig",
            "bremen",
            "dresden",
            "hannover",
            "nürnberg",
            "duisburg",
            "bochum",
            "wuppertal",
            "bielefeld",
            "deutschland",
            "germany",
            "österreich",
            "schweiz",
            "bayern",
            "sachsen",
            "nrw",
            "baden-württemberg",
            "hessen",
            "niedersachsen",
            "rheinland-pfalz",
            "schleswig-holstein",
            "thüringen",
            "brandenburg",
            "mecklenburg-vorpommern",
            "saarland",
            "europa",
            "afrika",
            "asien",
            "amerika",
            "australien",
        }

        # Known brand names
        self.brand_names = {
            "mercedes",
            "bmw",
            "audi",
            "volkswagen",
            "porsche",
            "adidas",
            "nike",
            "coca-cola",
            "pepsi",
            "mcdonald",
            "burger king",
            "apple",
            "samsung",
            "google",
            "facebook",
            "amazon",
            "microsoft",
            "sony",
            "toyota",
            "siemens",
            "bosch",
            "lufthansa",
            "bayer",
            "basf",
        }

        # Known acronyms/abbreviations
        self.acronyms = {
            "usa",
            "eu",
            "nato",
            "uno",
            "who",
            "unesco",
            "fbi",
            "cia",
            "nasa",
            "brd",
            "ddr",
            "fdj",
            "sed",
            "cdu",
            "spd",
            "fdp",
            "linke",
            "afd",
            "csu",
            "pkw",
            "lkw",
            "gmbh",
            "ag",
            "kg",
            "eg",
            "bzw",
            "usw",
            "etc",
            "z.b.",
            "d.h.",
            "u.a.",
            "o.ä.",
            "cd",
            "dvd",
            "tv",
            "pc",
            "it",
            "an",
            "auf",  # These appear to be prepositions wrongly marked as acronyms
        }

        # Interjections and sounds
        self.interjections = {
            "äh",
            "ähm",
            "hmm",
            "hm",
            "oh",
            "ah",
            "ahh",
            "wow",
            "hey",
            "hallo",
            "tschüss",
            "tschüs",
            "okay",
            "ok",
            "na",
            "naja",
            "tja",
            "ach",
        }

        # Technical terms that are too specialized
        self.technical_terms = {
            "cyberangriff",
            "automatisierung",
            "digitalisierung",
            "atomkraftwerk",
            "atommeiler",
            "atombombe",
            "atomenergie",
            "bakterium",
            "blutzuckerspiegel",
            "computerspielsucht",
            "datenverarbeitung",
            "datensicherheit",
            "diskriminierung",
            "durchschnittstemperatur",
            "entwicklungsland",
            "forschungseinrichtung",
            "fingerspitzengefühl",
            "firmenkultur",
            "automobilhersteller",
            "bachelorarbeit",
            "branchenverband",
            "bundesverband",
            "chancengleichheit",
            "desinteresse",
            "dienstleistung",
            "dissertation",
            "durchführung",
            "durchmesser",
            "dürreperiode",
            "einschränkung",
            "entwicklungsperspektive",
            "entschädigung",
            "erwerbstätigkeit",
            "fachbereich",
            "fachliteratur",
            "forschungsteam",
            "führungskraft",
            "arbeitgeber",
            "arbeitnehmer",
            "arbeitsmarkt",
            "arbeitsrechtler",
            "arbeitssituation",
            "arbeitsumfeld",
        }

        # Colloquial/slang terms
        self.colloquial_terms = {
            "cool",
            "super",
            "toll",
            "boss",
            "quatsch",
            "mist",
            "blöd",
            "doof",
            "geil",
            "krass",
            "ätzend",
            "nervig",
        }

        # English loanwords that are just English in German text
        self.english_loanwords = {
            "sorry",
            "deal",
            "captain",
            "major",
            "sir",
            "madam",
            "ma'am",
            "lord",
            "mr",
            "mrs",
            "blog",
            "comic",
            "fitness",
            "show",
            "team",
            "fan",
            "festival",
            "hamburger",
            "pizza",
            "laptop",
            "container",
            "video",
            "basketball",
            "tennis",
            "volleyball",
            "club",
        }

        # Number words (unless specifically for teaching numbers)
        self.number_words = {
            "null",
            "eins",
            "zwei",
            "drei",
            "vier",
            "fünf",
            "sechs",
            "sieben",
            "acht",
            "neun",
            "zehn",
            "elf",
            "zwölf",
            "dreizehn",
            "vierzehn",
            "fünfzehn",
            "sechzehn",
            "siebzehn",
            "achtzehn",
            "neunzehn",
            "zwanzig",
        }

        # Words that should be flagged based on patterns
        self.pattern_checks = [
            (r"^[A-Z]{2,}$", "acronym_pattern", "All caps abbreviation"),
            (r".*-.*-.*", "complex_compound", "Overly complex compound word"),
            (r".*ierung$", "technical_suffix", 'Technical "-ierung" suffix'),
            (r".*wissenschaft$", "academic_term", 'Academic field ending in "-wissenschaft"'),
        ]

    def analyze_word(self, german_word: str, spanish_translation: str) -> list[str]:
        """Analyze a word and return list of violation types."""
        violations = []
        word_lower = german_word.lower().strip()

        # Skip empty or very short entries
        if len(word_lower) < 2:
            return violations

        # Check for personal names (capitalized common names)
        if word_lower in self.personal_names:
            violations.append("personal_name")

        # Check for place names
        if word_lower in self.place_names:
            violations.append("place_name")

        # Check for brand names
        if word_lower in self.brand_names:
            violations.append("brand_name")

        # Check for acronyms
        if word_lower in self.acronyms:
            violations.append("acronym")

        # Check for interjections
        if word_lower in self.interjections:
            violations.append("interjection")

        # Check for technical terms
        if word_lower in self.technical_terms:
            violations.append("technical_term")

        # Check for colloquial terms
        if word_lower in self.colloquial_terms:
            violations.append("colloquial")

        # Check for English loanwords
        if word_lower in self.english_loanwords:
            violations.append("english_loanword")

        # Check for number words
        if word_lower in self.number_words:
            violations.append("number_word")

        # Pattern-based checks
        for pattern, vtype, _description in self.pattern_checks:
            if re.match(pattern, german_word):
                violations.append(vtype)

        # Check for titles (Herr, Frau, Dr., Prof., etc.)
        if word_lower in ["herr", "frau", "dr.", "prof.", "dr", "prof"]:
            violations.append("title")

        # Check for words that are clearly proper nouns (start with capital and are uncommon)
        if (
            german_word[0].isupper()
            and len(german_word) > 3
            and word_lower not in ["deutschland", "german", "deutsch"]
            and german_word
            not in [
                "Januar",
                "Februar",
                "März",
                "April",
                "Mai",
                "Juni",
                "Juli",
                "August",
                "September",
                "Oktober",
                "November",
                "Dezember",
                "Montag",
                "Dienstag",
                "Mittwoch",
                "Donnerstag",
                "Freitag",
                "Samstag",
                "Sonntag",
            ]
            and not any(
                german_word.startswith(prefix) for prefix in ["Auto", "Bahn", "Fahr", "Haus", "Schul", "Arbeits"]
            )
        ):
            # This is likely a proper noun that we haven't caught
            violations.append("likely_proper_noun")

        return violations

    def get_violation_details(self, violation_type: str) -> tuple[str, str]:
        """Get reason and suggested action for a violation type."""
        details = {
            "personal_name": (
                "Personal name - not appropriate for vocabulary learning",
                "Remove - personal names aren't vocabulary",
            ),
            "place_name": (
                "Place name - too specific for general vocabulary",
                "Remove or move to geography-specific lesson",
            ),
            "brand_name": ("Brand/company name - not general vocabulary", "Remove - brand names aren't vocabulary"),
            "acronym": ("Acronym/abbreviation - not suitable for vocabulary learning", "Remove or expand to full form"),
            "interjection": (
                "Interjection/sound - not proper vocabulary",
                "Remove - interjections aren't structured vocabulary",
            ),
            "technical_term": ("Overly technical/specialized term", "Remove or move to advanced/technical vocabulary"),
            "colloquial": ("Too colloquial/slang for structured learning", "Replace with standard German equivalent"),
            "english_loanword": (
                "English loanword - not native German vocabulary",
                "Remove or replace with German equivalent",
            ),
            "number_word": (
                "Number word - should be in dedicated numbers lesson",
                "Move to numbers-specific vocabulary",
            ),
            "title": ("Title/form of address - not general vocabulary", "Remove or move to etiquette/titles lesson"),
            "likely_proper_noun": ("Likely proper noun based on capitalization", "Review - may be proper name"),
            "acronym_pattern": ("Pattern suggests acronym/abbreviation", "Review - may be inappropriate abbreviation"),
            "complex_compound": ("Overly complex compound word", "Consider simpler alternatives"),
            "technical_suffix": ("Technical suffix suggests specialized term", "Review for appropriateness"),
            "academic_term": ("Academic field term", "Move to academic/professional vocabulary"),
        }
        return details.get(violation_type, ("Unknown violation", "Review entry"))

    def analyze_file(self, file_path: str) -> list[Violation]:
        """Analyze a single CSV file for violations."""
        violations = []

        if not os.path.exists(file_path):
            return violations

        try:
            with open(file_path, encoding="utf-8") as csvfile:
                # Skip empty files
                content = csvfile.read()
                if not content.strip():
                    return violations

                csvfile.seek(0)
                reader = csv.reader(csvfile)

                for line_num, row in enumerate(reader, 1):
                    # Skip header row
                    if line_num == 1:
                        continue

                    # Skip empty rows
                    if not row or len(row) < 2:
                        continue

                    german_word = row[0].strip()
                    spanish_translation = row[1].strip() if len(row) > 1 else ""

                    # Skip empty entries
                    if not german_word:
                        continue

                    violation_types = self.analyze_word(german_word, spanish_translation)

                    for violation_type in violation_types:
                        reason, suggested_action = self.get_violation_details(violation_type)

                        violation = Violation(
                            file_name=os.path.basename(file_path),
                            line_number=line_num,
                            german_word=german_word,
                            spanish_translation=spanish_translation,
                            violation_type=violation_type,
                            reason=reason,
                            suggested_action=suggested_action,
                        )
                        violations.append(violation)

        except Exception:
            pass

        return violations


def main():
    """Main analysis function."""
    data_dir = "/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/data"
    files_to_analyze = ["A1_vokabeln.csv", "A2_vokabeln.csv", "B1_vokabeln.csv", "B2_vokabeln.csv", "C1_vokabeln.csv"]

    analyzer = VocabularyAnalyzer()
    all_violations = []

    for filename in files_to_analyze:
        file_path = os.path.join(data_dir, filename)

        violations = analyzer.analyze_file(file_path)
        all_violations.extend(violations)

        if violations:
            pass
        else:
            pass

    # Group violations by file
    violations_by_file = {}
    for violation in all_violations:
        if violation.file_name not in violations_by_file:
            violations_by_file[violation.file_name] = []
        violations_by_file[violation.file_name].append(violation)

    # Report results

    total_violations = 0
    for filename in files_to_analyze:
        violations = violations_by_file.get(filename, [])
        total_violations += len(violations)

        if violations:
            # Group by violation type
            by_type = {}
            for v in violations:
                if v.violation_type not in by_type:
                    by_type[v.violation_type] = []
                by_type[v.violation_type].append(v)

            for vtype, vlist in by_type.items():
                for v in vlist[:10]:  # Show first 10 of each type
                    pass
                if len(vlist) > 10:
                    pass
        else:
            pass

    # Summary statistics

    violation_type_counts = {}
    for violation in all_violations:
        vtype = violation.violation_type
        violation_type_counts[vtype] = violation_type_counts.get(vtype, 0) + 1

    for vtype, _count in sorted(violation_type_counts.items(), key=lambda x: x[1], reverse=True):
        pass


if __name__ == "__main__":
    main()
