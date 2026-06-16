# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
- This tool searches the mock thrift listings dataset for secondhand clothing items that match the user's requested description, size, and maximum price. It checks listing field such as title, description, category, style tags, size, price, color, brand, and platform to find useful matches.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The clothing item or style the user is searching for, such as "vintage graphic tee" or "black jacket". 
- `size` (str): The cloting size the user wants, such as "S", "M", "L".  ...
- `max_price` (float): The highest price the user wants to pay. ...

**What it returns:**
- The tool returns a list of matching listing dictionaries. Each listing may contain field such as id, title, description, category, style_tags, size, condition, price, colors, brand, platform. 
<!-- Describe the return value — what fields does a result contain? -->

**What happens if it fails or returns nothing:**
- If no listings match the user’s request, the agent should not continue to compare_price, suggest_outfit, or create_fit_card. Instead, the agent should save an error message in the session and tell the user something like: "I couldn't find any listings that matched that description, size, and price. Try raising your budget, removing the size filter, or using a broader description."
<!-- What should the agent do if no listings match? -->

---

### Tool 2: suggest_outfit

**What it does:**
This tool takes the selected thrift listing and the user's wardrobe, then suggests one or more outfit combinations using the new item and items the user already owns. It should give practical styling advice, not just list clothing items.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing from search_listings. This should include fields like title, category, price, colors, style tags, brand, condition, and platform. 
- `wardrobe` (dict): The user's current wardrobe data. This includes wardrobe items the user already owns, such as jeans, shoes, jackets, tops, or accessories.

**What it returns:** 
- The tool returns a string with a complete outfit suggestion. The suggestion should explain how to wear the new item with wardrobe pieces and should include styling details such as shoes, bottoms, layering, colors, or vibe.
<!-- Describe the return value -->

**What happens if it fails or returns nothing:** 
- If the wardrobe is empty or minimal, the tool should still return useful general styling advice instead of crashing. For example, it can suggest basic pieces that would work well, such as jeans, sneakers, a hoodie, or simple accessories.
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---

### Tool 3: create_fit_card

**What it does:** This tool creates a short, shareable fit card for the outfit. The fit card should sound like a casual caption someone might post on Instagram, TikTok, or a style board.
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str ): The outfit suggestion returned by suggest_outfit.
- `new_item` (dict): The selected thrift listing used in the outfit. This includes information like title, price, platform, color, brand, and condition. 

**What it returns:** The tool returns a short caption-style string that describes the outfit in a fun, shareable way. It should mention the new thrifted item and the general vibe of the outfit. The wording should change depending on the item and outfit input.
<!-- Describe the return value -->

**What happens if it fails or returns nothing:** If the outfit input is missing, empty, or incomplete, the tool should not crash. It should return a clear error string like: "I need a complete outfit suggestion before I can create a fit card."
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)

What it does:
This tool estimates whether the selected thrift listing is a good deal, fair price, overpriced, or unknown by comparing it with similar listings in the mock dataset. It looks for comparable items using fields such as category, style tags, brand, colors, condition, and item type.
<!-- Copy the block above for any tools beyond the required three -->

Input Parameters: new_item (dict): The selected listing from search_listings. This dictionary should iclude fields such as title, category, style_tags, price, condition, brand, colors, and platform. 

What it returns: The tool returns a dictionary containing a price status, the item’s price, the average price of comparable listings, and a short explanation.

What happens if it fails or returns nothing:

If the tool cannot find enough comparable listings, it should not crash. It should return a result with status set to "unknown" and include a helpful message explaining that there was not enough data to judge the price confidently.

The agent should still continue to suggest_outfit and create_fit_card even if the price comparison is "unknown" because price comparison is helpful extra information, but it is not required to style the item.
## Planning Loop

**How does your agent decide which tool to call next?**
The agent uses a conditional planning loop instead of calling every tool automatically. First, it reads the user's query and extracts the main item description, size, max price, and wardrobe details. Then it calls search_listings(description, size, max_price).

After search_listings returns, the agent checks whether the result list is empty.

If results == [], the agent stores an error message in the session and returns early. It does not call compare_price, suggest_outfit, or create_fit_card because there is no selected item.

If results are found, the agent chooses the first listing as the selected item and stores it in session["selected_item"].

Next, the agent calls compare_price(selected_item) to estimate whether the selected item is a good deal, fair price, overpriced, or unknown. The result is stored in session["price_comparison"]. If the price comparison returns "unknown", the agent still continues because price comparison is helpful but not required for styling.

Then the agent calls suggest_outfit(selected_item, wardrobe).

After the outfit suggestion is created, the agent stores it in session["outfit_suggestion"]. If the outfit suggestion is missing or empty, the agent stores an error message and stops before creating a fit card.

If the outfit suggestion exists, the agent calls create_fit_card(outfit_suggestion, selected_item). The final fit card is stored in session["fit_card"].

The loop is done when the session contains either a completed fit_card or an error.
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
The agent stores information in a session dictionary during one user interaction. This allows the output from one tool to become the input for the next tool without asking the user to repeat information.

The session will track:

query: the original user request
description: the clothing item or style extracted from the request
size: the requested size, or None
max_price: the user's budget, or None
wardrobe: the user's wardrobe data
search_results: the list returned by search_listings
selected_item: the item chosen from the search results
price_comparison: the dictionary returned by compare_price
outfit_suggestion: the string returned by suggest_outfit
fit_card: the caption returned by create_fit_card
error: an error message if something fails

For example, search_listings returns a list of item dictionaries. The agent stores the first item as session["selected_item"]. Then it passes that exact dictionary into compare_price and stores the result as session["price_comparison"].

After that, the agent passes the same selected item into suggest_outfit. After suggest_outfit returns a string, the agent stores it as session["outfit_suggestion"] and passes it into create_fit_card.
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The agent stores an error in session["error"], tells the user no listings matched, and suggests broadening the search, increasing the budget, or removing the size filter. The agent stops early and does not call the other tools. |
| suggest_outfit | Wardrobe is empty | The tool returns a general styling suggestion using common basics instead of crashing. The agent tells the user it used general outfit advice because there were no wardrobe items available. |
| create_fit_card | Outfit input is missing or incomplete | The tool returns a clear message saying it needs a complete outfit suggestion before making a fit card. The agent stores this message as an error or displays it instead of crashing. |

| compare_price | Not enough similar listings to compare price | The tool returns "unknown" with a message explaining that there were not enough comparable listings. The agent still continues to outfit suggestion and fit card creation. |

---

## Architecture

User query 
| 
v 
Planning Loop 
| 
| extracts description, size,     max_price, wardrobe 
v 
Session State - query - description - size - max_price - wardrobe - search_results - selected_item - price_comparison - outfit_suggestion - fit_card - error 
| 
v 
search_listings(description, size, max_price) 
| 
| results == [] +-----------------------------> ERROR: 
| "No listings found. Try a broader search, 
| higher budget, or no size filter." 
| return session 
| 
| results found 
v 
Session: selected_item = results[0] 
| 
v compare_price(selected_item) 
| 
| not enough comparable items 
| returns status = "unknown" 
| agent continues anyway v Session: price_comparison = price result 
| v suggest_outfit(selected_item, wardrobe) 
| 
| wardrobe empty 
| tool gives general styling advice v 
Session: outfit_suggestion = outfit result 
| 
| outfit missing or empty +-----------------------------> ERROR: 
| "I need a complete outfit suggestion first." 
| return session 
| v create_fit_card(outfit_suggestion, selected_item) 
| v Session: fit_card = shareable caption 
| 
v Return final session to user                                

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will use ChatGPT to help implement each tool one at a time.

For search_listings, I will give ChatGPT the Tool 1 section from this planning document and ask it to implement the function using load_listings() from utils/data_loader.py. Before using the generated code, I will check that it filters by description, size, and max price, returns a list of listing dictionaries, and returns [] when nothing matches.

For compare_price, I will give ChatGPT the Tool 4 section and ask it to compare the selected item against similar listings from the mock dataset. I will verify that the code does not crash when there are not enough comparable listings and that it returns one of the expected statuses: "good deal", "fair", "overpriced", or "unknown".

For suggest_outfit, I will give ChatGPT the Tool 2 section and ask it to use Groq with llama-3.3-70b-versatile to generate a styling suggestion. I will verify that it accepts new_item and wardrobe, handles an empty wardrobe, and returns a useful string instead of crashing.

For create_fit_card, I will give ChatGPT the Tool 3 section and ask it to generate a caption-style fit card using the selected item and outfit suggestion. I will verify that it checks for an empty outfit string, returns a useful error message when needed, and produces varied captions for different inputs.

I will test the tools with pytest before connecting them to the agent. I will include tests for normal results and failure modes.

**Milestone 4 — Planning loop and state management:** 
I will use ChatGPT to help implement run_agent() in agent.py. I will give it the Planning Loop section, State Management section, and Architecture diagram from this document. I expect it to produce code that calls the tools conditionally, stores outputs in the session dictionary, and stops early when search results are empty.

Before trusting the code, I will check that it does not call all four tools blindly. I will verify that compare_price and suggest_outfit only run after a listing is found, and create_fit_card only runs after an outfit suggestion exists. I will also print the session dictionary after a complete query to confirm that selected_item, price_comparison, outfit_suggestion, and fit_card are being passed correctly.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:** The agent reads the user query and identifies the search request.

The agent extracts:

description = "vintage graphic tee"
size = None because the user did not give a size
max_price = 30.0
wardrobe details: baggy jeans and chunky sneakers

The agent calls:

search_listings(description="vintage graphic tee", size=None, max_price=30.0)
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:** 
The search tool returns a list of matching listings. For example:

[
    {
        "id": "item_001",
        "title": "Faded Band Tee",
        "description": "Vintage-style graphic tee with a worn-in look",
        "category": "tops",
        "style_tags": ["vintage", "graphic", "streetwear"],
        "size": "M",
        "condition": "Good",
        "price": 22.0,
        "colors": ["black", "gray"],
        "brand": "Unknown",
        "platform": "Depop"
    }
]

The agent checks that the list is not empty. It chooses the first result and stores it:

session["selected_item"] = results[0]
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:** The agent calls the extra credit price comparison tool:

compare_price(new_item=session["selected_item"])

The price comparison tool returns a result such as:

{
    "status": "fair",
    "item_price": 22.0,
    "average_comparable_price": 25.5,
    "message": "This looks like a fair price because similar tops in the dataset average around $25.50."
}

The agent stores this result:

session["price_comparison"] = price_comparison

Even if the status is "unknown", the agent continues because price comparison is not required for styling.
<!-- Continue until the full interaction is complete -->
Step 4:

The agent calls:

suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"])

The outfit tool returns a styling suggestion. For example:

Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s streetwear look. Add a simple zip hoodie or silver jewelry if you want the outfit to feel more styled without making it too formal.

The agent stores this:

session["outfit_suggestion"] = outfit_suggestion

Step 5:

The agent calls:

create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])

The fit card tool returns a short shareable caption. For example:

thrifted this faded band tee for $22 and it was made for baggy denim + chunky sneakers 🖤 easy 90s streetwear fit.

The agent stores this:

session["fit_card"] = fit_card

**Final output to user:** The user sees the selected listing, price comparison, outfit suggestion, and final fit card.

Example final response:

Found item:
Faded Band Tee — $22 on Depop, Good condition

Price check:
This looks like a fair price because similar tops in the dataset average around $25.50.

Outfit suggestion:
Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s streetwear look. Add a simple zip hoodie or silver jewelry if you want the outfit to feel more styled without making it too formal.

Fit card:
thrifted this faded band tee for $22 and it was made for baggy denim + chunky sneakers 🖤 easy 90s streetwear fit.

If the search returned no results, the user would instead see:

I couldn't find any listings that matched that description, size, and price. Try raising your budget, removing the size filter, or using a broader description.
<!-- What does the user actually see at the end? -->
