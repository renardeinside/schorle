import requests
from lxml import etree

from schorle.component import Component


class Icon(Component):
    name: str

    def render(self):
        icon_url = f"https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{self.name}.svg"
        response = requests.get(icon_url, timeout=5)
        response.raise_for_status()
        parser = etree.XMLParser(ns_clean=True, resolve_entities=False, no_network=True)
        # we can disable security check here because we've set the parser to not resolve entities
        # read https://github.com/PyCQA/bandit/issues/767 for more information
        icon = etree.fromstring(response.text, parser)  # noqa: S320
        self.controller.current.append(icon)
