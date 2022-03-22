document.addEventListener('DOMContentLoaded', (e) => {
  searchFilters('#search-ubicacion', '#menu-ubicacion', '.search-item');
  searchFilters('#search-clase', '#menu-clase', '.search-item');
  searchFilters('#search-flota', '#menu-flota', '.search-item');
  searchFilters('#search-app', '#menu-app', '.search-item');
  searchFilters('#search-eje', '#menu-eje', '.search-item');
  searchFilters('#search-vehiculo', '#menu-vehiculo', '.search-item');
  searchFilters('#search-pos', '#menu-pos', '.search-item');
  searchFilters('#search-producto', '#menu-producto', '.search-item');
});

const searchFilters = (input = '', container = '', selector = '') => {
  document.addEventListener('keyup', (e) => {
    if (e.target.matches(input)) {
      if (e.key === 'Esc') e.target.value = '';

      document
        .querySelectorAll(`${container} > ${selector}`)
        .forEach((item) =>
          item.textContent.toLowerCase().includes(e.target.value.toLowerCase())
            ? item.classList.remove('filter')
            : item.classList.add('filter')
        );
    }
  });
};
