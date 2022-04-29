import { profundidad } from "./profundidad.js";

document.addEventListener('DOMContentLoaded', (e) => {
  onSelectTire();
  confirmAlert();
  handleForms();
  handleTire();

  validateInputList('#llanta', 'llanta');
  validateInputList('#producto', 'producto');
  noDoubleValues();

  manualObserver();
  profundidad();
});

const manualObserver = () => {
  const observations = document.querySelectorAll('[data-check-id]');

  observations.forEach((observation) => {
    observation.addEventListener('input', () => {
      let container = document.querySelector(
        `[data-container-id="${observation.getAttribute('data-check-id')}"]`
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

const confirmAlert = () => {
  const form = document.getElementById('tire-form');

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const duplicate = noDoubleValues('llanta');

    if (duplicate) return;

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
