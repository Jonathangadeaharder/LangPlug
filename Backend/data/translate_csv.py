import csv

from googletrans import Translator

# Initialize translator
translator = Translator()

# Input and output file paths
input_file = "10K_csv.csv"
output_file = "10K_csv_translated.csv"

# Read the original CSV and translate
with open(input_file, encoding="utf-8") as infile, open(output_file, "w", newline="", encoding="utf-8") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        if len(row) == 2:
            frequency, german_word = row
            try:
                # Translate German word to Spanish
                translation = translator.translate(german_word, src="de", dest="es").text
                # Write new row: german_word, spanish_translation
                writer.writerow([german_word, translation])
            except Exception:
                # Fallback: write original if translation fails
                writer.writerow([german_word, german_word])

# Optional: Replace original file (uncomment if desired)
# import os
# os.replace(output_file, input_file)
