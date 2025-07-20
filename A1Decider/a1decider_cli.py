#!/usr/bin/env python3
"""
Command-line interface for A1Decider subtitle processing.
This script provides a non-interactive interface that can be called from Node.js.
"""

import os
import sys
import json
import argparse
import re
from collections import Counter
from typing import List, Dict, Tuple, Any
import pysrt
import webvtt
from tqdm import tqdm

# Import centralized configuration
from config import get_config, get_core_word_list_files

# Import the existing functions from a1decider.py
try:
    from a1decider import (
        analyze_vocabulary_batch_offline,
        load_word_list,
        load_global_unknowns,
        save_global_unknowns,
        load_subtitles
    )
except ImportError:
    print("Error: Could not import functions from a1decider.py", file=sys.stderr)
    sys.exit(1)

def process_subtitles_cli(subtitle_path: str, known_words: set) -> Tuple[Any, Counter, int, int, int, Dict[str, List[int]], str]:
    """Process subtitles and return analysis data."""
    if not os.path.exists(subtitle_path):
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

    try:
        subs, subtitle_format = load_subtitles(subtitle_path)
        total_subtitles = len(subs)
        word_counter = Counter()
        skipped_subtitles = 0
        skipped_hard = 0
        
        # Dictionary to track which word is the only unknown in which subtitles
        word_to_subtitles = {}

        for i, sub in enumerate(tqdm(subs, desc="Processing subtitles")):
            # Extract text (different properties based on format)
            if subtitle_format == 'srt':
                text = sub.text.lower()
            else:  # vtt
                text = sub.text.lower()
            
            # Simple tokenization
            tokens = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text)
            unknown_words = [word for word in tokens if word not in known_words]

            if not unknown_words:
                skipped_subtitles += 1
            elif len(set(unknown_words)) == 1:
                word = unknown_words[0]
                word_counter[word] += 1
                skipped_hard += 1
                
                # Track which subtitles have this word as the only unknown
                if word not in word_to_subtitles:
                    word_to_subtitles[word] = []
                word_to_subtitles[word].append(i)
            else:
                pass  # Subtitles with multiple unknown words

        return subs, word_counter, total_subtitles, skipped_subtitles, skipped_hard, word_to_subtitles, subtitle_format
    except Exception as e:
        raise RuntimeError(f"Error processing subtitles: {e}")

def analyze_vocabulary_cli(unknown_words: List[str], gemini_client) -> Dict[str, Dict[str, Any]]:
    """Analyze vocabulary using only local models and heuristics."""
    vocabulary_analysis = {}
    if not unknown_words:
        return vocabulary_analysis
    batch_size = 20
    for i in range(0, len(unknown_words), batch_size):
        batch = unknown_words[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(unknown_words) + batch_size - 1)//batch_size}...", file=sys.stderr)
        batch_results = analyze_vocabulary_batch_offline(batch)
        for lemma, lemma_translation, is_relevant in batch_results:
            vocabulary_analysis[lemma] = {
                'lemma_translation': lemma_translation,
                'is_relevant': is_relevant
            }
    return vocabulary_analysis

def generate_filtered_subtitles_cli(subs, known_words: set, output_path: str, subtitle_format: str) -> None:
    """Generate filtered subtitles with only known words."""
    try:
        if subtitle_format == 'srt':
            # Create new SRT file
            filtered_subs = pysrt.SubRipFile()
            
            for sub in subs:
                text = sub.text.lower()
                tokens = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text)
                unknown_words = [word for word in tokens if word not in known_words]
                
                if not unknown_words:
                    # Keep subtitle if all words are known
                    filtered_subs.append(sub)
            
            filtered_subs.save(output_path, encoding='utf-8')
        
        elif subtitle_format == 'vtt':
            # Create new VTT file
            filtered_subs = webvtt.WebVTT()
            
            for sub in subs:
                text = sub.text.lower()
                tokens = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text)
                unknown_words = [word for word in tokens if word not in known_words]
                
                if not unknown_words:
                    # Keep subtitle if all words are known
                    filtered_subs.captions.append(sub)
            
            filtered_subs.save(output_path)
        
        print(f"Filtered subtitles saved to: {output_path}", file=sys.stderr)
    
    except Exception as e:
        raise RuntimeError(f"Error generating filtered subtitles: {e}")

def main():
    parser = argparse.ArgumentParser(description='A1Decider CLI - Process subtitles for German vocabulary learning')
    parser.add_argument('subtitle_file', help='Path to subtitle file (.srt or .vtt)')
    parser.add_argument('--output', '-o', help='Output file for filtered subtitles')
    parser.add_argument('--vocabulary-only', action='store_true', help='Only analyze vocabulary, don\'t generate filtered subtitles')
    parser.add_argument('--known-words-dir', default='.', help='Directory containing known word files (a1.txt, charaktere.txt, giuliwords.txt)')
    parser.add_argument('--batch-size', type=int, default=20, help='Batch size for vocabulary analysis')
    
    args = parser.parse_args()
    
    try:
        # Load known words using centralized configuration
        print("Loading known word lists...", file=sys.stderr)
        config = get_config()
        known_words = set()
        
        # Use configured word list files, with fallback to command line directory
        word_files = config.word_lists.get_core_files()
        if args.known_words_dir != '.':
            # Override with command line directory if specified
            word_files = [
                os.path.join(args.known_words_dir, 'a1.txt'),
                os.path.join(args.known_words_dir, 'charaktere.txt'),
                os.path.join(args.known_words_dir, 'giuliwords.txt')
            ]
        
        for file_path in word_files:
            if os.path.exists(file_path):
                words = load_word_list(file_path)
                known_words.update(words)
                file_name = os.path.basename(file_path)
                print(f"Loaded {len(words)} words from {file_name}", file=sys.stderr)
            else:
                file_name = os.path.basename(file_path)
                print(f"Warning: {file_name} not found at {file_path}", file=sys.stderr)
        print(f"Total known words: {len(known_words)}", file=sys.stderr)
        # Process subtitles
        print("Processing subtitles...", file=sys.stderr)
        subs, word_counts, total_subtitles, skipped_subtitles, skipped_hard, word_to_subtitles, subtitle_format = process_subtitles_cli(
            args.subtitle_file, known_words
        )
        print(f"Total subtitles: {total_subtitles}", file=sys.stderr)
        print(f"Subtitles with all known words: {skipped_subtitles}", file=sys.stderr)
        print(f"Subtitles with one unknown word: {skipped_hard}", file=sys.stderr)
        print(f"Unique unknown words: {len(word_counts)}", file=sys.stderr)
        # Analyze vocabulary offline
        unknown_words_list = [word for word, count in word_counts.most_common()]
        if unknown_words_list:
            print("Analyzing vocabulary offline...", file=sys.stderr)
            vocabulary_analysis = analyze_vocabulary_cli(unknown_words_list, None)
            # Filter to only relevant vocabulary
            relevant_words = [(word, count) for word, count in word_counts.most_common() 
                             if vocabulary_analysis.get(word, {}).get('is_relevant', True)]
            print(f"Relevant vocabulary words: {len(relevant_words)} of {len(word_counts)}", file=sys.stderr)
        else:
            vocabulary_analysis = {}
            relevant_words = []
        # Prepare output data
        output_data = {
            'subtitle_file': args.subtitle_file,
            'total_subtitles': total_subtitles,
            'skipped_subtitles': skipped_subtitles,
            'skipped_hard': skipped_hard,
            'total_unknown_words': len(word_counts),
            'relevant_vocabulary_count': len(relevant_words),
            'vocabulary': [
                {
                    'word': word,
                    'frequency': count,
                    'translation': vocabulary_analysis.get(word, {}).get('lemma_translation', '[Translation not available]'),
                    'is_relevant': vocabulary_analysis.get(word, {}).get('is_relevant', True),
                    'affected_subtitles': len(word_to_subtitles.get(word, []))
                }
                for word, count in relevant_words
            ]
        }
        # Generate filtered subtitles if requested
        if not args.vocabulary_only:
            if args.output:
                output_path = args.output
            else:
                # Generate default output filename
                base_name = os.path.splitext(args.subtitle_file)[0]
                extension = os.path.splitext(args.subtitle_file)[1]
                output_path = f"{base_name}_a1filtered{extension}"
            print(f"Generating filtered subtitles...", file=sys.stderr)
            generate_filtered_subtitles_cli(subs, known_words, output_path, subtitle_format)
            output_data['filtered_subtitle_file'] = output_path
        # Output JSON result to stdout
        print(json.dumps(output_data, ensure_ascii=False, indent=2))
    except Exception as e:
        error_data = {
            'error': str(e),
            'type': type(e).__name__
        }
        print(json.dumps(error_data, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()