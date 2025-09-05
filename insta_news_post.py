# insta_news_post.py
import telegram
import asyncio
import os
import sys
import json
from utils.news_fetcher import fetch_newapi_articles
from config import MODEL_ID
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import datetime
from llm_api.openaiAPI import call_llm
from prompts.news_analyzer_prompts import ANALYZE_NEWS_ARTICLE_PROMPT


# ---- Windows event loop policy to avoid "Event loop is closed" (Proactor) ----
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


def draw_text_with_shadow(draw, position, text, font, fill, shadow_color="black", shadow_radius=3, spacing=6):
    """
    Draws text with a thicker shadow by looping offsets around the text.
    shadow_radius controls the thickness of the shadow.
    """
    x, y = position
    # shadow (draw multiple layers)
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if dx == 0 and dy == 0:
                continue
            draw.multiline_text((x + dx, y + dy), text, font=font, fill=shadow_color, spacing=spacing)
    # main text
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=spacing)


# def create_instagram_post(post_count, news_item):
#     # Try to fetch article image
#     img = download_image(news_item.get("urlToImage", ""))
#     if img is None:
#         img = Image.new("RGB", (1080, 1080), (10, 10, 40))  # fallback plain bg

#     # Resize to Instagram square format
#     img = img.resize((1080, 1080)).convert("RGBA")

#     # Gradient overlay (darker at bottom)
#     gradient = Image.new("L", (1, img.height), color=0xFF)
#     for y in range(img.height):
#         gradient.putpixel((0, y), int(255 * (y / img.height)))  # top=transparent, bottom=dark
#     alpha_gradient = gradient.resize(img.size)
#     black_img = Image.new("RGBA", img.size, color=(0, 0, 0, 200))
#     img = Image.composite(black_img, img, alpha_gradient)

#     draw = ImageDraw.Draw(img)

#     # Load fonts (professional mix)
#     title_font = ImageFont.truetype("fonts/Montserrat/static/Montserrat-Bold.ttf", 52)
#     desc_font = ImageFont.truetype("fonts/Roboto/static/Roboto-Regular.ttf", 34)
#     footer_font = ImageFont.truetype("fonts/Montserrat/Montserrat-Italic-VariableFont_wght.ttf", 26)
#     watermark_font = ImageFont.truetype("fonts/Merriweather/Merriweather-Italic-VariableFont_opsz,wdth,wght.ttf", 26)

#     # Wrap text
#     title_text = textwrap.fill(news_item["title"], width=25)
#     desc_text = textwrap.fill(news_item.get("description", ""), width=35)

#     # Draw title with thick shadow
#     x, y = 50, 100
#     draw_text_with_shadow(draw, (x, y), title_text, title_font, fill="white", shadow_color="black", shadow_radius=4)
#     title_bbox = draw.multiline_textbbox((x, y), title_text, font=title_font, spacing=8)
#     title_height = title_bbox[3] - title_bbox[1]

#     # Draw description with slightly lighter shadow
#     y += title_height + 30
#     draw_text_with_shadow(draw, (x, y), desc_text, desc_font, fill="lightgray", shadow_color="black", shadow_radius=3)

#     # Footer
#     footer = f"Source: {news_item['source']}"
#     footer_y = img.height - 80
#     footer_x = 50
#     draw.text((footer_x, footer_y), footer, font=footer_font, fill="yellow")

#     # Watermark (bottom-right, aligned with footer)
#     watermark = "@mks_newsline"
#     wm_bbox = draw.textbbox((0, 0), watermark, font=watermark_font)
#     wm_width = wm_bbox[2] - wm_bbox[0]
#     wm_height = wm_bbox[3] - wm_bbox[1]
#     wm_x = img.width - wm_width - 40
#     wm_y = footer_y  # same vertical alignment as footer
#     draw.text((wm_x, wm_y), watermark, font=watermark_font, fill="grey")

#     # Save post
#     os.makedirs("posts", exist_ok=True)
#     filename = f"posts/post{post_count}_{news_item['source']}.png"
#     img.save(filename)
#     return filename


# def generate_caption(news_item):
#     caption = f"""📰 {news_item['title']}

#     {news_item['description']}

#     🔗 Read more: {news_item['url']}
#     📌 Source: {news_item['source']}
#     #MKSNewsline #Politics #Geopolitics #Markets
#     """
#     return caption


def create_instagram_post(post_count, news_item, analysis_result):
    """
    Create Instagram post image with highlighted analysis text only.
    analysis_result is the JSON object from LLM with "analysis" and "hashtags".
    """
    # Try to fetch article image
    img = download_image(news_item.get("urlToImage", ""))
    if img is None:
        img = Image.new("RGB", (1080, 1080), (10, 10, 40))  # fallback plain bg

    # Resize to Instagram square format
    img = img.resize((1080, 1080)).convert("RGBA")

    # Gradient overlay (darker at bottom)
    gradient = Image.new("L", (1, img.height), color=0xFF)
    for y in range(img.height):
        gradient.putpixel((0, y), int(255 * (y / img.height)))  # top=transparent, bottom=dark
    alpha_gradient = gradient.resize(img.size)
    black_img = Image.new("RGBA", img.size, color=(0, 0, 0, 200))
    img = Image.composite(black_img, img, alpha_gradient)

    draw = ImageDraw.Draw(img)

    # Load fonts
    highlight_font = ImageFont.truetype("fonts/Montserrat/static/Montserrat-Bold.ttf", 46)
    body_font = ImageFont.truetype("fonts/Roboto/static/Roboto-Regular.ttf", 34)
    footer_font = ImageFont.truetype("fonts/Montserrat/Montserrat-Italic-VariableFont_wght.ttf", 26)
    watermark_font = ImageFont.truetype("fonts/Merriweather/Merriweather-Italic-VariableFont_opsz,wdth,wght.ttf", 26)

    # Start text placement
    x, y = 50, 120  

    # Process analysis text (separate highlighted part inside {})
    analysis_text = analysis_result["analysis"]
    parts = []
    temp = ""
    in_braces = False
    for char in analysis_text:
        if char == "{":
            if temp: parts.append(("normal", temp.strip()))
            temp = ""
            in_braces = True
        elif char == "}":
            if temp: parts.append(("highlight", temp.strip()))
            temp = ""
            in_braces = False
        else:
            temp += char
    if temp:
        parts.append(("normal" if not in_braces else "highlight", temp.strip()))

    # Draw analysis text with highlight effect
    for part_type, text in parts:
        wrapped_text = textwrap.fill(text, width=35)
        if part_type == "highlight":
            draw_text_with_shadow(
                draw, (x, y), wrapped_text, highlight_font, 
                fill="yellow", shadow_color="black", shadow_radius=5
            )
        else:
            draw_text_with_shadow(
                draw, (x, y), wrapped_text, body_font, 
                fill="lightgray", shadow_color="black", shadow_radius=3
            )
        text_height = draw.multiline_textbbox(
            (x, y), wrapped_text, 
            font=(highlight_font if part_type == "highlight" else body_font), spacing=6
        )[3] - y
        y += text_height + 30

    # Footer
    footer = f"Source: {news_item['source']}"
    footer_y = img.height - 80
    footer_x = 50
    draw.text((footer_x, footer_y), footer, font=footer_font, fill="yellow")

    # Watermark
    watermark = "@mks_newsline"
    wm_bbox = draw.textbbox((0, 0), watermark, font=watermark_font)
    wm_x = img.width - wm_bbox[2] - 40
    wm_y = footer_y
    draw.text((wm_x, wm_y), watermark, font=watermark_font, fill="grey")

    # Save post
    os.makedirs("posts", exist_ok=True)
    filename = f"posts/post{post_count}_{news_item['source']}.png"
    img.save(filename)
    return filename


def generate_caption(news_item, analysis_result):
    """
    Generate Instagram caption with analysis and hashtags.
    """
    caption = f"""{analysis_result['analysis']}

🔗 Read more: {news_item['url']}
📌 Source: {news_item['source']}

{analysis_result['hashtags']}
"""
    return caption


async def main():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_NEWSBOT_TOKEN"))
    try:
        query = "BJP"
        news_data = fetch_newapi_articles(query)
        post_count = 0
        print(json.dumps(news_data, indent=2))
        for news in news_data:  # your fetched list
            analyzed_news = call_llm(ANALYZE_NEWS_ARTICLE_PROMPT,news)
            print(json.dumps(analyzed_news,indent=2))
            post_file = create_instagram_post(post_count, news, analyzed_news)
            # caption = generate_caption(news)
            break
            post_count += 1
            # cl.photo_upload(post_file, caption)
    finally:
        try:
            if hasattr(bot, "close") and callable(getattr(bot, "close")):
                await bot.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
