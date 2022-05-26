import getTires from './getTires.js';
import { setFilters, setValues } from './setFilters.js';

document.addEventListener('DOMContentLoaded', (e) => {
  getTires(window.location.search);
  setFilters();
  setValues();
});
