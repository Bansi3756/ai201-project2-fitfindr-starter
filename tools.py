"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import random

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    try:
        listings = load_listings()
    except Exception:
        return []

    if not description:
        description = ""

    keywords = description.lower().split()
    scored_results = []

    for item in listings:
        try:
            item_price = float(item.get("price", 0))
        except (TypeError, ValueError):
            continue

        if max_price is not None and item_price > float(max_price):
            continue

        if size:
            requested_size = size.lower()
            item_size = str(item.get("size", "")).lower()

            # Allows "M" to match exact "M" or combined sizes like "S/M"
            if requested_size not in item_size:
                continue

        searchable_parts = [
            str(item.get("title", "")),
            str(item.get("description", "")),
            str(item.get("category", "")),
            str(item.get("brand", "")),
            str(item.get("platform", "")),
        ]

        style_tags = item.get("style_tags", [])
        if isinstance(style_tags, list):
            searchable_parts.extend(style_tags)
        else:
            searchable_parts.append(str(style_tags))

        colors = item.get("colors", [])
        if isinstance(colors, list):
            searchable_parts.extend(colors)
        else:
            searchable_parts.append(str(colors))

        searchable_text = " ".join(searchable_parts).lower()

        score = 0
        for keyword in keywords:
            if keyword in searchable_text:
                score += 1

        if score > 0:
            scored_results.append((score, item))

    scored_results.sort(key=lambda pair: pair[0], reverse=True)

    return [item for score, item in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    if not new_item:
        return "I need a selected thrift item before I can suggest an outfit."

    wardrobe_items = []
    if isinstance(wardrobe, dict):
        wardrobe_items = wardrobe.get("items", [])

    item_title = new_item.get("title", "this thrifted item")
    item_category = new_item.get("category", "item")
    item_colors = new_item.get("colors", [])
    item_tags = new_item.get("style_tags", [])

    color_text = ", ".join(item_colors) if isinstance(item_colors, list) else str(item_colors)
    tag_text = ", ".join(item_tags) if isinstance(item_tags, list) else str(item_tags)

    try:
        client = _get_groq_client()

        if not wardrobe_items:
            prompt = f"""
You are FitFindr, a helpful thrift styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Category: {item_category}
- Colors: {color_text}
- Style tags: {tag_text}
- Condition: {new_item.get("condition", "unknown")}

The user's wardrobe is empty or unavailable.

Suggest 1 complete outfit using general basics someone might own or buy cheaply.
Be specific and practical. Mention bottoms, shoes, layers, and the overall vibe.
Keep the answer concise.
"""
        else:
            prompt = f"""
You are FitFindr, a helpful thrift styling assistant.

The user is considering this thrifted item:
{new_item}

The user's wardrobe items are:
{wardrobe_items}

Suggest 1-2 complete outfit combinations using the thrifted item and named pieces from the wardrobe.
Be specific about bottoms, shoes, layers, colors, and styling details.
Keep the answer concise and useful.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful fashion styling assistant who gives practical outfit suggestions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        result = response.choices[0].message.content.strip()

        if result:
            return result

        return (
            f"Style {item_title} with relaxed denim, clean sneakers, and a simple jacket. "
            "Keep the colors balanced so the thrifted item stays the focus."
        )

    except Exception:
        if not wardrobe_items:
            return (
                f"Your wardrobe looks empty, so here is general styling advice: pair {item_title} "
                "with relaxed jeans, simple sneakers, and a neutral hoodie or jacket. "
                "Add one accessory, like a belt or small jewelry piece, to make it feel styled."
            )

        return (
            f"I could not generate a full outfit right now, but {item_title} would work well with "
            "neutral basics like denim, sneakers, and a simple jacket."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "I need a complete outfit suggestion before I can create a fit card."

    if not new_item:
        return "I need a selected thrift item before I can create a fit card."

    item_title = new_item.get("title", "this thrifted item")
    price = new_item.get("price", "a good price")
    platform = new_item.get("platform", "a secondhand platform")

    fallback_captions = [
        f"Found {item_title} for ${price} on {platform} and built the whole fit around it. Easy thrifted outfit with a styled, everyday vibe.",
        f"{item_title} from {platform} for ${price} is the kind of thrift find that makes the whole outfit feel intentional.",
        f"Thrifted {item_title} for ${price} on {platform}. Styled it into a simple fit that still feels put together.",
    ]

    try:
        client = _get_groq_client()

        prompt = f"""
Create a short, casual outfit caption for a thrifted fit.

Thrifted item:
- Title: {item_title}
- Price: {price}
- Platform: {platform}
- Category: {new_item.get("category", "unknown")}
- Colors: {new_item.get("colors", [])}
- Style tags: {new_item.get("style_tags", [])}

Outfit suggestion:
{outfit}

Requirements:
- 2 to 4 sentences
- Sounds like an Instagram or TikTok OOTD caption
- Mention the item name, price, and platform naturally once each
- Capture the outfit vibe in specific terms
- Do not sound like a product description
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You write casual, authentic outfit captions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=1.0,
        )

        result = response.choices[0].message.content.strip()

        if result:
            return result

        return random.choice(fallback_captions)

    except Exception:
        return random.choice(fallback_captions)


# ── Extra Credit Tool: compare_price ──────────────────────────────────────────

def compare_price(new_item: dict) -> dict:
    """
    Compare the selected item price against similar listings in the mock dataset.

    Args:
        new_item: A listing dict selected from search_listings().

    Returns:
        A dictionary with:
            status: "good deal", "fair", "overpriced", or "unknown"
            item_price: the selected item's price
            average_comparable_price: average price of similar listings, or None
            message: short explanation of the price judgment

    This tool is for the stretch feature: Price comparison tool.
    """
    if not new_item:
        return {
            "status": "unknown",
            "item_price": None,
            "average_comparable_price": None,
            "message": "I could not compare the price because no item was selected.",
        }

    try:
        item_price = float(new_item.get("price"))
    except (TypeError, ValueError):
        return {
            "status": "unknown",
            "item_price": None,
            "average_comparable_price": None,
            "message": "I could not compare the price because the selected item has no valid price.",
        }

    try:
        listings = load_listings()
    except Exception:
        return {
            "status": "unknown",
            "item_price": item_price,
            "average_comparable_price": None,
            "message": "I could not compare the price because the listing data could not be loaded.",
        }

    selected_id = new_item.get("id")
    selected_category = str(new_item.get("category", "")).lower()
    selected_brand = str(new_item.get("brand", "")).lower()

    selected_tags = new_item.get("style_tags", [])
    if not isinstance(selected_tags, list):
        selected_tags = []

    selected_colors = new_item.get("colors", [])
    if not isinstance(selected_colors, list):
        selected_colors = []

    selected_tags = {tag.lower() for tag in selected_tags if isinstance(tag, str)}
    selected_colors = {color.lower() for color in selected_colors if isinstance(color, str)}

    comparable_prices = []

    for item in listings:
        if item.get("id") == selected_id:
            continue

        score = 0

        item_category = str(item.get("category", "")).lower()
        item_brand = str(item.get("brand", "")).lower()

        if selected_category and item_category == selected_category:
            score += 2

        if selected_brand and item_brand == selected_brand:
            score += 1

        item_tags = item.get("style_tags", [])
        if not isinstance(item_tags, list):
            item_tags = []
        item_tags = {tag.lower() for tag in item_tags if isinstance(tag, str)}

        item_colors = item.get("colors", [])
        if not isinstance(item_colors, list):
            item_colors = []
        item_colors = {color.lower() for color in item_colors if isinstance(color, str)}

        if selected_tags.intersection(item_tags):
            score += 1

        if selected_colors.intersection(item_colors):
            score += 1

        if score >= 2:
            try:
                comparable_prices.append(float(item.get("price")))
            except (TypeError, ValueError):
                continue

    if len(comparable_prices) < 2:
        return {
            "status": "unknown",
            "item_price": item_price,
            "average_comparable_price": None,
            "message": "There were not enough similar listings to judge the price confidently.",
        }

    average_price = round(sum(comparable_prices) / len(comparable_prices), 2)

    if item_price <= average_price * 0.85:
        status = "good deal"
        message = (
            f"This looks like a good deal because it costs ${item_price:.2f}, "
            f"while similar items average around ${average_price:.2f}."
        )
    elif item_price >= average_price * 1.15:
        status = "overpriced"
        message = (
            f"This may be overpriced because it costs ${item_price:.2f}, "
            f"while similar items average around ${average_price:.2f}."
        )
    else:
        status = "fair"
        message = (
            f"This looks like a fair price because it costs ${item_price:.2f}, "
            f"close to the similar-item average of ${average_price:.2f}."
        )

    return {
        "status": status,
        "item_price": item_price,
        "average_comparable_price": average_price,
        "message": message,
    }
