# A1Decider Configuration Migration Guide

## Overview

The A1Decider system has been updated with a centralized configuration system that eliminates the DRY (Don't Repeat Yourself) violations and provides a single source of truth for all application settings.

## What Changed

### Before (Scattered Configuration)
- Word list file paths were hardcoded in multiple files
- Model names were repeated across different modules
- API settings were scattered throughout the codebase
- No central place to manage configuration

### After (Centralized Configuration)
- All configuration is managed through `config.py`
- Single source of truth for file paths, model names, and settings
- Environment variable support for deployment flexibility
- Validation and error checking built-in

## New Configuration System

### Core Components

1. **`config.py`** - Main configuration module
2. **`validate_config.py`** - Configuration validation script
3. **Environment variable support** - For deployment customization

### Configuration Sections

#### Word Lists
```python
from config import get_config

config = get_config()
print(config.word_lists.a1_words)        # Path to a1.txt
print(config.word_lists.giuliwords)      # Path to giuliwords.txt
print(config.word_lists.get_all_files()) # All word list files
```

#### Models
```python
print(config.models.spacy_model)      # spaCy model name
print(config.models.whisper_model)    # Whisper model name
print(config.models.translation_model) # Translation model name
```

#### File Paths
```python
print(config.file_paths.base_dir)     # Base directory
print(config.file_paths.output_dir)   # Output directory
print(config.file_paths.temp_dir)     # Temporary files directory
```

#### API Settings
```python
print(config.api.host)                # API host
print(config.api.port)                # API port
print(config.api.cors_origins)        # CORS origins
```

## Migration Steps

### 1. Validate Current Setup

Run the configuration validation script:

```bash
python validate_config.py
```

This will show you:
- Which word list files are found
- Directory structure status
- Model availability
- API configuration
- Environment variables

### 2. Update Your Code (If Extending)

If you have custom scripts that use A1Decider, update them to use the centralized configuration:

#### Old Way
```python
# DON'T DO THIS ANYMORE
known_words = set()
for word_file in ["a1.txt", "charaktere.txt", "giuliwords.txt"]:
    with open(word_file, 'r') as f:
        known_words.update(line.strip() for line in f)
```

#### New Way
```python
# DO THIS INSTEAD
from config import get_config
from shared_utils.subtitle_utils import load_word_list

config = get_config()
known_words = set()
for word_file in config.word_lists.get_core_files():
    if os.path.exists(word_file):
        known_words.update(load_word_list(word_file))
```

### 3. Environment Variables (Optional)

You can now customize the configuration using environment variables:

```bash
# Override API settings
export API_HOST=localhost
export API_PORT=8080
export API_DEBUG=true

# Override model settings
export WHISPER_MODEL=large
export SPACY_MODEL=de_core_news_lg
export DEVICE=cuda

# Override base path
export A1_DECIDER_PATH=/custom/path/to/a1decider
```

## Configuration Reference

### Word List Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `a1_words` | `{base_dir}/a1.txt` | A1 level German words |
| `charaktere_words` | `{base_dir}/charaktere.txt` | Character names |
| `giuliwords` | `{base_dir}/giuliwords.txt` | User's known words |
| `brands` | `{base_dir}/brands.txt` | Brand names |
| `onomatopoeia` | `{base_dir}/onomatopoeia.txt` | Sound words |
| `interjections` | `{base_dir}/interjections.txt` | Interjection words |

### Model Configuration

| Setting | Default | Environment Variable | Description |
|---------|---------|---------------------|-------------|
| `spacy_model` | `de_core_news_sm` | `SPACY_MODEL` | spaCy German model |
| `whisper_model` | `base` | `WHISPER_MODEL` | Whisper ASR model |
| `translation_model` | `Helsinki-NLP/opus-mt-de-es` | - | Translation model |
| `device` | `auto` | `DEVICE` | Processing device |

### API Configuration

| Setting | Default | Environment Variable | Description |
|---------|---------|---------------------|-------------|
| `host` | `0.0.0.0` | `API_HOST` | API server host |
| `port` | `8000` | `API_PORT` | API server port |
| `debug` | `false` | `API_DEBUG` | Debug mode |
| `cors_origins` | `["*"]` | - | CORS allowed origins |
| `max_file_size` | `100MB` | - | Maximum upload size |

### Processing Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `batch_size` | `20` | Processing batch size |
| `max_subtitle_length` | `200` | Maximum subtitle length |
| `min_word_frequency` | `1` | Minimum word frequency |
| `default_language` | `de` | Default processing language |
| `supported_languages` | `["de", "en", "es", "fr", "it"]` | Supported languages |
| `subtitle_formats` | `[".srt", ".vtt"]` | Supported subtitle formats |

## Troubleshooting

### Common Issues

1. **Word list files not found**
   - Run `python validate_config.py` to check file locations
   - Ensure all required `.txt` files are in the base directory
   - Use `A1_DECIDER_PATH` environment variable if files are elsewhere

2. **Model loading errors**
   - Check that spaCy German model is installed: `python -m spacy download de_core_news_sm`
   - Verify Whisper is installed: `pip install openai-whisper`
   - Check GPU availability if using CUDA

3. **API connection issues**
   - Verify API configuration with `python validate_config.py`
   - Check firewall settings for the configured port
   - Ensure no other services are using the same port

### Validation Commands

```bash
# Full configuration validation
python validate_config.py

# Test configuration loading
python -c "from config import get_config; print('Config loaded successfully')"

# Check specific components
python -c "from config import get_config; config = get_config(); print(config.validate_config())"
```

## Benefits of Centralized Configuration

1. **DRY Principle**: No more repeated file paths or settings
2. **Single Source of Truth**: All configuration in one place
3. **Environment Support**: Easy deployment customization
4. **Validation**: Built-in configuration validation
5. **Maintainability**: Easier to update and manage settings
6. **Consistency**: Prevents configuration drift between components

## Next Steps

1. Run `python validate_config.py` to ensure your setup is correct
2. Test the system with your existing workflows
3. Customize environment variables as needed for your deployment
4. Update any custom scripts to use the new configuration system

## Support

If you encounter issues with the new configuration system:

1. Run the validation script first
2. Check the environment variables
3. Verify all required files are present
4. Review the configuration reference above

The centralized configuration system makes A1Decider more robust, maintainable, and easier to deploy across different environments.