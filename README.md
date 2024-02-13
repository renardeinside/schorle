<p align="center">
    <img src="https://raw.githubusercontent.com/renardeinside/schorle/main/raw/with_text.svg" class="align-center" height="150" alt="logo" />
</p>

**`Schorle` (pronounced as [ˈʃɔʁlə](https://en.wikipedia.org/wiki/Schorle)) is a server-driven UI kit for Python with
async support.**

---

<p align="center">
    <img src="https://img.shields.io/pypi/v/schorle?color=green&amp;style=for-the-badge" alt="Latest Python Release"/>
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="We use black for formatting"/>
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
uvicorn examples.simple:app --reload
```

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) - web framework
- [HTMX](https://htmx.org/) - client-side library for dynamic HTML
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [DaisyUI](https://daisyui.com/) - Component library for Tailwind CSS
- [Pydantic](https://docs.pydantic.dev/latest/) - classes and utilities for elements


## Roadmap

- [ ] Add more elements
- [ ] Introduce `suspense` for loading states
- [ ] Add more examples
- [ ] Add tests
- [ ] Add CI/CD
- [ ] Add documentation
- [ ] Add support for Plotly-based charts
- [ ] Refactor the imports