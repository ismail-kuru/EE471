"""The sentences the librarian says after a voice command has run."""

from custom_classes import DVD

# How many titles to read aloud when listing, so the answer stays short.
MAX_TITLES_READ = 5


def _describe(item):
    """Return e.g. "book '1984' by George Orwell, 328 pages"."""
    if item["type"] == "dvd":
        return f"DVD '{item['title']}' by {item['author']}, {item['duration']} minutes"
    return f"book '{item['title']}' by {item['author']}, {item['page_count']} pages"


def _list_reply(items, query):
    words = []
    if query.get("available") == "true":
        words.append("available")
    elif query.get("available") == "false":
        words.append("checked out")
    noun = {"book": "book", "dvd": "DVD"}.get(query.get("type"), "item")
    words.append(noun if len(items) == 1 else f"{noun}s")
    description = " ".join(words)

    if not items:
        return f"There are no {description}."
    titles = [f"'{item['title']}'" for item in items[:MAX_TITLES_READ]]
    extra = len(items) - len(titles)
    more = f", and {extra} more" if extra else ""
    return f"Found {len(items)} {description}: {', '.join(titles)}{more}."


def success(command, data):
    """Return the sentence for a request that succeeded."""
    if command.action == "list":
        return _list_reply(data, command.query)
    if command.action == "delete":
        return f"Item {command.item_id} has been deleted."

    # Checkout and return answer {"message": ..., "item": {...}}; the others send the item itself.
    item = data.get("item", data)
    item_id = item["id"]
    if command.action == "create":
        kind = "DVD" if item["type"] == "dvd" else "book"
        return f"Successfully created {kind} '{item['title']}' with ID {item_id}."
    if command.action == "get":
        status = "available" if item["is_available"] else "checked out"
        return f"Item {item_id} is the {_describe(item)}. It is {status}."
    if command.action == "checkout":
        reminder = f" {DVD.CARE_REMINDER}" if item["type"] == "dvd" else ""
        return f"Item {item_id}, '{item['title']}', has been checked out.{reminder}"
    if command.action == "return":
        return f"Item {item_id}, '{item['title']}', has been returned."
    if command.action == "replace":
        return f"Item {item_id} has been replaced. It is now the {_describe(item)}."
    return f"Item {item_id} has been updated. It is now the {_describe(item)}."


# The API's 409 messages name the title; the librarian says the item number instead.
CONFLICTS = {
    "checkout": "Sorry, item {id} is already checked out.",
    "return": "Sorry, item {id} is not checked out.",
    "delete": "Sorry, item {id} cannot be deleted while it is checked out.",
}


def failure(command, status, message):
    """Return the sentence for a request the API rejected."""
    if status == 404:
        return f"Sorry, item {command.item_id} was not found."
    if status == 409 and command.action in CONFLICTS:
        return CONFLICTS[command.action].format(id=command.item_id)
    # Make the API's message easy to say: "Missing field(s): page_count" → "missing fields: page count".
    spoken = message.replace("_", " ").replace("field(s)", "fields")
    return f"Sorry, {spoken[0].lower()}{spoken[1:]}"
