# Schorle

Server-driven UI kit for Python, allowing users to create web, desktop and mobile applications using a single codebase
in Python.

## Concept

Schorle represents a new approach to building user interfaces. It is a server-driven UI kit, which means that the UI is
rendered on the server and then streamed to the client.
This allows for a single codebase to be used for web, desktop and mobile applications.
The UI is defined in Python, which is then compiled to a JSON representation that is sent to the client.
To suffice SSR, the initial response is sent as HTML. As user interactions occur, the UI is updated by sending JSON
patches to the client.
This allows for a very fast and responsive UI, as only the necessary changes are sent and then rendered on the client.

Schorle also logically separates the representation from the state.

Entrypoint for Schorle is the `App` class. It is used to define the UI and the routes of the application.
Each route is associated with a `Page` class, which is used to define the UI of the page:

```python
from schorle import Schorle, Page, div, button, p

app = Schorle()


@app.route("/")
def index():
    with Page() as page:
        with div():
            p("Hello World!")
            button("Click me!")
```