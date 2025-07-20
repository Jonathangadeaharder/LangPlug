import os
import sys
import tkinter as tk
from tkinter import filedialog
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from pynput import keyboard
import json

# Import centralized configuration
from config import get_config, get_core_word_list_files, get_global_unknowns_file

# Add the parent directory to the system path to allow imports from shared_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_utils.model_utils import ModelManager
from shared_utils.subtitle_utils import (
    load_subtitles,
    save_subtitles,
    load_word_list,
)

# Rich Console initialization
console = Console()

# Global variables to handle key presses
key_pressed = None
new_known_words = []

def display_progress(layout, skipped_percentage, potential_percentage):
    progress_content = (
        f"[bold yellow]Omitido:[/bold yellow] {skipped_percentage:.2f}%\n"
        f"[bold green]Potencial al aprender las próximas palabras:[/bold green] {potential_percentage:.2f}%"
    )
    progress_panel = Panel(
        Align.left(progress_content, vertical="middle"),
        title="Estadísticas",
        box=box.ROUNDED
    )
    layout["progress_panel"].update(progress_panel)

def display_word(layout, word, translation, index, total):
    word_content = f"[bold cyan]{word}[/bold cyan]\n[italic green]{translation}[/italic green]"
    word_panel = Panel(
        Align.center(word_content, vertical="middle"),
        title=f"Palabra {index}/{total}",
        subtitle="¿La conoces? (← No / → Sí / ↑ Revertir / ↓ Terminar)",
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

def calculate_percentages(skipped, skipped_hard, total_subtitles):
    skipped_percentage = (skipped / total_subtitles) * 100 if total_subtitles > 0 else 0
    potential_percentage = ((skipped + skipped_hard) / total_subtitles) * 100 if total_subtitles > 0 else 0
    return skipped_percentage, potential_percentage

def main():
    global key_pressed, new_known_words

    root = tk.Tk()
    root.withdraw()

    subtitle_file = filedialog.askopenfilename(
        title="Selecciona el archivo de subtítulos",
        filetypes=[("Archivos de subtítulos", "*.srt *.vtt"), ("Todos los archivos", "*.* ")]
    )

    if not subtitle_file:
        console.print("[bold red]No se seleccionó ningún archivo. Saliendo...[/bold red]")
        sys.exit(1)

    model_manager = ModelManager()
    spacy_processor = model_manager.get_spacy_model()

    console.print("[bold blue]Cargando listas de palabras conocidas...[/bold blue]")
    config = get_config()
    known_words = set()
    for word_list_file in config.word_lists.get_all_files():
        if os.path.exists(word_list_file):
            known_words.update(load_word_list(word_list_file))
    console.print("[bold green]Carga de palabras conocidas COMPLETADA.[/bold green]")

    global_unknowns_file = get_global_unknowns_file()
    try:
        with open(global_unknowns_file, 'r', encoding='utf-8') as f:
            global_unknowns = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        global_unknowns = {}

    subs = load_subtitles(subtitle_file)
    if not subs:
        sys.exit(1)

    from collections import Counter
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

    for word, count in word_counts.items():
        if word not in known_words:
            global_unknowns[word] = global_unknowns.get(word, 0) + count

    sorted_words = word_counts.most_common()
    
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
    console.print("\n[bold magenta]¡Bienvenido al juego de vocabulario![/bold magenta]")

    initial_skipped_percentage, initial_potential_percentage = calculate_percentages(
        skipped=skipped,
        skipped_hard=current_skipped_hard,
        total_subtitles=total_subtitles
    )

    def on_press(key):
        global key_pressed
        try:
            if key == keyboard.Key.left: key_pressed = 'left'
            elif key == keyboard.Key.right: key_pressed = 'right'
            elif key == keyboard.Key.up: key_pressed = 'up'
            elif key == keyboard.Key.down: key_pressed = 'down'
            return False
        except AttributeError:
            pass

    with Live(layout, refresh_per_second=4, console=console, screen=True):
        display_progress(layout, initial_skipped_percentage, initial_potential_percentage)
        
        while index < len(sorted_words):
            word, count = sorted_words[index]
            translation = "[Traducción no disponible]"
            display_word(layout, word, translation, index + 1, len(sorted_words))

            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()

            affected_subtitles = word_to_subtitles.get(word, [])
            subtitles_count = len(affected_subtitles)

            if key_pressed == 'right':
                action_history.append((index, word, count, skipped, current_skipped_hard, affected_subtitles))
                skipped += count
                current_skipped_hard -= subtitles_count
                new_known_words.append(word)
                display_message(layout, "¡Genial! Sabes esta palabra.", style="bold green")

            elif key_pressed == 'left':
                action_history.append((index, word, count, skipped, current_skipped_hard, affected_subtitles))
                display_message(layout, "No te preocupes, aprenderás esta palabra pronto.", style="bold yellow")

            elif key_pressed == 'up':
                if action_history:
                    prev_index, prev_word, _, prev_skipped, prev_skipped_hard, _ = action_history.pop()
                    if prev_word in new_known_words:
                        new_known_words.remove(prev_word)
                    index = prev_index
                    skipped = prev_skipped
                    current_skipped_hard = prev_skipped_hard
                    display_message(layout, "Última acción revertida.", style="bold cyan")
                    key_pressed = None
                    continue
                else:
                    display_message(layout, "No hay acciones para revertir.", style="bold red")

            elif key_pressed == 'down':
                display_message(layout, "Has decidido terminar el juego.", style="bold red")
                break

            key_pressed = None

            skipped_percentage, potential_percentage = calculate_percentages(
                skipped=skipped,
                skipped_hard=current_skipped_hard,
                total_subtitles=total_subtitles
            )
            display_progress(layout, skipped_percentage, potential_percentage)

            index += 1

    console.clear()

    if new_known_words:
        known_words.update(new_known_words)

    skipped_percentage, _ = calculate_percentages(skipped=skipped, skipped_hard=0, total_subtitles=total_subtitles)
    console.print(f"\n[bold magenta]¡Juego terminado![/bold magenta] Tu puntuación: [bold]{skipped}/{total_subtitles}[/bold] ({skipped_percentage:.2f}%)")

    with open(global_unknowns_file, 'w', encoding='utf-8') as f:
        json.dump(global_unknowns, f, indent=4)

    if new_known_words:
        giuliwords_path = config.word_lists.giuliwords
        giuliwords = load_word_list(giuliwords_path)
        new_words_to_add = set(new_known_words) - giuliwords
        if new_words_to_add:
            with open(giuliwords_path, 'a', encoding='utf-8') as f:
                for word in sorted(list(new_words_to_add)):
                    f.write(f"{word}\n")
            console.print("Actualización de palabras conocidas completada.")

    output_subtitle_file = os.path.splitext(subtitle_file)[0] + '_a1filtered.srt'
    import pysrt
    filtered_subs = pysrt.SubRipFile()
    for sub in subs:
        text = sub.text
        doc = spacy_processor(text)
        lemmas = [token.lemma_.lower() for token in doc if token.is_alpha]
        unknown_words = [lemma for lemma in lemmas if lemma not in known_words]
        if unknown_words:
            filtered_subs.append(sub)
    save_subtitles(filtered_subs, output_subtitle_file)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
        sys.exit(1)
