let defineLucide = () => {
  htmx.defineExtension('lucide', {
    onEvent: (name) => {
      // supported events: afterProcessNode, htmx:load
      let supportedEvents = ['afterProcessNode', 'htmx:load'];
      if (supportedEvents.includes(name)) {
        lucide.createIcons();
      }
    }
  });
};

defineLucide();

let devLoader = () => {
  return document.getElementById('dev_loader');
};

let refetchPage = (retry, retries) => {
  fetch(window.location.href)
    .then((response) => {
      if (response.ok) {
        console.log('Connection re-established, refreshing the window...');
        response.text().then((text) => {
          const parser = new DOMParser();
          const newDocument = parser.parseFromString(text, 'text/html');
          for (let attribute of newDocument.documentElement.attributes) {
            document.documentElement.setAttribute(attribute.name, attribute.value);
          }
          // remove all attributes that are not present in the new document
          for (let attribute of document.documentElement.attributes) {
            if (!newDocument.documentElement.hasAttribute(attribute.name)) {
              document.documentElement.removeAttribute(attribute.name);
            }
          }
          // replace head
          Idiomorph.morph(document.head, newDocument.head, { head: { style: 'morph' } });
          // morph body
          Idiomorph.morph(document.body, newDocument.body);
          htmx.process(document.body);
          addDevTools();
          lucide.createIcons();
        });

      } else {
        retries++;
        setTimeout(retry, Math.pow(2, retries) * 1000);
      }
    })
    .catch((error) => {
      retries++;
      setTimeout(retry, Math.pow(2, retries) * 1000);
    });
};

let addDevTools = () => {
  const schorleDev = document.querySelector('meta[name="schorle-dev"]');
  if (schorleDev) {
    if (window.Worker) {
      // Create a new web worker from the worker script
      const worker = new Worker('/_schorle/dev/assets/worker.js');
      worker.postMessage({ origin: window.location.origin });
      worker.onmessage = (event) => {
        // retry the connection using fetch with exponential backoff
        if (event.data.reload) {
          let retries = 0;
          devLoader().classList.remove('hidden');
          const retry = () => {
            refetchPage(retry, retries);
          };
          setTimeout(retry, 100);
        }
      };
    } else {
      console.log('Web workers are not supported in this browser.');
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  addDevTools();
});