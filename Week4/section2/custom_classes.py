class ItemNotFoundError(Exception):
    """Raised when no item in the collection has the requested id."""


class ItemStateError(Exception):
    """Raised when an action does not fit the item's current state.

    For example: checking out an item that is already out, returning an item
    that is on the shelf, or deleting an item that is checked out.
    """


def _require_text(name, value):
    """Return value if it is a non-empty string, otherwise raise ValueError."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _require_positive_int(name, value):
    """Return value if it is a positive integer, otherwise raise ValueError."""
    # bool is a subclass of int, so True would otherwise count as 1.
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


class MediaItem:
    """A generic item in a library that can be checked out and returned.

    Attributes:
        id: Unique id given by LibraryCollection.add_item(); None until added.
        title: The title of the item.
        author: The author, director or artist of the item.
        is_available: True if the item is on the shelf, False if checked out.
    """

    TYPE = "item"
    # Fields that update_item() may change; subclasses add their own.
    EDITABLE_FIELDS = ("title", "author")

    def __init__(self, title, author, is_available=True):
        """Create an item with a title, an author and an availability status."""
        self.id = None
        self.title = _require_text("title", title)
        self.author = _require_text("author", author)
        self.is_available = is_available

    def checkout(self):
        """Check the item out.

        Returns:
            "Successful checkout".

        Raises:
            ItemStateError: If the item is already checked out.
        """
        if not self.is_available:
            raise ItemStateError(f"'{self.title}' is already checked out.")
        self.is_available = False
        return "Successful checkout"

    def return_item(self):
        """Put the item back on the shelf.

        Returns:
            "Successful return".

        Raises:
            ItemStateError: If the item is not checked out.
        """
        if self.is_available:
            raise ItemStateError(f"'{self.title}' is not checked out.")
        self.is_available = True
        return "Successful return"

    def validate_field(self, name, value):
        """Return value checked for the editable field name, or raise ValueError."""
        return _require_text(name, value)

    def to_dict(self):
        """Return the item as a dictionary that can be sent as JSON."""
        return {
            "id": self.id,
            "type": self.TYPE,
            "title": self.title,
            "author": self.author,
            "is_available": self.is_available,
        }

    @property
    def status(self):
        """Return "Available" or "Checked Out" based on is_available."""
        return "Available" if self.is_available else "Checked Out"

    def __str__(self):
        """Return the item as "Title by Author [Available/Checked Out]"."""
        return f"{self.title} by {self.author} [{self.status}]"


class Book(MediaItem):
    """A book, which also knows how many pages it has.

    Attributes:
        page_count: The number of pages in the book.
    """

    TYPE = "book"
    EDITABLE_FIELDS = MediaItem.EDITABLE_FIELDS + ("page_count",)

    def __init__(self, title, author, page_count, is_available=True):
        """Create a book with a title, an author and a page count."""
        super().__init__(title, author, is_available)
        self.page_count = _require_positive_int("page_count", page_count)

    def validate_field(self, name, value):
        """Check page_count here and leave title/author to MediaItem."""
        if name == "page_count":
            return _require_positive_int(name, value)
        return super().validate_field(name, value)

    def to_dict(self):
        """Return the item dictionary plus page_count."""
        return {**super().to_dict(), "page_count": self.page_count}

    def __str__(self):
        """Return the book as "Title by Author, N pages [Available/Checked Out]"."""
        return f"{self.title} by {self.author}, {self.page_count} pages [{self.status}]"


class DVD(MediaItem):
    """A DVD, which is fragile and needs a care reminder on checkout.

    Attributes:
        duration: The running time of the DVD in minutes.
    """

    TYPE = "dvd"
    EDITABLE_FIELDS = MediaItem.EDITABLE_FIELDS + ("duration",)
    CARE_REMINDER = "Handle with care: Do not scratch the disc."

    def __init__(self, title, author, duration, is_available=True):
        """Create a DVD with a title, an author and a duration in minutes."""
        super().__init__(title, author, is_available)
        self.duration = _require_positive_int("duration", duration)

    def checkout(self):
        """Check the DVD out and add the care reminder to the success message.

        Raises:
            ItemStateError: If the DVD is already checked out.
        """
        return f"{super().checkout()}. {self.CARE_REMINDER}"

    def validate_field(self, name, value):
        """Check duration here and leave title/author to MediaItem."""
        if name == "duration":
            return _require_positive_int(name, value)
        return super().validate_field(name, value)

    def to_dict(self):
        """Return the item dictionary plus duration."""
        return {**super().to_dict(), "duration": self.duration}

    def __str__(self):
        """Return the DVD as "Title by Author, N min [Available/Checked Out]"."""
        return f"{self.title} by {self.author}, {self.duration} min [{self.status}]"


class LibraryCollection:
    """A container that holds the library's media items, keyed by id.

    Attributes:
        items: The MediaItem objects (or subclasses) in the collection.
    """

    # Changing these through update_item() would break the item's identity or state.
    PROTECTED_FIELDS = ("id", "type", "is_available")

    def __init__(self):
        """Create an empty collection."""
        self.items = []
        # Kept separately from len(items) so ids are never reused after a delete.
        self._next_id = 1

    def add_item(self, item):
        """Add a MediaItem, Book or DVD and return its new id.

        Raises:
            TypeError: If item is not a MediaItem.
            ValueError: If item already belongs to a collection.
        """
        if not isinstance(item, MediaItem):
            raise TypeError("Only MediaItem objects can be added.")
        if item.id is not None:
            raise ValueError(f"'{item.title}' already has id {item.id}.")
        item.id = self._next_id
        self._next_id += 1
        self.items.append(item)
        return item.id

    def get_item(self, item_id):
        """Return the item with item_id.

        Raises:
            ItemNotFoundError: If no item has that id.
        """
        for item in self.items:
            if item.id == item_id:
                return item
        raise ItemNotFoundError(f"Item {item_id} not found.")

    def list_items(self, available=None, item_type=None):
        """Return all items, optionally only available ones and/or one type.

        Args:
            available: True or False to filter by availability; None for all.
            item_type: "book", "dvd" or "item" to filter by type; None for all.

        Raises:
            ValueError: If a filter has an invalid value.
        """
        if available not in (None, True, False):
            raise ValueError("available must be true or false.")
        valid_types = [cls.TYPE for cls in (MediaItem, Book, DVD)]
        if item_type is not None and item_type not in valid_types:
            raise ValueError(f"type must be one of: {', '.join(valid_types)}.")
        return [
            item for item in self.items
            if (available is None or item.is_available == available)
            and (item_type is None or item.TYPE == item_type)
        ]

    def update_item(self, item_id, **fields):
        """Change the given editable fields of an item and return the item.

        All fields are checked before any of them is changed, so a bad value
        never leaves the item half-updated.

        Raises:
            ItemNotFoundError: If no item has that id.
            ValueError: If a field is protected, not editable for this type,
                or has an invalid value.
        """
        item = self.get_item(item_id)
        checked = {}
        for name, value in fields.items():
            if name in self.PROTECTED_FIELDS:
                raise ValueError(f"'{name}' cannot be changed.")
            if name not in item.EDITABLE_FIELDS:
                raise ValueError(
                    f"'{name}' is not an editable field for a {item.TYPE}. "
                    f"Editable: {', '.join(item.EDITABLE_FIELDS)}."
                )
            checked[name] = item.validate_field(name, value)
        for name, value in checked.items():
            setattr(item, name, value)
        return item

    def remove_item(self, item_id):
        """Remove the item with item_id from the collection.

        Raises:
            ItemNotFoundError: If no item has that id.
            ItemStateError: If the item is checked out.
        """
        item = self.get_item(item_id)
        if not item.is_available:
            raise ItemStateError(f"Cannot delete '{item.title}' while it is checked out.")
        self.items.remove(item)
