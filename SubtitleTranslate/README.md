# Subtitle Translation with Batch Speed Testing

This project provides subtitle translation capabilities with comprehensive batch processing speed testing for the Helsinki-NLP MarianMT models.

## Features

- **Subtitle Translation**: Translate SRT and VTT subtitle files between languages
- **Batch Speed Testing**: Comprehensive performance testing with different batch sizes
- **Performance Optimization**: Find optimal batch sizes for your hardware
- **Rich Visualization**: Performance charts and detailed reports

## Files

- `subtitle_translate.py` - Main subtitle translation script with GUI
- `batch_speed_test.py` - Comprehensive batch speed testing framework
- `run_batch_test.py` - Quick runner script for batch testing
- `requirements.txt` - Python dependencies

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have CUDA support for GPU acceleration (recommended):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Usage

### Basic Subtitle Translation

Run the main translation script:
```bash
python subtitle_translate.py
```

This will open a GUI to:
- Select subtitle files (SRT/VTT)
- Choose source and target languages
- Translate with default settings

### Batch Speed Testing

#### Quick Test
For a quick performance assessment:
```bash
python run_batch_test.py
```
Choose option 1 for quick test (batch sizes 1-16, 2 runs each)

#### Comprehensive Test
For detailed performance analysis:
```bash
python run_batch_test.py
```
Choose option 2 for comprehensive test (batch sizes 1-128, 3 runs each)

#### Custom Testing
For custom batch testing:
```bash
python batch_speed_test.py
```

## Batch Speed Testing Features

### What it Tests
- **Multiple Batch Sizes**: Tests batch sizes from 1 to 128 (configurable)
- **Multiple Runs**: Averages results across multiple runs for accuracy
- **GPU Memory Management**: Clears GPU cache between tests
- **Comprehensive Metrics**: Time, throughput, speedup calculations

### Output
- **Console Table**: Real-time results display
- **Performance Plots**: Visual charts showing time vs batch size and throughput
- **Detailed Reports**: Text files with complete results
- **Optimal Batch Size**: Recommendation based on throughput

### Sample Output
```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Batch Size ┃ Avg Time (s) ┃ Std Dev (s) ┃ Texts/Second  ┃ Speedup vs Batch=1 ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ 1          │ 45.23        │ 1.12        │ 2.21          │ 1.00x             │
│ 2          │ 24.56        │ 0.89        │ 4.07          │ 1.84x             │
│ 4          │ 14.78        │ 0.65        │ 6.77          │ 3.06x             │
│ 8          │ 9.34         │ 0.43        │ 10.71         │ 4.84x             │
│ 16         │ 7.12         │ 0.31        │ 14.04         │ 6.35x             │
└────────────┴──────────────┴─────────────┴───────────────┴───────────────────┘

Optimal batch size: 16
Best throughput: 14.04 texts/second
```

## Configuration

### Language Pairs
The script is configured for German to Spanish translation (`de` → `es`). To change languages, modify:
- `src_lang = 'de'` (source language)
- `tgt_lang = 'es'` (target language)

### Test Parameters
In `batch_speed_test.py`, you can modify:
- `batch_sizes`: List of batch sizes to test
- `num_runs`: Number of runs per batch size for averaging
- Test text limit (currently 100 subtitles for speed)

### Hardware Requirements
- **GPU Recommended**: CUDA-compatible GPU for best performance
- **RAM**: At least 8GB system RAM
- **VRAM**: 4GB+ GPU memory for larger batch sizes

## Performance Tips

1. **Use GPU**: Ensure CUDA is available for significant speedup
2. **Optimal Batch Size**: Use the testing to find your hardware's sweet spot
3. **Memory Management**: Larger batches need more VRAM
4. **Text Length**: Longer subtitles may require smaller batch sizes

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**:
   - Reduce batch size
   - Use CPU instead of GPU
   - Close other GPU-intensive applications

2. **Model Download Issues**:
   - Check internet connection
   - Verify language code format (e.g., 'de', 'es')
   - Ensure sufficient disk space

3. **Slow Performance**:
   - Verify GPU is being used
   - Check if model is loaded on correct device
   - Consider using smaller models for faster inference

### Error Messages

- `Model not found`: Check if the language pair is supported by Helsinki-NLP
- `File not found`: Verify subtitle file path is correct
- `Encoding error`: Try different encoding (utf-8, latin-1)

## Example Test Results

Typical performance improvements with batching:
- **Batch Size 1**: Baseline (1.00x)
- **Batch Size 8**: 4-5x speedup
- **Batch Size 16**: 6-7x speedup
- **Batch Size 32+**: Diminishing returns, potential memory issues

## Contributing

Feel free to:
- Add support for more subtitle formats
- Implement additional language pairs
- Optimize batch processing algorithms
- Add more visualization options

## License

This project is open source. Please check individual model licenses for the Helsinki-NLP models used.