const API = 'http://localhost:8083';

function show(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');
}

document.querySelectorAll('nav button').forEach(b => {
  b.addEventListener('click', () => show(b.dataset.page));
});

async function getJSON(url) {
  const r = await fetch(url);
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function loadHealth() {
  const out = document.getElementById('healthOut');
  try {
    const res = await getJSON(`${API}/health`);
    out.textContent = JSON.stringify(res, null, 2);
  } catch (e) {
    out.textContent = e.toString();
  }
}

async function loadTasks() {
  const out = document.getElementById('tasksOut');
  try {
    const res = await getJSON(`${API}/tasks`);
    out.textContent = JSON.stringify(res.data, null, 2);
  } catch (e) {
    out.textContent = e.toString();
  }
}

document.getElementById('addForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('titleInput').value.trim();
  if (!title) return;
  await fetch(`${API}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  document.getElementById('titleInput').value = '';
  loadTasks();
});

function setCheck(id, pass, detail) {
  const li = document.getElementById(id);
  const span = li.querySelector('span');
  li.classList.toggle('ok', !!pass);
  li.classList.toggle('bad', !pass);
  span.textContent = pass ? 'PASS' : `FAIL${detail ? ': ' + detail : ''}`;
}

async function loadSecurity() {
  const raw = document.getElementById('secRaw');
  const resHealth = await getJSON(`${API}/health`);
  const resInfo = await getJSON(`${API}/security/info`);
  raw.textContent = JSON.stringify({ health: resHealth, info: resInfo }, null, 2);

  setCheck('sec-health', resHealth.ok && resHealth.status === 200);

  if (resInfo.ok) {
    const i = resInfo.data;
    setCheck('sec-nonroot', i.uid !== 0, `uid=${i.uid}`);
    setCheck('sec-rofs', !!i.readonly);
    const nnp = i.caps && i.caps.NoNewPrivs === "1";
    setCheck('sec-nnp', nnp, `NoNewPrivs=${i.caps?.NoNewPrivs}`);
  } else {
    setCheck('sec-nonroot', false, 'no data');
    setCheck('sec-rofs', false, 'no data');
    setCheck('sec-nnp', false, 'no data');
  }
}

window.addEventListener('load', () => {
  loadHealth();
  loadTasks();
  loadSecurity();
});

