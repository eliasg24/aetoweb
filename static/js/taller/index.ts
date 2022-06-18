(() => {
  const tires = document.querySelectorAll('.tire');

  tires.forEach((tire) => {
    tire.addEventListener('click', (e) => {
      let tireTs = tire as unknown as HTMLInputElement;
      const id: string | undefined = tireTs.dataset.id;

      const modal = document.querySelector(`[data-modal="${id}"]`);
      modal?.classList.add('active');

      document.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        if (target.matches('.close-modal')) {
          modal?.classList.remove('active');
        }
      });
    });
  });
})();

(() => {
  interface Form {
    balancear: string;
    inflar: string;
    llantaId: string;
    llantaOrigen: string | null;
    otroVehiculo: string | null;
    llantaOrigenPos: string | null;
    llantaPos: string | null;
    nuevaLlanta: string;
    razon: string;
    reparar: string;
    rotar: string;
    valvula: string;
    costado: string;
    stock: string;
    tipoServicio: 'desmontaje' | 'sr';
  }

  interface Event {}

  const saveData: any[] = [];

  document.addEventListener('submit', (e) => {
    const target = e.target as HTMLFormElement;
    if (target.matches('#taller-form')) return;

    if (target.matches('.service-page')) {
      e.preventDefault();
      const form: HTMLFormElement = e.target as HTMLFormElement;
      const data = Object.fromEntries(new FormData(form));

      const formHidden = document.getElementById(
        'hoja-servicio'
      ) as unknown as HTMLInputElement;
      formHidden.value = JSON.stringify( data );
      return;
    }

    e.preventDefault();
    const form: HTMLFormElement = e.target as HTMLFormElement;
    const data = Object.fromEntries(new FormData(form));
    const eventList = document.querySelector('.tire-list') as HTMLElement;

    switch (data.tipoServicio) {
      case 'desmontaje':
        const $div = document.createElement('div');
        $div.classList.add('tire-item');
        $div.innerHTML = `
          <div class="service__img">
            <span class="icon-llanta-outline"></span>
          </div>
          <div>
            <h3>Desmontaje</h3>
            <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
            <p>
              <strong>Razón de desmontaje:</strong> 
              ${data.razon}
            </p>
            <p><strong>Nueva llanta</strong>: ${data.nuevaLlanta}</p>
            <p><strong>Stock origen</strong>: ${data.stock}</p>
          </div>
        `;

        eventList.appendChild($div);

        break;

      case 'sr':
        if (data.inflar) {
          const $div = document.createElement('div');
          $div.classList.add('tire-item');

          $div.innerHTML = `
            <div class="service__img">
              <span class="icon-llanta-outline"></span>
            </div>
            <div>
              <h3>Inflado</h3>
              <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
            </div>
          `;

          eventList.appendChild($div);
        }

        if (data.balancear) {
          const $div = document.createElement('div');
          $div.classList.add('tire-item');

          $div.innerHTML = `
            <div class="service__img">
              <span class="icon-llanta-outline"></span>
            </div>
            <div>
              <h3>Balanceado</h3>
              <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
            </div>
          `;

          eventList.appendChild($div);
        }

        if (data.reparar) {
          const $div = document.createElement('div');
          $div.classList.add('tire-item');

          $div.innerHTML = `
            <div class="service__img">
              <span class="icon-llanta-outline"></span>
            </div>
            <div>
              <h3>Reparación</h3>
              <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
            </div>
          `;

          eventList.appendChild($div);
        }

        if (data.costado) {
          const $div = document.createElement('div');
          $div.classList.add('tire-item');

          $div.innerHTML = `
            <div class="service__img">
              <span class="icon-llanta-outline"></span>
            </div>
            <div>
              <h3>Reparación de costado</h3>
              <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
            </div>
          `;

          eventList.appendChild($div);
        }

        if (data.valvula) {
          const $div = document.createElement('div');
          $div.classList.add('tire-item');

          $div.innerHTML = `
            <div class="service__img">
              <span class="icon-llanta-outline"></span>
            </div>
            <div>
              <h3>Reparación de valvula</h3>
              <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
            </div>
          `;

          eventList.appendChild($div);
        }

        if (data.rotar) {
          let $div = document.createElement('div');
          $div.classList.add('tire-item');
          switch (data.rotar) {
            case 'no':
              break;
            case 'mismo':
              $div.innerHTML = `
                <div class="service__img">
                  <span class="icon-llanta-outline"></span>
                </div>
                <div>
                  <h3>Rotación</h3>
                  <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
                  <p><strong>Rotada por:</strong> ${data.llantaOrigen}</p>
                </div>
              `;

              eventList.appendChild($div);
              break;

            case 'otro':
              console.log(data);
              $div.innerHTML = `
                <div class="service__img">
                  <span class="icon-llanta-outline"></span>
                </div>
                <div>
                  <h3>Rotación entre vehiculos</h3>
                  <p><strong>Llanta ID:</strong> ${data.llantaId}</p>
                  <p><strong>Vehiculo origen:</strong> ${data.otroVehiculo}</p>
                  <p><strong>Rotada por:</strong> ${data.llantaOrigen}</p>
                </div>
              `;

              eventList.appendChild($div);
              break;

            default:
              break;
          }
        }

        break;

      default:
        break;
    }

    form
      .querySelectorAll('input, select, .btn-submit')
      .forEach((input) => input.setAttribute('disabled', ''));

    saveData.push(data);

    const formHidden = document.getElementById(
      'data-taller'
    ) as unknown as HTMLInputElement;
    formHidden.value = JSON.stringify(saveData);
  });

  document.addEventListener('change', (e) => {
    const target = e.target as HTMLInputElement;

    if (target.matches('#alinearVehiculo')) {
      const formHidden = document.getElementById(
        'vehiculo-data'
      ) as unknown as HTMLInputElement;

      formHidden.value = JSON.stringify([{
        alinearVehiculo: target.value,
      }]);
    }

    if (target.name === 'rotar') {
      switch (target.value) {
        case 'no':
          document
            .querySelectorAll<HTMLInputElement>(`[data-rotar-id="${target.dataset.radioid}"]`)
            .forEach((label) => (label.style.display = 'none'));
          break;

        case 'mismo':
          document.querySelectorAll<HTMLInputElement>(
            `[data-rotar-id="${target.dataset.radioid}"]`
          )[0].style.display = 'none';
          document.querySelectorAll<HTMLInputElement>(
            `[data-rotar-id="${target.dataset.radioid}"]`
          )[1].style.display = 'block';
          break;

        case 'otro':
          document
            .querySelectorAll<HTMLInputElement>(`[data-rotar-id="${target.dataset.radioid}"]`)
            .forEach((label) => (label.style.display = 'block'));
          break;

        default:
          break;
      }
    }

    if (target.dataset.nav) {
      if (target.value === 'desmontaje') {
        document
          .querySelectorAll(`[data-view="${target.dataset.nav}"]`)
          .forEach((item) => item.classList.remove('active'));

        target.classList.add('active');
        document
          .querySelectorAll<HTMLDivElement>(`[data-view="${target.dataset.nav}"]`)
          .forEach((view) => (view.style.display = 'none'));

        document.querySelectorAll<HTMLDivElement>(
          `[data-view="${target.dataset.nav}"]`
        )[1].style.display = 'block';
      } else {
        document
          .querySelectorAll<HTMLDivElement>(`[data-view="${target.dataset.nav}"]`)
          .forEach((item) => item.classList.remove('active'));

        target.classList.add('active');
        document
          .querySelectorAll<HTMLDivElement>(`[data-view="${target.dataset.nav}"]`)
          .forEach((view) => (view.style.display = 'none'));

        document.querySelectorAll<HTMLDivElement>(
          `[data-view="${target.dataset.nav}"]`
        )[0].style.display = 'block';
      }
    }
  });

})();

(() => {
  document.addEventListener('change', (e) => {
    const target = e.target as HTMLInputElement;
    if (target.name === 'stock') {
      const llanta = target.nextElementSibling
        ?.nextElementSibling as HTMLInputElement;

      switch (target.value) {
        case 'nueva':
          fetch('/api/tiresearchtaller?inventario=Nueva')
            .then((res) => res.json())
            .then((json) => {
              console.log(json);
              let options = `<option value="">Seleccione una llanta</option>`;

              json.result.forEach((item: any) => {
                options += `<option value="${item.numero_economico}">${item.numero_economico} - ${item.producto__dimension}</option>`;
              });

              llanta.innerHTML = options;
            })
            .catch((error) => console.error(error));

          break;
        case 'renovada':
          fetch('/api/tiresearchtaller?inventario=Renovada')
            .then((res) => res.json())
            .then((json) => {
              console.log(json);
              let options = `<option value="">Seleccione una llanta</option>`;

              json.result.forEach((item: any) => {
                options += `<option value="${item.numero_economico}">${item.numero_economico} - ${item.producto__dimension}</option>`;
              });

              llanta.innerHTML = options;
            })
            .catch((error) => console.error(error));

          break;
        case 'servicio':
          fetch('/api/tiresearchtaller?inventario=Servicio')
            .then((res) => res.json())
            .then((json) => {
              console.log(json);
              let options = `<option value="">Seleccione una llanta</option>`;

              json.result.forEach((item: any) => {
                options += `<option value="${item.numero_economico}">${item.numero_economico} - ${item.producto__dimension}</option>`;
              });

              llanta.innerHTML = options;
            })
            .catch((error) => console.error(error));

          break;

        default:
          break;
      }
    }
  });
})();

(() => {
  document.addEventListener('change', (e) => {
    const target = e.target as HTMLInputElement;
    const origen = document.getElementById(
      `origen-llanta-${target.dataset.radioid}`
    ) as HTMLInputElement;
    const vehiculoOrigen = document.getElementById(
      `origen-vehiculo-${target.dataset.radioid}`
    ) as HTMLInputElement;

    if (target.value === 'mismo') {
      let data = Array.from(document.querySelectorAll('[data-pos]'));
      const positions = data.map((item) => {
        return {
          position: item.getAttribute('data-pos'),
          id: item.getAttribute('data-id'),
        };
      });

      let allPos = positions.filter(
        (item) => item.id !== target.dataset.radioid
      );

      if (origen) {
        origen.innerHTML = `<option value="">Seleccione una llanta</option>`;
        origen.innerHTML += allPos
          .map((item) => {
            return `<option value="${item.id}">${item.position}</option>`;
          })
          .join('');
      }
    }

    if (target.value === 'otro') {
      origen.innerHTML = `<option value="">Seleccione una llanta</option>`;

      fetch('/api/vehicleandtiresearchtaller')
        .then((res) => (res.ok ? res.json() : Promise.reject(res)))
        .then((json) => {
          vehiculoOrigen.innerHTML = `<option value="">Seleccione un vehiculo</option>`;
          vehiculoOrigen.innerHTML += json.vehiculos_list.map((item: any) => {
            return `<option value="${item.id}">${item.numero_economico}</option>`;
          });
        })
        .catch((error) => console.error(error));

      vehiculoOrigen.addEventListener('change', (e) => {
        if (vehiculoOrigen.value === '') return;

        fetch(
          '/api/vehicleandtiresearchtaller?id_select=' +
            vehiculoOrigen.value.toLocaleLowerCase()
        )
          .then((res) => (res.ok ? res.json() : Promise.reject(res)))
          .then((json) => {
            origen.innerHTML = `<option value="">Seleccione un vehiculo</option>`;
            origen.innerHTML += json.llantas.map((item: any) => {
              return `<option value="${item.id}">${item.posicion}</option>`;
            });
          })
          .catch((error) => console.error(error));
      });
    }
  });
})();
