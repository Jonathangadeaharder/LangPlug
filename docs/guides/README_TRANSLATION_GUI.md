# LangPlug SRT Translation GUI

A simple graphical interface for translating SRT subtitle files using LangPlug's translation services.

## Features

- **SRT File Translation**: Translate entire subtitle files at once
- **Multiple Languages**: Translate between German, Spanish, and English
- **Multiple Models**: Choose from different translation models:
  - OPUS-MT DE-ES (Fast) - Best for German to Spanish
  - OPUS-MT DE-EN (Fast) - Best for German to English
  - NLLB-600M (Multilingual) - Supports any language pair
- **Progress Tracking**: Real-time status updates during translation
- **Auto-Save**: Automatically saves translated SRT with new filename
- **Clean Interface**: Simple and intuitive Tkinter GUI

## Usage

### Windows

Double-click `run_translation_gui.bat` or run from command line:

```batch
run_translation_gui.bat
```

### Linux/Mac

```bash
./api_venv/bin/python scripts/translation_gui.py
```

## How to Use

1. **Select SRT File**:
   - Click "Browse..." button
   - Choose your source SRT file (e.g., German subtitles)

2. **Select Languages**:
   - Choose source language (default: German)
   - Choose target language (default: Spanish)

3. **Select Translation Model**:
   - OPUS-MT models are faster for specific language pairs
   - NLLB is more flexible but slower

4. **Translate**:
   - Click "Translate SRT File" button
   - Watch progress in status bar
   - Wait for completion message

5. **Result**:
   - Translated SRT file is automatically saved
   - Filename: `original_translated_es.srt` (or target language code)
   - Location: Same directory as source file

## Example

**Input File**: `Episode_18.srt` (German)
```srt
1
00:00:01,000 --> 00:00:03,000
Was bisher geschah.

2
00:00:04,000 --> 00:00:06,000
Ist jemand hier?
```

**Output File**: `Episode_18_translated_es.srt` (Spanish)
```srt
1
00:00:01,000 --> 00:00:03,000
Lo que pasó antes.

2
00:00:04,000 --> 00:00:06,000
¿Hay alguien aquí?
```

## Supported Language Pairs

### OPUS-MT DE-ES (Default)
- German → Spanish (optimized, fast)

### OPUS-MT DE-EN
- German → English (optimized, fast)

### NLLB-600M
- German ↔ Spanish
- German ↔ English
- English ↔ Spanish
- Any other language pair (200+ languages supported)

## Performance

- **Model Loading**: 10-30 seconds (first time only)
- **Translation Speed**: ~1-2 subtitles/second with OPUS-MT
- **Models are cached** between sessions

### Example Timing

For a typical episode with 700 subtitles:
- OPUS-MT: 5-10 minutes
- NLLB-600M: 15-20 minutes

## Troubleshooting

### GUI doesn't open
- Make sure you're in the `src/backend` directory
- Verify virtual environment is activated
- Check Python and tkinter are installed

### Translation errors
- Ensure translation models are downloaded (happens automatically on first use)
- Check internet connection (for initial model download)
- Verify SRT file is properly formatted

### Slow performance
- Use OPUS-MT models for faster translation
- NLLB models are slower but more flexible
- First translation always takes longer (model loading)

### SRT file not found
- Ensure file path doesn't contain special characters
- Try copying SRT file to a simpler path (e.g., `C:\temp\`)

## Output Files

Translated SRT files are saved with naming pattern:
- `original_name_translated_{target_lang}.srt`

Examples:
- German → Spanish: `Episode_18_translated_es.srt`
- German → English: `Episode_18_translated_en.srt`

## Notes

- Translation models are 200MB-600MB and download automatically on first use
- Models are cached in `~/.cache/huggingface/` for reuse
- Timestamps are preserved exactly from source SRT
- Subtitle formatting (bold, italic) is not preserved
- For production use, consider using the backend API instead of the GUI
