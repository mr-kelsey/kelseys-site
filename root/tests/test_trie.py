from app.trie import Trie


def test_search_prefix_returns_empty_list_when_no_match():
    trie = Trie([("Tomato Soup", "soup")])
    assert trie.search_prefix("zz") == []


def test_search_prefix_matches_full_name_prefix():
    trie = Trie([("Tomato Soup", "soup")])
    assert trie.search_prefix("tom") == ["soup"]


def test_search_prefix_matches_word_boundary_within_name():
    trie = Trie([("Chocolate Cake", "cake")])
    assert trie.search_prefix("cake") == ["cake"]


def test_search_prefix_with_empty_prefix_returns_all_entries():
    trie = Trie([("Tomato Soup", "soup"), ("Chocolate Cake", "cake")])
    assert trie.search_prefix("") == ["soup", "cake"]


def test_search_prefix_is_case_insensitive():
    trie = Trie([("Tomato Soup", "soup")])
    assert trie.search_prefix("TOM") == ["soup"]


def test_search_prefix_does_not_return_duplicate_payload_for_multiword_match():
    trie = Trie([("Cake Pop Cake", "double-cake")])
    assert trie.search_prefix("cake") == ["double-cake"]
