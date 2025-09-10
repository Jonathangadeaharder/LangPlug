# NLLB-200 Translation Service

## Overview

The NLLB-200 (No Language Left Behind) translation service provides state-of-the-art multilingual machine translation supporting 200+ languages. It's based on Facebook/Meta's research focusing on low-resource languages and providing quality translation for underserved communities.

## Key Advantages over MADLAD

- **Smaller Model Size**: ~600MB vs 11.8GB for MADLAD-400 3B
- **Faster Download**: Minutes vs hours
- **Lower Memory Usage**: Runs comfortably on 4GB GPU
- **Better Documentation**: Extensive language codes and evaluation metrics
- **Production Ready**: Used by Meta for production translation

## Features

- **200+ Languages**: Comprehensive coverage including low-resource languages
- **Distilled Model**: 600M parameters optimized for efficiency
- **High Quality**: Evaluated on FLORES-200 benchmark
- **Batch Processing**: Efficient batch translation support
- **GPU Acceleration**: Automatic CUDA support for faster processing

## Installation

```bash
# Install required dependencies (if not already installed)
pip install transformers torch sentencepiece protobuf

# Or install all requirements
pip install -r requirements.txt
```

## Usage

### Basic Translation

```python
from processing.services import TranslationServiceFactory

# Create NLLB service
nllb = TranslationServiceFactory.create_service(
    'nllb',
    model_name='facebook/nllb-200-distilled-600M',
    device=None,  # Auto-detect GPU/CPU
    batch_size=8
)

# Translate text
result = nllb.translate(
    "Hello, world!",
    source_lang='en',
    target_lang='es'
)

print(result.segments[0].translated_text)  # "¡Hola, mundo!"
```

### Batch Translation

```python
from processing.services.base import ProcessingResult, Segment

# Create segments for batch translation
texts = ["Hello", "How are you?", "Good bye"]
segments = [Segment(i, i+1, text) for i, text in enumerate(texts)]
input_result = ProcessingResult(segments=segments, language='en', duration=len(segments))

# Batch translate
result = nllb.translate(
    input_result,
    source_lang='en',
    target_lang='fr'
)

for seg in result.segments:
    print(f"{seg.original_text} → {seg.translated_text}")
```

### Subtitle Translation

```python
# Translate subtitle file
output_file = nllb.translate_subtitle_file(
    'input.srt',
    source_lang='en',
    target_lang='de'
)
```

## Supported Languages

NLLB-200 supports 200+ languages with specific script codes. Common examples:

| Language | Simple Code | NLLB Code | Script |
|----------|------------|-----------|--------|
| English | en | eng_Latn | Latin |
| Spanish | es | spa_Latn | Latin |
| French | fr | fra_Latn | Latin |
| German | de | deu_Latn | Latin |
| Italian | it | ita_Latn | Latin |
| Portuguese | pt | por_Latn | Latin |
| Russian | ru | rus_Cyrl | Cyrillic |
| Chinese (Simplified) | zh | zho_Hans | Simplified Chinese |
| Chinese (Traditional) | zh-tw | zho_Hant | Traditional Chinese |
| Japanese | ja | jpn_Jpan | Japanese |
| Korean | ko | kor_Hang | Hangul |
| Arabic | ar | arb_Arab | Arabic |
| Hindi | hi | hin_Deva | Devanagari |
| Thai | th | tha_Thai | Thai |
| Vietnamese | vi | vie_Latn | Latin |
| Indonesian | id | ind_Latn | Latin |
| Swahili | sw | swh_Latn | Latin |
| Hebrew | he | heb_Hebr | Hebrew |
| Turkish | tr | tur_Latn | Latin |

Full language list: [FLORES-200 Languages](https://github.com/facebookresearch/flores/blob/main/flores200/README.md#languages-in-flores-200)

## Model Information

### NLLB-200-distilled-600M (Recommended)
- **Parameters**: 600M
- **Download Size**: ~1.2GB (model files)
- **Memory Usage**: ~2-3GB GPU RAM (float16)
- **Speed**: Fast inference
- **Quality**: Excellent for most use cases

### Other Variants
- **nllb-200-distilled-1.3B**: Higher quality, 1.3B parameters
- **nllb-200-3.3B**: Best quality, 3.3B parameters

## Configuration Options

```python
nllb = TranslationServiceFactory.create_service(
    'nllb',
    model_name='facebook/nllb-200-distilled-600M',  # Model variant
    device='cuda',                                  # Device: 'cuda', 'cpu', or None (auto)
    max_length=512,                                 # Maximum sequence length
    batch_size=8,                                   # Batch size for processing
    cache_dir='/path/cache'                         # Directory for model caching
)
```

## Performance Tips

1. **Use GPU**: Enable CUDA for 5-10x faster translation
2. **Batch Processing**: Process multiple texts together for better throughput
3. **Model Caching**: Models are cached after first download
4. **Optimal Batch Size**: 8-16 for GPU, 2-4 for CPU

## Integration with Service Facade

```python
from processing.services import ServiceFacade

facade = ServiceFacade()

# Translate using facade
result = facade.translate(
    "Hello, world!",
    source_lang='en',
    target_lang='es',
    service='nllb'
)
```

## Error Handling

```python
try:
    result = nllb.translate(text, source_lang='en', target_lang='es')
except ProcessingError as e:
    print(f"Translation failed: {e}")
```

## Advantages

- **Efficient**: 600M model is 20x smaller than MADLAD-400 "3B" (actually 11.8GB)
- **Fast Download**: ~1.2GB vs 11.8GB
- **Production Ready**: Used by Meta in production
- **Well Documented**: Clear language codes and extensive documentation
- **Low Resource Focus**: Special attention to underserved languages

## Limitations

- Maximum sequence length is 512 tokens
- Some language pairs may have lower quality than others
- Best for sentence-level translation (not full documents)

## References

- [NLLB Paper](https://arxiv.org/abs/2207.04672)
- [HuggingFace Model Card](https://huggingface.co/facebook/nllb-200-distilled-600M)
- [FLORES-200 Dataset](https://github.com/facebookresearch/flores)
- [Meta AI Blog](https://ai.meta.com/research/no-language-left-behind/)