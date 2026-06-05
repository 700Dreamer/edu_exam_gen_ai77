"""
nursery_images.py
Generates and caches simple black-outline clip art images for nursery exam objects.
Uses DALL-E to produce coloring-book style illustrations, cached to disk.
"""

import os
import base64
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Cache directory inside the project
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "static" / "nursery_imgs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# DALL-E prompt template — produces consistent black-and-white line art
IMAGE_PROMPT = (
    "Simple black and white line-art illustration of {object_name}. "
    "Thick continuous black outlines, pure white fill, no shading, no gradients. "
    "If the prompt describes a scene, include a simple, minimalist background to provide context. "
    "Coloring book style, educational worksheet clip-art for children. "
    "Highly consistent flat 2D style, no text, perfectly centered."
)

# Common nursery objects we pre-generate
COMMON_OBJECTS = [
    "an apple", "a ball", "a chair", "a cup", "a book",
    "a pencil", "a tree", "a flower", "a star", "an egg",
    "a tin can", "a mango", "a banana", "a cooking pot",
    "a stool", "a sweet candy", "a house", "a stick",
    "a fish", "a bird", "a cow", "a goat", "a cat", "a dog",
    "a bag", "a shoe", "a table", "a bed", "a spoon",
    "a bottle", "a drum", "a hat",
]

# Map display names → prompt-friendly names
OBJECT_NAME_MAP = {
    "apple": "an apple", "apples": "an apple",
    "ball": "a ball", "balls": "a ball",
    "chair": "a chair", "chairs": "a chair",
    "cup": "a cup", "cups": "a cup",
    "book": "a book", "books": "a book",
    "pencil": "a pencil", "pencils": "a pencil",
    "pen": "a pencil pen",
    "tree": "a tree", "trees": "a tree",
    "flower": "a flower", "flowers": "a flower",
    "star": "a star", "stars": "a star",
    "egg": "an egg", "eggs": "an egg",
    "tin": "a tin can", "tins": "a tin can",
    "mango": "a mango", "mangoes": "a mango",
    "banana": "a banana", "bananas": "a banana",
    "pot": "a cooking pot", "pots": "a cooking pot",
    "stool": "a stool", "stools": "a stool",
    "sweet": "a round sweet candy", "sweets": "a round sweet candy",
    "house": "a simple house", "houses": "a simple house",
    "stick": "a wooden stick",
    "fish": "a fish", "fishes": "a fish",
    "bird": "a bird", "birds": "a bird",
    "cow": "a cow", "cows": "a cow",
    "goat": "a goat", "goats": "a goat",
    "cat": "a cat", "cats": "a cat",
    "dog": "a dog", "dogs": "a dog",
    "bag": "a school bag", "bags": "a school bag",
    "shoe": "a shoe", "shoes": "a shoe",
    "table": "a table", "tables": "a table",
    "bed": "a bed", "beds": "a bed",
    "spoon": "a spoon", "spoons": "a spoon",
    "bottle": "a bottle", "bottles": "a bottle",
    "drum": "a drum", "drums": "a drum",
    "hat": "a hat", "hats": "a hat",
    "car": "a car", "cars": "a car",
    "bus": "a bus",
}


def _cache_key(object_name: str) -> str:
    """Return a safe filename for the object."""
    key = object_name.lower().strip().replace(" ", "_")
    key = "".join(c for c in key if c.isalnum() or c == "_")
    return key


def _cache_path(object_name: str) -> Path:
    return CACHE_DIR / f"{_cache_key(object_name)}.png"


def get_cached_b64(object_name: str) -> Optional[str]:
    """Return base64 PNG string if cached, else None."""
    path = _cache_path(object_name)
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return None


async def generate_object_image(object_name: str, client) -> Optional[str]:
    """
    Generate a DALL-E image for the object and cache it.
    Returns base64 PNG string or None on failure.
    """
    # Check cache first
    cached = get_cached_b64(object_name)
    if cached:
        return cached

    prompt_name = OBJECT_NAME_MAP.get(object_name.lower(), f"a {object_name}")
    prompt = IMAGE_PROMPT.format(object_name=prompt_name)

    try:
        response = await client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="low",
            n=1,
        )
        img_data = response.data[0]

        # gpt-image-1 returns b64_json directly
        if hasattr(img_data, "b64_json") and img_data.b64_json:
            b64 = img_data.b64_json
        elif hasattr(img_data, "url") and img_data.url:
            # Fall back: download from URL
            import urllib.request
            with urllib.request.urlopen(img_data.url) as r:
                b64 = base64.b64encode(r.read()).decode()
        else:
            return None

        # Save to cache
        path = _cache_path(object_name)
        path.write_bytes(base64.b64decode(b64))
        logger.info(f"Generated and cached image for: {object_name}")
        return b64

    except Exception as e:
        logger.warning(f"Image generation failed for '{object_name}': {e}")
        return None


async def _safe_generate(obj: str, client, timeout: int = 25) -> tuple:
    """Generate one image with a timeout. Returns (obj, b64_or_None)."""
    try:
        b64 = await asyncio.wait_for(
            generate_object_image(obj, client),
            timeout=timeout
        )
        return (obj, b64)
    except asyncio.TimeoutError:
        logger.warning(f"Image generation timed out for: {obj}")
        return (obj, None)
    except Exception as e:
        logger.warning(f"Image generation failed for '{obj}': {e}")
        return (obj, None)


async def ensure_exam_images(questions: list, client) -> dict:
    """
    Pre-generate images for all objects in the exam concurrently.
    Returns a dict mapping object_name -> base64 PNG string.
    Uses asyncio.gather so all images generate in parallel (not sequential).
    """
    needed = set()

    for q in questions:
        qtype = q.get("type", "")
        content = q.get("content", {})

        if qtype in ("count_write", "count_circle"):
            for item in (content.get("items") or []):
                pic = item.get("picture", "")
                if pic:
                    needed.add(pic.lower())
                    needed.add(pic.lower().rstrip("s"))

        elif qtype in ("match_words", "match_pictures"):
            for word in (content.get("left") or []) + (content.get("right") or []):
                w = str(word).lower()
                # Clean up AI hallucinations like "A picture of a book"
                w = w.replace("a picture of an ", "").replace("a picture of a ", "").replace("a picture of ", "").strip()
                if w:
                    needed.add(w)

        elif qtype == "draw_colour":
            for item in (content.get("items") or []):
                if isinstance(item, dict):
                    word = str(item.get("picture") or item.get("object") or "").lower()
                else:
                    word = str(item).lower()
                word = word.replace("a picture of ", "").strip()
                if word:
                    needed.add(word)

        elif qtype == "name_sets":
            for s in (content.get("sets") or []):
                obj = s.get("object", "").lower()
                if obj:
                    needed.add(obj.rstrip("s"))
                    
        elif qtype == "circle_correct":
            for opt in (content.get("options") or []):
                w = str(opt).lower().replace("a ", "").replace("an ", "").strip().split()[0]
                if w:
                    needed.add(w)

        elif qtype == "name_picture":
            for word in (content.get("words") or []):
                w = str(word).lower().replace("a ", "").replace("an ", "").strip().split()[0]
                if w:
                    needed.add(w)
            for item in (content.get("items") or []):
                if isinstance(item, dict):
                    w = str(item.get("picture") or item.get("object") or "").lower()
                else:
                    w = str(item).lower()
                w = w.replace("a ", "").replace("an ", "").strip().split(" ")[0]
                if w:
                    needed.add(w)

        elif qtype == "odd_one_out":
            for g in (content.get("groups") or []):
                for word in (g.get("words") or []):
                    w = str(word).lower().replace("a ", "").replace("an ", "").strip().split()[0]
                    if w:
                        needed.add(w)

    objects_to_generate = list(needed)

    if not objects_to_generate:
        return {}

    # Run ALL image generations with a concurrency limit to avoid rate limits
    sem = asyncio.Semaphore(5)
    
    async def _safe_generate_with_sem(obj: str):
        async with sem:
            return await _safe_generate(obj, client)
            
    tasks = [_safe_generate_with_sem(obj) for obj in objects_to_generate]
    results_list = await asyncio.gather(*tasks)

    # Build result dict with singular/plural aliases
    results = {}
    failed = []
    for obj, b64 in results_list:
        if b64:
            results[obj] = b64
            results[obj + "s"] = b64
            if obj.endswith("s"):
                results[obj[:-1]] = b64
        else:
            failed.append(obj)

    return results, failed



def img_tag(b64: str, size: int = 80) -> str:
    """Return an HTML img tag with embedded base64 PNG."""
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'width="{size}" height="{size}" '
        f'style="object-fit:contain;display:block;" />'
    )
