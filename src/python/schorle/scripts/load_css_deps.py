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
    CdnInfo("https://cdn.tailwindcss.com", "tailwind", "tailwind.min.js"),
    CdnInfo("https://cdn.jsdelivr.net/npm/daisyui@4.10.2/dist/full.min.css", "daisyui", "daisyui.min.css"),
]

dist_path = ASSETS_PATH / "dist"


def load_deps():
    print("Loading CSS dependencies...")  # noqa T201
    if not dist_path.exists():
        dist_path.mkdir()

    for cdn in cdns:
        print(f"Fetching {cdn.name}...")  # noqa T201
        _text = cdn.fetch()

        if cdn.name == "tailwind":
            _text = replace_tw_message(_text)

        output_path = dist_path / cdn.output_file_name

        if output_path.exists():
            output_path.unlink()

        with open(output_path, "w") as f:
            f.write(_text)

        with open(output_path.with_suffix(f"{output_path.suffix}.br"), "wb") as f:
            f.write(brotli.compress(_text.encode("utf-8")))

        print(f"Saved {cdn.name} to {output_path}")  # noqa T201

    print("All CSS dependencies loaded!")  # noqa T201


if __name__ == "__main__":
    load_deps()
