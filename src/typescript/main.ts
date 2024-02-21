// @ts-ignore
import {Idiomorph} from 'idiomorph/dist/idiomorph.esm';
import {createIcons, icons} from 'lucide';

interface Cookie {
    name: string;
    value: string;
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
    return new WebSocket(`${scheme}://${window.location.host}/_schorle/events`);
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

const sendWhenReady = async (io: WebSocket, message: string) => {
    if (io.readyState === WebSocket.OPEN) {
        io.send(message);
    } else {
        setTimeout(() => sendWhenReady(io, message), 100);
    }
}

const applyTriggers = async (io: WebSocket) => {
    triggerable().filter(
        (trigger) => trigger.getAttribute('sle-processed') === null
    ).forEach((trigger) => {

        let event = trigger.getAttribute('sle-trigger');
        if (event === null) {
            throw new Error('Attribute sle-trigger not found');
        }

        let listener = (e: Event) => {
            sendWhenReady(
                io,
                JSON.stringify({
                    trigger: event,
                    target: trigger.id,
                    value: event === 'click' ? null : (e.target as HTMLInputElement).value
                })
            ).catch(e => console.error(`Error sending message: ${e} on event ${trigger.id}`))
        };

        trigger.addEventListener(event, listener);

        // mark the element as processed
        trigger.setAttribute('sle-processed', 'true');

        // if the event is load, send a message to the server immediately
        if (event === 'load') {
            sendWhenReady(io, JSON.stringify({
                trigger: event,
                target: trigger.id,
                value: null
            }));
        }
    });
}

const main = () => {
    document.addEventListener('DOMContentLoaded', () => {
        // parse the cookie and extract the value of X-Schorle-Session-Id into a variable
        let cookies = parseCookie(document.cookie);
        let expectedCookieNames = ['X-Schorle-Session-Id', 'X-Schorle-Session-Path'];
        expectedCookieNames.forEach((cookieName) => {
            let cookie = cookies.find((cookie) => cookie.name === cookieName);
            if (cookie === undefined) {
                throw new Error(`Cookie ${cookieName} not found`);
            }
        });

        // create icons
        createIcons({icons});

        // prepare a websocket with sessionId passed as protocol
        const io = prepareIO();

        io.onerror = (e) => {
            console.error(e);
        }
        io.onclose = (e) => {
            console.warn(`Connection closed with code ${e.code} and reason ${e.reason}`);
        }

        io.onmessage = (e) => {
            let payload: { target: string, html: string } = JSON.parse(e.data);
            let target = document.getElementById(payload.target);
            if (target === null) {
                throw new Error(`Element with id ${payload.target} not found`);
            }
            Idiomorph.morph(target, payload.html, {
                callbacks: {
                    beforeAttributeUpdated: (attributeName: string) => {
                        if (attributeName === 'sle-processed') {
                            return false;
                        }
                    }
                }
            });

            applyTriggers(io).catch(e => console.error(e));
        }

        applyTriggers(io).catch(e => console.error(e));
    });
};

main();