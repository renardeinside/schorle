import * as proto from "./proto_gen/protobuf/message";

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
socket.onmessage = (raw_event) => {
    // all incoming messages are protobuf encoded
    console.log(`received raw event ${raw_event.data}`);
    let event = proto.ReloadEvent.decode(new Uint8Array(raw_event.data));
    if (event) {
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
                // re-register all event handlers
                registerEventHandlers();
            });
    } else {
        console.warn(`unknown event type ${raw_event.data}`);
    }
};


// List of all possible events
const events = [
    'change',
    'click', 'dblclick',
    'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'mouseenter', 'mouseleave',
    'keydown', 'keyup', 'keypress',
    'submit', 'change',
    'focus', 'blur', 'copy', 'cut', 'paste',
    'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop',
    'resize', 'scroll', 'select', 'load', 'unload'
];

const sendEventToWebSocket = (event: Event) => {
    // stringify the whole event and send it to the websocket
    // const data = {
    //     type: event.type,
    //     target: (event.target as Element).id,
    //     timestamp: event.timeStamp
    // };
    // console.log(`sending event ${JSON.stringify(data)} to websocket`);
    // socket.send(JSON.stringify(data));
};

const registerEventHandlers = () => {
    console.log('registering event handlers');
    document.querySelectorAll('[id^="schorle-"]').forEach(element => {
        console.log(`adding event listeners to ${element.id}`)
        events.forEach(event => {
            element.addEventListener(event, sendEventToWebSocket);
        });
    });
    console.log('done registering event handlers');
}

window.onload = () => {
    registerEventHandlers();
}