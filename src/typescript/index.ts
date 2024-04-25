import { createIcons, icons } from 'lucide';
import { Idiomorph } from 'idiomorph/dist/idiomorph.esm.js';

let processIcons = () => createIcons({ icons });

let getCookieByName = (name: string): string | undefined => {
  let cookies = document.cookie.split(';');
  let sessionId = cookies.find(cookie => cookie.includes(name));
  return sessionId.split('=').at(1);
};

let getSessionId = () => getCookieByName('X-Schorle-Session-Id');
let getDevMode = () => getCookieByName('X-Schorle-Dev-Mode');

let getWsUrl = (subPath: string): string => {
  let protocol = window.location.protocol.replace('http', 'ws');
  let host = window.location.host;
  return `${protocol}//${host}/${subPath}`;
};

let getEventsEndpoint = () => getWsUrl('_schorle/events');
let getDevEndpoint = () => getWsUrl('_schorle/dev/events');

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
      switch (handler.event) {
        case 'click':
          worker.postMessage({ type: 'event', handlerId: handler.handler });
          break;
        case 'input':
          let target = event.target as HTMLInputElement;
          worker.postMessage({ type: 'event', handlerId: handler.handler, value: target.value });
          break;
      }

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

  Idiomorph.morph(target, event.data.html, event.data.config);
  processPage(worker);
};

let showDevLoader = () => {
  document.getElementById('dev-loader')!.classList.remove('hidden');
};

let hideDevLoader = () => {
  document.getElementById('dev-loader')!.classList.add('hidden');
};


let refetchPage = () => {
  fetch(window.location.href, { cache: 'reload' }).then(
    (response) => response.text().then((html) => {
        let newDoc = new DOMParser().parseFromString(html, 'text/html');

        // process the theme
        let theme = document.documentElement.getAttribute('data-theme');
        let newTheme = newDoc.documentElement.getAttribute('data-theme');

        if (theme !== newTheme) {
          document.documentElement.setAttribute('data-theme', newTheme);
        }

        // process the title
        let title = document.title;
        let newTitle = newDoc.title;

        if (title !== newTitle) {
          document.title = newTitle;
        }

        // process the div with schorle-page id

        let page = document.getElementById('schorle-page');
        let newPage = newDoc.getElementById('schorle-page');

        if (page && newPage) {
          page.innerHTML = newPage.innerHTML;
        }

        document.dispatchEvent(new Event('DOMContentLoaded'));
        hideDevLoader();
      }
    ))
    .catch(() => {
      // retry after 1 second
      setTimeout(refetchPage, 1000);
    });
};

let devReload = () => {
  console.log('[dev] reloading page...');
  showDevLoader();
  refetchPage();
};

document.addEventListener('DOMContentLoaded', () => {
  let sessionId = getSessionId();
  if (!sessionId) {
    console.error('No session id found, cannot start worker.');
    return;
  } else {
    console.log('Session id found, starting worker.');
    let worker = new Worker('/_schorle/js/workers/mainWorker.js');
    worker.postMessage({ type: 'init', sessionId: sessionId, wsUrl: getEventsEndpoint() });
    worker.addEventListener('message', (event) => processEvent(event, worker));
    processPage(worker);
  }

  let devMode = getDevMode();
  if (devMode === 'true') {
    console.log('Dev mode enabled');
    let devIo = new WebSocket(getDevEndpoint());
    devIo.addEventListener('close', devReload);
  }
});