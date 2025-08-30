from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import cairosvg  # <--- pip install cairosvg
from prompts.quote_prompt import QUOTES_PROMPT
from llm_api.openaiAPI import call_llm_text_output
from notification.telegram_msg import send_image_to_telegram


def create_quote_post(quote, output_dir="posts", logo_path="logos/ai_robo_logo.png"):
    os.makedirs(output_dir, exist_ok=True)

    # Create background
    img_size = 1080
    img = Image.new("RGB", (img_size, img_size), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    font_path = "fonts/Lato-Regular.ttf"
    font_watermark_path = "fonts/Lato-Italic.ttf"
    font_size = 50
    font_quote = ImageFont.truetype(font_path, font_size)
    max_width = int(img_size * 0.85)  # 85% of image width

    # --- Step 0: Add Small Logo + "AI speaking" ---
    logo_bottom = 120  # default top margin
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")

        # Make logo small (like watermark)
        logo_width = int(img_size * 0.10)  # ~12% of canvas
        aspect_ratio = logo.height / logo.width
        logo_height = int(logo_width * aspect_ratio)
        logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

        # Position top center
        logo_x = (img_size - logo_width) // 2
        logo_y = 100
        img.paste(logo, (logo_x, logo_y), logo)

        # Add small text beneath logo
        font_small = ImageFont.truetype(font_watermark_path, 24)
        caption = "AI speaking"
        cap_w = draw.textlength(caption, font=font_small)
        cap_x = (img_size - cap_w) // 2
        cap_y = logo_y + logo_height + 5
        draw.text((cap_x, cap_y), caption, font=font_small, fill=(180, 180, 180))

        logo_bottom = cap_y + 60  # leave space after caption

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

    # --- Step 1: Detect highlight before wrapping ---
    raw_lines = quote.split("\n")

    def process_lines(font):
        processed_lines = []
        highlight_flags = []
        for rl in raw_lines:
            rl = rl.strip()
            highlight = False
            if rl.startswith("{") and rl.endswith("}"):
                rl = rl[1:-1]  # remove braces
                highlight = True

            wrapped = wrap_text(rl, font, max_width)
            processed_lines.extend(wrapped)
            highlight_flags.extend([highlight] * len(wrapped))
        return processed_lines, highlight_flags

    processed_lines, highlight_flags = process_lines(font_quote)

    # --- Step 2: Adjust font size if text is too long ---
    while len(processed_lines) > 10 and font_size > 30:
        font_size -= 4
        font_quote = ImageFont.truetype(font_path, font_size)
        processed_lines, highlight_flags = process_lines(font_quote)

    # --- Step 3: Center text vertically (but push below logo) ---
    line_height = font_quote.getbbox("A")[3] + 20
    text_height = len(processed_lines) * line_height
    y = max((img_size - text_height) / 2, logo_bottom)

    # --- Step 4: Draw text with highlight ---
    for line, highlight in zip(processed_lines, highlight_flags):
        w = draw.textlength(line, font=font_quote)
        x = (img_size - w) / 2
        fill_color = (255, 230, 50) if highlight else (255, 255, 255)  # Yellow or White
        draw.text((x, y), line, font=font_quote, fill=fill_color)
        y += line_height

    # --- Step 5: Add watermark ---
    font_watermark = ImageFont.truetype(font_watermark_path, 30)
    watermark_text = "@mksmindset"
    wm_w = draw.textlength(watermark_text, font=font_watermark)
    wm_x = (img_size - wm_w) / 2
    wm_y = img_size - (line_height // 2) - 60  # ~60px above bottom
    draw.text((wm_x, wm_y), watermark_text, font=font_watermark, fill=(180, 180, 180))

    # --- Step 6: Save image ---
    filename = f"{output_dir}/quote_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    print(f"✅ Post with small logo + caption saved: {filename}")
    return filename


if __name__ == "__main__":
    # print("INFO: Generating Quote...")
    # quote = call_llm_text_output(QUOTES_PROMPT)
    # print(f"INFO: {quote}")

    quote = """You think you need clarity, but you're avoiding the decision.
No one is coming to fix it, including future you.
{Action beats intention, every boring day.}"""

    # Generate post with highlighted impactful line and logo
    filename = create_quote_post(quote)
    # send_image_to_telegram(f"{filename}", "Your Insta Post")
