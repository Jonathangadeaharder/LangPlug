# Unified Subtitle Processor

This script combines three separate subtitle processing tools into one unified workflow:

1. **Subtitle Creation** - Creates German subtitles from video files using OpenAI Whisper
2. **A1 Level Filtering** - Filters subtitles to show only lines containing unknown words (based on A1 German vocabulary)
3. **Translation** - Translates the filtered subtitles from German to Spanish

## Features

- **Automatic Processing**: Select a video file and the script handles all three steps automatically
- **Default Settings**: Uses optimized default settings from the original scripts
- **No Game Mode**: Filters subtitles without the interactive vocabulary game
- **GPU Acceleration**: Uses CUDA when available for faster processing
- **Multiple Formats**: Supports SRT and VTT subtitle formats

## Requirements

### System Requirements
- Python 3.8+
- CUDA-compatible GPU (recommended for faster processing)
- FFmpeg installed and accessible in PATH

### Python Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

### Additional Setup

1. **SpaCy German Model**:
   ```bash
   python -m spacy download de_core_news_lg
   ```

2. **Word Lists** (for A1 filtering):
   The script expects these files in `G:/My Drive/`:
   - `a1.txt` - A1 level German vocabulary
   - `charaktere.txt` - Character names and proper nouns
   - `giuliwords.txt` - Additional known words
   
   If these files don't exist, the script will continue but filtering may be less effective.

## Usage

1. Run the script:
   ```bash
   python unified_subtitle_processor.py
   ```

2. Select a video file when prompted

3. The script will automatically:
   - Extract audio from the video
   - Generate German subtitles using Whisper
   - Filter subtitles to show only unknown words
   - Translate filtered subtitles to Spanish

## Output Files

For a video file named `example.mp4`, the script creates:
- `example.srt` - Original German subtitles
- `example_a1filtered.srt` - Filtered subtitles (unknown words only)
- `example_a1filtered_es.srt` - Spanish translation of filtered subtitles

## Configuration

### Default Settings
- **Language**: German (de) for subtitle creation
- **Translation**: German to Spanish (de → es)
- **Whisper Model**: turbo (good balance of speed and accuracy)
- **Device**: CUDA if available, otherwise CPU

### Customization
To modify default settings, edit the following in the script:
- Change `language="de"` in the `create_subtitles()` call
- Modify `src_lang="de"` and `tgt_lang="es"` in the `translate_subtitle_file()` call
- Update word list file paths in the `filter_subtitles()` function

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**:
   - The script will automatically fall back to CPU if CUDA fails
   - Consider using a smaller Whisper model (change "turbo" to "base" or "small")

2. **Missing Word Lists**:
   - The script will show warnings but continue processing
   - Filtering will be less effective without proper word lists

3. **FFmpeg Not Found**:
   - Install FFmpeg and ensure it's in your system PATH
   - On Windows, you can download from https://ffmpeg.org/

4. **SpaCy Model Missing**:
   - Run: `python -m spacy download de_core_news_lg`

### Performance Tips

- Use CUDA-compatible GPU for faster processing
- For very long videos, consider splitting them first
- Close other GPU-intensive applications during processing

## Original Scripts

This unified script is based on three separate tools:
- `SubtitleMaker/subtitle_maker.py` - Video to subtitle conversion
- `A1Decider/a1decider.py` - Vocabulary-based subtitle filtering
- `SubtitleTranslate/subtitle_translate.py` - Subtitle translation

The unified version uses the same core functionality but removes interactive elements for automated processing.