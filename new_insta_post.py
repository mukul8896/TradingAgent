# insta_news_post.py
import telegram
import asyncio
import os
import sys
import json
from utils.news_fetcher import fetch_newapi_articles
from config import MODEL_ID
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import textwrap
from llm_api.openaiAPI import call_llm
from prompts.news_analyzer_prompts import ANALYZE_NEWS_ARTICLE_PROMPT


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def download_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print("Error downloading image:", e)
    return None


def draw_text_with_shadow(draw, position, text, font, fill,
                         shadow_color="black", shadow_radius=3, spacing=0):
    """Draws text with a thicker shadow."""
    x, y = position
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if dx == 0 and dy == 0:
                continue
            draw.multiline_text((x + dx, y + dy), text, font=font,
                                fill=shadow_color, spacing=spacing)
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=spacing)


def draw_paragraph_with_highlights(draw, parts, x_start, y_start,
                                   max_width, base_font, highlight_font,
                                   line_spacing=8, normal_color="white", highlight_color="yellow"):
    """
    Draws continuous paragraph with inline highlighting and wrapping.
    `parts` is a list of (type, text).
    """
    x, y = x_start, y_start
    space_width = draw.textlength(" ", font=base_font)
    line_height = max(base_font.size, highlight_font.size)

    words = []
    for part_type, text in parts:
        font = highlight_font if part_type == "highlight" else base_font
        color = highlight_color if part_type == "highlight" else normal_color
        for w in text.split():
            words.append((w, font, color))

    for word, font, color in words:
        word_width = draw.textlength(word, font=font)
        if x + word_width > x_start + max_width:
            x = x_start
            y += line_height + line_spacing

        draw_text_with_shadow(draw, (x, y), word, font, fill=color,
                              shadow_color="black", shadow_radius=3)
        x += word_width + space_width

    return y + line_height


def create_instagram_post(post_count, news_item, analysis_result):
    img_width, img_height = 1080, 1080
    image_portion_target_height = int(img_height * 0.55) # Top half height
    bluish_color = (10, 10, 40) # Solid bluish color for background
    
    # Start with a solid bluish background for the entire post
    final_img = Image.new("RGBA", (img_width, img_height), bluish_color + (255,))

    article_img_original = download_image(news_item.get("urlToImage", ""))
    
    img_paste_x = 0
    img_paste_y = 0
    current_image_height = 0

    if article_img_original:
        original_width, original_height = article_img_original.size
        
        # Calculate new dimensions to fit height while maintaining aspect ratio
        # and centering horizontally
        ratio = min(img_width / original_width, image_portion_target_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        article_img = article_img_original.resize((new_width, new_height)).convert("RGBA")
        
        img_paste_x = (img_width - new_width) // 2 # Center horizontally
        current_image_height = new_height
    else:
        # Fallback if no image is downloaded
        article_img = Image.new("RGBA", (img_width, image_portion_target_height), bluish_color + (255,))
        current_image_height = image_portion_target_height

    # Paste the (potentially scaled and centered) article image
    final_img.paste(article_img, (img_paste_x, img_paste_y))

    # --- Create Cloud-like Frame for Sides ---
    cloud_blur_radius = 40 # Increased blur for softer clouds
    
    # Left side cloud
    if img_paste_x > 0: # Only if there's space on the left
        left_matte = Image.new('L', (img_paste_x, current_image_height), 0)
        draw_left_cloud = ImageDraw.Draw(left_matte)
        # Draw some overlapping ellipses for a cloud shape at the right edge of this matte
        draw_left_cloud.ellipse([-img_paste_x, 0, img_paste_x + 50, current_image_height + 50], fill=255)
        left_matte = left_matte.filter(ImageFilter.GaussianBlur(radius=cloud_blur_radius))
        
        left_overlay_color = Image.new("RGBA", (img_paste_x, current_image_height), bluish_color + (255,))
        left_overlay_color.putalpha(left_matte)
        final_img.alpha_composite(left_overlay_color, (0, 0))

    # Right side cloud
    right_side_width = img_width - (img_paste_x + article_img.width)
    if right_side_width > 0: # Only if there's space on the right
        right_matte = Image.new('L', (right_side_width, current_image_height), 0)
        draw_right_cloud = ImageDraw.Draw(right_matte)
        # Draw some overlapping ellipses for a cloud shape at the left edge of this matte
        draw_right_cloud.ellipse([-50, 0, right_side_width + 50, current_image_height + 50], fill=255)
        right_matte = right_matte.filter(ImageFilter.GaussianBlur(radius=cloud_blur_radius))

        right_overlay_color = Image.new("RGBA", (right_side_width, current_image_height), bluish_color + (255,))
        right_overlay_color.putalpha(right_matte)
        final_img.alpha_composite(right_overlay_color, (img_paste_x + article_img.width, 0))

    # --- Create Cloud-like Frame for Bottom Transition ---
    transition_zone_height = int(img_height * 0.25) 
    # This cloud starts where the image ends, and goes into the bluish background below
    transition_start_y = current_image_height - transition_zone_height // 2 # Cloud starts slightly into the image
    if transition_start_y < 0: transition_start_y = 0 # Ensure it doesn't go above image

    bottom_cloud_matte = Image.new('L', (img_width, transition_zone_height), 0) 
    draw_bottom_cloud = ImageDraw.Draw(bottom_cloud_matte)

    # Draw cloud shape for the bottom, ensure it covers the width
    draw_bottom_cloud.ellipse([-100, 0, img_width + 100, transition_zone_height + 50], fill=255) # Large ellipse for a wide cloud base
    draw_bottom_cloud.ellipse([img_width // 4, -50, img_width * 3 // 4, transition_zone_height + 80], fill=255) # A central hump
    
    bottom_cloud_matte = bottom_cloud_matte.filter(ImageFilter.GaussianBlur(radius=cloud_blur_radius))

    bottom_cloud_overlay_color = Image.new("RGBA", (img_width, transition_zone_height), bluish_color + (255,))
    bottom_cloud_overlay_color.putalpha(bottom_cloud_matte)

    final_img.alpha_composite(bottom_cloud_overlay_color, (0, transition_start_y))
    # --- End Cloud-like Frame ---


    draw = ImageDraw.Draw(final_img)

    # fonts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    base_font_path = os.path.join(base_dir, "fonts", "Roboto", "static", "Roboto-Regular.ttf")
    highlight_font_path = os.path.join(base_dir, "fonts", "Roboto", "static", "Roboto-Bold.ttf")
    watermark_font_path = os.path.join(base_dir, "fonts", "Roboto", "static", "Roboto-Bold.ttf")
    heading_font_path = os.path.join(base_dir, "fonts", "Roboto", "static", "Roboto-Bold.ttf")
    emoji_font_path = os.path.join(base_dir, "fonts", "NotoColorEmoji.ttf") 

    watermark_font_size = 24
    heading_font_size = 40
    try:
        base_font = ImageFont.truetype(base_font_path, 20)
        highlight_font = ImageFont.truetype(highlight_font_path, 20)
        watermark_font = ImageFont.truetype(watermark_font_path, watermark_font_size)
        heading_font = ImageFont.truetype(heading_font_path, heading_font_size)
        try:
            emoji_font = ImageFont.truetype(emoji_font_path, watermark_font_size)
        except IOError:
            print(f"Warning: Emoji font '{emoji_font_path}' not found. Using watermark_font for globe.")
            emoji_font = watermark_font 
    except IOError as e:
        print(f"Warning: Font file not found. {e}")
        base_font = ImageFont.load_default()
        highlight_font = ImageFont.load_default()
        watermark_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        emoji_font = ImageFont.load_default()

    # watermark + globe icon
    watermark_text = "@mks_newslines"
    globe_icon = "🌎"
    
    wm_text_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
    wm_text_width = wm_text_bbox[2] - wm_text_bbox[0]
    wm_text_height = wm_text_bbox[3] - wm_text_bbox[1]

    globe_bbox = draw.textbbox((0, 0), globe_icon, font=emoji_font)
    globe_width = globe_bbox[2] - globe_bbox[0]
    globe_height = globe_bbox[3] - globe_bbox[1]

    spacing_between_icon_text = 10
    total_wm_width = globe_width + spacing_between_icon_text + wm_text_width
    
    wm_x_start_group = (img_width - total_wm_width) // 2
    # Adjust y_start for watermark to be relative to the bottom of the article image / start of the cloud frame
    wm_y_start = current_image_height - (transition_zone_height // 2) + 10 
    if wm_y_start < current_image_height: wm_y_start = current_image_height + 10 # Ensure watermark isn't over image

    draw_text_with_shadow(draw, (wm_x_start_group, wm_y_start + (wm_text_height - globe_height) // 2), 
                          globe_icon, emoji_font,
                          fill="white", shadow_color="black", shadow_radius=2)
    
    wm_x_start_text = wm_x_start_group + globe_width + spacing_between_icon_text
    wm_y_start_text = wm_y_start
    
    draw_text_with_shadow(draw, (wm_x_start_text, wm_y_start_text),
                          watermark_text, watermark_font,
                          fill="white", shadow_color="black", shadow_radius=2)

    # news content
    padding = 30
    x_start = padding
    y_current = wm_y_start + max(globe_height, wm_text_height) + 30
    max_text_width = img_width - 2 * padding
    
    # Draw heading
    heading_text = analysis_result["heading"]
    draw_text_with_shadow(draw, (x_start, y_current), heading_text, heading_font,
                          fill="yellow", shadow_color="black", shadow_radius=3)
    
    y_current += draw.textbbox((0, 0), heading_text, font=heading_font)[3] - draw.textbbox((0, 0), heading_text, font=heading_font)[1] + 30
    
    # Draw pointers
    for pointer in analysis_result["pointers"]:
        parts = []
        temp, in_braces = "", False
        for char in pointer:
            if char == "{":
                if temp: parts.append(("normal", temp.strip()))
                temp, in_braces = "", True
            elif char == "}":
                if temp: parts.append(("highlight", temp.strip()))
                temp, in_braces = "", False
            else:
                temp += char
        if temp:
            parts.append(("highlight" if in_braces else "normal", temp.strip()))
            
        draw_text_with_shadow(draw, (x_start, y_current), "•", base_font,
                              fill="white", shadow_color="black", shadow_radius=2)
                              
        y_current = draw_paragraph_with_highlights(
            draw, parts, x_start + 20, y_current, max_text_width - 20,
            base_font, highlight_font, line_spacing=10
        )
        y_current += 10

    os.makedirs("posts", exist_ok=True)
    filename = f"posts/post{post_count}_{news_item['source']}.png"
    final_img.save(filename)
    return filename


def generate_caption(news_item, analysis_result):
    pointers_text = "\n".join([f"• {p}" for p in analysis_result['pointers']])
    
    return f"""{analysis_result['heading']}
    
{pointers_text}

🔗 Read more: {news_item['url']}
📌 Source: {news_item['source']}

{analysis_result['hashtags']}
"""


async def main():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_NEWSBOT_TOKEN"))
    try:
        query = "Bihar Election"
        news_data = fetch_newapi_articles(query)
        post_count = 0
        print(json.dumps(news_data, indent=2))
        for news in news_data:
            analyzed_news = call_llm(ANALYZE_NEWS_ARTICLE_PROMPT, news)
            post_file = create_instagram_post(post_count, news, analyzed_news)
            break
            post_count += 1
    finally:
        try:
            if hasattr(bot, "close") and callable(getattr(bot, "close")):
                await bot.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())