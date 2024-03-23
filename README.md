<p align="center">
    <img src="https://raw.githubusercontent.com/renardeinside/schorle/main/raw/with_text.svg" class="align-center" height="150" alt="logo" />
</p>

**`Schorle` (pronounced as [ˈʃɔʁlə](https://en.wikipedia.org/wiki/Schorle)) is a server-driven UI kit for Python with
async support.**

---

<p align="center">
    <a href="https://pypi.org/project/schorle/">
        <img src="https://img.shields.io/pypi/v/schorle?color=green&amp;style=for-the-badge" alt="Latest Python Release"/>
    </a>
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="We use black for formatting"/>
    <a href="https://codecov.io/gh/renardeinside/schorle">
        <img src="https://img.shields.io/codecov/c/gh/renardeinside/schorle?style=for-the-badge"
             alt="codecov"/>
    </a>
</p>

---

**Note:** This project is in an early stage of development. It is not ready for production use.

## Installation

```bash
pip install schorle
```

## Usage

Take a look at the [examples](examples) directory.

## Concepts

### Elements

TODO: rewrite

### Reacting to client-side events

TODO: rewrite

### Server-side effects

TODO: rewrite

## Running the application

Schorle application is a thin wrapper around [FastAPI](https://fastapi.tiangolo.com/). To run the application,
use `uvicorn`:

```bash
uvicorn examples.todo:app --reload
```

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) - web framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [DaisyUI](https://daisyui.com/) - Component library for Tailwind CSS
- [Pydantic](https://docs.pydantic.dev/latest/) - classes and utilities for elements
- [HTMX](https://htmx.org/) - server interop
- [Hyperscript](https://hyperscript.org/) - client-side scripting
-

## Roadmap

- [ ] Add more elements
- [ ] Add hot reload
- [x] Add support for icons
- [x] Add support for onload events
- [ ] Add convenient attributes API
- [ ] Add more examples
- [ ] Add tests
- [ ] Add CI/CD
- [ ] Add documentation
- [ ] Add support for Plotly-based charts
- [ ] Add support for Vega-based charts
- [ ] Refactor the imports