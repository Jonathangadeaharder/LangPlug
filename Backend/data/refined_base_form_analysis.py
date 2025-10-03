#!/usr/bin/env python3
"""
Refined German Vocabulary Base Form Analysis
Analyzes CSV files to find German words that are NOT in their base forms (lemma/Grundform)
This version reduces false positives by better handling exceptions and patterns.
"""

import csv
import re
from pathlib import Path


class RefinedGermanBaseFormAnalyzer:
    def __init__(self):
        # Definite violations - words we know are not base forms
        self.definite_violations = {
            # Common verb conjugations (past tense forms that should be infinitive)
            "machte": ("machen", "conjugated_verb_past"),
            "ging": ("gehen", "conjugated_verb_past"),
            "kam": ("kommen", "conjugated_verb_past"),
            "war": ("sein", "conjugated_verb_past"),
            "hatte": ("haben", "conjugated_verb_past"),
            "wurde": ("werden", "conjugated_verb_past"),
            "wollte": ("wollen", "conjugated_verb_past"),
            "sollte": ("sollen", "conjugated_verb_past"),
            "konnte": ("können", "conjugated_verb_past"),
            "musste": ("müssen", "conjugated_verb_past"),
            "durfte": ("dürfen", "conjugated_verb_past"),
            # Common plural nouns that should be singular
            "Häuser": ("Haus", "plural_noun"),
            "Männer": ("Mann", "plural_noun"),
            "Frauen": ("Frau", "plural_noun"),
            "Kinder": ("Kind", "plural_noun"),
            "Bücher": ("Buch", "plural_noun"),
            "Tiere": ("Tier", "plural_noun"),
            "Leute": ("Person", "plural_noun"),  # Special case
            "Autos": ("Auto", "plural_noun"),
            "Hotels": ("Hotel", "plural_noun"),
            "Tische": ("Tisch", "plural_noun"),
            "Stühle": ("Stuhl", "plural_noun"),
            # Declined adjectives that should be base form
            "große": ("groß", "declined_adjective"),
            "großer": ("groß", "declined_adjective"),
            "großen": ("groß", "declined_adjective"),
            "großes": ("groß", "declined_adjective"),
            "schöne": ("schön", "declined_adjective"),
            "schöner": ("schön", "inflected_adjective"),
            "schönen": ("schön", "declined_adjective"),
            "schönes": ("schön", "declined_adjective"),
            "gute": ("gut", "declined_adjective"),
            "guten": ("gut", "declined_adjective"),
            "guter": ("gut", "declined_adjective"),
            "gutes": ("gut", "declined_adjective"),
            "neue": ("neu", "declined_adjective"),
            "neuen": ("neu", "declined_adjective"),
            "neuer": ("neu", "declined_adjective"),
            "neues": ("neu", "declined_adjective"),
            "kleine": ("klein", "declined_adjective"),
            "kleinen": ("klein", "declined_adjective"),
            "kleiner": ("klein", "inflected_adjective"),
            "kleines": ("klein", "declined_adjective"),
            "alte": ("alt", "declined_adjective"),
            "alten": ("alt", "declined_adjective"),
            "alter": ("alt", "declined_adjective"),
            "altes": ("alt", "declined_adjective"),
            # Comparative/superlative forms
            "größer": ("groß", "comparative"),
            "größte": ("groß", "superlative"),
            "schönste": ("schön", "superlative"),
            "besser": ("gut", "comparative"),
            "beste": ("gut", "superlative"),
            "kleinste": ("klein", "superlative"),
            # Past participles used as adjectives (instead of infinitive verbs)
            "gebrochen": ("brechen", "past_participle"),
            "geschrieben": ("schreiben", "past_participle"),
            "gesprochen": ("sprechen", "past_participle"),
            "verloren": ("verlieren", "past_participle"),
        }

        # Words that are definitely correct base forms (exceptions to avoid false positives)
        self.correct_base_forms = {
            # Infinitive verbs (these are correct)
            "arbeiten",
            "sprechen",
            "verstehen",
            "antworten",
            "bedeuten",
            "begleiten",
            "behalten",
            "behaupten",
            "beobachten",
            "beraten",
            "berichten",
            "anbieten",
            "aufhalten",
            "auftreten",
            "ausrichten",
            "beachten",
            "beantworten",
            "achten",
            # Nouns that end in -er but are correct base forms
            "Vater",
            "Mutter",
            "Lehrer",
            "Fahrer",
            "Verkäufer",
            "Arbeiter",
            "Computer",
            "Hamburger",
            "Finger",
            "Winter",
            "Sommer",
            "Bruder",
            "Schwester",
            "Besucher",
            "Meter",
            "Liter",
            "Kilometer",
            "Theater",
            "Wetter",
            "Vermieter",
            "Anbieter",
            "Empfänger",
            "Absender",
            "Sprecher",
            "Hörer",
            "aber",
            "ander",
            "unter",
            "über",
            "auseinander",
            "durcheinander",
            "gegenüber",
            "besonder",
            "bitter",
            "bisher",
            "entweder",
            # Nouns that end in -e but are correct base forms
            "Blume",
            "Katze",
            "Straße",
            "Kirche",
            "Schule",
            "Lampe",
            "Tasse",
            "Flasche",
            "Tasche",
            "Brücke",
            "Küche",
            "Ecke",
            "Liebe",
            "Farbe",
            "Seite",
            "Reise",
            "Karte",
            "Torte",
            "Sahne",
            "Schere",
            "Garage",
            "Orange",
            "Minute",
            "Bitte",
            "beide",
            "beinahe",
            "danke",
            "gerade",
            # Other correct base forms
            "Best",
            "Test",
            "Rest",
            "West",
            "Ost",
            "Nord",
            "Süd",
            "Text",
            "Fest",
            "Ernst",
            "August",
            "Herbst",
            "Frost",
            "Durst",
            "Verlust",
            "Kunst",
            "absolut",
            "bereit",
            "beliebt",
            "berühmt",
            "bestimmt",
            "breit",
            "direkt",
            "ernst",
            "fest",
            "damit",
            "dicht",
            "erschöpft",
            "feucht",
            "geeignet",
            "gesamt",
            "befreit",
            "begeistert",
            "behindert",
            "ausgebildet",
            "ausgezeichnet",
            # Time and other expressions that are correct
            "früh",
            "früher",
            "jetzt",
            "immer",
            "nie",
            "oft",
            "manchmal",
            "bald",
        }

        # Common problematic patterns to ignore (these generate too many false positives)
        self.ignore_patterns = [
            r"^(der|die|das|den|dem|des)$",  # Articles
            r"^(ein|eine|einen|einem|einer|eines)$",  # Indefinite articles
            r"^(ich|du|er|sie|es|wir|ihr|sie)$",  # Pronouns
            r"^(mein|dein|sein|ihr|unser|euer)e?[nrs]?$",  # Possessive pronouns
            r"^(dieser|diese|dieses|diesen|diesem)$",  # Demonstrative pronouns
            r"^[A-Z][a-z]*$",  # Proper names (capitalized single words)
        ]

    def should_ignore_word(self, word: str) -> bool:
        """Check if a word should be ignored based on patterns."""
        return any(re.match(pattern, word) for pattern in self.ignore_patterns)

    def analyze_word(self, word: str) -> tuple[bool, str, str]:
        """
        Analyze if a German word is in its base form.
        Returns: (is_violation, violation_type, suggested_correction)
        """
        if not word or len(word) < 2:
            return False, "", ""

        # Skip words that should be ignored
        if self.should_ignore_word(word):
            return False, "", ""

        # Skip if word is a known correct base form
        if word.lower() in self.correct_base_forms or word in self.correct_base_forms:
            return False, "", ""

        # Check definite violations first
        if word in self.definite_violations:
            correction, violation_type = self.definite_violations[word]
            return True, violation_type, correction

        # Check case-insensitive violations
        word_lower = word.lower()
        if word_lower in self.definite_violations:
            correction, violation_type = self.definite_violations[word_lower]
            return True, violation_type, correction

        return False, "", ""

    def analyze_file(self, file_path: Path) -> list[dict]:
        """Analyze a CSV file for German base form violations."""
        violations = []

        if not file_path.exists():
            return violations

        try:
            with open(file_path, encoding="utf-8") as file:
                csv_reader = csv.reader(file)
                next(csv_reader, None)  # Skip header

                for line_num, row in enumerate(csv_reader, start=2):
                    if not row or len(row) < 1:
                        continue

                    german_word = row[0].strip()
                    spanish_translation = row[1].strip() if len(row) > 1 else ""

                    if not german_word:
                        continue

                    # Handle multi-word phrases
                    words = german_word.split()
                    for word_idx, word in enumerate(words):
                        # Remove punctuation but keep hyphens
                        clean_word = re.sub(r"[^\w\-äöüÄÖÜß]", "", word)
                        if not clean_word or len(clean_word) < 2:
                            continue

                        is_violation, violation_type, suggested_correction = self.analyze_word(clean_word)

                        if is_violation:
                            violations.append(
                                {
                                    "file": file_path.name,
                                    "line": line_num,
                                    "full_entry": german_word,
                                    "word": clean_word,
                                    "word_position": word_idx + 1 if len(words) > 1 else None,
                                    "violation_type": violation_type,
                                    "suggested_correction": suggested_correction,
                                    "spanish_translation": spanish_translation,
                                }
                            )

        except Exception:
            pass

        return violations

    def generate_report(self, all_violations: dict[str, list[dict]]) -> str:
        """Generate a comprehensive report of all violations."""
        report = []
        report.append("=" * 80)
        report.append("REFINED GERMAN VOCABULARY BASE FORM ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        total_violations = sum(len(violations) for violations in all_violations.values())
        report.append(
            f"SUMMARY: Found {total_violations} definite base form violations across {len(all_violations)} files"
        )
        report.append("(This analysis focuses on high-confidence violations only)")
        report.append("")

        # Summary by violation type
        violation_types = {}
        for file_violations in all_violations.values():
            for violation in file_violations:
                vtype = violation["violation_type"]
                violation_types[vtype] = violation_types.get(vtype, 0) + 1

        if violation_types:
            report.append("VIOLATIONS BY TYPE:")
            for vtype, count in sorted(violation_types.items()):
                report.append(f"  - {vtype}: {count} cases")
            report.append("")

        # Detailed results by file
        for filename, violations in all_violations.items():
            if not violations:
                report.append(f"FILE: {filename}")
                report.append("  ✓ No definite base form violations found")
                report.append("")
                continue

            report.append(f"FILE: {filename} ({len(violations)} violations)")
            report.append("-" * 50)

            # Group by violation type
            violations_by_type = {}
            for violation in violations:
                vtype = violation["violation_type"]
                if vtype not in violations_by_type:
                    violations_by_type[vtype] = []
                violations_by_type[vtype].append(violation)

            for vtype, type_violations in sorted(violations_by_type.items()):
                report.append(f"\n{vtype.upper().replace('_', ' ')} ({len(type_violations)} cases):")

                for violation in type_violations:
                    line_info = f"Line {violation['line']}"
                    if violation["word_position"]:
                        line_info += f", word {violation['word_position']}"

                    report.append(f"  {line_info}: '{violation['word']}' → '{violation['suggested_correction']}'")
                    if violation["full_entry"] != violation["word"]:
                        report.append(f'    Full entry: "{violation["full_entry"]}"')
                    if violation["spanish_translation"]:
                        report.append(f"    Spanish: {violation['spanish_translation']}")
                    report.append("")

        return "\n".join(report)


def main():
    """Main analysis function."""
    analyzer = RefinedGermanBaseFormAnalyzer()

    # Files to analyze
    data_dir = Path()
    csv_files = ["A1_vokabeln.csv", "A2_vokabeln.csv", "B1_vokabeln.csv", "B2_vokabeln.csv", "C1_vokabeln.csv"]

    all_violations = {}

    for filename in csv_files:
        file_path = data_dir / filename

        violations = analyzer.analyze_file(file_path)
        all_violations[filename] = violations

    # Generate and save report
    report = analyzer.generate_report(all_violations)

    # Save to file
    with open("refined_base_form_violations_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    # Also print report to console


if __name__ == "__main__":
    main()
