"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re 

from tools import search_listings, suggest_outfit, create_fit_card, compare_price


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,
        "price_comparison": None,    # result of compare_price, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """
    session = _new_session(query, wardrobe)

    # Step 2: Parse query for max_price, size, and description.
    # This is a simple regex/string parser instead of an LLM parser because the
    # starter queries are short and predictable.
    query_lower = query.lower()

    max_price = None
    price_match = re.search(r"(?:under|below|less than|\$)\s*\$?(\d+(?:\.\d+)?)", query_lower)
    if price_match:
        max_price = float(price_match.group(1))

    size = None
    size_match = re.search(r"\bsize\s+([a-z0-9/.-]+)\b", query_lower)
    if size_match:
        size = size_match.group(1).upper()

    description = query_lower

    # Remove price phrases from description.
    description = re.sub(r"(?:under|below|less than)\s*\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"\$\d+(?:\.\d+)?", "", description)

    # Remove size phrase from description.
    description = re.sub(r"\bsize\s+[a-z0-9/.-]+\b", "", description)

    # Remove common filler words.
    filler_words = [
        "looking for",
        "i am looking for",
        "i'm looking for",
        "i want",
        "find me",
        "show me",
        "please",
    ]

    for filler in filler_words:
        description = description.replace(filler, "")

    description = description.strip(" ,.-")

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    # Step 3: Search listings.
    results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )
    session["search_results"] = results

    # If no results, stop early.
    if not results:
        session["error"] = (
            "I couldn't find any listings that matched that description, size, and price. "
            "Try using a broader description, removing the size filter, or increasing your budget."
        )
        return session

    # Step 4: Select the top result.
    selected_item = results[0]
    session["selected_item"] = selected_item

    # Extra credit step: compare price.
    session["price_comparison"] = compare_price(selected_item)

    # Step 5: Suggest outfit.
    outfit_suggestion = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit_suggestion

    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = "I found an item, but I could not create an outfit suggestion."
        return session

    # Step 6: Create fit card.
    fit_card = create_fit_card(outfit_suggestion, selected_item)
    session["fit_card"] = fit_card

    if not fit_card or not fit_card.strip():
        session["error"] = "I created an outfit suggestion, but I could not create a fit card."
        return session

    # Step 7: Return completed session.
    return session



# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nPrice check: {session['price_comparison']['message']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
