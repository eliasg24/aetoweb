export const profundidad = () => {
  const profundidades = document.querySelectorAll('[data-profundidad-id]');

  profundidades.forEach((inputs) => {
    let id = inputs.getAttribute('data-profundidad-id');
    let puntoRetiro = parseFloat(inputs.getAttribute('data-punto-retiro'));

    inputs.querySelectorAll('input').forEach((input) => {
      input.addEventListener('input', (e) => {
        let left = parseFloat(
          inputs.querySelector('input[name="profundidad_izquierda"]').value
        );
        let central = parseFloat(
          inputs.querySelector('input[name="profundidad_central"]').value
        );
        let right = parseFloat(
          inputs.querySelector('input[name="profundidad_derecha"]').value
        );

        const profArray = [];
        profArray.push(left, central, right);

        const minValue = Math.min.apply(null, profArray);

        let tag = document.querySelector(`[data-prof-tag="profundidad-${id}"]`);
        tag.textContent = minValue;

        let container = document.querySelector(`[data-container-id="${id}"]`);

        // Validaciones de colores
        if (minValue <= puntoRetiro) {
          tag.parentElement.classList.add('bad');
          container
            .querySelector('[data-icon-profundidad="Baja profundidad"]')
            .classList.add('visible');
        } else {
          container
            .querySelector('[data-icon-profundidad="Baja profundidad"]')
            .classList.remove('visible');
        }

        if (minValue >= puntoRetiro + 0.01 && minValue <= puntoRetiro + 1) {
          tag.parentElement.classList.remove('bad');
          tag.parentElement.classList.add('yellow');
        } else {
          tag.parentElement.classList.remove('yellow');
          tag.parentElement.classList.add('good');
        }

        if (minValue === puntoRetiro + 0.6) {
          container
            .querySelector('[data-icon-retiro="En punto de retiro"]')
            .classList.add('visible');
        } else {
          container
            .querySelector('[data-icon-retiro="En punto de retiro"]')
            .classList.remove('visible');
        }

        if (right < left && right < central) {
          container
            .querySelectorAll('[data-icon-desgaste]')
            .forEach((icon) => icon.classList.remove('visible'));
          container
            .querySelector(
              '[data-icon-desgaste="Desgaste inclinado a la derecha"]'
            )
            .classList.add('visible');
        }

        if (left < central && left < right) {
          container
            .querySelectorAll('[data-icon-desgaste]')
            .forEach((icon) => icon.classList.remove('visible'));
          container
            .querySelector(
              '[data-icon-desgaste="Desgaste inclinado a la izquierda"]'
            )
            .classList.add('visible');
        }

        if (left < central && central > right) {
          container
            .querySelectorAll('[data-icon-desgaste]')
            .forEach((icon) => icon.classList.remove('visible'));
          container
            .querySelector('[data-icon-desgaste="Desgaste  costilla interna"]')
            .classList.add('visible');
        }

        if (left > central && central < right) {
          container
            .querySelectorAll('[data-icon-desgaste]')
            .forEach((icon) => icon.classList.remove('visible'));
          container
            .querySelector('[data-icon-desgaste="Desgaste alta presión"]')
            .classList.add('visible');
        }
      });
    });
  });
};
