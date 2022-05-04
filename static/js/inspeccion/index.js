import { search } from './buscador.js';
import { profundidad } from './profundidad.js';

document.addEventListener('DOMContentLoaded', (e) => {
  onSelectTire();
  profundidad();
  confirmAlert();
  handleForms();
  handleTire();

  validateInputList('#llanta', 'llanta');
  validateInputList('#producto', 'producto');
  noDoubleValues();

  manualObserver('data-check-id');
  vehiculoManual('data-vehiculo-item');

  search('#vehiculo-search', '#vehiculo-observaciones', '.search-item');
});

const desdualizacion = (duales = document.documentElement, mm) => {
  let tires = duales.querySelectorAll('.tire');

  tires.forEach((tire) => {
    const inputs = document.querySelectorAll(
      `[data-profundidad-id="${tire.getAttribute('data-tire-id')}"]`
    );

    inputs.forEach((input) => {
      input.querySelectorAll('input').forEach((controllers) => {
        controllers.addEventListener('input', (e) => {
          let prof1 = tires[0].querySelector('[data-prof-tag]').textContent;
          let prof2 = tires[1].querySelector('[data-prof-tag]').textContent;
          const container = document.querySelectorAll(
            `[data-container-id="${tire.getAttribute('data-tire-id')}"]`
          );

          let container1 = tires[0].getAttribute('data-tire-id');
          let container2 = tires[1].getAttribute('data-tire-id');

          let ids = [container1, container2];
          if (prof1 - prof2 >= mm || prof2 - prof1 >= mm) {
            ids.forEach((id) => {
              let content = document.querySelector(
                `[data-container-id="${id}"]`
              );
              content
                .querySelector('[data-icon-dual="Desdualización"]')
                .classList.add('visible');
            });
          } else {
            ids.forEach((id) => {
              let content = document.querySelector(
                `[data-container-id="${id}"]`
              );

              content
                .querySelector('[data-icon-dual="Desdualización"]')
                .classList.remove('visible');
            });
          }
        });
      });
    });
  });
};

const diferenciaDual = (duales = document.documentElement) => {
  let tires = duales.querySelectorAll('.tire');

  tires.forEach((tire) => {
    const input = document.querySelector(
      `input[data-input-id="${tire.getAttribute('data-tire-id')}"]`
    );

    input.addEventListener('input', (e) => {
      let presion1 = tires[0].querySelector('[data-tag-id]').textContent;
      let presion2 = tires[1].querySelector('[data-tag-id]').textContent;

      presion1 = parseFloat(presion1);
      presion2 = parseFloat(presion2);

      let container1 = tires[0].getAttribute('data-tire-id');
      let container2 = tires[1].getAttribute('data-tire-id');

      let ids = [container1, container2];

      let porcentajeDif1 = (presion1 - presion2) / presion1;
      let porcentajeDif2 = (presion2 - presion1) / presion2;

      if (
        porcentajeDif1 > 0.1 ||
        porcentajeDif1 < 0 ||
        porcentajeDif2 > 0.1 ||
        porcentajeDif2 < 0
      ) {
        ids.forEach((id) => {
          let content = document.querySelector(`[data-container-id="${id}"]`);
          content
            .querySelector(
              '[data-icon-dual="Diferencia de presión entre los duales"]'
            )
            .classList.add('visible');
        });
      } else {
        ids.forEach((id) => {
          let content = document.querySelector(`[data-container-id="${id}"]`);
          content
            .querySelector(
              '[data-icon-dual="Diferencia de presión entre los duales"]'
            )
            .classList.remove('visible');
        });
      }
    });
  });
};

const dual = () => {
  const duales = document.querySelectorAll('.double-tire');
  const mmDiferencia = document
    .querySelector('.double-tire')
    .getAttribute('data-mm-dif');

  duales.forEach((dual) => {
    diferenciaDual(dual);
    desdualizacion(dual, mmDiferencia);
  });
};

dual();

const vehiculoManual = (item = '') => {
  const observations = document.querySelectorAll(`[${item}]`);

  observations.forEach((observation) => {
    observation.addEventListener('input', () => {
      let container = document.querySelector('.observations__container');
      if (observation.checked) {
        container
          .querySelector(`[data-icon-type="${observation.value}"]`)
          .classList.add('visible');
      } else {
        container
          .querySelector(`[data-icon-type="${observation.value}"]`)
          .classList.remove('visible');
      }
    });
  });
};

const manualObserver = (item = '') => {
  const observations = document.querySelectorAll(`[${item}]`);

  observations.forEach((observation) => {
    observation.addEventListener('input', () => {
      let container = document.querySelector(
        `[data-container-id="${observation.getAttribute(item)}"]`
      );
      if (observation.checked) {
        container
          .querySelector(`[data-icon-type="${observation.value}"]`)
          .classList.add('visible');
      } else {
        container
          .querySelector(`[data-icon-type="${observation.value}"]`)
          .classList.remove('visible');
      }
    });
  });
};

const validateInputList = (listItem = '', inputName = '') => {
  const list = document.querySelector(listItem)?.options;

  // Si ya se inspecciono
  if (!list) return;

  let listValues = [];

  for (let i = 0; i < list.length; i++) {
    listValues.push(list[i].value);
  }

  // Traemos todos los inputs para modificar el numero econimico
  const inputs = document.querySelectorAll(`input[name="${inputName}"]`);

  // Le asignamos el evento al escribir
  inputs.forEach((input) => {
    let isValid = false;

    input.addEventListener('keyup', (e) => {
      if (listValues.indexOf(input.value) > -1) {
        input.parentNode
          .querySelector('.alert__error')
          .classList.remove('active');
        input.parentNode
          .querySelector('.alert__warn')
          .classList.remove('active');
        document.querySelector('.btn-info').classList.remove('disabled');
        isValid = true;
      } else {
        input.parentNode.querySelector('.alert__error').classList.add('active');
        input.focus();
        document.querySelector('.btn-info').classList.add('disabled');
        isValid = false;
      }

      if (input.value === '') {
        input.parentNode.querySelector('.alert__warn').classList.add('active');
        document.querySelector('.btn-info').classList.add('disabled');
        isValid = false;
      }
    });

    input.addEventListener('keypress', (e) => {
      if (!isValid) {
        if (e.key === 'Enter') e.preventDefault();
      }
    });
  });
};

const noDoubleValues = (inputName = '') => {
  const elements = document.querySelectorAll(`input[name="${inputName}"]`);
  let values = [];

  elements.forEach((value) => {
    values.push(value.value);
  });

  const tempArray = [...values].sort();
  let duplicate = [];

  for (let i = 0; i < tempArray.length; i++) {
    if (tempArray[i + 1] === tempArray[i]) {
      duplicate.push(tempArray[i]);
    }
  }

  if (duplicate.length > 0) {
    const alert = Swal.fire({
      title: 'Error',
      text: 'No puede haber elementos duplicados',
      icon: 'error',
      backdrop: true,
      allowOutsideClick: false,
      allowEscapeKey: false,
    });
    return true; // Si hay elementos duplicados retorna true para la validación con sweetalert
  }

  return false; // Si no hay elementos duplicados
};

const handleTire = () => {
  const buttons = document.querySelectorAll('.tire');
  const items = document.querySelectorAll('.form__wrapper');

  buttons.forEach((button) => {
    button.addEventListener('click', (e) => {
      const id = button.getAttribute('data-tire-id');

      items.forEach((item) => {
        const itemId = item.getAttribute('data-item-id');
        if (id === itemId) {
          items.forEach((item) => item.classList.remove('select'));

          item.classList.add('select');
        }
      });
    });
  });
};

const handleForms = () => {
  const forms = document.querySelectorAll('form');

  forms[0].addEventListener('submit', (e) => {
    if (forms[0].querySelector('input').value === '') {
      e.preventDefault();
      alert('El campo no puede estar vacío');
      forms[0].querySelector('input').focus();
    }
  });
};

const emptyProfs = () => {
  const profundidades = document.querySelectorAll('.form__prof input');

  profundidades.forEach(input => {
    if (!input.value) {
      return true;
    } else if (input.value) {
      console.log(input.value)
      return false;
    }
  })
}

const confirmAlert = () => {
  const form = document.getElementById('tire-form');

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const duplicate = noDoubleValues('llanta');
    // const empty = emptyProfs();
    const empty = true;

    if (duplicate) return;
    if (!empty) {
      const error = Swal.fire({
        title: 'Error',
        text: 'Las llantas al menos deben tener una profundidad',
        icon: 'error',
        backdrop: true,
        allowOutsideClick: false,
        allowEscapeKey: false,
      })
    } else {
      const alert = Swal.fire({
        title: 'Confirmación',
        text: '¿Seguro que desea continuar?',
        icon: 'question',
        confirmButtonText: 'Si',
        backdrop: true,
        showDenyButton: true,
        allowOutsideClick: false,
        allowEscapeKey: false,
      }).then((res) => {
        res.value && form.submit();
      });
    }

  });
};

const onSelectTire = () => {
  const tires = document.querySelectorAll('.tire');
  const hidden = document.querySelector("input[type='hidden']");

  tires.forEach((tire) => {
    tire.addEventListener('click', (e) => {
      tires.forEach((tire) => tire.classList.remove('select'));

      hidden.value = tire.getAttribute('id');

      tire.classList.add('select');
    });
  });
};
