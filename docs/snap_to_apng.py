#!/home/kda/prodpy3/bin/python3

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from apng import APNG

def find_system_monospace_font():
    """Locates a guaranteed monospaced font file based on the OS."""
    font_selections = []

    if sys.platform.startswith("darwin"):  # macOS
        font_selections = [
            "/System/Library/Fonts/Constants/Menlo.ttc",
            "/Library/Fonts/Courier New.ttf",
            "/System/Library/Fonts/SFNSMono.ttf"
        ]
    elif sys.platform.startswith("win"):  # Windows
        windir = os.environ.get("WINDIR", "C:\\Windows")
        font_selections = [
            os.path.join(windir, "Fonts", "consola.ttf"),
            os.path.join(windir, "Fonts", "cour.ttf")
        ]
    else:  # Linux / BSD
        font_selections = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
        ]

    for path in font_selections:
        if os.path.exists(path):
            return path
    return None

def extract_snap_body(filepath):
    """Strips the insta YAML header and returns only the snapshot body."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---\n')
    if len(parts) >= 3:
        return ''.join(parts[2:]).strip('\n')
    return content.strip('\n')

def render_snap_to_png(text_content, output_png, font_path, font_size=16):
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        print("Warning: Could not find system monospace font path. Using basic fallback.")
        font = ImageFont.load_default()

    lines = text_content.split('\n')
    max_line_len = max(len(line) for line in lines) if lines else 0
    num_lines = len(lines)

    bbox = font.getbbox("M")
    char_width = bbox[2] - bbox[0]
    char_height = (bbox[3] - bbox[1]) * 1.4  # 1.4x terminal line-height multiplier

    padding = 30
    img_width = int(max_line_len * char_width) + (padding * 2)
    img_height = int(num_lines * char_height) + (padding * 2)

    img = Image.new("RGBA", (img_width, img_height), "#1e1e1e")
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        draw.text((padding, y), line, fill="#d4d4d4", font=font)
        y += char_height

    img.save(output_png, "PNG")

def make_animation():
    # Ensure we have at least an input file and an output destination
    if len(sys.argv) < 3:
        print("Error: Missing input snapshots or output file name.")
        print("Usage: python snap_to_apng.py <input1.snap> [input2.snap ...] <output.png>")
        sys.exit(1)

    # The last argument is the output file name
    output_apng = sys.argv[-1]
    # Everything in between the script name and the last item are input snapshots
    snap_files = sys.argv[1:-1]

    font_path = find_system_monospace_font()
    if font_path:
        print(f"Using monospaced font: {os.path.basename(font_path)}")

    png_frames = []
    print(f"Processing {len(snap_files)} snapshots -> Target Destination: {output_apng}")

    for i, snap_file in enumerate(snap_files):
        if not os.path.exists(snap_file):
            print(f"Skipping missing file: {snap_file}")
            continue

        body = extract_snap_body(snap_file)
        frame_name = f"frame_{i:03d}.png"
        render_snap_to_png(body, frame_name, font_path)
        png_frames.append(frame_name)

    if not png_frames:
        print("Error: No valid frames were generated from the input files.")
        return

    # Compile the frames into the custom named output file
    APNG.from_files(png_frames, delay=1000).save(output_apng)

    for frame in png_frames:
        os.remove(frame)

    print(f"Successfully generated APNG: {output_apng}")

if __name__ == "__main__":
    make_animation()

