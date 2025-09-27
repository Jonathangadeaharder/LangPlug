# Supported Language Pairs

LangPlug currently supports the following translation pairs for subtitle generation and vocabulary translation:

## Available Translation Pairs

| Native Language | Target Language | Helsinki Model | Status |
|----------------|-----------------|----------------|---------|
| Spanish (es)   | German (de)     | opus-mt-de-es | ✅ Active |
| Spanish (es)   | English (en)    | opus-mt-en-es | ✅ Active |
| English (en)   | Chinese (zh)    | opus-mt-zh-en | ✅ Active |
| German (de)    | Spanish (es)    | opus-mt-es-de | ✅ Active |
| German (de)    | French (fr)     | opus-mt-fr-de | ✅ Active |

## How It Works

- **Native Language**: The language you speak fluently (used for translations)
- **Target Language**: The language you want to learn (video content language)

When you watch videos in your target language, LangPlug will:
1. Extract vocabulary you don't know yet
2. Generate subtitles in the target language with unknown words highlighted
3. Provide translations of those segments in your native language

## Required Models

### spaCy Language Models
These must be installed before running LangPlug:

```bash
python -m spacy download en_core_web_sm  # English
python -m spacy download de_core_news_sm # German
python -m spacy download es_core_news_sm # Spanish
python -m spacy download fr_core_news_sm # French
python -m spacy download zh_core_web_sm  # Chinese
```

### Helsinki-NLP Translation Models
These are automatically downloaded on first use:

- `Helsinki-NLP/opus-mt-de-es` (German → Spanish)
- `Helsinki-NLP/opus-mt-es-de` (Spanish → German)
- `Helsinki-NLP/opus-mt-en-es` (English → Spanish)
- `Helsinki-NLP/opus-mt-es-en` (Spanish → English)
- `Helsinki-NLP/opus-mt-zh-en` (Chinese → English)
- `Helsinki-NLP/opus-mt-en-zh` (English → Chinese)
- `Helsinki-NLP/opus-mt-fr-de` (French → German)
- `Helsinki-NLP/opus-mt-de-fr` (German → French)

### Fallback Model
- `facebook/nllb-200-distilled-600M` (auto-downloaded)

### Model Verification
Run the verification script to check installed models:

```bash
cd Backend
python verify_models.py --check-only
```

## Technical Implementation

### Backend Configuration
- Translation pairs are validated in `Backend/core/language_preferences.py`
- Uses Helsinki-NLP OPUS-MT models for primary translation
- Falls back to NLLB models when OPUS-MT is unavailable

### Frontend Validation
- UI prevents selection of unsupported language combinations
- Provides clear error messages for invalid pairs
- Profile screen only shows supported language options

## Adding New Language Pairs

To add support for a new language pair:

1. **Update Backend Constants** (`Backend/core/language_preferences.py`):
   ```python
   SUPPORTED_TRANSLATION_PAIRS.add(("new_native", "new_target"))
   SUPPORTED_LANGUAGES["new_code"] = {"name": "Language Name", "flag": "flag_code"}
   SPACY_MODEL_MAP["new_code"] = "spacy_model_name"
   ```

2. **Update Frontend Constants** (`Frontend/src/screens/ProfileScreen.tsx`):
   ```typescript
   SUPPORTED_TRANSLATION_PAIRS.push(['new_native', 'new_target'])
   LANGUAGE_LIBRARY.push({ code: 'new_code', name: 'Language Name', flag: 'flag_code' })
   ```

3. **Verify Translation Models**:
   - Ensure Helsinki-NLP has an `opus-mt-{source}-{target}` model
   - Test that NLLB supports the language pair as fallback

4. **Test End-to-End**:
   - Create user with new language preferences
   - Process video chunks to verify subtitle generation
   - Confirm translation quality and timing

## Current Limitations

- Only 5 language pairs are currently supported
- Translation quality depends on available training data
- Some specialized vocabulary may not translate accurately
- Chinese support is limited to Simplified Chinese (zh)

## Future Expansion

Planned additions based on model availability:
- Portuguese (pt) ↔ Spanish (es)
- Italian (it) ↔ English (en)
- Dutch (nl) ↔ German (de)
- More Chinese dialects and variants

Last Updated: September 2025