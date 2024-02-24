from types import MethodType
from typing import Callable

from lxml.etree import _Element as Element

LXMLElement = Element
Reactives = dict[str, dict[str, MethodType | Callable]]
