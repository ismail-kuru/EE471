from custom_classes import (
    DVD,
    Book,
    ItemNotFoundError,
    ItemStateError,
    LibraryCollection,
)


def show(title, items):
    """Print a heading and one line per item."""
    print(f"\n{title}")
    for item in items:
        print(f"  #{item.id} {item}")


def main():
    """Call every LibraryCollection method once and trigger each exception."""
    library = LibraryCollection()

    print("--- add_item() ---")
    gatsby_id = library.add_item(Book("The Great Gatsby", "F. Scott Fitzgerald", 180))
    inception_id = library.add_item(DVD("Inception", "Christopher Nolan", 148))
    orwell_id = library.add_item(Book("1984", "George Orwell", 328))
    print(f"New ids: {gatsby_id}, {inception_id}, {orwell_id}")

    print("\n--- get_item() and to_dict() ---")
    print(library.get_item(inception_id).to_dict())

    print("\n--- checkout() and return_item() ---")
    print(library.get_item(inception_id).checkout())
    print(library.get_item(gatsby_id).checkout())
    print(library.get_item(gatsby_id).return_item())

    print("\n--- list_items() ---")
    show("All items:", library.list_items())
    show("Available only:", library.list_items(available=True))
    show("Books only:", library.list_items(item_type="book"))

    print("\n--- update_item() ---")
    updated = library.update_item(orwell_id, title="Nineteen Eighty-Four", page_count=336)
    print(updated.to_dict())

    print("\n--- remove_item() and id reuse ---")
    library.remove_item(orwell_id)
    new_id = library.add_item(Book("Dune", "Frank Herbert", 412))
    print(f"Removed id {orwell_id}; the next item got id {new_id}, not {orwell_id}.")

    print("\n--- Exceptions ---")
    try:
        library.get_item(99)
    except ItemNotFoundError as error:
        print(f"ItemNotFoundError: {error}")

    try:
        library.get_item(inception_id).checkout()
    except ItemStateError as error:
        print(f"ItemStateError (checkout): {error}")

    try:
        library.get_item(gatsby_id).return_item()
    except ItemStateError as error:
        print(f"ItemStateError (return): {error}")

    try:
        library.remove_item(inception_id)
    except ItemStateError as error:
        print(f"ItemStateError (remove): {error}")

    try:
        library.update_item(gatsby_id, is_available=False)
    except ValueError as error:
        print(f"ValueError (protected field): {error}")

    try:
        library.update_item(gatsby_id, duration=90)
    except ValueError as error:
        print(f"ValueError (wrong field for type): {error}")

    try:
        library.list_items(item_type="vinyl")
    except ValueError as error:
        print(f"ValueError (bad filter): {error}")

    show("Final collection:", library.list_items())


if __name__ == "__main__":
    main()
