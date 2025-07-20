#!/usr/bin/env python3
"""
Command-line interface for A1Decider subtitle processing using ProcessingPipeline.
This script provides a non-interactive interface that can be called from Node.js.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

# Import centralized configuration
from config import get_config
from shared_utils.subtitle_utils import load_word_list
from shared_utils.model_utils import ModelManager

# Import processing pipeline
from processing_steps import ProcessingContext, ProcessingPipeline
from concrete_processing_steps import CLIAnalysisStep, A1FilterStep

def create_cli_pipeline() -> ProcessingPipeline:
    """Create a processing pipeline for CLI analysis."""
    steps = [
        CLIAnalysisStep(),
        A1FilterStep()
    ]
    return ProcessingPipeline(steps)

def analyze_vocabulary_offline(unknown_words: list) -> Dict[str, Dict[str, Any]]:
    """Analyze vocabulary using offline heuristics."""
    vocabulary_analysis = {}
    
    for word in unknown_words:
        # Simple heuristic analysis
        vocabulary_analysis[word] = {
            'lemma_translation': '[Translation not available]',
            'is_relevant': True  # Assume all words are relevant for CLI
        }
    
    return vocabulary_analysis

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
        
        # Initialize model manager
        model_manager = ModelManager()
        
        # Create processing context
        context = ProcessingContext(
            video_file="",  # Not needed for subtitle-only processing
            model_manager=model_manager,
            language="de",
            src_lang="de",
            tgt_lang="es",
            no_preview=True,
            known_words=known_words,
            word_list_files={
                'a1_words': config.word_lists.a1_words,
                'charaktere_words': config.word_lists.charaktere_words,
                'giuliwords': config.word_lists.giuliwords,
                'brands': config.word_lists.brands,
                'onomatopoeia': config.word_lists.onomatopoeia,
                'interjections': config.word_lists.interjections
            },
            processing_config={
                'batch_size': config.processing.batch_size,
                'default_language': config.processing.default_language,
                'supported_languages': config.processing.supported_languages,
                'subtitle_formats': config.processing.subtitle_formats
            }
        )
        
        # Set the subtitle file as the full SRT for processing
        context.full_srt = args.subtitle_file
        
        # Create and execute pipeline
        pipeline = create_cli_pipeline()
        success = pipeline.execute(context)
        
        if not success:
            raise RuntimeError("Pipeline execution failed")
        
        # Extract analysis results from context
        metadata = context.metadata
        word_counts = metadata['word_counts']
        word_to_subtitles = metadata['word_to_subtitles']
        unknown_words_list = metadata['unknown_words_list']
        
        print(f"Total subtitles: {metadata['total_subtitles']}", file=sys.stderr)
        print(f"Subtitles with all known words: {metadata['skipped_subtitles']}", file=sys.stderr)
        print(f"Subtitles with one unknown word: {metadata['skipped_hard']}", file=sys.stderr)
        print(f"Unique unknown words: {len(word_counts)}", file=sys.stderr)
        
        # Analyze vocabulary offline
        if unknown_words_list:
            print("Analyzing vocabulary offline...", file=sys.stderr)
            vocabulary_analysis = analyze_vocabulary_offline(unknown_words_list)
            
            # Filter to only relevant vocabulary
            relevant_words = [(word, count) for word, count in 
                             sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
                             if vocabulary_analysis.get(word, {}).get('is_relevant', True)]
            print(f"Relevant vocabulary words: {len(relevant_words)} of {len(word_counts)}", file=sys.stderr)
        else:
            vocabulary_analysis = {}
            relevant_words = []
        
        # Prepare output data
        output_data = {
            'subtitle_file': args.subtitle_file,
            'total_subtitles': metadata['total_subtitles'],
            'skipped_subtitles': metadata['skipped_subtitles'],
            'skipped_hard': metadata['skipped_hard'],
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
            
            # The filtered subtitles should already be generated by A1FilterStep
            if context.filtered_srt and os.path.exists(context.filtered_srt):
                # Copy to desired output location if different
                if context.filtered_srt != output_path:
                    import shutil
                    shutil.copy2(context.filtered_srt, output_path)
                output_data['filtered_subtitle_file'] = output_path
                print(f"Filtered subtitles saved to: {output_path}", file=sys.stderr)
            else:
                print("Warning: Filtered subtitles were not generated", file=sys.stderr)
        
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