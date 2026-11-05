class _TrieNode:
    __slots__ = ("children", "payloads")

    def __init__(self) -> None:
        self.children: dict[str, "_TrieNode"] = {}
        self.payloads: list = []


class Trie:
    """A fresh, in-memory, per-request prefix index built from whatever
    candidates already passed the other filters -- never persisted or
    incrementally maintained, since a personal recipe book's record
    count never justifies that complexity. Indexes each entry at its
    full-name start AND at every word-boundary offset, so typing "cake"
    finds "Chocolate Cake" as well as "Cake Pop"."""

    def __init__(self, entries: list[tuple[str, object]]) -> None:
        self._root = _TrieNode()
        for text, payload in entries:
            for start in self._word_start_offsets(text.lower()):
                self._insert(text.lower()[start:], payload)

    @staticmethod
    def _word_start_offsets(text: str) -> list[int]:
        if not text:
            return []
        offsets = [0]
        for i in range(1, len(text)):
            if text[i - 1] == " " and text[i] != " ":
                offsets.append(i)
        return offsets

    def _insert(self, suffix: str, payload: object) -> None:
        node = self._root
        node.payloads.append(payload)
        for character in suffix:
            node = node.children.setdefault(character, _TrieNode())
            node.payloads.append(payload)

    def search_prefix(self, prefix: str) -> list:
        node = self._root
        for character in prefix.lower():
            node = node.children.get(character)
            if node is None:
                return []
        return self._dedupe(node.payloads)

    @staticmethod
    def _dedupe(payloads: list) -> list:
        seen_ids: set[int] = set()
        unique = []
        for payload in payloads:
            if id(payload) in seen_ids:
                continue
            seen_ids.add(id(payload))
            unique.append(payload)
        return unique
