# FitFindr — README.md

FitFindr is a multi-tool AI agent that helps users search for secondhand clothing items, compare prices, get outfit ideas, and create a short shareable fit card. The agent uses a planning loop to decide which tool to call next based on the result of the previous step.

---

## Project Overview

FitFindr helps with the thrift shopping process. The user gives a natural language request, such as:

```text
vintage graphic tee under $30
```

The agent then:

1. Searches the mock listings dataset.
2. Selects the best matching item.
3. Compares the selected item’s price with similar listings.
4. Suggests an outfit using the selected item and the user’s wardrobe.
5. Creates a short caption-style fit card.

If something fails, the agent gives a helpful response instead of crashing.

---

## Tool Inventory

### Tool 1: `search_listings`

**Purpose:**

This tool searches the mock thrift listings dataset for secondhand clothing items that match the user's description, size, and maximum price.

**Function signature:**

```python
search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]
```

**Inputs:**

* `description` (`str`): The clothing item or style the user is searching for, such as `"vintage graphic tee"` or `"black jacket"`.
* `size` (`str | None`): The clothing size the user wants, such as `"S"`, `"M"`, `"L"`, or `None` if no size is provided.
* `max_price` (`float | None`): The highest price the user wants to pay, or `None` if no price is provided.

**What it returns:**

* The tool returns a list of matching listing dictionaries.
* Each listing dictionary can include:

  * `id`
  * `title`
  * `description`
  * `category`
  * `style_tags`
  * `size`
  * `condition`
  * `price`
  * `colors`
  * `brand`
  * `platform`
* If no listings match, it returns an empty list `[]`.

**Failure behavior:**

If no listings match, the tool returns `[]`. The agent stores an error message and stops early instead of calling the other tools.

---

### Tool 2: `suggest_outfit`

**Purpose:**

This tool takes the selected thrift listing and the user's wardrobe, then suggests one or more outfit combinations using the new item and items the user already owns.

**Function signature:**

```python
suggest_outfit(new_item: dict, wardrobe: dict) -> str
```

**Inputs:**

* `new_item` (`dict`): The selected listing from `search_listings`. This includes fields like title, category, price, colors, style tags, condition, brand, and platform.
* `wardrobe` (`dict`): The user's current wardrobe data. This contains an `items` list with wardrobe pieces such as jeans, shoes, jackets, tops, or accessories.

**What it returns:**

* The tool returns a string with a complete outfit suggestion.
* The suggestion explains how to wear the selected item with wardrobe pieces.
* It can include details like shoes, bottoms, layering, colors, and overall vibe.

**Failure behavior:**

If the wardrobe is empty, the tool still returns general styling advice instead of crashing.

---

### Tool 3: `create_fit_card`

**Purpose:**

This tool creates a short, shareable fit card for the outfit. The fit card sounds like a casual caption someone might post on Instagram, TikTok, or a style board.

**Function signature:**

```python
create_fit_card(outfit: str, new_item: dict) -> str
```

**Inputs:**

* `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): The selected thrift listing used in the outfit.

**What it returns:**

* The tool returns a short caption-style string.
* The caption describes the outfit in a fun, shareable way.
* It mentions the thrifted item, the price/platform when natural, and the outfit vibe.

**Failure behavior:**

If the outfit input is missing or empty, the tool returns:

```text
I need a complete outfit suggestion before I can create a fit card.
```

---

### Additional Tool: `compare_price`

**Purpose:**

This is my stretch feature. This tool estimates whether the selected thrift listing is a good deal, fair price, overpriced, or unknown by comparing it with similar listings in the mock dataset.

**Function signature:**

```python
compare_price(new_item: dict) -> dict
```

**Inputs:**

* `new_item` (`dict`): The selected listing from `search_listings`.

**What it returns:**

The tool returns a dictionary with:

* `status`: `"good deal"`, `"fair"`, `"overpriced"`, or `"unknown"`
* `item_price`: the selected item’s price
* `average_comparable_price`: the average price of similar listings, or `None`
* `message`: a short explanation of the price judgment

Example:

```python
{
    "status": "good deal",
    "item_price": 18.0,
    "average_comparable_price": 29.47,
    "message": "This looks like a good deal because it costs $18.00, while similar items average around $29.47."
}
```

**How comparisons are made:**

The tool compares the selected item with other listings using fields such as:

* category
* brand
* style tags
* colors

If enough similar items are found, the tool calculates the average comparable price and compares the selected item’s price to that average.

**Failure behavior:**

If there are not enough comparable listings, the tool returns `"unknown"` with a helpful explanation. The agent still continues to outfit suggestion and fit card creation because price comparison is extra information.

---

## Planning Loop

**How the agent decides which tool to call next:**

The agent uses a conditional planning loop. It does not call every tool automatically no matter what.

The loop works like this:

1. The agent starts a new session dictionary.
2. The agent reads the user query.
3. The agent extracts:

   * description
   * size
   * max price
4. The agent calls:

```python
search_listings(description, size, max_price)
```

5. After `search_listings` returns, the agent checks whether the result list is empty.

If `results == []`:

* The agent stores an error message in `session["error"]`.
* The agent returns early.
* The agent does not call `compare_price`, `suggest_outfit`, or `create_fit_card`.

If results are found:

* The agent chooses the first result.
* The agent stores it in `session["selected_item"]`.

6. The agent calls:

```python
compare_price(session["selected_item"])
```

The result is stored in:

```python
session["price_comparison"]
```

7. The agent calls:

```python
suggest_outfit(session["selected_item"], wardrobe)
```

The result is stored in:

```python
session["outfit_suggestion"]
```

8. If the outfit suggestion is missing or empty:

* The agent stores an error message.
* The agent stops before creating a fit card.

9. If the outfit suggestion exists, the agent calls:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

The final fit card is stored in:

```python
session["fit_card"]
```

10. The loop is done when the session contains either a completed `fit_card` or an `error`.

---

## State Management

**How information passes from one tool to the next:**

The agent stores information in a session dictionary during one user interaction. This allows the output from one tool to become the input for the next tool without asking the user to repeat information.

The session tracks:

* `query`: the original user request
* `parsed`: the extracted description, size, and max price
* `search_results`: the list returned by `search_listings`
* `selected_item`: the item chosen from the search results
* `price_comparison`: the dictionary returned by `compare_price`
* `wardrobe`: the user's wardrobe data
* `outfit_suggestion`: the string returned by `suggest_outfit`
* `fit_card`: the caption returned by `create_fit_card`
* `error`: an error message if something fails

Example of state passing:

```python
session["selected_item"] = results[0]
```

The same selected item is passed into:

```python
compare_price(session["selected_item"])
```

and:

```python
suggest_outfit(session["selected_item"], wardrobe)
```

Then the outfit suggestion is stored:

```python
session["outfit_suggestion"] = outfit_suggestion
```

That same outfit suggestion is passed into:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

This shows that the item returned by `search_listings` is the same item used by the later tools.

---

## Error Handling

For each tool, I handled a specific failure mode.

| Tool              | Failure mode                                 | Agent response                                                                                                                                                                                                                              |
| ----------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_listings` | No results match the query                   | The agent stores an error in `session["error"]`, tells the user no listings matched, and suggests using a broader description, removing the size filter, or increasing the budget. The agent stops early and does not call the other tools. |
| `suggest_outfit`  | Wardrobe is empty                            | The tool returns a general styling suggestion using common basics instead of crashing.                                                                                                                                                      |
| `create_fit_card` | Outfit input is missing or incomplete        | The tool returns a clear message saying it needs a complete outfit suggestion before creating a fit card.                                                                                                                                   |
| `compare_price`   | Not enough similar listings to compare price | The tool returns `"unknown"` with a message explaining that there was not enough data to judge the price confidently. The agent still continues to outfit suggestion and fit card creation.                                                 |

**Concrete failure example:**

Command:

```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
```

Output:

```text
[]
```

Full agent response:

```text
I couldn't find any listings that matched that description, size, and price. Try using a broader description, removing the size filter, or increasing your budget.
```

This response is specific and actionable because it tells the user what failed and what to try next.

---

## Complete Interaction Walkthrough

**Example user query:**

```text
vintage graphic tee under $30
```

### Step 1: Search

The agent extracts:

```python
description = "vintage graphic tee"
size = None
max_price = 30.0
```

The agent calls:

```python
search_listings(description="vintage graphic tee", size=None, max_price=30.0)
```

The tool returns matching listings. The agent chooses the top result and stores it:

```python
session["selected_item"] = results[0]
```

### Step 2: Price Comparison

The agent calls:

```python
compare_price(session["selected_item"])
```

The result is stored:

```python
session["price_comparison"] = price_comparison
```

### Step 3: Outfit Suggestion

The agent calls:

```python
suggest_outfit(session["selected_item"], wardrobe)
```

The result is stored:

```python
session["outfit_suggestion"] = outfit_suggestion
```

### Step 4: Fit Card

The agent calls:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

The result is stored:

```python
session["fit_card"] = fit_card
```

### Final Output

The user sees:

* the top listing found
* the price comparison
* the outfit suggestion
* the final fit card

If search returns no results, the user instead sees an error message and the agent stops early.

---

## Testing

I tested the tools in isolation with pytest.

Test file:

```text
tests/test_tools.py
```

The tests cover:

* `search_listings` returns results
* `search_listings` returns `[]` for no results
* `search_listings` respects the price filter
* `compare_price` returns a dictionary
* `compare_price` handles a missing item
* `suggest_outfit` handles an empty wardrobe
* `suggest_outfit` works with the example wardrobe
* `create_fit_card` handles an empty outfit string
* `create_fit_card` works with a valid outfit

Final result:

```text
9 passed
```

---

## Spec Reflection

**One way the spec helped:**

The spec helped me define the tools before coding. Because I wrote the inputs, outputs, and failure behavior in `planning.md`, it was easier to implement each function and test it by itself before connecting the tools through the agent.

**One way the implementation diverged from the spec:**

I added the stretch feature `compare_price`. This added an extra step to the workflow after the agent selects an item from `search_listings`. The selected item is passed into `compare_price` before it is passed into `suggest_outfit`. I added this because the project allowed a price comparison tool as a bonus feature.

---

## AI Usage

### Instance 1: Planning

I used ChatGPT to help fill out `planning.md`.

I gave ChatGPT the project requirements and asked it to help write:

* tool descriptions
* input and output definitions
* failure behavior
* planning loop logic
* state management notes
* architecture diagram
* AI tool plan

I reviewed the output to make sure the tool names and function signatures matched the starter code and the project requirements.

### Instance 2: Tool implementation

I used ChatGPT to help implement the functions in `tools.py`.

I gave ChatGPT the tool sections from `planning.md` and asked it to implement each function while keeping the starter function signatures.

I reviewed and revised the generated code to make sure:

* `search_listings` returns `[]` when no matches are found
* `suggest_outfit` handles an empty wardrobe
* `create_fit_card` handles an empty outfit string
* `compare_price` returns `"unknown"` when it cannot compare prices

### Instance 3: Planning loop and state

I used ChatGPT to help implement `run_agent()` in `agent.py`.

I gave ChatGPT the Planning Loop and State Management sections from `planning.md`.

I verified that the code:

* stores information in the session dictionary
* passes `selected_item` into the next tools
* passes `outfit_suggestion` into `create_fit_card`
* stops early when `search_listings` returns no results
* does not call all tools blindly

### Instance 4: Tests

I used ChatGPT to help write pytest tests for the tools.

I reviewed the tests, fixed path and syntax issues, and confirmed that all 9 tests passed.

---

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_key_here
```

Run tests:

```bash
pytest tests/
```

Run the terminal agent:

```bash
python agent.py
```

Run the Gradio app:

```bash
python app.py
```

Then open the localhost URL shown in the terminal.

---

## Demo Video

The demo video shows:

1. A successful interaction from natural language query to final fit card.
2. All three required tools being used in one interaction.
3. The selected item from `search_listings` passing into `suggest_outfit`.
4. The outfit suggestion from `suggest_outfit` passing into `create_fit_card`.
5. The extra credit `compare_price` tool returning a price assessment with reasoning.
6. A deliberate no-results failure query.
7. The agent giving a specific and actionable error message.
8. Pytest showing all 9 tests passing.
