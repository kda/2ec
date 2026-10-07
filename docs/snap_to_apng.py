#!/home/kda/prodpy3/bin/python3

import os
import sys
import re
from PIL import Image, ImageColor, ImageDraw, ImageFont
from apng import APNG

# Standard 16 terminal color palette map (Adjust hex values to match your terminal theme)
COLOR_PALETTE = {
    "Black": "#000000",
    "Red": "#cd3131",
    "Green": "#0dbc79",
    "Yellow": "#e5e510",
    "Blue": "#2472c8",
    "Magenta": "#bc3fbc",
    "Cyan": "#11a8cd",
    "White": "#e5e5e5",
    "LightBlack": "#666666",
    "LightRed": "#f14c4c",
    "LightGreen": "#23d18b",
    "LightYellow": "#f5f543",
    "LightBlue": "#3b8eea",
    "LightMagenta": "#d670d6",
    "LightCyan": "#29b8db",
    "LightWhite": "#e5e5e5",
    "Reset": "#d4d4d4",  # Default text color fallback
}
DEFAULT_BG = "#1e1e1e"
DEFAULT_FG = "#d4d4d4"

def find_system_monospace_font():
    """Locates a guaranteed monospaced font file based on Linux/BSD systems."""
    font_selections = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
    ]
    for path in font_selections:
        if os.path.exists(path):
            return path
    return None

def extract_clean_snap_body(filepath):
    """Strips the insta YAML header and extracts the raw content block."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---\n')
    if len(parts) >= 3:
        body = ''.join(parts[2:])
    else:
        body = content
    return body.strip()

def parse_ratatui_buffer(buffer_text):
    """
    Parses a Ratatui TestBackend Buffer string layout into a structured grid.
    Correctly correlates a plain text 'content' array with a sparse coordinate 'styles' array.
    """
    if "buffer: Buffer" not in buffer_text and "Buffer {" not in buffer_text:
        return None

    # 1. Parse terminal dimensions from the Rect specification
    width_match = re.search(r'width:\s*(\d+)', buffer_text)
    height_match = re.search(r'height:\s*(\d+)', buffer_text)
    if not width_match or not height_match:
        return None

    width = int(width_match.group(1))
    height = int(height_match.group(1))

    # 2. Extract the plain text lines inside the content block
    content_block_match = re.search(r'content:\s*\[(.*?)\]', buffer_text, re.DOTALL)
    if not content_block_match:
        return None

    content_raw = content_block_match.group(1)
    # Match quoted string lines, handling inner escape codes cleanly
    line_pattern = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
    lines = [match.group(1) for match in line_pattern.finditer(content_raw)]

    # 3. Create a raw character grid initialized to baseline default terminal styles
    grid = []
    for y in range(height):
        # Fallback to spaces if the content array line doesn't completely span the terminal layout bounds
        raw_line = lines[y] if y < len(lines) else ""
        chars = list(raw_line)
        while len(chars) < width:
            chars.append(" ")

        row = []
        for x in range(width):
            row.append({
                "char": chars[x],
                "fg": "Reset",
                "bg": "Reset",
                "underline": "Reset",
                "modifier": "NONE"
            })
        grid.append(row)

    # 4. Extract and overlay the stateful sparse coordinate styles table
    styles_block_match = re.search(r'styles:\s*\[(.*?)\]', buffer_text, re.DOTALL)
    if styles_block_match:
        styles_raw = styles_block_match.group(1)
        # Regex scans coordinate blocks: x: 1, y: 8, fg: Reset, bg: Reset, underline: Reset, modifier: DIM
        style_pattern = re.compile(
            r'x:\s*(\d+),\s*y:\s*(\d+),\s*fg:\s*(\w+),\s*bg:\s*(\w+),\s*underline:\s*([\w:]+),\s*modifier:\s*(\w+)'
        )

        for match in style_pattern.finditer(styles_raw):
            sx = int(match.group(1))
            sy = int(match.group(2))
            fg = match.group(3)
            bg = match.group(4)
            underline_val = match.group(5)
            modifier = match.group(6).upper()

            # Safeguard boundaries to prevent index panic anomalies on corrupted snapshot sets
            if sy < height and sx < width:
                # Changes take effect starting from the matched coordinate moving forward to the end of the row
                for x in range(sx, width):
                    grid[sy][x]["fg"] = fg
                    grid[sy][x]["bg"] = bg
                    grid[sy][x]["underline"] = underline_val
                    grid[sy][x]["modifier"] = modifier

    print(f'grid: {grid}')
    return grid

def render_snap_to_png(buffer_text, output_png, font_path, font_size=16):
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        print("Warning: Could not find system monospace font path. Using basic fallback.")
        font = ImageFont.load_default()

    grid = parse_ratatui_buffer(buffer_text)

    # --- FALLBACK PROCESSING FOR MONOCHROME / PLAIN TEXT SNAPSHOTS ---
    if grid is None:
        lines = buffer_text.split('\n')
        clean_lines = []
        for line in lines:
            line = line.rstrip()
            if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                line = line[1:-1]
            clean_lines.append(line.rstrip())

        max_line_len = max(len(line) for line in clean_lines) if clean_lines else 0
        num_lines = len(clean_lines)

        bbox = font.getbbox("M")
        char_width = bbox[2] - bbox[0]
        char_height = int((bbox[3] - bbox[1]) * 1.4)

        padding = 30
        img_width = int(max_line_len * char_width) + (padding * 2)
        img_height = int(num_lines * char_height) + (padding * 2)

        img = Image.new("RGBA", (img_width, img_height), DEFAULT_BG)
        draw = ImageDraw.Draw(img)

        y = padding
        for line in clean_lines:
            draw.text((padding, y), line, fill=DEFAULT_FG, font=font)
            y += char_height

        img.save(output_png, "PNG")
        return
    # -----------------------------------------------------------------

    # --- STRUCTURED COLOR & MODIFIER RENDERING ---
    num_lines = len(grid)
    max_line_len = max(len(row) for row in grid) if grid else 0

    bbox = font.getbbox("M")
    char_width = bbox[2] - bbox[0]
    char_height = int((bbox[3] - bbox[1]) * 1.4)

    padding = 30
    img_width = int(max_line_len * char_width) + (padding * 2)
    img_height = int(num_lines * char_height) + (padding * 2)

    img = Image.new("RGBA", (img_width, img_height), DEFAULT_BG)
    draw = ImageDraw.Draw(img)

    y = padding
    for row in grid:
        x = padding
        for cell in row:
            char = cell["char"]
            fg_label = cell["fg"]
            bg_label = cell["bg"]
            modifier = cell["modifier"]
            underline_label = cell["underline"]

            fg_color = COLOR_PALETTE.get(fg_label, DEFAULT_FG)
            bg_color = COLOR_PALETTE.get(bg_label, None)

            # 1. Background Grid Block Fills
            if bg_color and bg_label != "Reset":
                draw.rectangle(
                    [x, y, x + char_width, y + char_height],
                    fill=bg_color
                )

            # 2. Handle Text Opacity for "DIM" layout modifier structures
            if "DIM" in modifier:
                print('found DIM')
                #fg_color_rgba = draw._get_rgba(fg_color)
                fg_color_rgba = ImageColor.getrgb(fg_color)
                # Keep original RGB channels but cut the alpha visibility channel down to 50% opacity
                if isinstance(fg_color_rgba, tuple):
                    fg_color = (fg_color_rgba[0], fg_color_rgba[1], fg_color_rgba[2], 32)
                else:
                    fg_color = (32, 32, 32, 32)

            # 3. Handle Underline Modification Pass
            if "TRUE" in underline_label.upper():
                underline_y = y + int(char_height * 0.85)
                draw.line([(x, underline_y), (x + char_width, underline_y)], fill=fg_color, width=1)

            # 4. Text Glyph Placement Pass
            draw.text((x, y), char, fill=fg_color, font=font)

            # 5. Handle Bold Double Strike Effect Simulation
            if "BOLD" in modifier:
                draw.text((x + 1, y), char, fill=fg_color, font=font)

            x += char_width
        y += char_height

    img.save(output_png, "PNG")

def make_animation():
    if len(sys.argv) < 3:
        print("Error: Missing input snapshots or output file name.")
        print("Usage: python snap_to_apng.py <input1.snap> [input2.snap ...] <output.png>")
        sys.exit(1)

    output_apng = sys.argv[-1]
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

        body = extract_clean_snap_body(snap_file)
        frame_name = f"frame_{i:03d}.png"
        render_snap_to_png(body, frame_name, font_path)
        png_frames.append(frame_name)

    if not png_frames:
        print("Error: No valid frames were generated from the input files.")
        return

    APNG.from_files(png_frames, delay=1000).save(output_apng)

    for frame in png_frames:
        os.remove(frame)

    print(f"Successfully generated APNG: {output_apng}")

if __name__ == "__main__":
    make_animation()

