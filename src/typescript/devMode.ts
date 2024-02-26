// @ts-ignore
import { Idiomorph } from 'idiomorph/dist/idiomorph.esm';

export const runningInDevMode = (): boolean => {
  // check if tag <meta name="schorle-dev" content="true"/> is present
  let meta = document.querySelector('meta[name="schorle-dev"]');
  return meta !== null;
};
const loadingIndicatorId = 'schorle-loading-indicator';
const devLoadingElement = () => {
  return document.getElementById(loadingIndicatorId);
};
export const devToggleLoading = (b: boolean) => {
  let loading = devLoadingElement();
  if (loading !== null && runningInDevMode()) {
    if (b) {
      loading.classList.remove('hidden');
    } else {
      loading.classList.add('hidden');
    }
  }
};
export const devReload = (func: () => void) => {
  console.log('[schorle][dev mode] reloading page');
  devToggleLoading(true);
  fetch(window.location.href, { cache: 'reload' })
    .then((response) => {
      if (response.ok) {
        return response.text();
      } else {
        throw new Error(`HTTP error: ${response.status}`);
      }
    })
    .then((html) => {
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
            } else if (node instanceof HTMLInputElement) {
              // clear the value of input elements
              node.value = '';
            }
          }
        }
      });
      func();
    })
    .catch((e) => {
      console.error(`[schorle][dev mode] failed to reload page: ${e}`);
    });
  console.log('[schorle][dev mode] finished reloading page');
};
