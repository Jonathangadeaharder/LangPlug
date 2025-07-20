import os
import sys
import argparse
import traceback
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
from rich.console import Console

# Add the parent directory to the system path to allow imports from shared_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_utils.model_utils import ModelManager
from shared_utils.subtitle_utils import dict_to_srt

console = Console()

def process_video(model_manager, video_file, language, skip_preview=False):
    """Processes a single video file for transcription."""
    console.print(f"\n--- Processing: {os.path.basename(video_file)} ---")
    script_dir = os.path.dirname(os.path.abspath(video_file))
    base_filename = os.path.splitext(os.path.basename(video_file))[0]

    temp_audio_file = os.path.join(script_dir, f"_temp_dup_{base_filename}.wav")
    audio_file = os.path.join(script_dir, f"_temp_extracted_{base_filename}.wav")
    audio_10min_file = os.path.join(script_dir, f"_temp_10min_{base_filename}.wav")
    srt_filename = os.path.join(script_dir, base_filename + ".srt")
    srt_10min_filename = os.path.join(script_dir, base_filename + "_10min.srt")

    try:
        model = model_manager.get_whisper_model()

        with VideoFileClip(video_file) as video:
            if video.audio is None:
                console.print(f"Error: Video file '{os.path.basename(video_file)}' has no audio track. Skipping.")
                return
            audio_duration = video.duration
            console.print(f"Video duration: {audio_duration:.2f} seconds")

            if audio_duration > 600 and not skip_preview:
                console.print("Extracting first 10 minutes for quick transcription...")
                audio_10min = video.audio.subclipped(0, 600)
                audio_10min.write_audiofile(audio_10min_file, codec='pcm_s16le')
                
                console.print("Starting quick transcription of first 10 minutes...")
                transcription_10min = model.transcribe(audio_10min_file, language=language, verbose=False, condition_on_previous_text=False)
                
                console.print("Converting 10-minute transcription to SRT format...")
                srt_output_10min = dict_to_srt(transcription_10min['segments'])
                with open(srt_10min_filename, "w", encoding="utf-8") as file:
                    file.write(srt_output_10min)
                console.print(f"10-minute preview subtitles saved to {srt_10min_filename}")
                console.print("\n*** You can now start watching with the 10-minute preview subtitles! ***")

            console.print("Extracting full audio for complete transcription...")
            video.audio.write_audiofile(audio_file, codec='pcm_s16le')

        transcribe_target_file = audio_file
        if 0 < audio_duration < 30:
            console.print("Audio duration is less than 30 seconds. Duplicating to improve detection.")
            audio_segment = AudioSegment.from_file(audio_file)
            middle_chunk = audio_segment[5000:15000] # 5s to 15s
            duplicated_audio = middle_chunk + audio_segment
            duplicated_audio.export(temp_audio_file, format="wav")
            transcribe_target_file = temp_audio_file

        console.print("Starting full transcription...")
        transcription = model.transcribe(transcribe_target_file, language=language, verbose=False, condition_on_previous_text=False)
        
        console.print("Converting full transcription to SRT format...")
        srt_output = dict_to_srt(transcription['segments'])
        with open(srt_filename, "w", encoding="utf-8") as file:
            file.write(srt_output)
        console.print(f"Full processing completed. Subtitles saved to {srt_filename}")

        if os.path.exists(srt_10min_filename):
            os.remove(srt_10min_filename)

    except Exception as e:
        console.print(f"\n--- ERROR processing {os.path.basename(video_file)} ---")
        console.print(f"An error occurred: {e}")
        traceback.print_exc()

    finally:
        for f in [temp_audio_file, audio_file, audio_10min_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError as e:
                    console.print(f"Error deleting temporary file {f}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate subtitles for video files using Whisper')
    parser.add_argument('language', nargs='?', default='de', help='Language for transcription [default: de]')
    parser.add_argument('--no-preview', action='store_true', help='Skip 10-minute preview for long videos')
    args = parser.parse_args()
    
    Tk().withdraw()
    video_files = askopenfilenames(
        title="Select Video Files",
        filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv"), ("All Files", "*.*”)]
    )

    if not video_files:
        console.print("No files selected. Exiting...")
        sys.exit(1)

    model_manager = ModelManager()

    for i, video_path in enumerate(video_files):
        console.print(f"\n>>> Processing file {i+1} of {len(video_files)} <<<")
        process_video(model_manager, video_path, args.language, args.no_preview)

    console.print("\n--- All selected videos processed. ---")
    model_manager.cleanup_all_models()
