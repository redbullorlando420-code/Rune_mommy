export function bindLogin(onJoin) {
  const form = document.getElementById('joinForm');
  const err = document.getElementById('loginErr');
  const saved = localStorage.getItem('rm_name') || '';
  if (saved) document.getElementById('nameIn').value = saved;
  form.onsubmit = (e) => {
    e.preventDefault();
    const name = document.getElementById('nameIn').value.trim();
    if (name.length < 2) { err.textContent = 'A name, wanderer.'; return; }
    localStorage.setItem('rm_name', name);
    err.textContent = '';
    onJoin(name);
  };
  return {
    hide() { document.getElementById('login').style.display = 'none'; },
    error(t) { err.textContent = t; },
  };
}
