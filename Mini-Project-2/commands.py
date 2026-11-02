"""Turn recognized speech into one of the library API's requests.

For example "Check out item 3." becomes POST /api/items/3/checkout. Every endpoint
accepts several phrasings, and nothing here knows the library rules: a bad value is
sent to the API as it is, and the API decides whether to reject it.
"""

import re
from collections import namedtuple
from urllib.parse import urlencode

Command = namedtuple("Command", "action method path item_id body query")


class UnknownCommandError(Exception):
    """Raised when the text cannot be turned into a library request."""


# --- Which request does the user want? ---

# Action → the verbs that ask for it. The verb said first decides, so the word
# "return" in "Create item, title Return of the King" does not count as a return.
# "lookup" is a get or a list, depending on whether an item number was said.
VERBS = {
    "checkout": r"check[- ]?out|borrow|take out|lend",
    "return": r"return|give back|bring back|hand back|check[- ]?in",
    "delete": r"delete|remove|discard|throw away|get rid of",
    "create": r"create|add|insert|register|new",
    "replace": r"replace|overwrite",
    "update": r"update|change|edit|modify|set|rename|correct",
    "lookup": r"list|show|display|browse|find|get|give me|read|tell me|describe|"
              r"what|which|how many|details",
}

# Words that help Azure recognize short commands correctly.
PHRASES = [
    "check out", "return", "delete", "create item", "replace item", "update item",
    "list items", "show item", "item", "type book", "type DVD", "title", "author",
    "director", "pages", "page count", "duration", "minutes", "available", "checked out",
]

BOOK = r"books?"
DVD = r"dvd'?s?|d\.?\s?v\.?\s?d\.?'?s?|movies?|films?"


def _find_action(text):
    """Return (action, position just after its verb), or (None, 0) if no verb was said."""
    found = None
    for action, verbs in VERBS.items():
        match = re.search(rf"\b(?:{verbs})\b", text, re.IGNORECASE)
        # Dict order settles ties: "get rid of" (delete) comes before "get" (lookup).
        if match and (found is None or match.start() < found.start()):
            found, found_action = match, action
    return (found_action, found.end()) if found else (None, 0)


# --- Numbers: Azure writes "3", "1,200" or sometimes "three" ---

UNITS = {word: value for value, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split()
)}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
SCALES = {"hundred": 100, "thousand": 1000}
# Only trusted right after "item": "item to" is "item two", but "to" is not a number elsewhere.
HOMOPHONES = {"won": 1, "to": 2, "too": 2, "tree": 3, "for": 4, "fore": 4, "ate": 8}

_NUMBER_WORD = "|".join([*UNITS, *TENS, *SCALES])
NUMBER = rf"\d[\d,.]*\d|\d|(?:{_NUMBER_WORD})(?:[\s-]+(?:and\s+)?(?:{_NUMBER_WORD}))*"


def _to_number(text):
    """Return text as an int, or unchanged if it is not a whole number (the API rejects it)."""
    cleaned = text.replace(",", "")
    if cleaned.isdigit():
        return int(cleaned)
    total = current = 0
    for word in re.findall(r"[a-z]+", text.lower()):
        if word in UNITS:
            current += UNITS[word]
        elif word in TENS:
            current += TENS[word]
        elif word == "hundred":
            current = max(current, 1) * 100
        elif word == "thousand":
            total += max(current, 1) * 1000
            current = 0
        elif word != "and":
            return text
    return total + current


# --- Which item? ---

_ITEM_ID = re.compile(
    r"\b(?:(?:of|for|on|from)\s+)?(?:the\s+)?(?:item|id|number|book|dvd|movie)\s*"
    r"(?:(?:number|id)\s*)?#?\s*"
    rf"({NUMBER}|{'|'.join(HOMOPHONES)})\b",
    re.IGNORECASE,
)
_BARE_ID = re.compile(rf"^\W*(?:the\s+)?({NUMBER})\b", re.IGNORECASE)


def _take_item_id(text):
    """Return (item id or None, text without the part that named the item)."""
    match = _ITEM_ID.search(text) or _BARE_ID.search(text)
    if not match:
        return None, text
    spoken = match.group(1).lower()
    item_id = HOMOPHONES[spoken] if spoken in HOMOPHONES else _to_number(spoken)
    if not isinstance(item_id, int):
        return None, text
    return item_id, text[:match.start()] + " " + text[match.end():]


# --- The fields of a new or edited item ---

_TYPE = re.compile(rf"\btype\b\W*(?:is\W+)?({BOOK}|{DVD})(?![\w'])", re.IGNORECASE)
_LEADING_TYPE = re.compile(
    rf"^\W*(?:(?:a|an|new)\s+)*(?:({BOOK}|{DVD})|items?)(?![\w'])", re.IGNORECASE
)

_PAGES_LABEL = r"page\s*count|number of pages|pages?"
_DURATION_LABEL = r"duration|running time|run\s*time|length"
_MINUTES = r"minutes?|mins?"

# Field → its spoken labels, most specific first. Only the first label found is used, so
# "by" counts only if no "author" was said, and "Stand by Me" can stay a title.
_TEXT_LABELS = {
    "title": ["title", "called", "named", "name"],
    "author": ["author", "director", "writer", "written by", "directed by", "by"],
    # A label whose value is not a number stays here, so the API can reject the value.
    "page_count": [_PAGES_LABEL],
    "duration": [_DURATION_LABEL],
}


def _item_type(match):
    return "book" if re.match(BOOK, match.group(1), re.IGNORECASE) else "dvd"


def _take_number_field(text, labels, units):
    """Find "pages 220", "220 pages" or "duration 148 minutes"; return (value or None, rest)."""
    labeled = rf"\b(?:{labels})\b(?:\s+(?:is|to|of|are)\b)?[\s:=,]*({NUMBER})\b(?:\s*(?:{units})\b)?"
    unit_after = rf"\b({NUMBER})[\s-]*(?:{units})\b"
    match = re.search(labeled, text, re.IGNORECASE) or re.search(unit_after, text, re.IGNORECASE)
    if not match:
        return None, text
    return _to_number(match.group(1)), text[:match.start()] + " " + text[match.end():]


def _find_label(text, labels):
    """Return the match of the first label in the list that appears in the text."""
    for label in labels:
        # The lookaround keeps "Director's Cut" from counting as the label "director".
        match = re.search(rf"(?<![\w'])(?:{label})(?![\w'])", text, re.IGNORECASE)
        if match:
            return match
    return None


def _clean_value(value, is_edit):
    """Remove the punctuation and joining words around a spoken value."""
    value = value.strip(" \t,;:!?\"'.")
    value = re.sub(r"^(?:is|as|be)\s+", "", value, flags=re.IGNORECASE)
    if is_edit:
        # "Change the title to Emma". Not for new items: "title To Kill a Mockingbird".
        value = re.sub(r"^to\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"[\s,;]+(?:and|with)$", "", value, flags=re.IGNORECASE)
    return value.strip(" \t,;:!?\"'.")


def _parse_fields(text, is_edit, implicit_title):
    """Read title, author, page_count and duration from the words after the verb."""
    fields = {}
    pages, text = _take_number_field(text, _PAGES_LABEL, r"pages?")
    if pages is not None:
        fields["page_count"] = pages
    duration, text = _take_number_field(text, f"{_DURATION_LABEL}|{_MINUTES}", _MINUTES)
    if duration is not None:
        fields["duration"] = duration

    found = []
    for name, labels in _TEXT_LABELS.items():
        match = None if name in fields else _find_label(text, labels)
        if match:
            found.append((match.start(), match.end(), name))
    found.sort()

    # Each value runs from its label to the next label.
    for index, (_, value_start, name) in enumerate(found):
        value_end = found[index + 1][0] if index + 1 < len(found) else len(text)
        value = _clean_value(text[value_start:value_end], is_edit)
        fields[name] = value

    # "Add a book Dune by Frank Herbert": the words before the first label are the title.
    if implicit_title and "title" not in fields:
        head = text[:found[0][0]] if found else text
        head = _clean_value(head, is_edit)
        if head:
            fields["title"] = head
    return fields


def _parse_create(rest):
    body = {}
    leading = _LEADING_TYPE.match(rest)
    if leading:
        if leading.group(1):
            body["type"] = _item_type(leading)
        rest = rest[leading.end():]
    spoken_type = _TYPE.search(rest)
    if spoken_type:
        body["type"] = _item_type(spoken_type)
        rest = rest[:spoken_type.start()] + " " + rest[spoken_type.end():]
    body.update(_parse_fields(rest, is_edit=False, implicit_title=True))
    return body


def _parse_edit(rest, renaming):
    # The type of an item cannot change, so "type book" is only a description here.
    rest = _TYPE.sub(" ", rest)
    return _parse_fields(rest, is_edit=True, implicit_title=renaming)


# --- Filters for listing ---

def _list_query(text):
    query = {}
    if re.search(r"\b(?:checked[- ]?out|unavailable|not available|borrowed|on loan)\b", text, re.IGNORECASE):
        query["available"] = "false"
    elif re.search(r"\b(?:available|in stock|on the shelf)\b", text, re.IGNORECASE):
        query["available"] = "true"
    if re.search(rf"\b(?:{BOOK})\b", text, re.IGNORECASE):
        query["type"] = "book"
    elif re.search(rf"(?<!\w)(?:{DVD})(?![\w])", text, re.IGNORECASE):
        query["type"] = "dvd"
    return query


# --- Putting it together ---

_ASKS_FOR_LIST = r"\b(?:list|browse|items?|have|everything|catalog|collection|library)\b"


def _require_id(item_id, example):
    if item_id is None:
        raise UnknownCommandError(f"Which item do you mean? Try saying: {example}.")
    return item_id


def parse(text):
    """Return the Command for the text, or raise UnknownCommandError."""
    action, verb_end = _find_action(text)
    rest = text[verb_end:]

    if action == "create":
        return Command("create", "POST", "/api/items", None, _parse_create(rest), {})

    item_id, rest = _take_item_id(rest)
    if action in (None, "lookup"):
        # "Item 3?" has no verb but is still clear, while "What a lovely day" names nothing.
        query = _list_query(text)
        if item_id is None and not query and not re.search(_ASKS_FOR_LIST, text, re.IGNORECASE):
            raise UnknownCommandError(f"Sorry, I heard “{text}”, but no library command.")
        if item_id is None:
            path = "/api/items" + (f"?{urlencode(query)}" if query else "")
            return Command("list", "GET", path, None, None, query)
        return Command("get", "GET", f"/api/items/{item_id}", item_id, None, {})

    if action == "checkout":
        _require_id(item_id, "check out item 3")
        return Command("checkout", "POST", f"/api/items/{item_id}/checkout", item_id, None, {})
    if action == "return":
        _require_id(item_id, "return item 3")
        return Command("return", "POST", f"/api/items/{item_id}/return", item_id, None, {})
    if action == "delete":
        _require_id(item_id, "delete item 3")
        return Command("delete", "DELETE", f"/api/items/{item_id}", item_id, None, {})
    if action == "replace":
        _require_id(item_id, "replace item 3, title Emma, author Jane Austen, pages 400")
        return Command("replace", "PUT", f"/api/items/{item_id}", item_id, _parse_edit(rest, False), {})

    _require_id(item_id, "change the title of item 3 to Emma")
    renaming = re.search(r"\brename\b", text, re.IGNORECASE) is not None
    return Command("update", "PATCH", f"/api/items/{item_id}", item_id, _parse_edit(rest, renaming), {})
