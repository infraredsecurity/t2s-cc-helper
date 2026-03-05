# VTT Caption Autocorrect Tool

A Python script that automatically corrects common text-to-speech transcription errors in WebVTT (.vtt) caption files using a customizable dictionary.

## Overview

When generating captions using text-to-speech engines, technical terms are often transcribed phonetically rather than correctly. For example:

| Transcribed (Mistake) | Corrected |
|-----------------------|-----------|
| dev you random | /dev/urandom |
| node js | Node.js |
| owasp top 10 | OWASP Top 10 |
| cross-site scripting | Cross-Site Scripting (XSS) |

This tool reads a dictionary of known mistakes and their corrections, then applies them to your VTT files while preserving timestamps, cue identifiers, and file structure.

## Requirements

- Python 3.6 or later (included with macOS)
- No external dependencies required

### Verify Python Installation

Open Terminal and run:

```bash
python3 --version
```

You should see output like `Python 3.x.x`. If not installed, you can install it via:

```bash
# Using Homebrew
brew install python3

# Or download from https://www.python.org/downloads/
```

## Installation

1. Clone or download this repository to your local machine:

```bash
git clone <repository-url>
cd t2s-cc-helper
```

2. Ensure both `main.py` and `dictionary.json` are in the same directory:

```
t2s-cc-helper/
├── main.py
├── dictionary.json
└── README.md
```

No additional installation steps are required.

## Usage

### Process a Single VTT File

```bash
python3 main.py /path/to/your/captions.vtt
```

### Process All VTT Files in a Directory

```bash
python3 main.py /path/to/captions/folder/
```

The script will recursively find and process all `.vtt` files in the directory and its subdirectories.

### Examples

```bash
# Process a single file
python3 main.py ~/Downloads/lecture.vtt

# Process all VTT files in a project
python3 main.py ~/Projects/course-videos/captions/

# Process files in the current directory
python3 main.py .
```

## Output

The script provides detailed output during execution:

```
Found 3 VTT file(s) in /Users/you/captions

Processing: /Users/you/captions/lesson1.vtt
Processing: /Users/you/captions/lesson2.vtt
Processing: /Users/you/captions/lesson3.vtt

============================================================
SUMMARY
============================================================
Files processed:  3
Files modified:   2
Total corrections: 15

------------------------------------------------------------
CORRECTION FREQUENCY
------------------------------------------------------------
Mistake                                       Count
------------------------------------------------------------
javascript                                        5
node js                                           4
api                                               3
owasp                                             2
json                                              1
------------------------------------------------------------
TOTAL                                            15
```

## How It Works

1. **Dictionary Loading**: Reads `dictionary.json` from the same directory as the script
2. **File Discovery**: Accepts a single `.vtt` file or recursively scans a directory
3. **Smart Parsing**: Identifies and skips VTT structural elements:
   - `WEBVTT` header
   - Timestamp lines (e.g., `00:00:01.000 --> 00:00:05.000`)
   - Cue identifiers
   - `NOTE` comments
   - `STYLE` blocks
4. **Text Normalization**: Before matching, text is normalized by:
   - Trimming whitespace
   - Collapsing multiple spaces
   - Converting smart quotes to ASCII
   - Converting to lowercase
5. **Longest Match First**: Applies longer patterns before shorter ones to avoid partial matches (e.g., "owasp top 10" before "owasp")
6. **In-Place Updates**: Modified files are overwritten with corrections

## Dictionary Format

The `dictionary.json` file contains the correction rules. Key sections:

### `runtime_map`

A simple key-value mapping of mistakes to corrections:

```json
{
  "runtime_map": {
    "javascript": "JavaScript",
    "node js": "Node.js",
    "api": "API"
  }
}
```

### `longest_match_first`

An ordered list ensuring longer phrases are matched before shorter ones:

```json
{
  "longest_match_first": [
    "cross site scripting",
    "node js",
    "api"
  ]
}
```

### Adding Custom Rules

To add a new correction rule:

1. Add the mapping to `runtime_map`:
   ```json
   "my term": "My Corrected Term"
   ```

2. Add the key to `longest_match_first` in the appropriate position (longer phrases should appear earlier in the list)

## Troubleshooting

### "Dictionary file not found"

Ensure `dictionary.json` is in the same directory as `main.py`:

```bash
ls -la /path/to/t2s-cc-helper/
# Should show both main.py and dictionary.json
```

### "File must have .vtt extension"

The script only processes WebVTT files. Ensure your file has a `.vtt` extension:

```bash
# Rename if necessary
mv captions.txt captions.vtt
```

### "No .vtt files found in directory"

The specified directory contains no VTT files. Verify your path:

```bash
find /your/path -name "*.vtt"
```

### Permission Denied

Ensure you have read/write permissions for the VTT files:

```bash
chmod 644 /path/to/your/file.vtt
```

### Encoding Issues

The script expects UTF-8 encoded files. If you encounter encoding errors, convert your files:

```bash
iconv -f ISO-8859-1 -t UTF-8 input.vtt > output.vtt
```

## Backup Recommendation

The script modifies files in place. Consider backing up your VTT files before processing:

```bash
# Create a backup
cp -r captions/ captions_backup/

# Then process
python3 main.py captions/
```

## License

See LICENSE file for details.
