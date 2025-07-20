import sys
from rich.console import Console
from rich.panel import Panel
from core.spacy_processor import SpacyProcessor
from core.file_io import load_word_list

# Import centralized configuration
from config import get_config

console = Console()

def update_known_words_with_lemmas(spacy_processor, a1_file, charaktere_file, giuliwords_file):
    a1_words = load_word_list(a1_file)
    charaktere_words = load_word_list(charaktere_file)
    giuliwords = load_word_list(giuliwords_file)

    known_words = a1_words.union(charaktere_words).union(giuliwords)
    console.print(f"[bold blue]Se han cargado {len(known_words)} palabras en total.[/bold blue]")

    new_lemmas = set()

    for word in known_words:
        doc = spacy_processor.nlp(word)
        for token in doc:
            lemma = token.lemma_.lower().strip()
            if lemma and lemma not in known_words:
                new_lemmas.add(lemma)

    if new_lemmas:
        console.print(Panel(f"Se encontraron [bold yellow]{len(new_lemmas)}[/bold yellow] lemas faltantes.",
                              title="Actualización de lemas", style="bold yellow"))
        try:
            with open(giuliwords_file, 'a', encoding='utf-8') as f:
                for lemma in sorted(new_lemmas):
                    f.write(f"{lemma}\n")
            console.print(Panel("La lista de palabras se ha actualizado exitosamente.",
                                title="Éxito", style="bold green"))
        except Exception as e:
            console.print(f"[bold red]Error al actualizar el archivo {giuliwords_file}: {e}[/bold red]")
    else:
        console.print(Panel("No se encontraron lemas faltantes. La lista de palabras ya está completa.",
                            title="Completado", style="bold green"))

    return known_words.union(new_lemmas)

def main():
    spacy_processor = SpacyProcessor()
    
    # Use centralized configuration for file paths
    config = get_config()
    a1_file = config.word_lists.a1_words
    charaktere_file = config.word_lists.charaktere_words
    giuliwords_file = config.word_lists.giuliwords

    update_known_words_with_lemmas(spacy_processor, a1_file, charaktere_file, giuliwords_file)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[bold red]Ocurrió un error: {e}[/bold red]")
        sys.exit(1)