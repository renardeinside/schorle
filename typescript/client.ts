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


const devReload = (theme: string) => {
    fetch(window.location.href)
        .then((response) => response.text())
        .then((html) => {
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, "text/html");
            const app = newDoc.getElementById("schorle-page");

            // apply theme to html element data-theme attribute
            document.documentElement.setAttribute('data-theme', theme);
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
}

const updateElementById = (id: string, html: string) => {
    console.log(`updating element with id ${id} with payload ${html}`);

    const parser = new DOMParser();
    const newDoc = parser.parseFromString(html, "text/html");
    const element = newDoc.getElementById(id);
    if (element) {
        let existingElement = document.getElementById(id);

        if (existingElement) {
            existingElement.replaceWith(element);
        } else {
            document.body.appendChild(element);
        }
    } else {
        console.error(`could not find element with id ${id}`);
    }
}

// a handler for incoming messages
socket.onmessage = async (raw_event: MessageEvent<ArrayBuffer>) => {
    // all incoming messages are protobuf encoded
    console.log(`received raw event ${raw_event.data}`);
    // decode the message by converting Blob to Uint8Array and then to a protobuf message
    const event = proto.Event.decode(new Uint8Array(raw_event.data));

    switch (event.event?.$case) {
        case 'reload':
            devReload(event.event.reload.theme);
            break;
        case 'elementUpdate':
            updateElementById(event.event.elementUpdate.id, event.event.elementUpdate.payload);
            break;
        default:
            console.warn(`decoded event ${JSON.stringify(event)}`);
    }


    // if (event.event?.$case === 'reload') {
    //     // fetch the current page again, parse the HTML and replace the div with the id "schorle-app"
    //     devReload();
    // } else {
    //     console.warn(`decoded event ${JSON.stringify(event)}`);
    // }
};


// List of all possible events
const events = [
    'click',
    // 'click', 'dblclick',
    // 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'mouseenter', 'mouseleave',
    // 'keydown', 'keyup', 'keypress',
    // 'submit', 'change',
    // 'focus', 'blur', 'copy', 'cut', 'paste',
    // 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop',
    // 'resize', 'scroll', 'select', 'load', 'unload'
];

const sendEventToWebSocket = (event: MouseEvent) => {
    let target = event.target as HTMLButtonElement;
    let encodedEvent = proto.Event.encode(
        {
            event: {
                $case: 'click',
                click: {
                    id: target.id,
                    ts: new Date(),
                    path: window.location.pathname,
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
            if (element instanceof HTMLButtonElement) {
                element.onclick = (event) => {
                    sendEventToWebSocket(event);
                };
            }
        });
    console.log('done registering event handlers');
}

window.onload = () => {
    registerEventHandlers();
}