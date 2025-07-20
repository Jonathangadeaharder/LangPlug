import os
import sys
import tkinter as tk
from tkinter import simpledialog, filedialog
from rich.console import Console
from tqdm import tqdm

# Add the parent directory to the system path to allow imports from shared_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_utils.model_utils import ModelManager
from shared_utils.subtitle_utils import load_subtitles, save_subtitles

console = Console()

def translate_subtitle_file(model_manager, subtitle_path, src_lang, tgt_lang):
    try:
        model, tokenizer = model_manager.get_translation_model(src_lang, tgt_lang)
        if not model or not tokenizer:
            return False

        subs = load_subtitles(subtitle_path)
        if not subs:
            return False

        batch_size = 64
        texts = [sub.text for sub in subs]
        translated_subs = subs.copy()

        for i in tqdm(range(0, len(texts), batch_size), desc=f"Translating {os.path.basename(subtitle_path)}"):
            batch_texts = texts[i:i + batch_size]
            inputs = tokenizer(batch_texts, return_tensors='pt', padding=True, truncation=True, max_length=512).to(model_manager.get_device())
            translated = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
            translations = tokenizer.batch_decode(translated, skip_special_tokens=True)

            for j, translation in enumerate(translations):
                translated_subs[i + j].text = translation

        output_path = os.path.splitext(subtitle_path)[0] + f'_{tgt_lang}.srt'
        save_subtitles(translated_subs, output_path)
        return True

    except Exception as e:
        console.print(f"[bold red]Error translating subtitles for {os.path.basename(subtitle_path)}: {e}[/bold red]")
        return False

def main():
    root = tk.Tk()
    root.withdraw()
    
    subtitle_files = filedialog.askopenfilenames(
        title="Select subtitle file(s) to translate",
        filetypes=[("Subtitle files", "*.srt *.vtt"), ("All files", "*.* ")]
    )
    
    if not subtitle_files:
        console.print("[bold red]No files selected. Exiting...[/bold red]")
        sys.exit(1)
    
    src_lang = simpledialog.askstring("Input", "Enter source language code (default: 'de'):", initialvalue="de") or "de"
    tgt_lang = simpledialog.askstring("Input", "Enter target language code (default: 'es'):", initialvalue="es") or "es"
    
    model_manager = ModelManager()
    
    success_count = 0
    for subtitle_path in subtitle_files:
        if translate_subtitle_file(model_manager, subtitle_path, src_lang, tgt_lang):
            success_count += 1
    
    console.print(f"[bold green]Translation completed. Successfully translated {success_count} out of {len(subtitle_files)} files.[/bold green]")
    model_manager.cleanup_all_models()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
        sys.exit(1)
