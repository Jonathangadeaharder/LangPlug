import os
import traceback
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from tqdm import tqdm
import pysrt

from processing_steps import ProcessingStep, ProcessingContext
from processing_interfaces import (
    ITranscriptionContext,
    IFilteringContext,
    ITranslationContext,
    IPreviewProcessingContext,
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
            model = context.model_manager.get_whisper_model()
            
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
            model = context.model_manager.get_whisper_model()
            
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
        nlp = context.model_manager.get_spacy_model()
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
        model, tokenizer = context.model_manager.get_translation_model(
            context.src_lang, context.tgt_lang
        )
        if not model or not tokenizer:
            raise Exception("Translation model not available")
        
        subs = load_subtitles(subtitle_file)
        if not subs:
            raise Exception("Failed to load subtitles")
        
        translated_subs = pysrt.SubRipFile()
        
        for sub in tqdm(subs, desc="Translating"):
            inputs = tokenizer([sub.text], return_tensors='pt', padding=True, truncation=True).to(
                context.model_manager.get_device()
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