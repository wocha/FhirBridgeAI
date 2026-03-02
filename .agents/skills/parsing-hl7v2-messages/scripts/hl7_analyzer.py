import os
import sys


def analyze_hl7(filepath):
    """
    Reads an HL7 file and provides a summary of its structure.
    Does not depend on external HL7 libraries to handle malformed files.
    """
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return

    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        print(f"--- HL7 Analysis for {os.path.basename(filepath)} ---")
        print(f"Total Lines: {len(lines)}")

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            segments = line.split('|')
            segment_name = segments[0]
            field_count = len(segments) - 1 # Exclude segment name

            print(f"Line {idx+1} [{segment_name}]: {field_count} fields")

            # Special inspection for MSH and PID
            if segment_name == "MSH" and field_count >= 8:
                print(f"  -> Message Type: {segments[8]}")
            if segment_name == "PID" and field_count >= 5:
                # PID-5 is index 5
                name_parts = segments[5].split('^')
                print(f"  -> Name Parts: {len(name_parts)}")

    except Exception as e:
        print(f"Failed to parse: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hl7_analyzer.py <path_to_hl7_file>")
    else:
        analyze_hl7(sys.argv[1])
