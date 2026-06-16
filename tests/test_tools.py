import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import search_listings, compare_price, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert isinstance(results, list)
    assert all(float(item["price"]) <= 10 for item in results)


def test_compare_price_returns_dict():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    price_check = compare_price(results[0])

    assert isinstance(price_check, dict)
    assert "status" in price_check
    assert price_check["status"] in ["good deal", "fair", "overpriced", "unknown"]
    assert "message" in price_check


def test_compare_price_missing_item():
    price_check = compare_price({})

    assert isinstance(price_check, dict)
    assert price_check["status"] == "unknown"


def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_empty_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit) > 0


def test_suggest_outfit_example_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_example_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit) > 0


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    fit_card = create_fit_card("", results[0])

    assert isinstance(fit_card, str)
    assert "complete outfit suggestion" in fit_card.lower()


def test_create_fit_card_success():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = "Pair it with baggy jeans and chunky sneakers for a relaxed streetwear look."
    fit_card = create_fit_card(outfit, results[0])

    assert isinstance(fit_card, str)
    assert len(fit_card) > 0