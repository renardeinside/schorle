import { Result, VisualizationSpec } from 'vega-embed';
import { sendWhenReady } from './io';
import { debounce } from 'throttle-debounce';

export const charts = () => {
  // find all elements inside element with id schorle-page with sle-chart attribute
  // return them as an array
  let page = document.getElementById('schorle-page');
  if (page === null) {
    throw new Error('Element with id schorle-page not found');
  }

  return Array.from(page.querySelectorAll('[sle-chart]'));
};

interface Param {
  name: string;
}

// @ts-ignore
export interface WithParams extends VisualizationSpec {
  params?: Array<Param>;
}

const signalHandler = (
  result: Result,
  param: Param,
  io: WebSocket,
  target: string
) => {
  console.log(`[schorle] event ${param.name}`);

  let state = result.view.getState({
    signals: (name) => name === param.name
  });

  sendWhenReady(io, {
    trigger: 'selection',
    target: target,
    value: JSON.stringify(state.signals[param.name])
  }).catch((e) =>
    console.error(`Error sending message: ${e} on event ${param.name}`)
  );
};

// debounced signal handler to avoid sending too many messages
export const debouncedSignalHandler = debounce(200, signalHandler);
