const state = {
  selectedDate: new Date().toISOString().slice(0, 10),
  currentDay: null,
  users: [],
};

const el = (id) => document.getElementById(id);

const nodes = {
  stats: el('stats'),
  status: el('global-status'),
  dateInput: el('date-input'),
  selectedDateLabel: el('selected-date-label'),
  readState: el('read-state'),
  toggleRead: el('toggle-read'),
  saveDay: el('save-day'),
  titleInput: el('title-input'),
  scriptureInput: el('scripture-input'),
  notesInput: el('notes-input'),
  readingTitle: el('reading-title'),
  readingScripture: el('reading-scripture'),
  recentDays: el('recent-days'),
  checklist: el('checklist'),
  dayTemplate: el('day-template'),
};

function formatDate(value) {
  return new Intl.DateTimeFormat('es-ES', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(`${value}T12:00:00`));
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

function renderStats(stats) {
  const cards = [
    ['Dias totales', stats.total_days],
    ['Completados', stats.completed_days],
    ['Pendientes', stats.pending_days],
    ['Avance general', `${stats.completion}%`],
  ];

  const perUserCards = (stats.per_user || []).map(
    (user) => `
      <article class="stat user-stat">
        <span>${user.name}</span>
        <strong>${user.read_days}/${stats.total_days}</strong>
        <small>${user.completion}% completado</small>
      </article>
    `,
  );

  nodes.stats.innerHTML = [
    ...cards.map(
      ([label, value]) => `
        <article class="stat">
          <span>${label}</span>
          <strong>${value}</strong>
        </article>
      `,
    ),
    ...perUserCards,
  ].join('');
}

function renderCurrentDay(day) {
  nodes.selectedDateLabel.textContent = formatDate(state.selectedDate);

  if (!day) {
    nodes.status.textContent = 'No hay lectura guardada para este dia';
    nodes.readState.textContent = 'Pendiente';
    nodes.readState.classList.remove('is-read');
    nodes.titleInput.value = '';
    nodes.scriptureInput.value = '';
    nodes.notesInput.value = '';
    nodes.readingTitle.textContent = 'Sin datos';
    nodes.readingScripture.textContent = 'Crea o edita la lectura de este dia.';
    nodes.toggleRead.textContent = 'Marcar leido';
    renderChecklist([]);
    return;
  }

  state.currentDay = day;
  nodes.status.textContent = day.is_read ? 'Leido por ambos' : 'Pendiente';
  nodes.readState.textContent = day.is_read ? 'Leido por ambos' : 'Pendiente';
  nodes.readState.classList.toggle('is-read', day.is_read);
  nodes.titleInput.value = day.title || '';
  nodes.scriptureInput.value = day.scripture || '';
  nodes.notesInput.value = day.notes || '';
  nodes.readingTitle.textContent = day.title || 'Sin titulo';
  nodes.readingScripture.textContent = day.scripture || 'Sin capitulos definidos';
  nodes.toggleRead.textContent = day.is_read ? 'Marcar no leido' : 'Marcar leido';
  renderChecklist(day.checklist || []);
}

function renderChecklist(checklist) {
  if (!checklist.length) {
    nodes.checklist.innerHTML = '<p class="empty">Todavia no hay usuarios configurados.</p>';
    return;
  }

  nodes.checklist.innerHTML = checklist
    .map(
      (item) => `
        <label class="check-row">
          <input type="checkbox" data-user-id="${item.user_id}" ${item.is_read ? 'checked' : ''} />
          <div>
            <strong>${item.name}</strong>
            <p>${item.is_read ? 'Ya lo leyo' : 'Pendiente de lectura'}</p>
          </div>
          <span>${item.is_read ? 'Hecho' : 'Pendiente'}</span>
        </label>
      `,
    )
    .join('');

  nodes.checklist.querySelectorAll('input[type="checkbox"]').forEach((input) => {
    input.addEventListener('change', async (event) => {
      const userId = input.dataset.userId;
      await request(`/api/days/${state.selectedDate}/checklist/${userId}`, {
        method: 'PUT',
        body: JSON.stringify({ is_read: event.target.checked }),
      });
      await loadSummary(state.selectedDate);
    });
  });
}

function renderRecentDays(days) {
  nodes.recentDays.innerHTML = '';

  days.forEach((day) => {
    const item = nodes.dayTemplate.content.cloneNode(true);
    const button = item.querySelector('.timeline-item');
    const dateLabel = item.querySelector('.timeline-date');
    const titleLabel = item.querySelector('.timeline-title');
    const stateLabel = item.querySelector('.timeline-state');

    dateLabel.textContent = formatDate(day.day_date);
    titleLabel.textContent = day.title || day.scripture || 'Sin titulo';
    stateLabel.textContent = day.is_read ? 'Leido por ambos' : 'Pendiente';
    stateLabel.classList.toggle('is-read', day.is_read);
    stateLabel.classList.toggle('is-pending', !day.is_read);

    button.addEventListener('click', () => {
      state.selectedDate = day.day_date;
      nodes.dateInput.value = day.day_date;
      loadSummary(day.day_date);
    });

    nodes.recentDays.appendChild(item);
  });
}

async function loadSummary(dateValue = state.selectedDate) {
  const data = await request(`/api/summary?day=${encodeURIComponent(dateValue)}`);
  state.selectedDate = data.target_day;
  state.users = data.users || [];
  nodes.dateInput.value = data.target_day;
  renderStats(data.stats);
  renderCurrentDay(data.day);
  renderRecentDays(data.recent_days);
}

async function saveDay() {
  const payload = {
    title: nodes.titleInput.value.trim(),
    scripture: nodes.scriptureInput.value.trim(),
    notes: nodes.notesInput.value.trim(),
  };
  await request(`/api/days/${state.selectedDate}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  await loadSummary(state.selectedDate);
}

async function toggleRead() {
  const current = state.currentDay?.is_read ?? false;
  const checklist = state.currentDay?.checklist || [];
  await Promise.all(
    checklist.map((item) =>
      request(`/api/days/${state.selectedDate}/checklist/${item.user_id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_read: !current }),
      }),
    ),
  );
  await loadSummary(state.selectedDate);
}

nodes.dateInput.value = state.selectedDate;
nodes.dateInput.addEventListener('change', () => {
  state.selectedDate = nodes.dateInput.value;
  loadSummary(state.selectedDate);
});
nodes.saveDay.addEventListener('click', saveDay);
nodes.toggleRead.addEventListener('click', toggleRead);

loadSummary().catch((error) => {
  nodes.status.textContent = 'No se pudo cargar la app';
  nodes.readingTitle.textContent = 'Error';
  nodes.readingScripture.textContent = error.message;
  console.error(error);
});
