#!/usr/bin/env python3
"""
VTT Caption Autocorrect Tool

This script reads a dictionary of common text-to-speech transcription errors
and corrects them in WebVTT caption files.
"""

import json
import os
import re
import sys
from pathlib import Path


def load_dictionary(dict_path: str) -> dict:
    """Load and validate the dictionary JSON file."""
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Dictionary file not found: {dict_path}")
        print("Please ensure 'dictionary.json' exists in the same directory as this script.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in dictionary file: {dict_path}")
        print(f"Details: {e}")
        sys.exit(1)

    # Validate required fields
    required_fields = ['runtime_map', 'longest_match_first']
    for field in required_fields:
        if field not in data:
            print(f"Error: Dictionary file is missing required field: '{field}'")
            sys.exit(1)

    return data


def normalize_text(text: str) -> str:
    """
    Normalize text for matching according to dictionary rules:
    - Trim leading/trailing whitespace
    - Collapse internal whitespace to single spaces
    - Normalize smart quotes to ASCII
    - Lowercase
    """
    # Normalize smart quotes to ASCII
    quote_map = {
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201C': '"',  # Left double quote
        '\u201D': '"',  # Right double quote
        '\u2032': "'",  # Prime
        '\u2033': '"',  # Double prime
    }
    for smart, ascii_char in quote_map.items():
        text = text.replace(smart, ascii_char)

    # Collapse whitespace and trim
    text = ' '.join(text.split())

    # Lowercase
    text = text.lower()

    return text


def is_timestamp_line(line: str) -> bool:
    """Check if a line is a VTT timestamp line (e.g., '00:00:01.000 --> 00:00:05.000')."""
    return '-->' in line


def is_cue_identifier(line: str, prev_line_blank: bool) -> bool:
    """
    Check if a line is a cue identifier.
    Cue identifiers appear after a blank line and before a timestamp line.
    They can be numeric or alphanumeric.
    """
    # If previous line wasn't blank, this can't be a cue identifier
    if not prev_line_blank:
        return False
    # Cue identifiers are typically simple: numbers or short alphanumeric strings
    # They don't contain '-->' and aren't the WEBVTT header
    stripped = line.strip()
    if not stripped:
        return False
    if '-->' in stripped:
        return False
    if stripped.upper().startswith('WEBVTT'):
        return False
    # Simple heuristic: cue IDs are usually short and don't have colons
    # (timestamps have colons)
    return True


def replace_mistakes_in_text(
    text: str,
    runtime_map: dict,
    longest_match_first: list,
    stats: dict
) -> str:
    """
    Replace mistakes in caption text.
    Uses case-insensitive matching but preserves surrounding text.
    """
    if not text.strip():
        return text

    result = text
    normalized = normalize_text(text)

    # Process each pattern in longest-first order
    for mistake in longest_match_first:
        if mistake not in runtime_map:
            continue

        replacement = runtime_map[mistake]

        # Create a regex pattern for case-insensitive word boundary matching
        # We need to match the mistake in the normalized space but apply to original
        pattern = re.compile(
            r'\b' + re.escape(mistake) + r'\b',
            re.IGNORECASE
        )

        # Find all matches in normalized text and count them
        matches = list(pattern.finditer(normalized))
        if matches:
            # Apply replacement to the result (which may have different case)
            new_result = pattern.sub(replacement, result)
            if new_result != result:
                count = len(matches)
                stats['total_corrections'] += count
                if mistake not in stats['frequency']:
                    stats['frequency'][mistake] = 0
                stats['frequency'][mistake] += count
                result = new_result
                # Update normalized version for subsequent matches
                normalized = normalize_text(result)

    return result


def process_vtt_file(
    file_path: Path,
    runtime_map: dict,
    longest_match_first: list,
    stats: dict
) -> bool:
    """
    Process a single VTT file, replacing mistakes.
    Returns True if the file was modified.
    """
    print(f"Processing: {file_path.resolve()}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Warning: Could not read file: {e}")
        return False

    lines = content.split('\n')
    new_lines = []
    modified = False
    prev_line_blank = False
    in_header = True  # Track if we're still in the WEBVTT header section

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for WEBVTT header
        if in_header and stripped.upper().startswith('WEBVTT'):
            new_lines.append(line)
            i += 1
            prev_line_blank = False
            continue

        # Empty lines mark section boundaries
        if not stripped:
            new_lines.append(line)
            prev_line_blank = True
            in_header = False
            i += 1
            continue

        # Skip timestamp lines
        if is_timestamp_line(line):
            new_lines.append(line)
            prev_line_blank = False
            in_header = False
            i += 1
            continue

        # Skip cue identifiers (appear after blank line, before timestamp)
        # Look ahead to see if next non-blank line is a timestamp
        if prev_line_blank:
            # Check if this could be a cue identifier by looking ahead
            look_ahead = i + 1
            while look_ahead < len(lines) and not lines[look_ahead].strip():
                look_ahead += 1
            if look_ahead < len(lines) and is_timestamp_line(lines[look_ahead]):
                # This is a cue identifier, skip it
                new_lines.append(line)
                prev_line_blank = False
                in_header = False
                i += 1
                continue

        # Skip NOTE comments
        if stripped.upper().startswith('NOTE'):
            new_lines.append(line)
            prev_line_blank = False
            in_header = False
            i += 1
            continue

        # Skip STYLE blocks
        if stripped.upper().startswith('STYLE'):
            new_lines.append(line)
            prev_line_blank = False
            in_header = False
            i += 1
            continue

        # This should be caption text - apply replacements
        in_header = False
        new_line = replace_mistakes_in_text(line, runtime_map, longest_match_first, stats)
        if new_line != line:
            modified = True
        new_lines.append(new_line)
        prev_line_blank = False
        i += 1

    if modified:
        try:
            new_content = '\n'.join(new_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            stats['files_modified'] += 1
        except Exception as e:
            print(f"  Warning: Could not write file: {e}")
            return False

    return modified


def collect_vtt_files(path: Path) -> list:
    """Recursively collect all .vtt files from a directory."""
    vtt_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith('.vtt'):
                vtt_files.append(Path(root) / file)
    return sorted(vtt_files)


def print_summary(stats: dict):
    """Print summary statistics and frequency table."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed:  {stats['files_processed']}")
    print(f"Files modified:   {stats['files_modified']}")
    print(f"Total corrections: {stats['total_corrections']}")

    if stats['frequency']:
        print("\n" + "-" * 60)
        print("CORRECTION FREQUENCY")
        print("-" * 60)
        print(f"{'Mistake':<40} {'Count':>10}")
        print("-" * 60)

        # Sort by frequency (descending) then alphabetically
        sorted_items = sorted(
            stats['frequency'].items(),
            key=lambda x: (-x[1], x[0])
        )

        for mistake, count in sorted_items:
            # Truncate long mistakes for display
            display_mistake = mistake if len(mistake) <= 38 else mistake[:35] + "..."
            print(f"{display_mistake:<40} {count:>10}")

        print("-" * 60)
        print(f"{'TOTAL':<40} {stats['total_corrections']:>10}")


def main():
    # Verify command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <file_or_directory>")
        print()
        print("Arguments:")
        print("  file_or_directory  A .vtt file or a directory containing .vtt files")
        print()
        print("Examples:")
        print("  python main.py captions.vtt")
        print("  python main.py ./captions/")
        sys.exit(1)

    target_path = Path(sys.argv[1])

    # Load dictionary from same directory as script
    script_dir = Path(__file__).parent.resolve()
    dict_path = script_dir / 'dictionary.json'
    dictionary = load_dictionary(str(dict_path))

    runtime_map = dictionary['runtime_map']
    longest_match_first = dictionary['longest_match_first']

    # Initialize statistics
    stats = {
        'files_processed': 0,
        'files_modified': 0,
        'total_corrections': 0,
        'frequency': {}
    }

    # Collect VTT files to process
    vtt_files = []

    if target_path.is_file():
        if not target_path.suffix.lower() == '.vtt':
            print(f"Error: File must have .vtt extension: {target_path}")
            print("Please provide a valid WebVTT file.")
            sys.exit(1)
        if not target_path.exists():
            print(f"Error: File not found: {target_path}")
            sys.exit(1)
        vtt_files = [target_path]

    elif target_path.is_dir():
        if not target_path.exists():
            print(f"Error: Directory not found: {target_path}")
            sys.exit(1)
        vtt_files = collect_vtt_files(target_path)
        if not vtt_files:
            print(f"Warning: No .vtt files found in directory: {target_path}")
            sys.exit(0)
        print(f"Found {len(vtt_files)} VTT file(s) in {target_path.resolve()}")
        print()

    else:
        print(f"Error: Path does not exist: {target_path}")
        sys.exit(1)

    # Process each VTT file
    for vtt_file in vtt_files:
        stats['files_processed'] += 1
        process_vtt_file(vtt_file, runtime_map, longest_match_first, stats)

    # Print summary
    print_summary(stats)


if __name__ == '__main__':
    main()
