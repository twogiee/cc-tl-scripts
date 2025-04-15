import os
import sys
import struct
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

@dataclass
class Command:
    opcode: str
    params: List[str]
    offset: int

def read_ws2_file(filename):
    with open(filename, 'rb') as f:
        return f.read()

def read_null_terminated_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Read a null-terminated string from data at offset. Returns (string, new_offset)"""
    end = offset
    while end < len(data) and data[end] != 0:
        end += 1
    if end == offset:
        return "", end + 1
    return data[offset:end].decode('ascii', errors='ignore'), end + 1

def parse_command(data: bytes, offset: int) -> Tuple[Optional[Command], int]:
    """Parse a command from the binary data. Returns (Command, new_offset) or (None, offset+1)"""
    if offset >= len(data):
        return None, offset
        
    try:
        # Skip any null bytes
        while offset < len(data) and data[offset] == 0:
            offset += 1
            
        if offset >= len(data):
            return None, offset
            
        # Read command name
        cmd_name, next_offset = read_null_terminated_string(data, offset)
        if not cmd_name:
            return None, offset + 1
            
        # Read parameters until we hit a sequence of nulls or control bytes
        params = []
        param_start = next_offset
        while next_offset < len(data):
            # Check for control bytes
            if data[next_offset:next_offset+2] == b'%K' or data[next_offset:next_offset+2] == b'%P':
                break
                
            # Read parameter
            param, next_offset = read_null_terminated_string(data, param_start)
            if param:
                params.append(param)
                param_start = next_offset
            else:
                # If we get an empty string, we've hit the end of parameters
                break
                
        return Command(cmd_name, params, offset), next_offset
        
    except Exception as e:
        print(f"Error parsing command at offset {offset}: {e}")
        return None, offset + 1

def clean_text(text: str) -> str:
    """Clean up text by removing control codes and formatting quotes"""
    # Remove control codes
    text = text.replace('%K', '').replace('%P', '')
    # Clean up quotes
    text = text.replace('\\d', '"')
    # Clean up newlines
    text = text.replace('\\n', '\n')
    return text.strip()

def hex_debug(data: bytes, offset: int, context: int = 16) -> str:
    """Print hex and ASCII representation of data around offset"""
    start = max(0, offset - context)
    end = min(len(data), offset + context)
    
    hex_str = ' '.join(f'{b:02x}' for b in data[start:end])
    ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[start:end])
    
    return f"Offset {offset:08x}: {hex_str}\n{' ' * 12}{ascii_str}"

def extract_script(filename: str) -> List[str]:
    """Extract script in Amaterasu format."""
    data = read_ws2_file(filename)
    script_lines = []
    current_character = None
    last_character = None
    
    offset = 0
    while offset < len(data):
        # Look for text markers
        if offset + 4 <= len(data) and data[offset:offset+4] == b'char':
            # Skip 'char' and any null bytes
            text_start = offset + 4
            while text_start < len(data) and data[text_start] == 0:
                text_start += 1
                
            # Find end of text (null or control code)
            text_end = text_start
            while text_end < len(data):
                if data[text_end] == 0:
                    break
                if text_end + 1 < len(data) and data[text_end] == ord('%'):
                    break
                text_end += 1
                
            if text_end > text_start:
                text = data[text_start:text_end].decode('ascii', errors='ignore')
                text = clean_text(text)
                if text:
                    # Check if this is a voice file reference
                    is_voice_ref = False
                    if text_start >= 4 and data[text_start-4:text_start] == b'char':
                        is_voice_ref = True
                    
                    if not is_voice_ref:
                        if current_character:
                            # Only add newline if character changed
                            if current_character != last_character:
                                script_lines.append("")
                                script_lines.append(f"[{current_character}]")
                            script_lines.append(f"{text}")
                            last_character = current_character
                            current_character = None
                        else:
                            # Only add newline if we're switching from character to non-character
                            if last_character is not None:
                                script_lines.append("")
                            script_lines.append(text)
                            last_character = None
                        
            offset = text_end + 1
            continue
            
        # Look for character markers
        if offset + 3 <= len(data) and data[offset:offset+3] == b'%LC':
            name_start = offset + 3
            name_end = name_start
            while name_end < len(data) and data[name_end] not in (0, ord('%')):
                name_end += 1
            if name_end > name_start:
                current_character = data[name_start:name_end].decode('ascii', errors='ignore')
            offset = name_end + 1
            continue
            
        # Skip voice file markers
        if offset + 8 <= len(data) and (data[offset:offset+8] == b'.(char' or data[offset:offset+6] == b'(char'):
            # Find next null byte or control code
            while offset < len(data):
                if data[offset] == 0 or (offset + 1 < len(data) and data[offset] == ord('%')):
                    break
                offset += 1
            continue
            
        offset += 1
    
    # Clean up empty lines at start/end
    while script_lines and not script_lines[0].strip():
        script_lines.pop(0)
    while script_lines and not script_lines[-1].strip():
        script_lines.pop()
        
    return script_lines

def has_meaningful_content(file_path: Path) -> bool:
    """Check if a file has any meaningful content (non-empty lines)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # If we find any non-empty line
                    return True
        return False
    except Exception:
        return False

def process_directory(directory: str):
    """Process all .ws2 files in the given directory"""
    script_dir = Path(directory)
    if not script_dir.exists():
        print(f"Error: Directory {directory} not found")
        return
        
    # Create output directory if it doesn't exist
    output_dir = Path("scripts/moenovel")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all .ws2 files
    ws2_files = list(script_dir.glob("*.ws2"))
    if not ws2_files:
        print(f"No .ws2 files found in {directory}")
        return
        
    print(f"Found {len(ws2_files)} .ws2 files to process")
    
    for ws2_file in ws2_files:
        print(f"Processing {ws2_file.name}...")
        # Extract script number from filename (e.g., CCA0002_en.ws2 -> cca0002)
        script_name = ws2_file.stem.split('_')[0].lower()
        
        # Extract script
        script_lines = extract_script(str(ws2_file))
        
        # Write to output file
        output_file = output_dir / f"{script_name}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))
        
        # Check if the file has any meaningful content
        if not has_meaningful_content(output_file):
            print(f"  -> No meaningful content, deleting {output_file}")
            output_file.unlink()
        else:
            print(f"  -> Extracted to {output_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_moenovel.py <ws2_file_or_directory>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    
    if os.path.isdir(input_path):
        process_directory(input_path)
    else:
        if not os.path.exists(input_path):
            print(f"Error: File {input_path} not found")
            sys.exit(1)
        
        # Extract script number from filename (e.g., CCA0002_en.ws2 -> cca0002)
        script_name = os.path.basename(input_path).split('_')[0].lower()
        
        # Create output directory if it doesn't exist
        output_dir = Path("scripts/moenovel")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract script
        script_lines = extract_script(input_path)
        
        # Write to output file
        output_file = output_dir / f"{script_name}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))
        
        print(f"Script extracted to {output_file}")

if __name__ == "__main__":
    main() 