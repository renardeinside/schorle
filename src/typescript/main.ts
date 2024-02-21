// @ts-ignore
import {Idiomorph} from 'idiomorph/dist/idiomorph.esm';
import {createIcons, icons} from 'lucide';
import {decode, encode} from "@msgpack/msgpack";

interface Cookie {
    name: string;
    value: string;
}

interface ClientMessage {
    trigger: string;
    target: string;
    value: string | null;
    meta?: { [key: string]: string };
}

interface ServerMessage {
    target: string;
    html: string;
    action?: string;
}

const parseCookie = (rawString: string): Array<Cookie> => {
    const cookies = rawString.split(';');
    return cookies.map((cookie) => {
        const [name, value] = cookie.split('=').map((part) => part.trim());
        return {name, value};
    });
}

const prepareIO = () => {
    // prepare a websocket with sessionId passed as protocol
    // it should connect to the server at the same host and port, with same scheme
    let scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    let socket = new WebSocket(`${scheme}://${window.location.host}/_schorle/events`);
    socket.binaryType = 'arraybuffer';
    return socket;
}

const runningInDevMode = (): boolean => {
    // check if tag <meta name="schorle-dev" content="true"/> is present
    let meta = document.querySelector('meta[name="schorle-dev"]');
    return meta !== null;

}

const triggerable = () => {
    // find all elements inside element with id schorle-page with sle-triggers attribute
    // return them as an array
    let page = document.getElementById('schorle-page');
    if (page === null) {
        throw new Error('Element with id schorle-page not found');
    }

    return Array.from(page.querySelectorAll('[sle-trigger]'));
}

const sendWhenReady = async (io: WebSocket, message: ClientMessage) => {
    if (io.readyState === WebSocket.OPEN) {
        io.send(encode(message));
    } else {
        setTimeout(() => sendWhenReady(io, message), 100);
    }
}


const defaultListener = (e: Event, io: WebSocket, event: string, trigger: Element) => {
    sendWhenReady(
        io,
        {
            trigger: event!,
            target: trigger.id,
            value: e.target instanceof HTMLInputElement ? e.target.value : null
        }
    ).catch(e => console.error(`Error sending message: ${e} on event ${trigger.id}`))
}

const fileUploadListener = (e: Event) => {
    // get the file from the input
    // and send it in parts to the server
    // add the file name to the message meta
    // do it for each file
    let input = e.target as HTMLInputElement;
    let files = input.files;
    if (files === null) {
        throw new Error('No files found');
    }
    let formData = new FormData();

    Array.from(files).forEach((file) => {
        formData.append('uploaded_files', file);
    });

    fetch(`/_schorle/upload`, {
        method: 'POST',
        body: formData,
        headers: {"X-Schorle-Trigger-Id": input.id}
    }).catch(e => console.error(e));
}

const applyTriggers = async (io: WebSocket) => {
    triggerable().filter(
        (trigger) => trigger.getAttribute('sle-processed') === null
    ).forEach((trigger) => {

        let event = trigger.getAttribute('sle-trigger');
        if (event === null) {
            throw new Error('Attribute sle-trigger not found');
        }

        if (event === 'change' && trigger instanceof HTMLInputElement && trigger.type === 'file') {
            trigger.addEventListener(event, fileUploadListener);
        } else {
            trigger.addEventListener(event, (e) => defaultListener(e, io, event!, trigger));
        }


        // mark the element as processed
        trigger.setAttribute('sle-processed', 'true');

        // if the event is load, send a message to the server immediately
        if (event === 'load') {
            sendWhenReady(io, {
                trigger: event,
                target: trigger.id,
                value: null
            });
        }
    });
}

const processCookies = () => {
    let cookies = parseCookie(document.cookie);
    let expectedCookieNames = ['X-Schorle-Session-Id', 'X-Schorle-Session-Path'];
    expectedCookieNames.forEach((cookieName) => {
        let cookie = cookies.find((cookie) => cookie.name === cookieName);
        if (cookie === undefined) {
            throw new Error(`Cookie ${cookieName} not found`);
        }
    });
}

const loadingIndicatorId = 'schorle-loading-indicator';
const devLoadingElement = () => {
    return document.getElementById(loadingIndicatorId);
}

const devToggleLoading = (b: boolean) => {
    let loading = devLoadingElement();
    if (loading !== null && runningInDevMode()) {
        if (b) {
            loading.classList.remove("hidden");
        } else {
            loading.classList.add("hidden");
        }
    }
}


const devReload = () => {
    console.log('[schorle][dev mode] reloading page');
    devToggleLoading(true);
    fetch(window.location.href, {cache: 'reload'}).then((response) => {
        if (response.ok) {
            return response.text();
        } else {
            throw new Error(`HTTP error: ${response.status}`);
        }
    }).then((html) => {
        let newDocument = new DOMParser().parseFromString(html, 'text/html');
        // check if data-theme is presented on html tag and set it
        let theme = newDocument.documentElement.getAttribute('data-theme');
        if (theme !== null) {
            document.documentElement.setAttribute('data-theme', theme);
        }

        // morph the head and body
        Idiomorph.morph(document.head, newDocument.head);
        Idiomorph.morph(document.body, newDocument.body, {
            callbacks: {
                beforeNodeMorphed: (node: Node) => {
                    // skip an element with id loadingIndicatorId
                    if (node instanceof HTMLElement && node.id === loadingIndicatorId) {
                        return false;
                    }
                    else if (node instanceof HTMLInputElement) {
                        // clear the value of input elements
                        node.value = '';
                    }
                }
            }
        });
        schorleSetup();
    }).catch(e => console.error(e));
    console.log('[schorle][dev mode] finished reloading page');
}

const schorleSetup = () => {
    console.log(`[schorle] setup started`)
    devToggleLoading(true);
    processCookies();

    // create icons
    createIcons({icons});

    // prepare a websocket with sessionId passed as protocol
    const io = prepareIO();

    io.onerror = (e) => {
        console.error(e);
    }
    io.onclose = (e) => {
        if (e.code === 1012 && runningInDevMode()) {
            console.log(`[schorle] connection closed by server, reloading page`);
            devReload();
        }
    }

    io.onmessage = (e) => {
        let payload = decode(e.data) as ServerMessage;
        let target = document.getElementById(payload.target);
        if (target === null) {
            throw new Error(`Element with id ${payload.target} not found`);
        }
        if (payload.action === 'morph') {
            console.log(`[schorle] morphing element with id ${payload.target} and html ${payload.html}`);
            Idiomorph.morph(target, payload.html, {
                callbacks: {
                    beforeAttributeUpdated: (attributeName: string) => {
                        if (attributeName === 'sle-processed') {
                            console.log(`[schorle] skipping attribute sle-processed`);
                            return false;
                        }
                    }
                }
            });
            applyTriggers(io).catch(e => console.error(e));
        } else if (payload.action === 'clear' && target instanceof HTMLInputElement) {
            console.log(`[schorle] clearing element with id ${payload.target}`);
            target.value = '';
        }
    }

    applyTriggers(io).catch(e => console.error(e));
    console.log(`[schorle] setup finished`)
    devToggleLoading(false);
}

const main = () => {
    document.addEventListener('DOMContentLoaded', schorleSetup);
};

main();