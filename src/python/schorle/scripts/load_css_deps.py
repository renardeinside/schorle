from dataclasses import dataclass
from http import HTTPStatus

import brotli
import requests

from schorle.utils import ASSETS_PATH


@dataclass
class CdnInfo:
    source_url: str
    name: str
    output_file_name: str

    def fetch(self):
        _payload = requests.get(self.source_url, timeout=5)

        if _payload.status_code != HTTPStatus.OK:
            msg = f"Failed to fetch {self.source_url}. Status code: {_payload.status_code}"
            raise Exception(msg)

        return _payload.text


def replace_tw_message(text):
    # Remove the warning message from the tailwind css
    tw_warning = (
        'console.warn("cdn.tailwindcss.com should not be used in production. '
        'To use Tailwind CSS in production, install it as a PostCSS plugin or use the Tailwind CLI: '
        'https://tailwindcss.com/docs/installation");'
    )
    return text.replace(tw_warning, "")


cdns = [
    CdnInfo("https://cdn.tailwindcss.com", "tailwind", "tailwind.min.js.br"),
    CdnInfo("https://cdn.jsdelivr.net/npm/daisyui@4.10.2/dist/full.min.css", "daisyui", "daisyui.min.css.br"),
]

dist_path = ASSETS_PATH / "dist"


def load_deps():
    if not dist_path.exists():
        dist_path.mkdir()

    for cdn in cdns:

        _text = cdn.fetch()

        if cdn.name == "tailwind":
            _text = replace_tw_message(_text)

        output_path = dist_path / cdn.output_file_name

        if output_path.exists():
            output_path.unlink()

        with open(output_path, "wb") as f:
            f.write(brotli.compress(_text.encode("utf-8")))


if __name__ == "__main__":
    load_deps()
