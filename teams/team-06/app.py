"""
📰 AI Comic Strip Generator — Turn news headlines into visual stories.

Setup Instructions:
  1. Get a free HF token at https://huggingface.co/settings/tokens
  2. Create .streamlit/secrets.toml with:  hf_api_token = "hf_YOUR_TOKEN"
  3. Place news_sample.csv (columns: category, headline) in the project root.
  4. Install deps:  pip install streamlit huggingface_hub Pillow pandas
  5. Run:  python -m streamlit run app.py
"""

# ─── Imports ────────────────────────────────────────────────────────────────────
import io
import json
import random
import textwrap
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

# ─── Constants ──────────────────────────────────────────────────────────────────
TEXT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
PANEL_SIZE = 512
GRID_SIZE = PANEL_SIZE * 2  # 1024
NEGATIVE_PROMPT = "superhero, cape, mask, spandex, muscles, action pose, marvel, dc comics, batman, superman, fighting, battle, weapon, armor, ugly, deformed, blurry, low quality, bad anatomy, extra fingers, mutated hands, poorly drawn face, watermark, text, signature"
NUM_PANELS = 4
MAX_JSON_RETRIES = 2
MAX_API_RETRIES = 3
API_TIMEOUT = 30

FUN_FACTS = [
    "🎨 Did you know? Comics increase news retention by 65%!",
    "📖 The first newspaper comic strip appeared in 1895!",
    "🧠 Visual storytelling activates 7 regions of the brain simultaneously!",
]

FALLBACK_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "Politics": [
        {"dialogue": "Citizens deserve better!",
         "scene_description": "A politician speaking at a podium in a grand hall",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, a politician in a suit speaking at a podium in a grand hall, warm lighting, soft colors, clean lines, panel 1 of 4"},
        {"dialogue": "But what about the budget?",
         "scene_description": "Two politicians debating across a table with documents",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, two politicians in suits debating across a wooden table with scattered papers, indoor office, clean lines, panel 2 of 4"},
        {"dialogue": "The people have spoken!",
         "scene_description": "A crowd cheering outside a government building",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, diverse crowd cheering outside a government building with columns, daytime, clean lines, panel 3 of 4"},
        {"dialogue": "Democracy wins today.",
         "scene_description": "A sunrise over a capitol dome with flags waving",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, golden sunrise over a capitol dome with flags waving, peaceful scene, clean lines, panel 4 of 4"},
    ],
    "Science": [
        {"dialogue": "The readings are off the charts!",
         "scene_description": "A scientist in a lab coat staring at glowing monitors in a lab",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, a scientist wearing a white lab coat looking at glowing computer monitors in a modern laboratory, clean lines, panel 1 of 4"},
        {"dialogue": "We need to run it again.",
         "scene_description": "Two researchers in lab coats examining a microscope together",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, two researchers in white lab coats examining a microscope together, lab equipment around them, clean lines, panel 2 of 4"},
        {"dialogue": "Eureka! It actually works!",
         "scene_description": "A joyful scientist in a lab coat holding a glowing vial",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, a happy scientist in a white lab coat holding up a glowing test tube triumphantly, laboratory background, clean lines, panel 3 of 4"},
        {"dialogue": "This changes everything.",
         "scene_description": "Scientists presenting discovery on a large screen at a conference",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, scientists presenting at a conference with a large screen showing a discovery, audience applauding, clean lines, panel 4 of 4"},
    ],
    "Sports": [
        {"dialogue": "Game time! Let's go!",
         "scene_description": "An athlete stretching on a brightly lit field",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, an athlete in sports uniform stretching on a green field in a bright stadium, clean lines, panel 1 of 4"},
        {"dialogue": "That was an incredible play!",
         "scene_description": "A player in sports gear scoring a goal in a stadium",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, a soccer player in jersey scoring a goal in a packed stadium, fans cheering, clean lines, panel 2 of 4"},
        {"dialogue": "The crowd goes wild!",
         "scene_description": "Fans in the stands cheering and waving banners",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, enthusiastic fans cheering and waving banners in stadium stands, confetti falling, clean lines, panel 3 of 4"},
        {"dialogue": "Champions at last!",
         "scene_description": "A sports team lifting a trophy on a podium with fireworks",
         "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, a sports team in uniforms lifting a golden trophy on a podium, fireworks in the sky, clean lines, panel 4 of 4"},
    ],
}

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Comic Strip Generator",
    page_icon="📰",
    layout="centered",
)

# ─── CSS Styling ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Inter:wght@400;600&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    .main-title {
        font-family: 'Bangers', cursive;
        font-size: 3.2rem;
        text-align: center;
        background: linear-gradient(90deg, #f7971e, #ffd200, #f7971e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 3px;
        margin-bottom: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .sub-caption {
        text-align: center;
        color: #b8b8d0;
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        margin-top: -8px;
        margin-bottom: 24px;
    }

    .comic-container {
        background: white;
        border-radius: 16px;
        padding: 12px;
        box-shadow: 0 8px 32px rgba(247, 151, 30, 0.25), 0 0 0 3px #f7971e;
        margin: 16px auto;
    }

    .stDownloadButton > button {
        background: linear-gradient(90deg, #f7971e, #ffd200) !important;
        color: #1a1a2e !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        transition: transform 0.15s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: scale(1.04) !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e0ff !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── API Helpers ────────────────────────────────────────────────────────────────
def setup_hf_client() -> InferenceClient:
    """Read HF token from Streamlit secrets and return an InferenceClient."""
    try:
        token = st.secrets["hf_api_token"]
    except (KeyError, FileNotFoundError):
        st.error(
            "🔑 **Hugging Face token not found!**\n\n"
            "Create `.streamlit/secrets.toml` with:\n```\nhf_api_token = \"hf_YOUR_TOKEN\"\n```"
        )
        st.stop()

    if not token or token == "your_huggingface_token_here":
        st.error(
            "🔑 **Please replace the placeholder in `.streamlit/secrets.toml` "
            "with your actual Hugging Face API token.**\n\n"
            "Get one free at https://huggingface.co/settings/tokens"
        )
        st.stop()

    return InferenceClient(token=token, timeout=API_TIMEOUT)


def query_text_api(
    client: InferenceClient,
    prompt: str,
) -> Optional[str]:
    """
    Call the HF text model via chat completions with retry logic.
    Returns the generated text or None on failure.
    """
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            response = client.chat_completion(
                model=TEXT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a newspaper comic strip writer. You ONLY output valid JSON. No extra text. "
                            "IMPORTANT: Your image prompts must describe REALISTIC scenes with NORMAL PEOPLE "
                            "(scientists in lab coats, politicians in suits, athletes in sports uniforms). "
                            "NEVER use superhero imagery, capes, masks, or action-hero poses. "
                            "Use the style prefix: 'high quality cartoon illustration, modern editorial comic style, detailed, professional artwork'. "
                            "Include specific details about facial expressions, body language, environment, and lighting. "
                            "Make each panel visually distinct with different camera angles and compositions."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.7,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "loading" in error_msg.lower():
                wait = 2 ** attempt + random.random()
                st.warning(
                    f"⏳ Model is loading… retrying in {wait:.0f}s "
                    f"(attempt {attempt}/{MAX_API_RETRIES})"
                )
                time.sleep(wait)
            elif "429" in error_msg or "rate" in error_msg.lower():
                wait = 5 * attempt
                st.warning(
                    f"⚠️ Rate limited — waiting {wait}s before retry "
                    f"(attempt {attempt}/{MAX_API_RETRIES})"
                )
                time.sleep(wait)
            else:
                st.warning(
                    f"⚠️ API error (attempt {attempt}/{MAX_API_RETRIES}): {error_msg[:150]}"
                )
                time.sleep(2 ** attempt)

    st.error("❌ All retry attempts exhausted for text generation. Please try again in a minute.")
    return None


def query_image_api(
    client: InferenceClient,
    prompt: str,
) -> Optional[Image.Image]:
    """
    Call the HF image model via text_to_image with retry logic.
    Returns a PIL Image or None on failure.
    """
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            img = client.text_to_image(
                prompt=prompt,
                model=IMAGE_MODEL,
                negative_prompt=NEGATIVE_PROMPT,
            )
            return img

        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "loading" in error_msg.lower():
                wait = 2 ** attempt + random.random()
                st.warning(
                    f"⏳ Image model loading… retrying in {wait:.0f}s "
                    f"(attempt {attempt}/{MAX_API_RETRIES})"
                )
                time.sleep(wait)
            elif "429" in error_msg or "rate" in error_msg.lower():
                wait = 5 * attempt
                st.warning(
                    f"⚠️ Rate limited — waiting {wait}s before retry "
                    f"(attempt {attempt}/{MAX_API_RETRIES})"
                )
                time.sleep(wait)
            else:
                st.warning(
                    f"⚠️ Image API error (attempt {attempt}/{MAX_API_RETRIES}): {error_msg[:150]}"
                )
                time.sleep(2 ** attempt)

    st.error("❌ All retry attempts exhausted for image generation.")
    return None


# ─── Data Loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_news_data(path: str = "news_sample.csv") -> pd.DataFrame:
    """Load and validate news_sample.csv."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        st.error(
            "📄 **news_sample.csv not found!**\n\n"
            "Place a CSV with columns `category` and `headline` in the project root."
        )
        st.stop()

    # Validate required columns
    missing = {"category", "headline"} - set(df.columns)
    if missing:
        st.error(
            f"📄 **news_sample.csv is missing columns:** `{'`, `'.join(missing)}`\n\n"
            "Required columns: `category`, `headline`"
        )
        st.stop()

    df = df.dropna(subset=["category", "headline"])
    return df


# ─── LLM Script Generation ─────────────────────────────────────────────────────
def get_comic_prompt(headline: str) -> str:
    """Build the LLM prompt for generating a 4-panel comic script as JSON."""
    return f"""Create a 4-panel comic from this news headline.
IMPORTANT RULES FOR IMAGE PROMPTS:
- Style must be "cartoon illustration, newspaper editorial style"
- First, define ONE main character profile (e.g., "Raj, 25yo, wearing a red and black sports jersey, short hair").
- YOU MUST COPY THIS EXACT CHARACTER DESCRIPTION INTO EVERY 'stable_diffusion_image_prompt'.
- NEVER include superheroes, capes, masks, or action-hero imagery
- Describe the actual scene setting, clothing, and environment in detail

OUTPUT MUST BE VALID JSON WITH EXACTLY THIS STRUCTURE (NO OTHER TEXT):
{{
  "main_character_profile": "Detailed physical description and clothing of the main character",
  "panels": [
    {{
      "dialogue": "Short character speech (max 12 words)",
      "scene_description": "Visual setting with realistic characters (max 18 words)",
      "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, [INSERT MAIN CHARACTER PROFILE HERE], [describe scene], soft colors, panel 1 of 4"
    }},
    {{
      "dialogue": "Short character speech (max 12 words)",
      "scene_description": "Visual setting with realistic characters (max 18 words)",
      "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, [INSERT MAIN CHARACTER PROFILE HERE], [describe scene], soft colors, panel 2 of 4"
    }},
    {{
      "dialogue": "Short character speech (max 12 words)",
      "scene_description": "Visual setting with realistic characters (max 18 words)",
      "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, [INSERT MAIN CHARACTER PROFILE HERE], [describe scene], soft colors, panel 3 of 4"
    }},
    {{
      "dialogue": "Short character speech (max 12 words)",
      "scene_description": "Visual setting with realistic characters (max 18 words)",
      "stable_diffusion_image_prompt": "Cartoon illustration, newspaper editorial style, [INSERT MAIN CHARACTER PROFILE HERE], [describe scene], soft colors, panel 4 of 4"
    }}
  ]
}}
Headline: "{headline}"
4-panel comic JSON:"""


def validate_comic_json(data: Any) -> Optional[List[Dict[str, str]]]:
    """Return a list of 4 panel dicts if valid, else None."""
    if not isinstance(data, dict):
        return None
    panels = data.get("panels")
    if not isinstance(panels, list) or len(panels) != 4:
        return None
    required_keys = {"dialogue", "scene_description", "stable_diffusion_image_prompt"}
    for p in panels:
        if not isinstance(p, dict) or not required_keys.issubset(p.keys()):
            return None
    return panels


def extract_json_from_text(text: str) -> Optional[dict]:
    """Try to pull a JSON object from potentially noisy LLM output."""
    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strategy 2: find the first { … } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


def generate_comic_script(
    headline: str,
    category: str,
    client: InferenceClient,
) -> List[Dict[str, str]]:
    """
    Ask the LLM for a 4-panel comic script.
    Re-prompts up to MAX_JSON_RETRIES times on invalid JSON, then falls back.
    """
    prompt_text = get_comic_prompt(headline)

    for attempt in range(MAX_JSON_RETRIES + 1):
        raw_text = query_text_api(client, prompt_text)
        if raw_text is None:
            continue

        parsed = extract_json_from_text(raw_text)
        if parsed:
            panels = validate_comic_json(parsed)
            if panels:
                return panels

        if attempt < MAX_JSON_RETRIES:
            st.info(f"🔄 LLM output wasn't valid JSON — retrying ({attempt + 1}/{MAX_JSON_RETRIES})…")

    # Fallback
    st.warning("⚠️ Using pre-built template — the LLM didn't produce valid JSON this time.")
    fallback_key = category if category in FALLBACK_TEMPLATES else "Science"
    return FALLBACK_TEMPLATES[fallback_key]


# ─── Image Generation & Pillow Rendering ────────────────────────────────────────
def generate_placeholder_image() -> Image.Image:
    """Create a simple placeholder when image generation fails."""
    img = Image.new("RGB", (PANEL_SIZE, PANEL_SIZE), color=(45, 45, 70))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    text = "[ Panel unavailable ]"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (PANEL_SIZE - tw) // 2
    y = (PANEL_SIZE - th) // 2
    draw.text((x, y), text, fill=(180, 180, 200), font=font)
    return img


def resize_and_crop(img: Image.Image, target: int = PANEL_SIZE) -> Image.Image:
    """Resize maintaining aspect ratio, then center-crop to target x target."""
    w, h = img.size
    scale = target / min(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target) // 2
    top = (new_h - target) // 2
    return img.crop((left, top, left + target, top + target))


def overlay_dialogue(img: Image.Image, dialogue: str) -> Image.Image:
    """Draw a classic comic book speech bubble with a tail."""
    img = img.copy()
    draw = ImageDraw.Draw(img)

    # Use a readable font
    font = ImageFont.load_default(size=20)
    font_small = ImageFont.load_default(size=16)

    if len(dialogue) > 60:
        active_font = font_small
        max_chars = 35
        line_height = 20
    else:
        active_font = font
        max_chars = 25
        line_height = 24

    wrapped = textwrap.fill(dialogue, width=max_chars)
    lines = wrapped.split("\n")

    padding_x = 20
    padding_y = 15
    
    max_line_width = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=active_font)
        max_line_width = max(max_line_width, bbox[2] - bbox[0])
        
    text_width = max_line_width
    text_height = line_height * len(lines)
    
    bubble_width = text_width + (padding_x * 2)
    bubble_height = text_height + (padding_y * 2)
    
    # Position bubble at the top center of the panel
    x1 = (PANEL_SIZE - bubble_width) // 2
    y1 = 20  # offset from top
    x2 = x1 + bubble_width
    y2 = y1 + bubble_height
    
    # Draw bubble background with rounded corners and outline
    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=20,
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=3
    )
    
    # Draw tail (polygon) pointing down and slightly left
    tail_width = 20
    tail_height = 25
    tail_x_start = x1 + (bubble_width // 2) - 10
    
    tail_points = [
        (tail_x_start, y2 - 2),  # Top left of tail (overlapping outline slightly)
        (tail_x_start + tail_width, y2 - 2), # Top right of tail
        (tail_x_start - 10, y2 + tail_height) # Bottom point
    ]
    
    # Draw tail background
    draw.polygon(tail_points, fill=(255, 255, 255, 255))
    
    # Draw tail outline (V shape)
    draw.line([(tail_x_start, y2 - 2), (tail_x_start - 10, y2 + tail_height)], fill=(0, 0, 0, 255), width=3)
    draw.line([(tail_x_start + tail_width, y2 - 2), (tail_x_start - 10, y2 + tail_height)], fill=(0, 0, 0, 255), width=3)

    # Draw text
    y_text = y1 + padding_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=active_font)
        tw = bbox[2] - bbox[0]
        x_text = x1 + (bubble_width - tw) // 2
        
        # Main black text
        draw.text((x_text, y_text + (i * line_height)), line, fill=(0, 0, 0, 255), font=active_font)

    return img


def stitch_grid(panels: List[Image.Image]) -> Image.Image:
    """Arrange 4 panels in a 2x2 grid with a thin border."""
    border = 4
    grid = Image.new("RGB", (GRID_SIZE + border, GRID_SIZE + border), color=(255, 255, 255))
    positions = [
        (0, 0),
        (PANEL_SIZE + border, 0),
        (0, PANEL_SIZE + border),
        (PANEL_SIZE + border, PANEL_SIZE + border),
    ]
    for img, (x, y) in zip(panels, positions):
        grid.paste(img, (x, y))
    return grid


def image_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ─── Main App ───────────────────────────────────────────────────────────────────
def main() -> None:
    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown('<h1 class="main-title">📰 AI Comic Strip Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-caption">Turn news into visual stories — powered by Llama 3 &amp; Stable Diffusion XL</p>', unsafe_allow_html=True)

    # ── Setup ───────────────────────────────────────────────────────────────
    client = setup_hf_client()
    df = load_news_data()

    # ── Sidebar ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🗂️ News Selection")
        categories = sorted(df["category"].unique().tolist())

        if not categories:
            st.warning("No categories found in the dataset.")
            st.stop()

        selected_category = st.selectbox(
            "Category",
            options=categories,
            index=0,
            key="category_select",
        )

        input_method = st.radio(
            "Headline Source",
            options=["Select from Dataset", "Write Custom Headline"],
            key="input_method"
        )

        if input_method == "Select from Dataset":
            filtered = df[df["category"] == selected_category]["headline"].tolist()

            if not filtered:
                st.warning(f"No headlines found for **{selected_category}**.")
                with st.expander("ℹ️ Setup Instructions", expanded=True):
                    st.markdown(
                        "Ensure `news_sample.csv` has rows with this category.\n\n"
                        "Required columns: `category`, `headline`"
                    )
                st.stop()

            selected_headline = st.selectbox(
                "Headline",
                options=filtered,
                index=0,
                key="headline_select",
            )
        else:
            selected_headline = st.text_area(
                "Custom Headline",
                placeholder="e.g., Local hackathon team wins 1st place with GenAI comic app!",
                key="custom_headline"
            )

        st.markdown("---")
        generate_btn = st.button(
            "🎨 Generate Comic",
            type="primary",
            use_container_width=True,
            key="generate_btn",
        )

        st.markdown("---")
        with st.expander("ℹ️ How it works"):
            st.markdown(
                "1. Select a **category** and **headline**.\n"
                "2. Click **Generate Comic**.\n"
                "3. The AI writes a 4-panel script (Llama 3).\n"
                "4. Each panel is illustrated (Stable Diffusion XL).\n"
                "5. Dialogue is overlaid and panels are stitched into a comic strip!"
            )

    # ── Generation ──────────────────────────────────────────────────────────
    if generate_btn:
        if not selected_headline or not selected_headline.strip():
            st.error("❌ Please enter a headline to generate a comic.")
            st.stop()
            
        fun_fact = random.choice(FUN_FACTS)
        with st.spinner(f"Creating your comic…  \n*{fun_fact}*"):
            # Step 1 — Script
            st.info("✍️ **Step 1/2** — Writing comic script…")
            panels_data = generate_comic_script(
                selected_headline, selected_category, client
            )

            # Step 2 — Images
            st.info("🖼️ **Step 2/2** — Generating panel images…")
            progress = st.progress(0, text="Generating panels…")
            panel_images: List[Image.Image] = []

            for idx, panel in enumerate(panels_data):
                progress.progress(
                    (idx) / NUM_PANELS,
                    text=f"Generating panel {idx + 1}/{NUM_PANELS}…",
                )
                img = query_image_api(client, panel["stable_diffusion_image_prompt"])
                if img is None:
                    st.warning(f"Panel {idx + 1} generation failed — using placeholder.")
                    img = generate_placeholder_image()

                img = resize_and_crop(img)
                img = overlay_dialogue(img, panel["dialogue"])
                panel_images.append(img)

            progress.progress(1.0, text="✅ All panels generated!")
            time.sleep(0.3)
            progress.empty()

        # ── Display Result ──────────────────────────────────────────────────
        grid = stitch_grid(panel_images)
        grid_bytes = image_to_bytes(grid)

        st.markdown("---")
        st.markdown(
            '<div class="comic-container">',
            unsafe_allow_html=True,
        )
        st.image(grid, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="⬇️ Download Comic (PNG)",
                data=grid_bytes,
                file_name="comic_strip.png",
                mime="image/png",
                use_container_width=True,
                key="download_btn",
            )

        with st.expander("📜 View Generated Script"):
            st.json({"panels": panels_data})

    else:
        # Landing state
        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; padding:60px 20px; color:#b8b8d0;'>"
            "<p style='font-size:3rem; margin-bottom:8px;'>🎬</p>"
            "<p style='font-size:1.15rem;'>Select a headline from the sidebar and click "
            "<strong>Generate Comic</strong> to begin!</p></div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
