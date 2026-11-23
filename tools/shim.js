/* Minimal stand-in for the Claude Data dashboard runtime, so the same page
   (src/index.html) runs as a static, password-protected site.
   window.__SFO_DATA holds the datasets as rows of strings, like CSV. */
(function () {
  var DATA = window.__SFO_DATA || {}, calcs = {}, cache = {}, draws = {}, hooks = [];
  function data(id) {
    if (Object.prototype.hasOwnProperty.call(DATA, id)) {
      var rows = DATA[id];
      return { status: 'ok', data: rows, columns: rows.length ? Object.keys(rows[0]) : [] };
    }
    if (calcs[id]) {
      if (!(id in cache)) {
        var c = calcs[id];
        try { cache[id] = c.fn.apply(null, c.inputs.map(function (i) { return data(i).data; })); }
        catch (e) { console.error('calc ' + id, e); cache[id] = null; }
      }
      return cache[id] == null ? { status: 'error', data: null } : { status: 'ok', data: cache[id] };
    }
    return { status: 'missing', data: [] };
  }
  function shown(el) { return !el.closest('[hidden]'); }
  function run(name) {
    var fn = draws[name]; if (!fn) return;
    document.querySelectorAll('[data-draw="' + name + '"]').forEach(function (el) {
      if (!shown(el)) return;
      try { fn(el); } catch (e) { console.error('draw ' + name, e); }
    });
  }
  function runAll() { hooks.forEach(function (f) { try { f(); } catch (e) { console.error(e); } }); Object.keys(draws).forEach(run); }
  window.dash = {
    data: data,
    calc: function (id, o) { if (!Object.prototype.hasOwnProperty.call(DATA, id)) calcs[id] = o; },
    loader: function () {},
    draw: function (n, fn) { if (fn) draws[n] = fn; else run(n); },
    onData: function (fn) { hooks.push(fn); },
    colors: ['var(--sfo-c0)', 'var(--sfo-c1)', 'var(--sfo-c2)', 'var(--sfo-c3)', 'var(--sfo-c4)'],
    setLink: function (id) { try { history.replaceState(null, '', '#' + id); } catch (e) {} },
    params: function () { return {}; }, setParams: function () {}, resetParams: function () {}, refresh: function () {},
    _runAll: runAll
  };
  var t;
  window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(runAll, 120); });
  document.addEventListener('DOMContentLoaded', function () {
    runAll();
    new MutationObserver(function (ms) {
      if (ms.some(function (m) { return m.attributeName === 'hidden'; })) runAll();
    }).observe(document.getElementById('dash-root'), { attributes: true, subtree: true, attributeFilter: ['hidden'] });
  });
})();
