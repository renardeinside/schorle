from dataclasses import dataclass, field
from typing import List, Union

from lxml.etree import _Element


@dataclass
class Difference:
    """Dataclass to store differences between lxml elements"""

    left_element: _Element | None
    right_element: _Element | None
    attribute_changes: List[str] = field(default_factory=list)
    children_changes: List["Difference"] = field(default_factory=list)
    text_change: Union[str, None] = None


class Comparator:
    """Comparator class for recursively comparing two lxml elements and returning a difference"""

    @classmethod
    def compare(cls, left: _Element, right: _Element) -> Difference:
        """Recursively compare two lxml elements and return the differences"""
        attribute_changes = []
        children_changes = []
        text_change = None

        # Compare attributes
        for key in set(left.attrib) | set(right.attrib):
            if left.attrib.get(key) != right.attrib.get(key):
                attribute_changes.append(key)

        # Compare text content
        if left.text != right.text:
            text_change = right.text

        # Compare children
        left_children = list(left)
        right_children = list(right)

        # Recursively compare each child
        for left_child, right_child in zip(left_children, right_children):
            child_difference = cls.compare(left_child, right_child)
            children_changes.append(child_difference)

        # Handle added or removed children
        if len(left_children) < len(right_children):
            for added_child in right_children[len(left_children) :]:
                children_changes.append(Difference(None, added_child))

        elif len(left_children) > len(right_children):
            for removed_child in left_children[len(right_children) :]:
                children_changes.append(Difference(removed_child, None))

        # Check for text change in children
        for left_child, right_child in zip(left_children, right_children):
            if left_child.text != right_child.text:
                children_changes.append(Difference(left_child, right_child, text_change=right_child.text))

        return Difference(left, right, attribute_changes, children_changes, text_change)
