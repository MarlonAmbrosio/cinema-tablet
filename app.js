(function () {
  'use strict';
  var items = window.CATALOGO || [], favorites = [], last = null, onlySaved = false, active = null, lastFocus = null;
  function expand(rows) { return rows.map(function (row) { return {id:row[0],title:row[1],kind:row[2],poster:row[3],source:row[4],servers:row[5],titleSource:row[6]}; }); }
  if (window.CATALOGO_COMPACTO) {
    items = expand(window.CATALOGO_COMPACTO);
    window.CATALOGO_COMPACTO = null;
  }
  var page = 1, pageSize = 36, totalPages = 1, searchTimer = null;
  function normalize(text) { text = text.toLowerCase(); return typeof text.normalize === 'function' ? text.normalize('NFD').replace(/[\u0300-\u036f]/g, '') : text; }
  items.forEach(function (item) { item.searchText = normalize(item.title); });
  var loadedKinds = {filme:true}, loadingKinds = {}, catalogTotal = items.length;
  if (window.CATALOGO_RESUMO) { catalogTotal = 0; Object.keys(window.CATALOGO_RESUMO).forEach(function (key) { catalogTotal += window.CATALOGO_RESUMO[key]; }); }
  window.SALA_RECEBER = function (kind, rows) { if (loadedKinds[kind]) return; var extra = expand(rows); extra.forEach(function (item) { item.searchText = normalize(item.title); }); items = items.concat(extra); loadedKinds[kind] = true; };
  function ensureKind(kind, done) {
    var wanted = kind ? [kind] : ['serie','temporada','episodio'];
    function next() {
      var pending = wanted.filter(function (key) { return !loadedKinds[key]; });
      if (!pending.length) { done(); return; }
      var key = pending[0]; byId('result-count').textContent = 'Carregando catálogo…';
      if (loadingKinds[key]) { setTimeout(next, 150); return; }
      loadingKinds[key] = true;
      var script = document.createElement('script'); script.src = 'dados/' + key + '.js';
      script.onload = function () { loadingKinds[key] = false; if (loadedKinds[key]) next(); else byId('result-count').textContent = 'Falha ao carregar catálogo. Selecione novamente.'; };
      script.onerror = function () { loadingKinds[key] = false; byId('result-count').textContent = 'Não foi possível carregar. Selecione novamente.'; script.parentNode.removeChild(script); };
      document.head.appendChild(script);
    }
    next();
  }
  function byId(id) { return document.getElementById(id); }
  function load(key, fallback) { try { var value = localStorage.getItem(key); return value ? JSON.parse(value) : fallback; } catch (e) { return fallback; } }
  function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {} }
  favorites = load('sala-favoritos', []); if (!Array.isArray(favorites)) favorites = [];
  last = load('sala-ultimo', null);
  function has(id) { return favorites.indexOf(id) !== -1; }
  function element(tag, cls, text) { var node = document.createElement(tag); if (cls) node.className = cls; if (text !== undefined) node.textContent = text; return node; }
  function safeUrl(url) { return typeof url === 'string' && /^https:\/\//i.test(url); }
  function render() {
    var query = normalize(byId('search').value), kind = byId('kind').value;
    var list = items.filter(function (item) { return (!onlySaved || has(item.id)) && (!kind || (item.kind || 'filme') === kind) && item.searchText.indexOf(query) !== -1; });
    totalPages = Math.max(1, Math.ceil(list.length / pageSize)); page = Math.max(1, Math.min(page, totalPages));
    var grid = byId('grid'); grid.textContent = '';
    byId('total').textContent = catalogTotal; byId('saved-count').textContent = favorites.length;
    byId('result-count').textContent = list.length + (list.length === 1 ? ' título' : ' títulos');
    byId('section-title').textContent = onlySaved ? 'Guardados para depois' : 'Explore o catálogo';
    byId('empty').hidden = list.length !== 0;
    byId('page-label').textContent = 'Página ' + page + ' de ' + totalPages;
    byId('previous').disabled = page <= 1; byId('next').disabled = page >= totalPages;
    list.slice((page - 1) * pageSize, page * pageSize).forEach(function (item) {
      var card = element('article', 'card'), wrap = element('div', 'poster-wrap');
      wrap.appendChild(element('div', 'poster-fallback', item.title));
      if (safeUrl(item.poster)) { var image = element('img', 'poster'); image.src = item.poster; image.alt = ''; image.loading = 'lazy'; image.referrerPolicy = 'no-referrer'; image.onerror = function () { image.style.display = 'none'; }; wrap.appendChild(image); }
      var watch = element('button', 'watch'); watch.setAttribute('aria-label', 'Assistir ' + item.title); watch.appendChild(element('span', 'watch-label', 'ASSISTIR')); watch.appendChild(element('span', 'play-circle', '▶')); watch.onclick = function () { openMovie(item); }; wrap.appendChild(watch);
      var save = element('button', 'save' + (has(item.id) ? ' saved' : ''), has(item.id) ? '✓' : '+'); save.setAttribute('aria-label', (has(item.id) ? 'Remover da lista: ' : 'Salvar na lista: ') + item.title); save.setAttribute('aria-pressed', String(has(item.id))); save.onclick = function () { var index = favorites.indexOf(item.id); if (index === -1) favorites.push(item.id); else favorites.splice(index, 1); store('sala-favoritos', favorites); render(); }; wrap.appendChild(save);
      card.appendChild(wrap); card.appendChild(element('h3', '', item.title)); card.appendChild(element('div', 'meta', item.servers.length ? item.servers.length + ' opções de player' : 'Abrir pela página de origem')); grid.appendChild(card);
    });
  }
  function chooseServer(server, index) {
    if (!safeUrl(server.url)) return;
    var player = byId('player'); player.textContent = '';
    var frame = element('iframe'); frame.title = active.title + ' — ' + server.name;
    frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-presentation');
    frame.setAttribute('allow', 'autoplay; encrypted-media; fullscreen; picture-in-picture'); frame.setAttribute('allowfullscreen', ''); frame.setAttribute('referrerpolicy', 'no-referrer'); frame.src = server.url; player.appendChild(frame);
    var buttons = byId('servers').getElementsByTagName('button'); for (var j = 0; j < buttons.length; j++) { buttons[j].className = j === index ? 'active' : ''; buttons[j].setAttribute('aria-pressed', String(j === index)); }
  }
  function openMovie(item) {
    active = item; lastFocus = document.activeElement; byId('modal-title').textContent = item.title; byId('servers').textContent = '';
    byId('source-link').href = safeUrl(item.source) ? item.source : '#';
    byId('player').textContent = ''; byId('player').appendChild(element('div', 'player-placeholder', item.servers.length ? 'Escolha um servidor para começar.' : 'Este título foi incluído no catálogo, mas seu player ainda não foi importado. Use o link da página de origem abaixo.'));
    item.servers.forEach(function (server, index) { var button = element('button', '', server.name); button.onclick = function () { chooseServer(server, index); }; byId('servers').appendChild(button); });
    byId('modal').hidden = false; document.body.classList.add('modal-open'); byId('close').focus();
    store('sala-ultimo', item.id); updateResume(item.id);
  }
  function closeMovie() { byId('player').textContent = ''; byId('modal').hidden = true; document.body.classList.remove('modal-open'); if (lastFocus) lastFocus.focus(); }
  function updateResume(id) { var item = items.filter(function (i) { return i.id === id; })[0]; if (!item) return; var box = byId('resume'); box.textContent = ''; box.appendChild(element('span', '', 'SEU ÚLTIMO TÍTULO')); var button = element('button', '', item.title + '  ↗'); button.onclick = function () { openMovie(item); }; box.appendChild(button); box.hidden = false; }
  byId('search').oninput = function () { clearTimeout(searchTimer); searchTimer = setTimeout(function () { page = 1; render(); }, 200); };
  byId('kind').onchange = function () { page = 1; ensureKind(byId('kind').value, render); };
  byId('previous').onclick = function () { page--; render(); byId('section-title').scrollIntoView(); };
  byId('next').onclick = function () { page++; render(); byId('section-title').scrollIntoView(); };
  byId('all').onclick = function () { onlySaved = false; tabs(); };
  byId('favorites').onclick = function () { onlySaved = true; tabs(); };
  function tabs() { page = 1; byId('all').className = 'filter' + (!onlySaved ? ' active' : ''); byId('favorites').className = 'filter' + (onlySaved ? ' active' : ''); byId('all').setAttribute('aria-pressed', String(!onlySaved)); byId('favorites').setAttribute('aria-pressed', String(onlySaved)); render(); }
  byId('close').onclick = closeMovie; byId('modal').onclick = function (e) { if (e.target === byId('modal')) closeMovie(); };
  byId('help').onclick = function () { lastFocus = document.activeElement; byId('info').hidden = false; document.body.classList.add('modal-open'); byId('close-info').focus(); };
  function closeInfo() { byId('info').hidden = true; if (byId('modal').hidden) document.body.classList.remove('modal-open'); if (lastFocus) lastFocus.focus(); }
  byId('close-info').onclick = closeInfo; byId('info').onclick = function (e) { if (e.target === byId('info')) closeInfo(); };
  document.addEventListener('keydown', function (e) { var dialog = !byId('info').hidden ? byId('info') : (!byId('modal').hidden ? byId('modal') : null); if (!dialog) return; if (e.key === 'Escape' || e.keyCode === 27) { if (!byId('info').hidden) closeInfo(); else closeMovie(); } if (e.key === 'Tab' || e.keyCode === 9) { var controls = dialog.querySelectorAll('button, a[href], iframe'); var first = controls[0], final = controls[controls.length - 1]; if (e.shiftKey && document.activeElement === first) { e.preventDefault(); final.focus(); } else if (!e.shiftKey && document.activeElement === final) { e.preventDefault(); first.focus(); } } });
  render(); if (last) updateResume(last);
}());
