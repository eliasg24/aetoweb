import { setFilters, setValues } from "./getByEconomic.js";
import getTires from "./getData.js";

document.addEventListener('DOMContentLoaded', (e) => {
  setFilters();
  setValues();
  getTires(window.location.search);
});