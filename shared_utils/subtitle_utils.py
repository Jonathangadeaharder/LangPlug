import os
import pysrt
import webvtt
from rich.console import Console

console = Console()

def load_subtitles(subtitle_path):
    """Load subtitles from SRT or VTT file and return a pysrt object."""
    try:
        file_ext = os.path.splitext(subtitle_path)[1].lower()

        if file_ext == '.srt':
            return pysrt.open(subtitle_path, encoding='utf-8')
        elif file_ext == '.vtt':
            return convert_vtt_to_srt_object(subtitle_path)
        else:
            console.print(f"[bold red]Unsupported subtitle format: {file_ext}[/bold red]")
            return None
    except Exception as e:
        console.print(f"[bold red]Error loading subtitles from {subtitle_path}: {e}[/bold red]")
        return None

def convert_vtt_to_srt_object(vtt_path):
    """Convert VTT file to a pysrt object in memory"""
    try:
        vtt_subs = webvtt.read(vtt_path)
        srt_subs = pysrt.SubRipFile()

        for i, caption in enumerate(vtt_subs):
            item = pysrt.SubRipItem()
            item.index = i + 1
            item.text = caption.text

            # Manually parse the VTT time format HH:MM:SS.mmm or MM:SS.mmm
            start_parts = caption.start.split(':')
            end_parts = caption.end.split(':')

            if len(start_parts) == 3:
                h, m, s_ms = start_parts
                s, ms = s_ms.split('.')
                item.start.hours = int(h)
                item.start.minutes = int(m)
                item.start.seconds = int(s)
                item.start.milliseconds = int(ms)
            elif len(start_parts) == 2:
                m, s_ms = start_parts
                s, ms = s_ms.split('.')
                item.start.minutes = int(m)
                item.start.seconds = int(s)
                item.start.milliseconds = int(ms)

            if len(end_parts) == 3:
                h, m, s_ms = end_parts
                s, ms = s_ms.split('.')
                item.end.hours = int(h)
                item.end.minutes = int(m)
                item.end.seconds = int(s)
                item.end.milliseconds = int(ms)
            elif len(end_parts) == 2:
                m, s_ms = end_parts
                s, ms = s_ms.split('.')
                item.end.minutes = int(m)
                item.end.seconds = int(s)
                item.end.milliseconds = int(ms)

            srt_subs.append(item)

        return srt_subs
    except Exception as e:
        console.print(f"[bold red]Error converting VTT to SRT object: {e}[/bold red]")
        return None


def save_subtitles(subs, output_path):
    """Saves subtitles to an SRT file."""
    try:
        subs.save(output_path, encoding='utf-8')
        console.print(f"[bold green]Subtitles saved to '{output_path}'.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error saving subtitles to {output_path}: {e}[/bold red]")


def format_srt_time(timestamp):
    """Convert timestamp (in seconds) to SRT time format string."""
    timestamp = max(0, timestamp)
    hours, remainder = divmod(timestamp, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"

def estimate_end_time(start_time, text, words_per_minute=100):
    """Estimate end time based on text length. Ensures end time is after start time."""
    word_count = len(text.split())
    if word_count == 0:
        return start_time + 1
    duration_in_seconds = max(0.5, (word_count / words_per_minute) * 60)
    return start_time + duration_in_seconds

def dict_to_srt(subtitles):
    """Convert Whisper output (list of dicts) to an SRT string."""
    srt_string = ""
    valid_subtitles = [s for s in subtitles if s.get('start') is not None and s.get('end') is not None and s['start'] >= 0 and s['end'] > s['start']]

    for index, subtitle in enumerate(valid_subtitles):
        start_time = subtitle["start"]
        end_time = subtitle.get("end")
        if end_time is None or end_time <= start_time:
             end_time = estimate_end_time(start_time, subtitle["text"])
             if end_time <= start_time:
                 end_time = start_time + 1

        srt_string += f"{index + 1}\n{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n{subtitle['text'].strip()}\n\n"
    return srt_string

def load_word_list(file_path):
    """Load word list from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(word.strip().lower() for word in f.readlines() if word.strip())
    except FileNotFoundError:
        console.print(f"[bold yellow]Warning: Word list file not found: {file_path}[/bold yellow]")
        return set()
    except Exception as e:
        console.print(f"[bold red]Error loading word list {file_path}: {e}[/bold red]")
        return set()
