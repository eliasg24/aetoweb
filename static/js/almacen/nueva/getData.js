const template = document.getElementById('card-template').content;
const container = document.querySelector('.cards__container');
const fragment = document.createDocumentFragment();
const loader = document.querySelector('.icon-spinner2');

let page = 1;

const getTires = async (querys = '') => {
  const origin = window.location.origin,
    api = `${origin}/api`,
    tires = `${api}/tiresearch`,
    apiSearch = `${tires}${
      querys || '?'
    }&inventario=Nueva&size=20&page=${page}`;

  loader.style.display = 'block';

  try {
    const resp = await fetch(apiSearch);
    const { result, pagination } = await resp.json();

    if (!resp.ok) throw new Error('Algo sucedió mal');

    result.forEach((item) => {
      template.querySelector('a').href = `/tireDetail/${item.id}`; // Poner el id del rodante
      template.querySelector('input').id = item.id;
      template.querySelector('input').value = item.id;
      template.querySelector('label').setAttribute('for', item.id);

      template.querySelector('.economic').textContent = item.numero_economico;
      template.querySelector('.economic').textContent = item.numero_economico;

      if (item.color === 'good') {
        template
          .querySelector('.tire__status')
          .classList.toggle('good', item.color === 'good');
      } else if (item.color === 'bad') {
        template
          .querySelector('.tire__status')
          .classList.toggle('bad', item.color === 'bad');
      } else if (item.color === 'yellow') {
        template
          .querySelector('.tire__status')
          .classList.toggle('yellow', item.color === 'yellow');
      }

      template.querySelector('.profundidad').textContent =
        item.min_profundidad || 'Sin profundidad';
      template.querySelector('.product').textContent = item.producto__producto;
      template.querySelector('.date').textContent =
        item.fecha_de_entrada_inventario;

      let clone = document.importNode(template, true);
      fragment.appendChild(clone);
    });

    loader.style.display = 'none';
    container.appendChild(fragment);
  } catch (error) {
    console.error(error);
  }

  window.addEventListener('scroll', (e) => {
    const { scrollTop, clientHeight, scrollHeight } = document.documentElement;

    if (scrollTop + clientHeight >= scrollHeight) {
      page++;
      getTires(window.location.search);
    }
  });
};

export default getTires;
