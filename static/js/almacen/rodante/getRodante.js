const template = document.getElementById('card-template').content;
const container = document.querySelector('.cards__container');
const fragment = document.createDocumentFragment();

let offset = 0,
  limit = 16;

export const getRodante = async () => {
  const loader = document.createElement('div');
  loader.classList.add('loader__container');
  loader.innerHTML = `<div class="loader"></div>`;
  container.appendChild(loader);

  try {
    const resp = await fetch(
      `${ window.location.origin }/api/tiresearch?inventario=Rodante&offset=${offset}&limit=${limit}`
    );
    const { result } = await resp.json();

    if (!resp.ok)
      throw new Error({
        status: resp.status,
        statusMessage: resp.statusText,
      });

    if (result.length === 0) {
      container.innerHTML = `
        <div>
          No hay resultados :(
        </div>
      `;
      return;
    }

    result.forEach((item) => {
      template.querySelector('a').href = `/tireDetail/${item.id}`; // Poner el id del rodante
      template.querySelector('input').id = item.id;
      template.querySelector('input').value = item.id;
      template.querySelector('label').setAttribute('for', item.id);

      template.querySelector('.economic').textContent = item.numero_economico;
      template.querySelector('.profundidad').textContent = item.min_profundidad || 'Sin profundidad';
      template.querySelector('.product').textContent = item.producto__producto;
      template.querySelector('.date').textContent =
        item.fecha_de_entrada_inventario;
      

      let clone = document.importNode(template, true);
      fragment.appendChild(clone);
    });

    container.innerHTML = '';
    loader.remove();
    container.appendChild(fragment);
  } catch (error) {
    console.error(`Error ${error.status}: ${error.statusMessage}`);
  }
};

window.addEventListener('scroll', (e) => {
  const { scrollTop, clientHeight, scrollHeight } = document.documentElement;

  if (scrollTop + clientHeight >= scrollHeight) {
    limit = limit + limit;
    getRodante();
  }
});