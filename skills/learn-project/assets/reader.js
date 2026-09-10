/* Progressive enhancement: the entire study remains in the generated HTML. */
(() => {
  const views = [...document.querySelectorAll('[data-view]')];
  const nodes = [...document.querySelectorAll('[data-node]')];
  const nodeDetails = [...document.querySelectorAll('[data-node-detail]')];
  const board = document.querySelector('.map-board');
  const svg = document.querySelector('.map-lines');
  const ns = 'http://www.w3.org/2000/svg';
  let currentRoute = '';

  function drawMap() {
    if (!board || !board.getBoundingClientRect().width) return;
    const bounds = board.getBoundingClientRect();
    svg.replaceChildren();
    svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
    const defs = document.createElementNS(ns, 'defs');
    const marker = document.createElementNS(ns, 'marker');
    Object.entries({id:'map-arrow',viewBox:'0 0 10 10',refX:'9',refY:'5',markerWidth:'6',markerHeight:'6',orient:'auto-start-reverse'}).forEach(([key,value]) => marker.setAttribute(key,value));
    const arrow = document.createElementNS(ns, 'polygon');
    arrow.setAttribute('points','0,0 10,5 0,10');
    arrow.setAttribute('fill','currentColor');
    marker.append(arrow); defs.append(marker); svg.append(defs);
    document.querySelectorAll('[data-edge-from]').forEach(edge => {
      const from = nodes.find(node => node.dataset.node === edge.dataset.edgeFrom);
      const to = nodes.find(node => node.dataset.node === edge.dataset.edgeTo);
      if (!from || !to || from === to) return; // Text relationships retain self-loops.
      const a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
      let x1, y1, x2, y2, curve;
      if (Math.abs(a.top - b.top) < 8) {
        const right = b.left > a.left;
        x1 = (right ? a.right : a.left) - bounds.left;
        x2 = (right ? b.left : b.right) - bounds.left;
        y1 = a.top + a.height / 2 - bounds.top;
        y2 = b.top + b.height / 2 - bounds.top;
        curve = `M${x1},${y1} C${(x1+x2)/2},${y1} ${(x1+x2)/2},${y2} ${x2},${y2}`;
      } else {
        const down = b.top > a.top;
        x1 = a.left + a.width / 2 - bounds.left;
        x2 = b.left + b.width / 2 - bounds.left;
        y1 = (down ? a.bottom : a.top) - bounds.top;
        y2 = (down ? b.top : b.bottom) - bounds.top;
        curve = `M${x1},${y1} C${x1},${(y1+y2)/2} ${x2},${(y1+y2)/2} ${x2},${y2}`;
      }
      const path = document.createElementNS(ns, 'path');
      path.setAttribute('d', curve);
      path.setAttribute('marker-end','url(#map-arrow)');
      svg.append(path);
    });
  }

  function navigate({focus = false} = {}) {
    const parts = location.hash.slice(1).split('/');
    const mechanism = parts[0] === 'mechanism' && views.find(view => view.dataset.view === parts[1]);
    const node = parts[0] === 'node' && nodes.find(item => item.dataset.node === parts[1]);
    const viewId = mechanism ? mechanism.dataset.view : 'overview';
    const active = views.find(view => view.dataset.view === viewId);
    views.forEach(view => { view.hidden = view !== active; });
    document.querySelectorAll('[data-nav]').forEach(link => {
      if (link.dataset.nav === viewId) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
    nodes.forEach(item => {
      if (item === node) item.setAttribute('aria-current','true');
      else item.removeAttribute('aria-current');
    });
    nodeDetails.forEach(item => { item.hidden = !node || item.dataset.nodeDetail !== node.dataset.node; });
    let focusTarget = active.querySelector('h1');
    if (node) focusTarget = nodeDetails.find(item => !item.hidden).querySelector('h3');
    if (mechanism) {
      const steps = [...mechanism.querySelectorAll('[data-step]')];
      const selected = steps.find(step => parts[2] === 'step' && step.dataset.step === parts[3]) || steps[0];
      steps.forEach(step => { step.hidden = step !== selected; });
      mechanism.querySelectorAll('[data-flow-step]').forEach(row => {
        row.classList.toggle('flow-active', !!selected && row.dataset.flowStep === selected.dataset.step);
      });
      mechanism.querySelectorAll('[data-step-link]').forEach(link => {
        if (selected && link.dataset.stepLink === selected.dataset.step) link.setAttribute('aria-current','step');
        else link.removeAttribute('aria-current');
      });
      if (selected && parts[2] === 'step') focusTarget = selected.querySelector('h3');
    }
    const routeChanged = currentRoute !== location.hash;
    currentRoute = location.hash;
    requestAnimationFrame(() => {
      drawMap();
      if (focus && routeChanged && focusTarget) {
        focusTarget.focus({preventScroll:true});
        const top = focusTarget.getBoundingClientRect().top + window.scrollY - 90;
        window.scrollTo({top: Math.max(0,top),behavior:'instant'});
      }
    });
  }
  document.documentElement.classList.add('enhanced');
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    const hash = link.getAttribute('href');
    if (!/^#(overview$|mechanism\/|node\/)/.test(hash)) return;
    event.preventDefault();
    if (hash !== location.hash) history.pushState(null,'',hash);
    navigate({focus:true});
  });
  window.addEventListener('hashchange', () => navigate({focus:true}));
  window.addEventListener('popstate', () => navigate({focus:true}));
  if (board) new ResizeObserver(drawMap).observe(board);
  let closedDetails = [];
  window.addEventListener('beforeprint', () => {
    closedDetails = [...document.querySelectorAll('details:not([open])')];
    closedDetails.forEach(item => { item.open = true; });
  });
  window.addEventListener('afterprint', () => {
    closedDetails.forEach(item => { item.open = false; });
    closedDetails = [];
  });
  document.querySelector('.print-button').addEventListener('click', () => window.print());
  navigate();
})();
