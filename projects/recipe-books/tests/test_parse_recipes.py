from pathlib import Path
from parse_recipes import split_paren_numbered

FIXTURES = Path(__file__).parent / "fixtures"


def test_paren_numbered_splits_sedley_sample():
    text = (FIXTURES / "sedley-sample.txt").read_text()
    recipes = split_paren_numbered(text)

    assert len(recipes) == 2

    assert recipes[0]["recipe_number"] == 1
    assert recipes[0]["raw_title"] == "A Receipt for the Dropsey."
    assert "Horehound" in recipes[0]["raw_body"]
    assert "Probatum est." in recipes[0]["raw_body"]

    assert recipes[1]["recipe_number"] == 2
    assert recipes[1]["raw_title"] == "To Make Snayle Water."
    assert "garden Snayles" in recipes[1]["raw_body"]


from parse_recipes import split_bare_number


def test_bare_number_splits_bulkeley_sample():
    text = (FIXTURES / "bulkeley-sample.txt").read_text()
    recipes = split_bare_number(text)

    assert len(recipes) == 2

    assert recipes[0]["recipe_number"] == 2
    assert recipes[0]["raw_title"] == "The Vertues of sages"
    assert "Sage is hot" in recipes[0]["raw_body"]

    assert recipes[1]["recipe_number"] == 3
    assert recipes[1]["raw_title"] == "The temperature of minte"
    assert "Mint is hott" in recipes[1]["raw_body"]


from parse_recipes import split_unnumbered


def test_unnumbered_splits_brumwich_sample():
    text = (FIXTURES / "brumwich-sample.txt").read_text()
    recipes = split_unnumbered(text)

    assert len(recipes) == 2

    assert recipes[0]["recipe_number"] is None
    assert recipes[0]["position"] == 1
    assert "balsome" in recipes[0]["raw_title"]
    assert "yellow wax" in recipes[0]["raw_body"]

    assert recipes[1]["recipe_number"] is None
    assert recipes[1]["position"] == 2
    assert recipes[1]["raw_title"] == "A Medicine for a Cough"
    assert "strong Ale" in recipes[1]["raw_body"]


from parse_recipes import detect_format


def test_detect_format_paren_numbered():
    text = (FIXTURES / "sedley-sample.txt").read_text()
    assert detect_format(text) == "paren_numbered"


def test_detect_format_bare_number():
    text = (FIXTURES / "bulkeley-sample.txt").read_text()
    assert detect_format(text) == "bare_number"


def test_detect_format_unnumbered():
    text = (FIXTURES / "brumwich-sample.txt").read_text()
    assert detect_format(text) == "unnumbered"


from parse_recipes import extract_book_metadata


def test_extract_book_metadata_sedley():
    text = (FIXTURES / "sedley-sample.txt").read_text()
    meta = extract_book_metadata(text)
    assert meta["title_raw"] is not None
    assert "Sedley" in meta["title_raw"]
    assert meta["date_inscribed"] == "1686"


def test_extract_book_metadata_bulkeley():
    text = (FIXTURES / "bulkeley-sample.txt").read_text()
    meta = extract_book_metadata(text)
    assert meta["attributed_compiler"] is not None
    assert "BULKELEY" in meta["attributed_compiler"].upper() or "Bulkeley" in meta["attributed_compiler"]
    assert meta["date_inscribed"] == "1627"


def test_extract_book_metadata_brumwich():
    text = (FIXTURES / "brumwich-sample.txt").read_text()
    meta = extract_book_metadata(text)
    assert meta["attributed_compiler"] is not None
    assert "Brumwich" in meta["attributed_compiler"]


import json
from parse_recipes import parse_file


def test_parse_file_produces_full_record(tmp_path):
    src = FIXTURES / "sedley-sample.txt"
    record = parse_file(src)

    assert record["ms_id"] == "sedley-sample"
    assert record["book"]["format_detected"] == "paren_numbered"
    assert record["book"]["recipe_count"] == 2
    assert record["book"]["date_inscribed"] == "1686"
    assert len(record["recipes"]) == 2
    assert record["recipes"][0]["raw_title"] == "A Receipt for the Dropsey."
