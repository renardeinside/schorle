// create a websocket connection to the server on the origin
const socket = new WebSocket(`ws://${window.location.host}/_schorle/ws`);
// write a handler for the connection
socket.onopen = () => {
    console.log("connected");
};
socket.onclose = () => {
    console.log("disconnected");
};

// a handler for incoming messages
socket.onmessage = (event) => {
    console.log(event.data);
    // all incoming messages are JSON encoded
    const message = JSON.parse(event.data);
    if (message.type === "reload") {
        console.log('received "reload" message');
        console.log(`reloading page ${window.location.href}`);

        // fetch the current page again, parse the HTML and replace the div with the id "schorle-app"
        fetch(window.location.href)
            .then((response) => response.text())
            .then((html) => {
                const parser = new DOMParser();
                const newDoc = parser.parseFromString(html, "text/html");
                const app = newDoc.getElementById("schorle-app");
                console.log(app);
                if (app) {
                    let existingApp = document.getElementById("schorle-app");

                    if (existingApp) {
                        existingApp.replaceWith(app);
                    } else {
                        document.body.appendChild(app);
                    }
                }
            });
    }
};
