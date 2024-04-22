import { createIcons, icons } from 'lucide';

let processIcons = () => createIcons({ icons });

document.addEventListener('DOMContentLoaded', () => {
  processIcons();
});