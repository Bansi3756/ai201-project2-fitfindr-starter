"""
app.py

Gradio interface for FitFindr. The layout and wiring are already set up —
your job is to fill in handle_query() so it calls run_agent() and maps
the session results to the three output panels.

Run with:
    python app.py

Then open the localhost URL shown in your terminal (usually http://localhost:7860,
but check your terminal — the port may differ).
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    if not user_query or not user_query.strip():
        return "Please enter a search query first.", "", ""

    if wardrobe_choice == "Empty wardrobe (new user)":
        wardrobe = get_empty_wardrobe()
    else:
        wardrobe = get_example_wardrobe()

    session = run_agent(
        query=user_query,
        wardrobe=wardrobe,
    )

    if session["error"]:
        return session["error"], "", ""

    selected_item = session["selected_item"]
    price_comparison = session.get("price_comparison")

    if selected_item:
        listing_text = (
            f"Title: {selected_item.get('title', 'Unknown item')}\n"
            f"Price: ${selected_item.get('price', 'N/A')}\n"
            f"Platform: {selected_item.get('platform', 'N/A')}\n"
            f"Size: {selected_item.get('size', 'N/A')}\n"
            f"Condition: {selected_item.get('condition', 'N/A')}\n"
            f"Category: {selected_item.get('category', 'N/A')}\n"
            f"Colors: {', '.join(selected_item.get('colors', [])) if isinstance(selected_item.get('colors', []), list) else selected_item.get('colors', 'N/A')}\n"
            f"Style tags: {', '.join(selected_item.get('style_tags', [])) if isinstance(selected_item.get('style_tags', []), list) else selected_item.get('style_tags', 'N/A')}\n"
            f"Description: {selected_item.get('description', 'No description available.')}"
        )
    else:
        listing_text = "No listing selected."

    if price_comparison:
        listing_text += (
            f"\n\nPrice check: {price_comparison.get('message', 'No price comparison available.')}"
        )

    outfit_text = session["outfit_suggestion"] or ""
    fit_card_text = session["fit_card"] or ""

    return listing_text, outfit_text, fit_card_text




# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]

def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=8,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=8,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=8,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
