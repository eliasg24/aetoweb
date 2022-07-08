(async () => {
  const getEvents = async () => {
    try {
      const resp = await fetch('api/calendario');
      const json = await resp.json();

      if (!resp.ok) throw new Error('Algo salió mal');

      let newEvents;

      for (const event of json.calendarios) {
        const { horario_start_str, horario_end_str, ...restEvent } = event;

        newEvents = [
          {
            ...restEvent,
            start: event.horario_start_str,
            end: event.horario_end_str,
          },
        ];
      }

      return newEvents;
    } catch (error) {
      console.error(error);
    }
  };

  const calendarEvents = await getEvents();

  const modal = (event) => {
    const modalContainer = document.querySelector('.modal__container');
    const closeBtn = document.querySelector('.btn.close');

    modalContainer.classList.add('active');
    modalContainer.querySelector('.modal-title').textContent = event.title;

    closeBtn.addEventListener('click', (e) => {
      modalContainer.classList.remove('active');
    });

    console.log(event);
  };

  const calendar = (calendarEvents = []) => {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
      locale: 'esLocale',
      initialView: 'timeGridWeek', // * timeGridWeek || dayGridMonth
      height: '100vh',
      selectable: true,
      events: calendarEvents,
      eventColor: '026cf5',
      eventClick: function (e) {
        const { event } = e;
        modal(event);
      },
    });

    calendar.render();
  };

  calendar(calendarEvents);
})();
