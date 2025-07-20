import os
import traceback
import json
from collections import Counter
from moviepy import VideoFileClip
from pydub import AudioSegment
from tqdm import tqdm
import pysrt
import tkinter as tk
from tkinter import filedialog
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.align import Align
from rich.panel import Panel
from pynput import keyboard

from processing_steps import ProcessingStep, ProcessingContext
from processing_interfaces import (
    ITranscriptionContext,
    IFilteringContext,
    ITranslationContext,
    IPreviewProcessingContext,
    IConfigurationContext,
    TranscriptionStep as BaseTranscriptionStep,
    FilteringStep as BaseFilteringStep,
    TranslationStep as BaseTranslationStep,
    PreviewProcessingStep as BasePreviewProcessingStep
)
from shared_utils.subtitle_utils import (
    load_subtitles,
    save_subtitles,
    dict_to_srt,
    load_word_list,
)
from config import get_config, get_global_unknowns_file

class PreviewTranscriptionStep(BaseTranscriptionStep):
    """Step to create 10-minute preview subtitles for long videos."""
    
    def __init__(self):
        super().__init__("Preview Transcription")
    
    def execute(self, context: ITranscriptionContext) -> bool:
        if context.no_preview:
            self.log_skip("Preview disabled by user")
            return True
        
        self.log_start()
        
        try:
            # Check video duration first
            with VideoFileClip(context.video_file) as video:
                if video.duration <= 600:
                    self.log_skip("Video is 10 minutes or shorter")
                    return True
                
                if video.audio is None:
                    self.log_error("Video file has no audio track")
                    return False
            
            context.preview_srt = self._create_preview_subtitles(context)
            
            if context.preview_srt:
                self.log_success(f"Preview saved: {os.path.basename(context.preview_srt)}")
                return True
            else:
                self.log_error("Failed to create preview subtitles")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False
    
    def _create_preview_subtitles(self, context: ProcessingContext) -> str:
        """Create 10-minute preview subtitles."""
        script_dir = os.path.dirname(os.path.abspath(context.video_file))
        base_filename = os.path.splitext(os.path.basename(context.video_file))[0]
        
        audio_10min_file = os.path.join(script_dir, f"_temp_10min_{base_filename}.wav")
        srt_10min_filename = os.path.join(script_dir, base_filename + "_10min.srt")
        
        try:
            with context.model_manager.get_whisper_model_safe() as model:
                with VideoFileClip(context.video_file) as video:
                    audio_10min = video.audio.subclipped(0, 600)
                    audio_10min.write_audiofile(audio_10min_file, codec='pcm_s16le')
                    
                    transcription_10min = model.transcribe(
                        audio_10min_file, 
                        language=context.language, 
                        verbose=False, 
                        condition_on_previous_text=False
                    )
                    sentences_10min = transcription_10min['segments']
                    
                    context.model_manager.cleanup_cuda_memory()
                    
                    srt_output_10min = dict_to_srt(sentences_10min)
                    with open(srt_10min_filename, "w", encoding="utf-8") as file:
                        file.write(srt_output_10min)
                    
                    return srt_10min_filename
                
        finally:
            if os.path.exists(audio_10min_file):
                try:
                    os.remove(audio_10min_file)
                except OSError:
                    pass

class FullTranscriptionStep(BaseTranscriptionStep):
    """Step to create full subtitles from video file using Whisper."""
    
    def __init__(self):
        super().__init__("Full Transcription")
    
    def execute(self, context: ITranscriptionContext) -> bool:
        self.log_start()
        
        try:
            context.full_srt = self._create_full_subtitles(context)
            
            if context.full_srt:
                self.log_success(f"Full subtitles saved: {os.path.basename(context.full_srt)}")
                return True
            else:
                self.log_error("Failed to create full subtitles")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False
    
    def _create_full_subtitles(self, context: ProcessingContext) -> str:
        """Create full subtitles from video file."""
        script_dir = os.path.dirname(os.path.abspath(context.video_file))
        base_filename = os.path.splitext(os.path.basename(context.video_file))[0]
        
        temp_audio_file = os.path.join(script_dir, f"_temp_dup_{base_filename}.wav")
        audio_file = os.path.join(script_dir, f"_temp_extracted_{base_filename}.wav")
        srt_filename = os.path.join(script_dir, base_filename + ".srt")
        
        try:
            with context.model_manager.get_whisper_model_safe() as model:
                with VideoFileClip(context.video_file) as video:
                    if video.audio is None:
                        raise Exception("Video file has no audio track")
                    
                    audio_duration = video.duration
                    audio = video.audio
                    audio.write_audiofile(audio_file, codec='pcm_s16le')
                
                audio_file_to_transcribe = audio_file
                if audio_duration < 30:
                    # Duplicate short audio to improve transcription quality
                    audio_segment = AudioSegment.from_file(audio_file)
                    middle_chunk = audio_segment[5000:15000]
                    duplicated_audio = middle_chunk + audio_segment
                    duplicated_audio.export(temp_audio_file, format="wav")
                    audio_file_to_transcribe = temp_audio_file
                
                transcription = model.transcribe(
                    audio_file_to_transcribe, 
                    language=context.language, 
                    verbose=False, 
                    condition_on_previous_text=False
                )
                sentences = transcription['segments']
                
                context.model_manager.cleanup_cuda_memory()
                
                srt_output = dict_to_srt(sentences)
                with open(srt_filename, "w", encoding="utf-8") as file:
                    file.write(srt_output)
                
                return srt_filename
            
        finally:
            for temp_file in [temp_audio_file, audio_file]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass

class A1FilterStep(BaseFilteringStep):
    """Step to filter subtitles to show only unknown words."""
    
    def __init__(self):
        super().__init__("A1 Filtering")
    
    def execute(self, context: IFilteringContext) -> bool:
        # Determine which subtitle file to filter
        subtitle_file = context.full_srt
        if not subtitle_file:
            self.log_error("No subtitle file available for filtering")
            return False
        
        self.log_start()
        
        try:
            context.filtered_srt = self._filter_subtitles(context, subtitle_file)
            
            if context.filtered_srt:
                self.log_success(f"Filtered subtitles saved: {os.path.basename(context.filtered_srt)}")
                return True
            else:
                self.log_error("Failed to filter subtitles")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False
    
    def _filter_subtitles(self, context: ProcessingContext, subtitle_file: str) -> str:
        """Filter subtitles to show only unknown words."""
        with context.model_manager.get_spacy_model_safe() as nlp:
            if not nlp:
                raise Exception("SpaCy model not available")
            
            # Use known words from context (loaded by the main application)
            if context.known_words is None:
                raise Exception("Known words not provided in processing context. "
                              "The main application should load word lists and populate the context.")
            
            known_words = context.known_words
            
            subs = load_subtitles(subtitle_file)
            if not subs:
                raise Exception("Failed to load subtitles")
            
            filtered_subs = pysrt.SubRipFile()
            for sub in tqdm(subs, desc="Filtering Subtitles"):
                text = sub.text.lower()
                doc = nlp(text)
                tokens = [token.text for token in doc if token.is_alpha]
                unknown_words = [word for word in tokens if word not in known_words]
                
                if unknown_words:
                    filtered_subs.append(sub)
            
            output_path = os.path.splitext(subtitle_file)[0] + '_a1filtered.srt'
            save_subtitles(filtered_subs, output_path)
            return output_path

class TranslationStep(BaseTranslationStep):
    """Step to translate subtitle file."""
    
    def __init__(self):
        super().__init__("Translation")
    
    def execute(self, context: ITranslationContext) -> bool:
        # Determine which subtitle file to translate
        subtitle_file = context.filtered_srt or context.full_srt
        if not subtitle_file:
            self.log_error("No subtitle file available for translation")
            return False
        
        self.log_start()
        
        try:
            context.translated_srt = self._translate_subtitles(context, subtitle_file)
            
            if context.translated_srt:
                self.log_success(f"Translated subtitles saved: {os.path.basename(context.translated_srt)}")
                return True
            else:
                self.log_error("Failed to translate subtitles")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False
    
    def _translate_subtitles(self, context: ProcessingContext, subtitle_file: str) -> str:
        """Translate subtitle file."""
        with context.model_manager.get_translation_model_safe(context.src_lang, context.tgt_lang) as (model, tokenizer):
            if not model or not tokenizer:
                raise Exception("Translation model not available")
            
            subs = load_subtitles(subtitle_file)
            if not subs:
                raise Exception("Failed to load subtitles")
            
            translated_subs = pysrt.SubRipFile()
            
            for sub in tqdm(subs, desc="Translating"):
                inputs = tokenizer([sub.text], return_tensors='pt', padding=True, truncation=True).to(
                    context.model_manager.device
                )
                translated = model.generate(**inputs)
                translation = tokenizer.decode(translated[0], skip_special_tokens=True)
                sub.text = translation
                translated_subs.append(sub)
            
            context.model_manager.cleanup_cuda_memory()
            
            output_path = os.path.splitext(subtitle_file)[0] + f'_{context.tgt_lang}.srt'
            save_subtitles(translated_subs, output_path)
            return output_path

class PreviewProcessingStep(BasePreviewProcessingStep):
    """Step to process preview subtitles (filter and translate)."""
    
    def __init__(self):
        super().__init__("Preview Processing")
    
    def execute(self, context: IPreviewProcessingContext) -> bool:
        if not context.preview_srt:
            self.log_skip("No preview subtitles available")
            return True
        
        self.log_start()
        
        try:
            # Create a temporary context for preview processing
            preview_context = ProcessingContext(
                video_file=context.video_file,
                model_manager=context.model_manager,
                language=context.language,
                src_lang=context.src_lang,
                tgt_lang=context.tgt_lang,
                known_words=context.known_words,
                word_list_files=context.word_list_files,
                processing_config=context.processing_config
            )
            preview_context.full_srt = context.preview_srt
            
            # Filter preview subtitles
            filter_step = A1FilterStep()
            if not filter_step.execute(preview_context):
                self.log_error("Failed to filter preview subtitles")
                return False
            
            # Translate filtered preview subtitles
            translation_step = TranslationStep()
            if not translation_step.execute(preview_context):
                self.log_error("Failed to translate preview subtitles")
                return False
            
            self.log_success("Preview processing completed")
            return True
            
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False

class CLIAnalysisStep(ProcessingStep):
    """Processing step for CLI-based subtitle analysis and filtering."""
    
    def __init__(self):
        super().__init__("CLI Analysis")
    
    def execute(self, context: ProcessingContext) -> bool:
        """Execute CLI analysis of subtitles."""
        self.log_start()
        
        try:
            import re
            from collections import Counter
            from tqdm import tqdm
            
            # Load subtitles
            if not context.full_srt or not os.path.exists(context.full_srt):
                self.log_error("Subtitle file not found for analysis")
                return False
            
            subs = load_subtitles(context.full_srt)
            if not subs:
                self.log_error("Failed to load subtitles")
                return False
            
            total_subtitles = len(subs)
            word_counter = Counter()
            skipped_subtitles = 0
            skipped_hard = 0
            word_to_subtitles = {}
            
            # Process each subtitle
            for i, sub in enumerate(tqdm(subs, desc="Processing subtitles")):
                text = sub.text.lower()
                tokens = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]+\b', text)
                unknown_words = [word for word in tokens if word not in context.known_words]
                
                if not unknown_words:
                    skipped_subtitles += 1
                elif len(set(unknown_words)) == 1:
                    word = unknown_words[0]
                    word_counter[word] += 1
                    skipped_hard += 1
                    
                    if word not in word_to_subtitles:
                        word_to_subtitles[word] = []
                    word_to_subtitles[word].append(i)
            
            # Store analysis results in context
            context.metadata = {
                'total_subtitles': total_subtitles,
                'skipped_subtitles': skipped_subtitles,
                'skipped_hard': skipped_hard,
                'word_counts': dict(word_counter),
                'word_to_subtitles': word_to_subtitles,
                'unknown_words_list': [word for word, count in word_counter.most_common()]
            }
            
            self.log_success(f"Analysis completed: {total_subtitles} subtitles, {len(word_counter)} unique unknown words")
            return True
            
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False

class VocabularyUpdateStep(ProcessingStep):
    """Step to update vocabulary with lemmas from known words."""
    
    def __init__(self):
        super().__init__("Vocabulary Update")
    
    def execute(self, context: IConfigurationContext) -> bool:
        self.log_start()
        
        try:
            config = get_config()
            
            with context.model_manager.get_spacy_model_safe() as spacy_processor:
                # Load all known words
                a1_words = load_word_list(config.word_lists.a1_words)
                charaktere_words = load_word_list(config.word_lists.charaktere_words)
                giuliwords = load_word_list(config.word_lists.giuliwords)
                
                known_words = a1_words.union(charaktere_words).union(giuliwords)
                self.log_success(f"Loaded {len(known_words)} known words")
                
                # Find missing lemmas
                new_lemmas = set()
                for word in tqdm(known_words, desc="Processing lemmas"):
                    doc = spacy_processor(word)
                    for token in doc:
                        lemma = token.lemma_.lower().strip()
                        if lemma and lemma not in known_words:
                            new_lemmas.add(lemma)
                
                if new_lemmas:
                    # Add new lemmas to giuliwords
                    with open(config.word_lists.giuliwords, 'a', encoding='utf-8') as f:
                        for lemma in sorted(new_lemmas):
                            f.write(f"{lemma}\n")
                    
                    self.log_success(f"Added {len(new_lemmas)} new lemmas to vocabulary")
                else:
                    self.log_success("No new lemmas found - vocabulary is complete")
                
                return True
            
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False

class A1DeciderStep(ProcessingStep):
    """Interactive step to decide which words are known/unknown."""
    
    def __init__(self):
        super().__init__("A1 Decider")
        self.key_pressed = None
        self.new_known_words = []
    
    def execute(self, context: IFilteringContext) -> bool:
        # Check if we have a subtitle file to process
        subtitle_file = context.full_srt
        if not subtitle_file:
            # Allow user to select a subtitle file
            root = tk.Tk()
            root.withdraw()
            
            subtitle_file = filedialog.askopenfilename(
                title="Select subtitle file",
                filetypes=[("Subtitle files", "*.srt *.vtt"), ("All files", "*.*")]
            )
            
            if not subtitle_file:
                self.log_error("No subtitle file selected")
                return False
        
        self.log_start()
        
        try:
            return self._run_interactive_session(context, subtitle_file)
            
        except Exception as e:
            self.log_error(str(e))
            traceback.print_exc()
            return False
    
    def _run_interactive_session(self, context: ProcessingContext, subtitle_file: str) -> bool:
        """Run the interactive A1 decision session."""
        config = get_config()
        
        with context.model_manager.get_spacy_model_safe() as spacy_processor:
            # Load known words
            known_words = set()
            for word_list_file in config.word_lists.get_all_files():
                if os.path.exists(word_list_file):
                    known_words.update(load_word_list(word_list_file))
            
            # Load global unknowns
            global_unknowns_file = get_global_unknowns_file()
            try:
                with open(global_unknowns_file, 'r', encoding='utf-8') as f:
                    global_unknowns = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                global_unknowns = {}
            
            # Process subtitles
            subs = load_subtitles(subtitle_file)
            if not subs:
                self.log_error("Failed to load subtitles")
                return False
            
            word_counts = Counter()
            word_to_subtitles = {}
            total_subtitles = len(subs)
            skipped_subtitles = 0
            skipped_hard = 0
            
            for i, sub in enumerate(subs):
                text = sub.text
                doc = spacy_processor(text)
                lemmas = [token.lemma_.lower() for token in doc if token.is_alpha]
                unknown_words = [lemma for lemma in lemmas if lemma not in known_words]
                
                if not unknown_words:
                    skipped_subtitles += 1
                elif len(set(unknown_words)) == 1:
                    word = unknown_words[0]
                    word_counts[word] += 1
                    skipped_hard += 1
                    if word not in word_to_subtitles:
                        word_to_subtitles[word] = []
                    word_to_subtitles[word].append(i)
            
            # Update global unknowns
            for word, count in word_counts.items():
                if word not in known_words:
                    global_unknowns[word] = global_unknowns.get(word, 0) + count
            
            sorted_words = word_counts.most_common()
            
            if not sorted_words:
                self.log_success("No unknown words found - all subtitles can be skipped!")
                return True
            
            # Run interactive session
            success = self._interactive_word_review(sorted_words, word_to_subtitles, 
                                                   skipped_subtitles, skipped_hard, total_subtitles)
            
            if success:
                # Save results
                self._save_results(config, global_unknowns, known_words, 
                                 spacy_processor, subtitle_file, subs)
                
            return success
    
    def _interactive_word_review(self, sorted_words, word_to_subtitles, 
                                skipped_subtitles, skipped_hard, total_subtitles):
        """Run the interactive word review session."""
        from rich.console import Console
        console = Console()
        
        skipped = skipped_subtitles
        current_skipped_hard = skipped_hard
        index = 0
        action_history = []
        
        layout = Layout()
        layout.split_column(
            Layout(name="word_panel", size=20),
            Layout(name="message_panel", size=5),
            Layout(name="progress_panel", size=5)
        )
        
        console.clear()
        console.print("\n[bold magenta]¡Welcome to the vocabulary game![/bold magenta]")
        
        def calculate_percentages(skipped, skipped_hard, total):
            skipped_percentage = (skipped / total) * 100 if total > 0 else 0
            potential_percentage = ((skipped + skipped_hard) / total) * 100 if total > 0 else 0
            return skipped_percentage, potential_percentage
        
        def display_progress(layout, skipped_percentage, potential_percentage):
            progress_content = (
                f"[bold yellow]Skipped:[/bold yellow] {skipped_percentage:.2f}%\n"
                f"[bold green]Potential after learning next words:[/bold green] {potential_percentage:.2f}%"
            )
            progress_panel = Panel(
                Align.left(progress_content, vertical="middle"),
                title="Statistics",
                box=box.ROUNDED
            )
            layout["progress_panel"].update(progress_panel)
        
        def display_word(layout, word, index, total):
            word_content = f"[bold cyan]{word}[/bold cyan]\n[italic green][Translation not available][/italic green]"
            word_panel = Panel(
                Align.center(word_content, vertical="middle"),
                title=f"Word {index}/{total}",
                subtitle="Do you know it? (← No / → Yes / ↑ Undo / ↓ Finish)",
                box=box.ROUNDED
            )
            layout["word_panel"].update(word_panel)
        
        def display_message(layout, message, style="bold green"):
            message_panel = Panel(
                Align.center(message, vertical="middle"),
                box=box.ROUNDED,
                style=style
            )
            layout["message_panel"].update(message_panel)
        
        def on_press(key):
            try:
                if key == keyboard.Key.left: self.key_pressed = 'left'
                elif key == keyboard.Key.right: self.key_pressed = 'right'
                elif key == keyboard.Key.up: self.key_pressed = 'up'
                elif key == keyboard.Key.down: self.key_pressed = 'down'
                return False
            except AttributeError:
                pass
        
        initial_skipped_percentage, initial_potential_percentage = calculate_percentages(
            skipped=skipped, skipped_hard=current_skipped_hard, total=total_subtitles
        )
        
        with Live(layout, refresh_per_second=4, console=console, screen=True):
            display_progress(layout, initial_skipped_percentage, initial_potential_percentage)
            
            while index < len(sorted_words):
                word, count = sorted_words[index]
                display_word(layout, word, index + 1, len(sorted_words))
                
                with keyboard.Listener(on_press=on_press) as listener:
                    listener.join()
                
                affected_subtitles = word_to_subtitles.get(word, [])
                subtitles_count = len(affected_subtitles)
                
                if self.key_pressed == 'right':
                    action_history.append((index, word, count, skipped, current_skipped_hard, affected_subtitles))
                    skipped += count
                    current_skipped_hard -= subtitles_count
                    self.new_known_words.append(word)
                    display_message(layout, "Great! You know this word.", style="bold green")
                
                elif self.key_pressed == 'left':
                    action_history.append((index, word, count, skipped, current_skipped_hard, affected_subtitles))
                    display_message(layout, "Don't worry, you'll learn this word soon.", style="bold yellow")
                
                elif self.key_pressed == 'up':
                    if action_history:
                        prev_index, prev_word, _, prev_skipped, prev_skipped_hard, _ = action_history.pop()
                        if prev_word in self.new_known_words:
                            self.new_known_words.remove(prev_word)
                        index = prev_index
                        skipped = prev_skipped
                        current_skipped_hard = prev_skipped_hard
                        display_message(layout, "Last action undone.", style="bold cyan")
                        self.key_pressed = None
                        continue
                    else:
                        display_message(layout, "No actions to undo.", style="bold red")
                
                elif self.key_pressed == 'down':
                    display_message(layout, "You decided to finish the game.", style="bold red")
                    break
                
                self.key_pressed = None
                
                skipped_percentage, potential_percentage = calculate_percentages(
                    skipped=skipped, skipped_hard=current_skipped_hard, total=total_subtitles
                )
                display_progress(layout, skipped_percentage, potential_percentage)
                
                index += 1
        
        console.clear()
        
        skipped_percentage, _ = calculate_percentages(skipped=skipped, skipped_hard=0, total=total_subtitles)
        console.print(f"\n[bold magenta]Game finished![/bold magenta] Your score: [bold]{skipped}/{total_subtitles}[/bold] ({skipped_percentage:.2f}%)")
        
        return True
    
    def _save_results(self, config, global_unknowns, known_words, spacy_processor, subtitle_file, subs):
        """Save the results of the A1 decision session."""
        # Save global unknowns
        global_unknowns_file = get_global_unknowns_file()
        with open(global_unknowns_file, 'w', encoding='utf-8') as f:
            json.dump(global_unknowns, f, indent=4)
        
        # Add new known words to giuliwords
        if self.new_known_words:
            known_words.update(self.new_known_words)
            giuliwords = load_word_list(config.word_lists.giuliwords)
            new_words_to_add = set(self.new_known_words) - giuliwords
            
            if new_words_to_add:
                with open(config.word_lists.giuliwords, 'a', encoding='utf-8') as f:
                    for word in sorted(list(new_words_to_add)):
                        f.write(f"{word}\n")
                self.log_success("Updated known words list")
        
        # Create filtered subtitle file
        output_subtitle_file = os.path.splitext(subtitle_file)[0] + '_a1filtered.srt'
        filtered_subs = pysrt.SubRipFile()
        
        for sub in subs:
            text = sub.text
            doc = spacy_processor(text)
            lemmas = [token.lemma_.lower() for token in doc if token.is_alpha]
            unknown_words = [lemma for lemma in lemmas if lemma not in known_words]
            
            if unknown_words:
                filtered_subs.append(sub)
        
        save_subtitles(filtered_subs, output_subtitle_file)
        self.log_success(f"Filtered subtitles saved: {os.path.basename(output_subtitle_file)}")