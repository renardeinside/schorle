import { createIcons, icons } from 'lucide';
import htmx from 'htmx.org';

htmx.defineExtension('lucide', {
  onEvent: (name) => {
    if (name === 'htmx:load') {
      createIcons({ icons });
      htmx.on('htmx:afterSwap', () => {
        createIcons({ icons });
      });
    }
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const schorleDev = document.querySelector('meta[name="schorle-dev"]');
  if (schorleDev) {
    console.log('Schorle is running in development mode');
  }
});