import { createIcons, icons } from 'lucide';
import { Idiomorph } from 'idiomorph/dist/idiomorph.esm.js';

let processIcons = () => createIcons({ icons });

let getSessionId = () => {
  let cookies = document.cookie.split(';');
  let sessionId = cookies.find(cookie => cookie.includes('X-Schorle-Session-Id'));
  return sessionId.split('=')[1];
};

let getWsUrl = () => {
  let protocol = window.location.protocol.replace('http', 'ws');
  let host = window.location.host;
  return `${protocol}//${host}/_schorle/events`;
};

let findElementsWithHandlers = (): Element[] => {
  // find all elements with attribute sle-on
  let elements = document.querySelectorAll('[sle-on]');
  return Array.from(elements);
};

interface ElementData {
  handlers: [{ event: string, handler: (event: Event) => void }];
}

let getElementData = (element: Element): ElementData | undefined => {
  return element['schorle-data'];
};

let setElementData = (element: Element, data: ElementData) => {
  element['schorle-data'] = data;
};

let processElement = (element: Element, worker: Worker) => {
  let handlers: [{ event: string, handler: string }] = JSON.parse(element.getAttribute('sle-on'));
  let handlerFunctions = handlers.map(handler => {
    let handlerFunc = (event: Event) => {
      worker.postMessage({ type: 'event', handlerId: handler.handler });
    };
    return { event: handler.event, handler: handlerFunc };
  }) as [{ event: string, handler: (event: Event) => void }];

  // first, we use the element data to remove any existing handlers
  let existingData = getElementData(element);
  if (existingData) {
    existingData.handlers.forEach(handler => {
      element.removeEventListener(handler.event, handler.handler);
    });
  }

  // then, we set the new handlers
  let newData = { handlers: handlerFunctions };
  setElementData(element, newData);
  newData.handlers.forEach(handler => {
    element.addEventListener(handler.event, handler.handler);
  });

  // finally, we remove the sle-on attribute
  element.removeAttribute('sle-on');
};


let processPage = (worker: Worker) => {
  processIcons();
  let elements = findElementsWithHandlers();
  elements.forEach((element) => processElement(element, worker));
};


let processEvent = (event: MessageEvent, worker: Worker) => {
  console.log('Received event from worker:', event.data);
  let target = document.getElementById(event.data.target);
  if (!target) {
    console.error('Target element not found:', event.data.target);
    return;
  }

  Idiomorph.morph(target, event.data.html);
  processPage(worker);
};

document.addEventListener('DOMContentLoaded', () => {
  let sessionId = getSessionId();
  if (!sessionId) {
    console.error('No session id found, cannot start worker.');
    return;
  } else {
    console.log('Session id found, starting worker.');
    let worker = new Worker('/_schorle/js/workers/mainWorker.js');
    worker.postMessage({ type: 'init', sessionId: sessionId, wsUrl: getWsUrl() });
    worker.addEventListener('message', (event) => processEvent(event, worker));
    processPage(worker);
  }
});