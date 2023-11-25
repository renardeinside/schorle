import * as proto from "./proto_gen/protobuf/message";

// create a websocket connection to the server on the origin
const socket = new WebSocket(`ws://${window.location.host}/_schorle/ws`);
socket.binaryType = "arraybuffer";

// write a handler for the connection
socket.onopen = () => {
    console.log("connected");
};
socket.onclose = () => {
    console.log("disconnected");
};

// a handler for incoming messages
socket.onmessage = async (raw_event: MessageEvent<ArrayBuffer>) => {
    // all incoming messages are protobuf encoded
    console.log(`received raw event ${raw_event.data}`);
    // decode the message by converting Blob to Uint8Array and then to a protobuf message
    const event = proto.Event.decode(new Uint8Array(raw_event.data));
    if (event.event?.$case === 'reload') {
        // fetch the current page again, parse the HTML and replace the div with the id "schorle-app"
        fetch(window.location.href)
            .then((response) => response.text())
            .then((html) => {
                const parser = new DOMParser();
                const newDoc = parser.parseFromString(html, "text/html");
                const app = newDoc.getElementById("schorle-page");
                if (app) {
                    let existingApp = document.getElementById("schorle-page");

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
        console.warn(`decoded event ${JSON.stringify(event)}`);
    }
};


// List of all possible events
const events = [
    'change',
    // 'click', 'dblclick',
    // 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'mouseenter', 'mouseleave',
    // 'keydown', 'keyup', 'keypress',
    // 'submit', 'change',
    // 'focus', 'blur', 'copy', 'cut', 'paste',
    // 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop',
    // 'resize', 'scroll', 'select', 'load', 'unload'
];

const sendEventToWebSocket = (event: Event) => {
    const target = event.target as HTMLInputElement;
    let encodedEvent = proto.Event.encode(
        {
            event: {
                $case: 'inputChange',
                inputChange: {
                    id: target.id,
                    ts: new Date(),
                    path: window.location.pathname,
                    value: {
                        $case: 'text',
                        text: target.value
                    }
                }
            }
        }
    ).finish();

    socket.send(encodedEvent);
};

const registerEventHandlers = () => {
    console.log('registering event handlers');
    document
        .querySelectorAll('[id^="schorle-"]')
        // filter only input elements
        .forEach(element => {
            if (element instanceof HTMLInputElement) {
                console.log(`registering event handlers for ${element.id}`);
                element.addEventListener('change', sendEventToWebSocket);
            }
        });
    console.log('done registering event handlers');
}

window.onload = () => {
    registerEventHandlers();
}