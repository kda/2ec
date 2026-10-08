#!/home/kda/prodpy3/bin/python3

import os
import sys
import re
from PIL import Image, ImageDraw, ImageFont, ImageColor
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

def determine_global_width(snap_files):
    """
    Scans all snapshot files to determine the largest required text width boundary.
    Checks explicit 'width' keys first, falling back to counting raw line character lengths.
    """
    max_width = 40  # Hard floor default width minimum matching your layout setup
    
    for snap_file in snap_files:
        if not os.path.exists(snap_file):
            continue
        body = extract_clean_snap_body(snap_file)
        
        # Check if the snapshot defines a structural width variable block
        width_match = re.search(r'width:\s*(\d+)', body)
        if width_match:
            max_width = max(max_width, int(width_match.group(1)))
        else:
            # Otherwise, check line-by-line lengths for monochrome raw inputs
            lines = body.split('\n')
            for line in lines:
                line = line.rstrip()
                if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                    line = line[1:-1]
                max_width = max(max_width, len(line.rstrip()))
                
    return max_width

def parse_ratatui_buffer(buffer_text, target_width):
    """
    Parses a Ratatui TestBackend Buffer string layout into a structured grid.
    Pads everything smoothly out to the globally synchronized target width.
    """
    if "buffer: Buffer" not in buffer_text and "Buffer {" not in buffer_text:
        return None

    height_match = re.search(r'height:\s*(\d+)', buffer_text)
    if not height_match:
        return None
    height = int(height_match.group(1))

    # Extract the plain text lines inside the content block
    content_block_match = re.search(r'content:\s*\[(.*?)\]', buffer_text, re.DOTALL)
    if not content_block_match:
        return None
    
    content_raw = content_block_match.group(1)
    line_pattern = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
    lines = [match.group(1) for match in line_pattern.finditer(content_raw)]

    # Create character grid cleanly padded out to the target width boundary
    grid = []
    for y in range(height):
        raw_line = lines[y] if y < len(lines) else ""
        chars = list(raw_line)
        while len(chars) < target_width:
            chars.append(" ")
            
        row = []
        for x in range(target_width):
            row.append({
                "char": chars[x],
                "fg": "Reset",
                "bg": "Reset",
                "underline": "Reset",
                "modifier": "NONE"
            })
        grid.append(row)

    # Extract and overlay the stateful sparse style transitions
    styles_block_match = re.search(r'styles:\s*\[(.*?)\]', buffer_text, re.DOTALL)
    if styles_block_match:
        styles_raw = styles_block_match.group(1)
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

            if sy < height and sx < target_width:
                for x in range(sx, target_width):
                    grid[sy][x]["fg"] = fg
                    grid[sy][x]["bg"] = bg
                    grid[sy][x]["underline"] = underline_val
                    grid[sy][x]["modifier"] = modifier

    return grid

def blend_colors(fg_hex, bg_hex, alpha=0.5):
    """Blends foreground and background colors together to simulate true dimming without alpha channels."""
    fg_rgb = ImageColor.getrgb(fg_hex)
    bg_rgb = ImageColor.getrgb(bg_hex)
    return tuple(int(f * alpha + b * (1.0 - alpha)) for f, b in zip(fg_rgb, bg_rgb))

def render_snap_to_png(buffer_text, output_png, font_path, target_width, font_size=16):
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        print("Warning: Could not find system monospace font path. Using basic fallback.")
        font = ImageFont.load_default()

    grid = parse_ratatui_buffer(buffer_text, target_width)

    # --- FALLBACK PROCESSING FOR MONOCHROME / PLAIN TEXT SNAPSHOTS ---
    if grid is None:
        lines = buffer_text.split('\n')
        clean_lines = []
        for line in lines:
            line = line.rstrip()
            if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                line = line[1:-1]
            clean_lines.append(line.rstrip())

        num_lines = len(clean_lines)

        bbox = font.getbbox("M")
        char_width = bbox[2] - bbox[0]
        char_height = int((bbox[3] - bbox[1]) * 1.4)

        padding = 30
        img_width = int(target_width * char_width) + (padding * 2)
        img_height = int(num_lines * char_height) + (padding * 2)

        img = Image.new("RGBA", (img_width, img_height), DEFAULT_BG)
        draw = ImageDraw.Draw(img)

        y = padding
        for line in clean_lines:
            draw.text((padding, y), line, fill=DEFAULT_FG, font=font)
            y += char_height

        img.convert("RGBA").save(output_png, "PNG")
        return
    # -----------------------------------------------------------------

    # --- STRUCTURED COLOR & MODIFIER RENDERING ---
    num_lines = len(grid)

    bbox = font.getbbox("M")
    char_width = bbox[2] - bbox[0]
    char_height = int((bbox[3] - bbox[1]) * 1.4)

    padding = 30
    img_width = int(target_width * char_width) + (padding * 2)
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

            fg_hex = COLOR_PALETTE.get(fg_label, DEFAULT_FG)
            bg_hex = COLOR_PALETTE.get(bg_label, DEFAULT_BG) if bg_label != "Reset" else DEFAULT_BG

            # 1. Background Grid Block Fills
            if bg_label != "Reset":
                draw.rectangle([x, y, x + char_width, y + char_height], fill=bg_hex)

            # 2. Color Blending for "DIM" Modifiers
            if "DIM" in modifier:
                fg_color = blend_colors(fg_hex, bg_hex, alpha=0.5)
            else:
                fg_color = ImageColor.getrgb(fg_hex)

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

    img.convert("RGBA").save(output_png, "PNG")

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

    # Pre-scan block: Extract matching layout width boundaries dynamically
    synchronized_width = determine_global_width(snap_files)
    print(f"Synchronizing frame boundaries globally to: {synchronized_width} character columns.")

    png_frames = []
    print(f"Processing {len(snap_files)} snapshots -> Target Destination: {output_apng}")

    for i, snap_file in enumerate(snap_files):
        if not os.path.exists(snap_file):
            print(f"Skipping missing file: {snap_file}")
            continue

        body = extract_clean_snap_body(snap_file)
        frame_name = f"frame_{i:03d}.png"
        render_snap_to_png(body, frame_name, font_path, synchronized_width)
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
