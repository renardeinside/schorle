// @ts-ignore
import { Idiomorph } from 'idiomorph/dist/idiomorph.esm';
import { createIcons, icons } from 'lucide';
import { decode } from '@msgpack/msgpack';
import { Action, ServerMessage } from './models';
import { devReload } from './devMode';
import { sendWhenReady } from './io';

interface Cookie {
  name: string;
  value: string;
}

const parseCookie = (rawString: string): Array<Cookie> => {
  const cookies = rawString.split(';');
  return cookies.map((cookie) => {
    const [name, value] = cookie.split('=').map((part) => part.trim());
    return { name, value };
  });
};

const prepareIO = () => {
  // prepare a websocket with sessionId passed as protocol
  // it should connect to the server at the same host and port, with same scheme
  let scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  let socket = new WebSocket(
    `${scheme}://${window.location.host}/_schorle/events`
  );
  socket.binaryType = 'arraybuffer';
  return socket;
};

const runningInDevMode = (): boolean => {
  // check if tag <meta name="schorle-dev" content="true"/> is present
  let meta = document.querySelector('meta[name="schorle-dev"]');
  return meta !== null;
};

const triggerable = () => {
  // find all elements inside element with id schorle-page with sle-triggers attribute
  // return them as an array
  let page = document.getElementById('schorle-page');
  if (page === null) {
    throw new Error('Element with id schorle-page not found');
  }

  return Array.from(page.querySelectorAll('[sle-trigger]'));
};

const defaultListener = async (
  io: WebSocket,
  event: string,
  trigger: Element
) => {
  await sendWhenReady(io, {
    trigger: event!,
    target: trigger.id,
    value: trigger instanceof HTMLInputElement ? trigger.value : null
  }).catch((e) =>
    console.error(`Error sending message: ${e} on event ${trigger.id}`)
  );
};

const fileUploadListener = (e: Event) => {
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
    headers: { 'X-Schorle-Trigger-Id': input.id }
  }).catch((e) => console.error(e));
};

const applyTriggers = async (io: WebSocket) => {
  triggerable()
    .filter((trigger) => trigger.getAttribute('sle-processed') === null)
    .forEach((trigger) => {
      let event = trigger.getAttribute('sle-trigger');
      if (event === null) {
        throw new Error('Attribute sle-trigger not found');
      }

      if (
        event === 'change' &&
        trigger instanceof HTMLInputElement &&
        trigger.type === 'file'
      ) {
        trigger.removeEventListener(event, fileUploadListener);
        trigger.addEventListener(event, fileUploadListener);
      } else {
        trigger.addEventListener(event, () => {
          defaultListener(io, event!, trigger);
        });
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
};

const processCookies = () => {
  let cookies = parseCookie(document.cookie);
  let expectedCookieNames = ['X-Schorle-Session-Id', 'X-Schorle-Session-Path'];
  expectedCookieNames.forEach((cookieName) => {
    let cookie = cookies.find((cookie) => cookie.name === cookieName);
    if (cookie === undefined) {
      throw new Error(`Cookie ${cookieName} not found`);
    }
  });
};

const loadingIndicatorId = 'schorle-loading-indicator';
const devLoadingElement = () => {
  return document.getElementById(loadingIndicatorId);
};

const devToggleLoading = (b: boolean) => {
  let loading = devLoadingElement();
  if (loading !== null && runningInDevMode()) {
    if (b) {
      loading.classList.remove('hidden');
    } else {
      loading.classList.add('hidden');
    }
  }
};

const schorleSetup = () => {
  console.log(`[schorle] setup started`);
  devToggleLoading(true);
  processCookies();

  // create icons
  createIcons({ icons });

  // prepare a websocket with sessionId passed as protocol
  const io = prepareIO();

  io.onerror = (e) => {
    console.error(e);
  };
  io.onclose = (e) => {
    if (e.code === 1012 && runningInDevMode()) {
      devReload(schorleSetup);
    }
  };

  io.onmessage = (e) => {
    let message = decode(e.data) as ServerMessage;
    let target = document.getElementById(message.target);
    if (target === null) {
      throw new Error(`Element with id ${message.target} not found`);
    }
    console.log(`[schorle] received message: ${JSON.stringify(message)}`);

    switch (message.action) {
      case Action.morph:
        Idiomorph.morph(target, message.payload, {
          callbacks: {
            beforeAttributeUpdated: (attributeName: string) => {
              if (attributeName === 'sle-processed') {
                return false;
              }
            }
          }
        });
        break;
      case Action.clear:
        if (target instanceof HTMLInputElement) {
          console.log(`[schorle] clearing element with id ${message.target}`);
          target.value = '';
        } else {
          console.warn(
            `[schorle] element with id ${message.target} is not an input`
          );
        }
        break;
      default:
        throw new Error(`Unknown action: ${message.action}`);
    }

    applyTriggers(io).catch((e) => console.error(e));
  };

  applyTriggers(io).catch((e) => console.error(e));
  console.log(`[schorle] setup finished`);
  devToggleLoading(false);
};

const main = () => {
  document.addEventListener('DOMContentLoaded', schorleSetup);
};

main();
