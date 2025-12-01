#!/usr/bin/env python3
"""Simple Tkinter GUI for transcribing video/audio files to SRT.

Features:
- Select a video/audio file to transcribe
- Choose language (default: German)
- Choose transcription model (Whisper variants)
- Extract audio and transcribe
- Save SRT file
"""

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.transcriptionservice.factory import TranscriptionServiceFactory, get_transcription_service
from utils.srt_parser import SRTParser, SRTSegment

# Language code mappings
LANGUAGES = {
    "German (de)": "de",
    "English (en)": "en",
    "Spanish (es)": "es",
    "French (fr)": "fr",
}


class TranscriptionApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("LangPlug Transcription Tool")
        self.root.geometry("600x350")

        self.selected_file_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")
        self.is_processing = False

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the user interface"""
        padding = {"padx": 10, "pady": 10}

        # File selection frame
        file_frame = tk.Frame(self.root)
        file_frame.pack(fill="x", **padding)

        tk.Label(file_frame, text="Video/Audio file:").pack(side="left")

        entry = tk.Entry(file_frame, textvariable=self.selected_file_var, width=50)
        entry.pack(side="left", padx=(5, 5))

        browse_btn = tk.Button(file_frame, text="Browse...", command=self._on_browse)
        browse_btn.pack(side="left")

        # Configuration frame
        config_frame = tk.Frame(self.root)
        config_frame.pack(fill="x", **padding)

        # Language
        tk.Label(config_frame, text="Language:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.lang_var = tk.StringVar(value="German (de)")
        lang_menu = tk.OptionMenu(config_frame, self.lang_var, *LANGUAGES.keys())
        lang_menu.grid(row=0, column=1, padx=5, pady=5)

        # Model
        tk.Label(config_frame, text="Model:").grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # Get available services/models
        available_services = TranscriptionServiceFactory.get_available_services()
        # Filter for whisper models as they are most common
        model_options = [k for k in available_services if "whisper" in k]
        if not model_options:
            model_options = list(available_services.keys())

        self.model_var = tk.StringVar(value="whisper-base")  # Default to base for balance
        model_menu = tk.OptionMenu(config_frame, self.model_var, *model_options)
        model_menu.grid(row=0, column=3, padx=5, pady=5)

        # Action frame
        action_frame = tk.Frame(self.root)
        action_frame.pack(fill="x", **padding)

        self.transcribe_btn = tk.Button(
            action_frame,
            text="Transcribe File",
            command=self._on_transcribe_click,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
        )
        self.transcribe_btn.pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.root, textvariable=self.status_var, fg="blue", font=("Arial", 10))
        self.status_label.pack(pady=5)

    def _on_browse(self) -> None:
        """Handle browse button click"""
        path = filedialog.askopenfilename(
            title="Select Video/Audio file",
            filetypes=[
                ("Media files", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.m4a"),
                ("Video files", "*.mp4 *.mkv *.avi *.mov"),
                ("Audio files", "*.mp3 *.wav *.m4a"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.selected_file_var.set(path)

    def _update_status(self, message: str) -> None:
        """Update status label"""
        self.status_var.set(message)
        self.root.update()

    def _toggle_inputs(self, enable: bool) -> None:
        """Enable or disable inputs during processing"""
        state = "normal" if enable else "disabled"
        self.transcribe_btn.config(state=state)
        if enable:
            self.transcribe_btn.config(bg="#4CAF50")
        else:
            self.transcribe_btn.config(bg="#cccccc")

    def _on_transcribe_click(self) -> None:
        """Handle transcribe button click"""
        if self.is_processing:
            return

        file_path = self.selected_file_var.get().strip()
        if not file_path:
            messagebox.showerror("Error", "Please select a file first.")
            return

        if not Path(file_path).exists():
            messagebox.showerror("Error", f"File not found: {file_path}")
            return

        # Start processing in a separate thread
        self.is_processing = True
        self._toggle_inputs(False)

        thread = threading.Thread(target=self._run_transcription, args=(file_path,))
        thread.daemon = True
        thread.start()

    def _run_transcription(self, file_path: str) -> None:
        """Run transcription process in background thread"""
        try:
            lang_code = LANGUAGES[self.lang_var.get()]
            model_name = self.model_var.get()

            self._update_status(f"Initializing {model_name} model...")

            # Get service
            service = get_transcription_service(model_name)

            # Check if audio extraction is needed
            input_path = Path(file_path)
            audio_path = input_path
            temp_audio = None

            if service.supports_video() and input_path.suffix.lower() in [".mp4", ".mkv", ".avi", ".mov"]:
                self._update_status("Extracting audio from video...")
                try:
                    # Create temp audio path
                    temp_audio = input_path.with_suffix(".wav")
                    extracted_path = service.extract_audio_from_video(str(input_path), str(temp_audio))
                    audio_path = Path(extracted_path)
                except Exception as e:
                    # If extraction fails, try passing video directly if supported, or fail
                    print(f"Audio extraction warning: {e}")
                    # Continue with original file

            self._update_status(f"Transcribing ({lang_code})... This may take a while.")

            # Transcribe
            result = service.transcribe(str(audio_path), language=lang_code)

            if not result.segments:
                raise ValueError("No segments returned from transcription.")

            self._update_status(f"Transcription complete! Found {len(result.segments)} segments.")

            # Convert to SRT segments
            srt_segments = []
            for i, seg in enumerate(result.segments, start=1):
                srt_segment = SRTSegment(
                    index=i, start_time=seg.start_time, end_time=seg.end_time, text=seg.text.strip()
                )
                srt_segments.append(srt_segment)

            # Save SRT
            output_path = input_path.with_suffix(".srt")
            self._update_status(f"Saving SRT to {output_path}...")

            SRTParser.save_segments(srt_segments, str(output_path))

            # Cleanup temp audio
            if temp_audio and temp_audio.exists() and temp_audio != input_path:
                try:
                    temp_audio.unlink()
                except Exception:
                    pass

            self._update_status("Done!")

            # Show success message (must be on main thread)
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success", f"Transcription complete!\n\nSegments: {len(srt_segments)}\nSaved to:\n{output_path}"
                ),
            )

        except Exception as e:
            self._update_status(f"Error: {e!s}")
            error_msg = str(e)  # Capture error message before exception cleanup
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Transcription Failed", f"Error:\n{msg}"))

        finally:
            self.is_processing = False
            self.root.after(0, lambda: self._toggle_inputs(True))

    def run(self) -> None:
        """Run the application"""
        self.root.mainloop()


def main() -> None:
    app = TranscriptionApp()
    app.run()


if __name__ == "__main__":
    main()
