import os
import re
import codecs
from pathlib import Path

def extract_text_from_dsf(file_path, translation_name):
    """Extract text, speaker, and comments from a dsf file."""
    # Read with Shift-JIS using codecs, replacing invalid characters
    try:
        # Try reading with Shift-JIS first
        with open(file_path, 'r', encoding='shift-jis', errors='ignore') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Failed to read {file_path} with Shift-JIS, trying UTF-8")
        # Fall back to UTF-8 if Shift-JIS fails
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    
    # Split into lines and process
    lines = content.split('\n')
    extracted_lines = []
    current_tlnote = None
    building_comment = []
    
    # Define the list of translator names and their possible formats
    translator_patterns = [
        r'- (IX|Raide|Sheeta|pondrthis|Neko|Spin|GHS.*?)$',  # Format: "- Name" with any GHS suffix
        r'-(IX|Raide|Sheeta|pondrthis|Neko|Spin|GHS.*?)$',   # Format: "-Name" with any GHS suffix
        r'〜(IX|Raide|Sheeta|pondrthis|Neko|Spin|GHS.*?)$',  # Format: "～Name" with any GHS suffix
    ]
    
    for line in lines:
        # Preserve leading spaces but strip trailing spaces
        leading_spaces = len(line) - len(line.lstrip())
        line = line.rstrip()
        
        # Skip empty lines and commands
        if not line or line.startswith(('GL', 'GS', 'SEF', '$CG', '//CP', 'WVP', 'TS', 'AL', 'GI', 'GO', 'TWS', 'WVS', 'WT', 'RET', 'GP')) or line == '>':
            continue
            
        # Handle TL and TP markers
        if line in ('TL', 'TP'):
            # If we were building a comment, attach it to previous line
            if building_comment and extracted_lines:
                comment = '\n//'.join(c[2:].strip() for c in building_comment)
                extracted_lines[-1]['comment'] = comment
                building_comment = []
            continue
            
        # Handle TL notes
        if line.startswith('IF $tlnote'):
            # Extract the note text, handling both formats
            if '(TL note:' in line:
                current_tlnote = line.split('(TL note:', 1)[1].strip().rstrip(')')
            elif '(TL note]' in line:
                current_tlnote = line.split('(TL note]', 1)[1].strip()
            else:
                current_tlnote = line.split(':', 1)[1].strip() if ':' in line else line[15:].strip()
            continue
            
        # Handle translator comments
        if line.startswith('//') and not line.startswith('//CP'):
            # Skip HACK comments
            if line.startswith('//HACK'):
                continue
                
            for pattern in translator_patterns:
                if re.search(pattern, line):
                    building_comment.append(line)
                    break
            continue
            
        # If we have a non-empty line that's not a command or comment, it's dialogue
        if line and not line.startswith(('//', 'GL', 'GS', 'SEF', '$CG')):
            # If we were building a comment, attach it to previous line
            if building_comment and extracted_lines:
                comment = '\n'.join(c[2:].strip() for c in building_comment)
                extracted_lines[-1]['comment'] = comment
                building_comment = []
            
            # Check if line has a speaker (format: "Speaker: text")
            speaker = None
            text = line
            
            # Look for pattern like "Name: " at start of line, limiting to 1-2 alphanumeric words
            speaker_match = re.match(r'^([a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]+)?):\s*(.*)', line)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
                # Preserve leading spaces in the text part
                text = ' ' * leading_spaces + text
            
            # Add the new line (without comments yet)
            extracted_lines.append({
                'speaker': speaker,
                'text': text,
                'comment': None,
                'tlnote': current_tlnote
            })
            
            # Reset TL note
            current_tlnote = None
    
    # Handle any remaining comment at end of file
    if building_comment and extracted_lines:
        comment = '\n'.join(c[2:].strip() for c in building_comment)
        extracted_lines[-1]['comment'] = comment
    
    return extracted_lines

def process_translation(translation_dir, output_dir):
    """Process all dsf files in a translation directory."""
    for root, _, files in os.walk(translation_dir):
        for file in files:
            if file.endswith('.dsf'):
                file_path = os.path.join(root, file)
                lines = extract_text_from_dsf(file_path, os.path.basename(translation_dir))
                
                # Create output file with same name but .txt extension
                output_file = os.path.join(output_dir, os.path.splitext(file)[0] + '.txt')
                with open(output_file, 'w', encoding='utf-8') as f:
                    last_speaker = None
                    for line in lines:
                        # Add extra newline if speaker changes
                        if line['speaker'] != last_speaker:
                            f.write("\n")
                        last_speaker = line['speaker']
                        
                        if line['speaker']:
                            f.write(f"[{line['speaker']}]\n")
                        f.write(f"{line['text']}\n")
                        if line['comment']:
                            f.write(f"//{line['comment']}\n")
                        if line['tlnote']:
                            f.write(f"(TL Note: {line['tlnote']})\n")

def main():
    # Create output directories if they don't exist
    os.makedirs('scripts/amaterasu', exist_ok=True)
    os.makedirs('scripts/georgehenryshaft', exist_ok=True)
    
    # Process each translation
    process_translation('raw/amaterasu/scripts', 'scripts/amaterasu')  # Fixed path
    process_translation('raw/georgehenryshaft/scripts', 'scripts/georgehenryshaft')

if __name__ == "__main__":
    main() 