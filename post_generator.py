from PIL import Image, ImageDraw, ImageFont
import os
import datetime
from prompts.quote_prompt import QUOTES_PROMPT
from llm_api.openaiAPI import call_llm_text_output
from notification.telegram_msg import send_image_to_telegram

def create_quote_post(quote, output_dir="posts"):
    os.makedirs(output_dir, exist_ok=True)

    # Create a square black background (perfect for Instagram)
    img_size = 1080
    img = Image.new("RGB", (img_size, img_size), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load fonts
    font_path = "fonts/Lato-Regular.ttf"
    font_watermark_path = "fonts/Lato-Italic.ttf"

    # Dynamically shrink font size if text is long
    font_size = 50
    font_quote = ImageFont.truetype(font_path, font_size)
    max_width = int(img_size * 0.85)  # 85% of image width

    # Wrap text dynamically
    def wrap_text(text, font, max_width):
        words = text.split()
        lines, line = [], ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    # Keep reducing font size until it fits nicely
    lines = wrap_text(quote, font_quote, max_width)
    while len(lines) > 10 and font_size > 30:
        font_size -= 4
        font_quote = ImageFont.truetype(font_path, font_size)
        lines = wrap_text(quote, font_quote, max_width)

    # Measure total text height
    line_height = font_quote.getbbox("A")[3] + 20
    text_height = len(lines) * line_height
    y = (img_size - text_height) / 2

    # Draw text centered, auto-highlight the second line if it exists
    for i, line in enumerate(lines):
        w = draw.textlength(line, font=font_quote)
        x = (img_size - w) / 2
        if i == 1:  # highlight second line
            fill_color = (255, 230, 50)  # bright yellow
        else:
            fill_color = (255, 255, 255)  # white
        draw.text((x, y), line, font=font_quote, fill=fill_color)
        y += line_height

    # Add watermark dynamically near bottom
    font_watermark = ImageFont.truetype(font_watermark_path, 30)
    watermark_text = "@mksmindset"
    wm_w = draw.textlength(watermark_text, font=font_watermark)
    wm_x = (img_size - wm_w) / 2
    wm_y = img_size - (line_height // 2) - 60  # ~60px above bottom
    draw.text((wm_x, wm_y), watermark_text, font=font_watermark, fill=(180, 180, 180))

    # Save image
    filename = f"{output_dir}/quote_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    print(f"✅ Clean Instagram-style post saved: {filename}")
    return filename


print("INFO: Generating Quote...")
quote = call_llm_text_output(QUOTES_PROMPT)
print(f"INFO: {quote}")

# Example usage (second line will be auto-highlighted)
filename = create_quote_post(quote)
send_image_to_telegram(f"{filename}","Your Insta Post")

