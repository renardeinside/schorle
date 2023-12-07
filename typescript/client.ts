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

const updateAttributesById = (id: string, attributes: { [key: string]: string }) => {
    const element = document.getElementById(id);
    if (element) {
        Object.entries(attributes).forEach(([key, value]) => {
            element.setAttribute(key, value);
        });
    }

}

const updateTextContentById = (id: string, content: string) => {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = content;
    }
}

const updateValueById = (id: string, value: string) => {
    const element = document.getElementById(id) as HTMLInputElement;
    if (element) {
        element.value = value;
    }
}

const updateHtmlById = (id: string, html: string) => {
    console.log(`updating html for ${id}`);
    const element = document.getElementById(id)!;
    const newElement = new DOMParser().parseFromString(html, "text/html").getElementById(id)!;
    element.replaceWith(newElement);
    // re-register all event handlers
    registerEventHandlers();
    console.log(`done updating html for ${id}`);
}

// a handler for incoming messages
socket.onmessage = async (raw_event: MessageEvent<ArrayBuffer>) => {
    // all incoming messages are protobuf encoded
    // decode the message by converting Blob to Uint8Array and then to a protobuf message
    const event = proto.Event.decode(new Uint8Array(raw_event.data));
    console.log(`received event ${JSON.stringify(event)}`);
    switch (event.event?.$case) {
        case 'reload':
            devReload(event.event.reload.theme);
            break;
        case 'attributesUpdate':
            updateAttributesById(event.event.attributesUpdate.id, event.event.attributesUpdate.attributes);
            break;
        case 'textContentUpdate':
            updateTextContentById(event.event.textContentUpdate.id, event.event.textContentUpdate.textContent);
            break;
        case 'valueUpdate':
            updateValueById(event.event.valueUpdate.id, event.event.valueUpdate.value);
            break;
        case 'fullUpdate':
            updateHtmlById(event.event.fullUpdate.id, event.event.fullUpdate.html);
            break;
        default:
            console.warn(`decoded event ${JSON.stringify(event)}`);
    }
};


// List of all possible events
// const events = [
//     'click',
//     // 'click', 'dblclick',
//     // 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'mouseenter', 'mouseleave',
//     // 'keydown', 'keyup', 'keypress',
//     // 'submit', 'change',
//     // 'focus', 'blur', 'copy', 'cut', 'paste',
//     // 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop',
//     // 'resize', 'scroll', 'select', 'load', 'unload'
// ];

const sendClickEvent = (event: MouseEvent) => {
    let target = event.target as HTMLButtonElement;
    let encodedEvent = proto.Event.encode(
        {
            event: {
                $case: 'click',
                click: {
                    targetId: target.id,
                    ts: new Date(),
                }
            }
        }
    ).finish();

    socket.send(encodedEvent);
};

const sendInputEvent = (event: Event) => {
    let target = event.target as HTMLInputElement;

    let encodedEvent = proto.Event.encode(
        {
            event: {
                $case: 'inputChange',
                inputChange: {
                    targetId: target.id,
                    reactiveId: target.getAttribute('schorle-bind')!,
                    ts: new Date(),
                    value: target.value,
                }
            }
        }
    ).finish();

    socket.send(encodedEvent);

}
const registerEventHandlers = () => {
    console.log('registering event handlers');
    document
        .querySelectorAll('[id^="schorle-"]')
        // filter only input elements
        .forEach(element => {
            if (element instanceof HTMLButtonElement) {
                console.log(`registering click handler for ${element.id}`);
                element.onclick = sendClickEvent;
            } else if (element.getAttribute('schorle-bind') && element instanceof HTMLInputElement) {
                console.log(`registering input handler for ${element.id}`);
                element.oninput = sendInputEvent;
            }
        });
    console.log('done registering event handlers');
}

window.onload = () => {
    registerEventHandlers();
}