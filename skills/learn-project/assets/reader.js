/* The reader progressively enhances a complete, sequential HTML study. */
(() => {
  'use strict';

  const body = document.body;
  const root = document.documentElement;
  const isChinese = (root.lang || '').toLowerCase().startsWith('zh');
  const strings = isChinese ? {
    search: '搜索',
    searchHint: '输入章节、概念或实现细节。',
    noResults: '没有找到匹配的内容。',
    resultCount: count => `找到 ${count} 条结果`,
    term: '术语',
    source: '源码证据',
    overview: '项目总览',
    chapter: '章节',
    step: '步骤',
    read: '已读',
    question: '待确认',
    unread: '未标记',
    stale: '内容已更新，请重新标记',
    storageUnavailable: '状态只保留在当前页面',
    progress: (read, total, questions) => `已读 ${read}/${total}${questions ? ` · 待确认 ${questions}` : ''}`,
    copied: '已复制',
    copyUnavailable: '剪贴板不可用，已打开可选中文本',
    copyFailed: '复制失败，请从打开的文本框中复制',
    fallbackTitle: '复制上下文',
    fallbackNote: '请选中下面的文本并复制。',
    close: '关闭',
    project: '项目',
    revision: '版本',
    currentChapter: '当前章节',
    currentStep: '当前步骤',
    context: '上下文',
    questionLabel: '问题',
    continueQuestion: '请基于这份上下文继续说明。',
  } : {
    search: 'Search',
    searchHint: 'Search chapters, concepts, or implementation details.',
    noResults: 'No matching content found.',
    resultCount: count => `${count} result${count === 1 ? '' : 's'}`,
    term: 'Glossary',
    source: 'Source evidence',
    overview: 'Overview',
    chapter: 'Chapter',
    step: 'Step',
    read: 'Read',
    question: 'Question',
    unread: 'Unmarked',
    stale: 'Content changed; mark again',
    storageUnavailable: 'State is kept for this page only',
    progress: (read, total, questions) => `${read}/${total} read${questions ? ` · ${questions} question${questions === 1 ? '' : 's'}` : ''}`,
    copied: 'Copied',
    copyUnavailable: 'Clipboard unavailable; selectable text is open',
    copyFailed: 'Copy failed; use the open text box',
    fallbackTitle: 'Copy context',
    fallbackNote: 'Select the text below and copy it.',
    close: 'Close',
    project: 'Project',
    revision: 'Revision',
    currentChapter: 'Current chapter',
    currentStep: 'Current step',
    context: 'Context',
    questionLabel: 'Question',
    continueQuestion: 'Please continue from this context.',
  };

  const query = (selector, scope = document) => scope ? scope.querySelector(selector) : null;
  const queryAll = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));
  const cleanText = value => String(value || '').replace(/\s+/g, ' ').trim();
  const elementText = element => element ? cleanText(element.textContent) : '';
  const encodePart = value => encodeURIComponent(String(value || ''));
  const safeDecode = value => {
    try { return decodeURIComponent(value); } catch (_error) { return value; }
  };

  const views = queryAll('.view[data-view]');
  const viewById = new Map(views.map(view => [view.dataset.view, view]));
  const nodes = queryAll('.map-node[data-node]');
  const nodesById = new Map(nodes.map(node => [node.dataset.node, node]));
  const nodeDetails = queryAll('.node-detail[data-node-detail]');
  const edgeRows = queryAll('.relationships li[data-edge-from][data-edge-to]');
  const mapBoard = query('.map-board');
  const relationships = query('.relationships');
  const searchDialog = query('#search-dialog');
  const searchInput = query('#study-search');
  const searchResults = query('.search-results', searchDialog || document);
  const termDialog = query('#term-dialog');
  const termContent = query('.term-content', termDialog || document);
  const resumeLink = query('.resume-link');
  const progressOutput = query('.reading-progress');
  const topbar = query('.topbar');
  const reducedMotion = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let currentViewId = 'overview';
  let currentStepId = '';
  let lastMainHash = '#overview';
  let termReturnHash = '#overview';
  let pendingStepId = '';
  let pendingStepUntil = 0;
  let scrollFrame = 0;
  let resumeTimer = 0;
  let statusTimer = 0;
  let resumeRecord = null;
  let storageUnavailable = false;
  const memoryStates = new Map();

  const studyKey = body.dataset.studyKey || location.pathname || 'study';
  const statePrefix = `learn-project:reading:${encodePart(studyKey)}:`;
  const resumeStorageKey = `learn-project:resume:${encodePart(studyKey)}`;
  const storage = (() => {
    try {
      if (typeof localStorage === 'undefined') return null;
      const probe = `${statePrefix}probe`;
      localStorage.setItem(probe, '1');
      localStorage.removeItem(probe);
      return localStorage;
    } catch (_error) {
      storageUnavailable = true;
      return null;
    }
  })();

  function routeFromHash(hash = location.hash) {
    const raw = safeDecode(String(hash || '').replace(/^#/, ''));
    const parts = raw.split('/');
    if (!raw || raw === 'overview') return { type: 'overview', viewId: 'overview' };
    if (parts[0] === 'mechanism' && viewById.has(parts[1])) {
      return {
        type: 'mechanism',
        viewId: parts[1],
        stepId: parts[2] === 'step' ? parts[3] : '',
      };
    }
    if (parts[0] === 'node' && nodesById.has(parts[1])) {
      return { type: 'node', viewId: 'overview', nodeId: parts[1] };
    }
    if (parts[0] === 'relationship' && /^\d+$/.test(parts[1] || '') && document.getElementById(`relationship/${parts[1]}`)) {
      return { type: 'relationship', viewId: 'overview', edgeId: parts[1] };
    }
    if (parts[0] === 'term' && parts[1] && document.getElementById(`term/${parts[1]}`)) {
      return { type: 'term', termId: parts[1] };
    }
    if (parts[0] === 'source' && parts[1] && /^\d+$/.test(parts[2] || '')) {
      const occurrence = Number(parts[2]);
      const sourceId = `source/${parts[1]}/${parts[2]}`;
      let evidence = document.getElementById(sourceId);
      if (!evidence) {
        const matches = queryAll('.evidence[data-evidence]').filter(item => item.dataset.evidence === parts[1]);
        evidence = matches[occurrence - 1] || null;
      }
      if (evidence && evidence.matches('details.evidence[data-evidence]')) {
        const view = evidence.closest('.view[data-view]');
        const mainHash = view ? routeForSearchElement(evidence, view) : '#overview';
        const targetType = parts[3] === 'line' && /^\d+$/.test(parts[4] || '')
          ? 'line'
          : parts[3] === 'note' && /^\d+$/.test(parts[4] || '')
            ? 'note'
            : 'summary';
        return {
          type: 'source',
          viewId: view ? view.dataset.view : 'overview',
          sourceId: evidence.id || sourceId,
          evidenceId: evidence.dataset.evidence,
          occurrence,
          evidence,
          targetType,
          line: targetType === 'line' ? Number(parts[4]) : 0,
          note: targetType === 'note' ? Number(parts[4]) : 0,
          mainRoute: routeFromHash(mainHash),
        };
      }
    }
    return { type: 'unknown', raw };
  }

  function mainHashFor(route, stepId = route.stepId || '') {
    if (route.type === 'source') {
      const mainRoute = route.mainRoute || { type: 'overview', viewId: 'overview' };
      return mainHashFor(mainRoute, stepId || mainRoute.stepId || '');
    }
    if (route.type === 'relationship') return `#relationship/${route.edgeId}`;
    if (route.type === 'node') return `#node/${encodePart(route.nodeId)}`;
    if (route.type === 'mechanism') {
      const base = `#mechanism/${encodePart(route.viewId)}`;
      return stepId ? `${base}/step/${encodePart(stepId)}` : base;
    }
    return '#overview';
  }

  function writeHash(hash, mode = 'push') {
    if (!hash || location.hash === hash) return false;
    if (mode === 'replace') history.replaceState(null, '', hash);
    else history.pushState(null, '', hash);
    return true;
  }

  function showDialog(dialog) {
    if (!dialog) return;
    try {
      if (typeof dialog.showModal === 'function' && !dialog.open) dialog.showModal();
      else {
        dialog.setAttribute('open', '');
        dialog.hidden = false;
      }
    } catch (_error) {
      dialog.setAttribute('open', '');
      dialog.hidden = false;
    }
  }

  function hideDialog(dialog) {
    if (!dialog) return;
    try {
      if (typeof dialog.close === 'function' && dialog.open) dialog.close();
      else {
        dialog.removeAttribute('open');
        dialog.hidden = true;
      }
    } catch (_error) {
      dialog.removeAttribute('open');
      dialog.hidden = true;
    }
  }

  function focusWithoutScroll(element) {
    if (!element || typeof element.focus !== 'function') return;
    try { element.focus({ preventScroll: true }); } catch (_error) { element.focus(); }
  }

  function scrollToElement(element, behavior = reducedMotion ? 'auto' : 'smooth') {
    if (!element) return;
    const offset = (topbar ? topbar.offsetHeight : 0) + 24;
    const top = Math.max(0, element.getBoundingClientRect().top + window.scrollY - offset);
    try { window.scrollTo({ top, behavior }); } catch (_error) { window.scrollTo(0, top); }
  }

  function populateTermDialog(termId) {
    if (!termContent) return false;
    const term = document.getElementById(`term/${termId}`) || query(`[data-term="${CSS.escape(termId)}"]`);
    if (!term) return false;
    const summary = query(':scope > summary', term) || query('summary', term);
    const definition = query(':scope > p', term) || query('p', term);
    const heading = document.createElement('h2');
    heading.textContent = elementText(summary) || termId;
    termContent.replaceChildren(heading);
    if (definition) termContent.append(definition.cloneNode(true));
    return true;
  }

  function openTerm(termId, { historyMode = 'push' } = {}) {
    if (!populateTermDialog(termId)) return;
    if (!location.hash.startsWith('#term/')) termReturnHash = location.hash || lastMainHash;
    if (historyMode !== 'none') writeHash(`#term/${encodePart(termId)}`, historyMode);
    showDialog(termDialog);
    const close = query('[data-close-term]', termDialog || document);
    focusWithoutScroll(close || termContent);
  }

  function closeTerm({ restore = true } = {}) {
    hideDialog(termDialog);
    if (termContent) termContent.replaceChildren();
    if (restore && location.hash.startsWith('#term/')) {
      const hash = termReturnHash || '#overview';
      writeHash(hash, 'replace');
      navigate({ scroll: false, focus: false });
    }
  }

  function updateMap(selectedId = '') {
    if (mapBoard) mapBoard.classList.toggle('has-selection', Boolean(selectedId));
    if (relationships) relationships.classList.toggle('has-selection', Boolean(selectedId));
    const neighbors = new Set();
    queryAll('.architecture [data-edge-index]').forEach(edge => {
      edge.classList.toggle('is-relevant', Boolean(selectedId && (edge.dataset.edgeFrom === selectedId || edge.dataset.edgeTo === selectedId)));
    });
    edgeRows.forEach(row => {
      const from = row.dataset.edgeFrom;
      const to = row.dataset.edgeTo;
      const relevant = Boolean(selectedId && (from === selectedId || to === selectedId));
      row.classList.toggle('is-relevant', relevant);
      if (selectedId && relevant) {
        if (from !== selectedId) neighbors.add(from);
        if (to !== selectedId) neighbors.add(to);
      }
    });
    nodes.forEach(node => {
      const selected = node.dataset.node === selectedId;
      const neighbor = !selected && neighbors.has(node.dataset.node);
      node.classList.toggle('is-selected', selected);
      node.classList.toggle('is-neighbor', neighbor);
      if (selected) node.setAttribute('aria-current', 'true');
      else node.removeAttribute('aria-current');
      node.toggleAttribute('data-related', neighbor);
    });
    nodeDetails.forEach(detail => {
      detail.hidden = !selectedId || detail.dataset.nodeDetail !== selectedId;
    });
  }

  function stepsFor(view) {
    return view ? queryAll('.step-panel[data-step]', view) : [];
  }

  function setActiveStep(view, selected) {
    const steps = stepsFor(view);
    const selectedId = selected ? selected.dataset.step : '';
    steps.forEach(step => {
      // Every step stays in the document and in the active reading flow.
      step.hidden = false;
      step.removeAttribute('aria-hidden');
      step.classList.toggle('is-active', step === selected);
    });
    queryAll('[data-step-link]', view).forEach(link => {
      if (selectedId && link.dataset.stepLink === selectedId) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    });
    queryAll('[data-flow-step]', view).forEach(row => {
      row.classList.toggle('flow-active', Boolean(selectedId && row.dataset.flowStep === selectedId));
    });
    currentStepId = selectedId;
  }

  function applyViewRoute(route, { focus = false, scroll = false, initial = false } = {}) {
    const activeRoute = route.type === 'node' ? { ...route, viewId: 'overview' } : route;
    const active = viewById.get(activeRoute.viewId) || viewById.get('overview') || views[0];
    if (!active) return;
    views.forEach(view => { view.hidden = view !== active; });
    currentViewId = active.dataset.view;
    queryAll('[data-nav]').forEach(link => {
      if (link.dataset.nav === currentViewId) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });

    let selectedStep = null;
    if (active.classList.contains('mechanism')) {
      const steps = stepsFor(active);
      selectedStep = steps.find(step => step.dataset.step === activeRoute.stepId) || steps[0] || null;
      setActiveStep(active, selectedStep);
    } else {
      currentStepId = '';
    }

    const selectedNode = activeRoute.type === 'node' ? activeRoute.nodeId : '';
    if (selectedNode) {
      const selector = query('#map-path');
      if (selector && selector.value) {
        selector.value = '';
        selector.dispatchEvent(new Event('change'));
      }
    }
    updateMap(currentViewId === 'overview' ? selectedNode : '');
    lastMainHash = mainHashFor(activeRoute, selectedStep && activeRoute.type === 'mechanism' ? selectedStep.dataset.step : '');
    updateReadingStateUi();

    const target = selectedNode
      ? query(`.node-detail[data-node-detail="${CSS.escape(selectedNode)}"] h3`)
      : selectedStep && activeRoute.stepId
        ? query('h3', selectedStep)
        : query('h1', active);
    if (activeRoute.type === 'relationship') {
      const row = document.getElementById(`relationship/${activeRoute.edgeId}`);
      relationships.open = true;
      queryAll('details', row).forEach(detail => { detail.open = true; });
      row.tabIndex = -1;
      if (focus) focusWithoutScroll(row);
      if (scroll) scrollToElement(row);
      if (!initial) scheduleResumeSave();
      return;
    }
    if (focus) focusWithoutScroll(target);
    if (scroll) {
      if (selectedNode) scrollToElement(query(`.node-detail[data-node-detail="${CSS.escape(selectedNode)}"]`));
      else if (selectedStep && activeRoute.stepId) {
        pendingStepId = selectedStep.dataset.step;
        pendingStepUntil = Date.now() + 1800;
        scrollToElement(selectedStep);
      } else scrollToElement(target);
    }
    if (!initial) scheduleResumeSave();
  }

  function navigate(options = {}) {
    const route = routeFromHash();
    if (route.type === 'term') {
      const mainRoute = routeFromHash(termReturnHash || '#overview');
      if (mainRoute.type === 'source') {
        applyViewRoute(mainRoute.mainRoute || { type: 'overview', viewId: 'overview' }, { initial: true });
        revealSourceRoute(mainRoute, { focus: false, scroll: false });
      } else {
        applyViewRoute(mainRoute, { initial: true });
      }
      openTerm(route.termId, { historyMode: 'none' });
      return;
    }
    if (termDialog && termDialog.open) closeTerm({ restore: false });
    if (route.type === 'source') {
      applyViewRoute(route.mainRoute || { type: 'overview', viewId: 'overview' }, { ...options, scroll: false, focus: false });
      revealSourceRoute(route, options);
      return;
    }
    clearSearchHighlights();
    if (route.type === 'unknown') {
      applyViewRoute({ type: 'overview', viewId: 'overview' }, options);
      return;
    }
    applyViewRoute(route, options);
  }

  function stateKey(view) {
    return `${statePrefix}${encodePart(view.dataset.view)}:${encodePart(view.dataset.fingerprint || 'unversioned')}`;
  }

  function stateFor(view) {
    if (!view) return { state: 'unread', stale: false };
    const viewId = view.dataset.view;
    const fingerprint = view.dataset.fingerprint || 'unversioned';
    const memory = memoryStates.get(viewId);
    let record = memory && memory.fingerprint === fingerprint ? memory : null;
    if (!record && storage) {
      try {
        const raw = storage.getItem(stateKey(view));
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && parsed.fingerprint === fingerprint && ['unread', 'read', 'question'].includes(parsed.state)) {
            record = parsed;
            memoryStates.set(viewId, parsed);
          }
        }
      } catch (_error) {
        storageUnavailable = true;
        try { storage.removeItem(stateKey(view)); } catch (_removeError) { /* blocked storage */ }
      }
    }
    let stale = false;
    if (storage) {
      const prefix = `${statePrefix}${encodePart(viewId)}:`;
      try {
        for (const key of Object.keys(storage)) {
          if (!key.startsWith(prefix)) continue;
          const parsed = JSON.parse(storage.getItem(key));
          if (parsed && parsed.fingerprint && parsed.fingerprint !== fingerprint && ['read', 'question'].includes(parsed.state)) {
            stale = true;
            break;
          }
        }
      } catch (_error) {
        storageUnavailable = true;
      }
    }
    return { state: record ? record.state : 'unread', stale };
  }

  function stateLabel(state) {
    return state === 'read' ? strings.read : state === 'question' ? strings.question : strings.unread;
  }

  function setReadingState(view, requestedState) {
    if (!view) return;
    const current = stateFor(view).state;
    const state = current === requestedState ? 'unread' : requestedState;
    const record = { version: 1, view: view.dataset.view, fingerprint: view.dataset.fingerprint || 'unversioned', state, updatedAt: Date.now() };
    memoryStates.set(view.dataset.view, record);
    if (storage) {
      try {
        const prefix = `${statePrefix}${encodePart(view.dataset.view)}:`;
        Object.keys(storage).filter(key => key.startsWith(prefix) && key !== stateKey(view)).forEach(key => storage.removeItem(key));
        if (state === 'unread') storage.removeItem(stateKey(view));
        else storage.setItem(stateKey(view), JSON.stringify(record));
      } catch (_error) {
        storageUnavailable = true;
      }
    }
    updateReadingStateUi();
  }

  function updateReadingStateUi() {
    let readCount = 0;
    let questionCount = 0;
    views.forEach(view => {
      const { state, stale } = stateFor(view);
      view.dataset.readingState = state;
      if (state === 'read') readCount += 1;
      if (state === 'question') questionCount += 1;
      queryAll('[data-reading-state]', view).forEach(button => {
        const active = button.dataset.readingState === state && state !== 'unread';
        button.setAttribute('aria-pressed', String(active));
      });
      const status = query('.chapter-status', view);
      if (status) {
        const labels = [stateLabel(state)];
        if (stale) labels.push(strings.stale);
        if (storageUnavailable) labels.push(strings.storageUnavailable);
        status.textContent = labels.join(' · ');
      }
      const navState = query(`[data-nav="${CSS.escape(view.dataset.view)}"] .nav-state`);
      if (navState) {
        if (state === 'unread') navState.removeAttribute('data-state');
        else navState.dataset.state = state;
      }
    });
    if (progressOutput) {
      progressOutput.value = strings.progress(readCount, views.length, questionCount);
      progressOutput.textContent = progressOutput.value;
    }
  }

  function validResume(record) {
    if (!record || typeof record.hash !== 'string' || !Number.isFinite(record.scrollY) || record.scrollY < 0) return false;
    const route = routeFromHash(record.hash);
    if (route.type === 'unknown' || route.type === 'term') return false;
    const view = viewById.get(route.viewId);
    return Boolean(view && record.fingerprint === (view.dataset.fingerprint || 'unversioned'));
  }

  function readResume() {
    if (!storage) return null;
    try {
      const raw = storage.getItem(resumeStorageKey);
      if (!raw) return null;
      const record = JSON.parse(raw);
      return validResume(record) ? record : null;
    } catch (_error) {
      storageUnavailable = true;
      try { storage.removeItem(resumeStorageKey); } catch (_removeError) { /* blocked storage */ }
      return null;
    }
  }

  function saveResume() {
    resumeTimer = 0;
    const route = routeFromHash();
    if (route.type === 'unknown' || route.type === 'term') return;
    const view = viewById.get(route.viewId);
    if (!view) return;
    const record = {
      hash: route.type === 'source' ? location.hash : mainHashFor(route, route.type === 'mechanism' ? currentStepId : ''),
      viewId: view.dataset.view,
      fingerprint: view.dataset.fingerprint || 'unversioned',
      scrollY: Math.max(0, Math.round(window.scrollY || 0)),
      updatedAt: Date.now(),
    };
    resumeRecord = record;
    if (storage) {
      try { storage.setItem(resumeStorageKey, JSON.stringify(record)); }
      catch (_error) { storageUnavailable = true; }
    }
    updateResumeLink();
  }

  function scheduleResumeSave() {
    if (resumeTimer) return;
    resumeTimer = window.setTimeout(saveResume, 220);
  }

  function updateResumeLink() {
    if (!resumeLink) return;
    if (!validResume(resumeRecord)) {
      resumeLink.hidden = true;
      return;
    }
    resumeLink.hidden = false;
    resumeLink.href = resumeRecord.hash;
    resumeLink.dataset.scrollY = String(Math.max(0, resumeRecord.scrollY || 0));
  }

  function searchText(element) {
    const clone = element.cloneNode(true);
    queryAll('pre', clone).forEach(code => code.remove());
    return cleanText(clone.textContent);
  }

  function searchHit(text, needle, words) {
    const value = String(text || '');
    const lower = value.toLocaleLowerCase();
    const exactOffset = lower.indexOf(needle);
    if (exactOffset >= 0) return { offset: exactOffset, length: needle.length, exact: true };
    for (const word of words) {
      const offset = lower.indexOf(word);
      if (offset >= 0) return { offset, length: word.length, exact: false };
    }
    return null;
  }

  function searchSnippet(text, hit, radius = 96) {
    const value = String(text || '');
    if (!hit) return cleanText(value).slice(0, radius * 2);
    const start = Math.max(0, hit.offset - radius);
    const end = Math.min(value.length, hit.offset + Math.max(hit.length, 1) + radius);
    return cleanText(`${start ? '…' : ''}${value.slice(start, end)}${end < value.length ? '…' : ''}`);
  }

  function sourceLineAtOffset(evidence, text, offset) {
    const firstLine = Number(query('.code-line[data-line]', evidence)?.dataset.line);
    if (!Number.isFinite(firstLine)) return 0;
    return firstLine + String(text || '').slice(0, offset).split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/).length - 1;
  }

  function sourceRouteForSearch(evidence, occurrence, target = null) {
    const sourceId = evidence.id || `source/${encodePart(evidence.dataset.evidence)}/${occurrence}`;
    const suffix = target && target.type === 'line'
      ? `/line/${target.value}`
      : target && target.type === 'note'
        ? `/note/${target.value}`
        : '';
    return `#${sourceId}${suffix}`;
  }

  function sourceSearchSegments(evidence) {
    const summary = query(':scope > summary', evidence) || query('summary', evidence);
    const body = queryAll(':scope > p', evidence).map(searchText).filter(Boolean).join(' ');
    const sourceCode = query('pre code[data-source-text]', evidence);
    const excerpt = sourceCode ? sourceExcerpt(evidence) : '';
    const segments = [];
    if (summary) segments.push({ kind: 'title', text: elementText(summary) });
    if (body) segments.push({ kind: 'body', text: body });
    if (excerpt) segments.push({ kind: 'source', text: excerpt });
    queryAll('.source-annotation-text', evidence).forEach((note, index) => {
      const text = elementText(note);
      if (text) segments.push({ kind: 'note', text, note: index + 1 });
    });
    return segments;
  }

  function sourceContextRank(evidence) {
    if (evidence.closest('.step-panel[data-step]')) return 3;
    if (evidence.closest('.view.mechanism[data-view]')) return 2;
    return 1;
  }

  function routeForSearchElement(element, view) {
    const nodeDetail = element.closest('[data-node-detail]');
    if (nodeDetail) return `#node/${encodePart(nodeDetail.dataset.nodeDetail)}`;
    const step = element.closest('.step-panel[data-step]');
    if (step) return `#mechanism/${encodePart(view.dataset.view)}/step/${encodePart(step.dataset.step)}`;
    return view.dataset.view === 'overview' ? '#overview' : `#mechanism/${encodePart(view.dataset.view)}`;
  }

  function buildSearchIndex() {
    const entries = [];
    views.forEach(view => {
      queryAll('h1, h2, h3, p', view).forEach(element => {
        if (element.closest('code, pre, .evidence')) return;
        const snippet = searchText(element);
        if (!snippet) return;
        const ownerStep = element.closest('.step-panel[data-step]');
        const ownerNode = element.closest('[data-node-detail]');
        const heading = ownerStep ? query('h3', ownerStep) : ownerNode ? query('h3', ownerNode) : query('h1', view);
        const title = element.matches('h1, h2, h3') ? snippet : elementText(heading) || strings.overview;
        entries.push({
          title,
          segments: element.matches('h1, h2, h3')
            ? [{ kind: 'title', text: snippet }]
            : [{ kind: 'title', text: title }, { kind: 'body', text: snippet }],
          href: routeForSearchElement(element, view),
          kind: ownerStep ? strings.step : ownerNode ? strings.overview : view.dataset.view === 'overview' ? strings.overview : strings.chapter,
          source: false,
        });
      });
    });
    const occurrences = new Map();
    const sourceByReference = new Map();
    queryAll('.evidence[data-evidence]').forEach(evidence => {
      const reference = evidence.dataset.evidence;
      if (!reference) return;
      const occurrence = (occurrences.get(reference) || 0) + 1;
      occurrences.set(reference, occurrence);
      const previous = sourceByReference.get(reference);
      if (!previous || sourceContextRank(evidence) > previous.rank) {
        sourceByReference.set(reference, { evidence, occurrence, rank: sourceContextRank(evidence) });
      }
    });
    sourceByReference.forEach(({ evidence, occurrence }, reference) => {
      const segments = sourceSearchSegments(evidence);
      if (!segments.length) return;
      const summary = query(':scope > summary', evidence) || query('summary', evidence);
      entries.push({
        title: elementText(summary) || reference,
        segments,
        href: sourceRouteForSearch(evidence, occurrence),
        kind: strings.source,
        source: true,
        evidence,
        occurrence,
      });
    });
    queryAll('#glossary details[data-term]').forEach(term => {
      const summary = query(':scope > summary', term) || query('summary', term);
      const definition = query(':scope > p', term) || query('p', term);
      const title = elementText(summary) || term.dataset.term;
      const snippet = searchText(definition || term);
      entries.push({
        title,
        segments: [{ kind: 'title', text: title }, { kind: 'body', text: snippet }],
        href: `#term/${encodePart(term.dataset.term)}`,
        kind: strings.term,
        source: false,
      });
    });
    return entries;
  }

  const searchIndex = buildSearchIndex();

  function renderSearchResults(value = '') {
    if (!searchResults) return;
    const needle = cleanText(value).toLocaleLowerCase();
    searchResults.replaceChildren();
    if (!needle) {
      const hint = document.createElement('p');
      hint.className = 'search-empty';
      hint.textContent = strings.searchHint;
      searchResults.append(hint);
      return;
    }
    const words = needle.split(/\s+/).filter(Boolean);
    const matches = searchIndex.map((entry, index) => {
      const haystack = entry.segments.map(segment => segment.text).join(' ').toLocaleLowerCase();
      if (!words.every(word => haystack.includes(word))) return null;
      const hits = entry.segments.map(segment => {
        const hit = searchHit(segment.text, needle, words);
        return hit ? { segment, hit } : null;
      }).filter(Boolean);
      if (!hits.length) return null;
      const roleWeight = { title: 5, body: 4, note: 3, source: 2 };
      const exactHits = hits.filter(item => item.hit.exact);
      const candidates = exactHits.length ? exactHits : hits;
      candidates.sort((a, b) => (roleWeight[b.segment.kind] || 0) - (roleWeight[a.segment.kind] || 0) || a.hit.offset - b.hit.offset);
      const selected = candidates[0];
      let target = null;
      if (entry.source && selected.segment.kind === 'source') {
        const line = sourceLineAtOffset(entry.evidence, selected.segment.text, selected.hit.offset);
        if (line) target = { type: 'line', value: line };
      } else if (entry.source && selected.segment.kind === 'note') {
        target = { type: 'note', value: selected.segment.note };
      }
      const score = (entry.source ? 0 : 1000)
        + (roleWeight[selected.segment.kind] || 0) * 20
        + (selected.hit.exact ? 12 : 0)
        + (entry.title.toLocaleLowerCase().includes(needle) ? 8 : 0);
      return {
        entry,
        score,
        index,
        href: entry.source ? sourceRouteForSearch(entry.evidence, entry.occurrence, target) : entry.href,
        snippet: searchSnippet(selected.segment.text, selected.hit),
      };
    }).filter(Boolean).sort((a, b) => b.score - a.score || a.index - b.index).slice(0, 80);

    const count = document.createElement('p');
    count.className = 'search-empty';
    count.textContent = matches.length ? strings.resultCount(matches.length) : strings.noResults;
    searchResults.append(count);
    matches.forEach(({ entry, href, snippet: snippetText }) => {
      const link = document.createElement('a');
      link.className = 'search-result';
      link.href = href;
      const title = document.createElement('strong');
      title.textContent = entry.title;
      const kind = document.createElement('small');
      kind.textContent = entry.kind;
      const snippet = document.createElement('span');
      snippet.textContent = snippetText;
      link.append(title, kind, snippet);
      searchResults.append(link);
    });
  }

  function openSearch() {
    if (!searchDialog) return;
    renderSearchResults(searchInput ? searchInput.value : '');
    showDialog(searchDialog);
    window.setTimeout(() => {
      focusWithoutScroll(searchInput);
      if (searchInput) searchInput.select();
    }, 0);
  }

  function closeSearch() { hideDialog(searchDialog); }

  function statusFor(button) {
    const evidence = button.closest('.evidence');
    return query('.copy-status', evidence || button.parentElement || document);
  }

  function showStatus(element, message) {
    if (!element) return;
    element.textContent = message;
    window.clearTimeout(statusTimer);
    statusTimer = window.setTimeout(() => { element.textContent = ''; }, 5200);
  }

  function ensureCopyDialog() {
    let dialog = document.getElementById('copy-dialog');
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    dialog.id = 'copy-dialog';
    const close = document.createElement('button');
    close.type = 'button';
    close.setAttribute('aria-label', strings.close);
    close.textContent = '×';
    const title = document.createElement('h2');
    title.textContent = strings.fallbackTitle;
    const note = document.createElement('p');
    note.className = 'copy-fallback-note';
    note.textContent = strings.fallbackNote;
    const textarea = document.createElement('textarea');
    textarea.className = 'copy-fallback-text';
    textarea.readOnly = true;
    dialog.append(close, title, note, textarea);
    document.body.append(dialog);
    close.addEventListener('click', () => hideDialog(dialog));
    dialog.addEventListener('cancel', event => { event.preventDefault(); hideDialog(dialog); });
    return dialog;
  }

  function showCopyFallback(value, status) {
    const dialog = ensureCopyDialog();
    const textarea = query('.copy-fallback-text', dialog);
    textarea.value = value;
    showDialog(dialog);
    focusWithoutScroll(textarea);
    textarea.select();
    showStatus(status, strings.copyUnavailable);
  }

  async function copyText(value, status) {
    if (!value) {
      showStatus(status, strings.copyFailed);
      return;
    }
    try {
      if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') throw new Error('clipboard unavailable');
      await navigator.clipboard.writeText(value);
      showStatus(status, strings.copied);
    } catch (_error) {
      showCopyFallback(value, status);
    }
  }

  function currentQuestionContext() {
    const view = viewById.get(currentViewId) || viewById.get('overview');
    const projectName = elementText(query('.project-name')) || studyKey;
    const revision = body.dataset.revision || elementText(query('.revision'));
    const title = elementText(query('h1', view));
    const question = elementText(query('.question', view));
    const lead = elementText(query('.lead', view));
    const currentStep = currentStepId && query(`.step-panel[data-step="${CSS.escape(currentStepId)}"]`, view);
    const stepTitle = elementText(query('h3', currentStep));
    const lines = [
      `${strings.project}: ${projectName}`,
      `${strings.revision}: ${revision}`,
      `${strings.currentChapter}: ${title}`,
    ];
    if (stepTitle) lines.push(`${strings.currentStep}: ${stepTitle}`);
    if (question) lines.push(`${strings.questionLabel}: ${question}`);
    if (lead) lines.push(`${strings.context}: ${lead}`);
    lines.push('', strings.continueQuestion);
    return lines.join('\n');
  }

  function sourceExcerpt(evidence) {
    const code = query('pre code', evidence);
    if (!code) return '';
    try { return JSON.parse(code.dataset.sourceText); }
    catch (_error) { return ''; }
  }

  function clearSearchHighlights() {
    queryAll('.search-hit').forEach(element => element.classList.remove('search-hit'));
  }

  function setSourceAnnotation(button, active, { searchHit = false } = {}) {
    const evidence = button && button.closest('.evidence');
    if (!evidence) return false;
    const buttons = queryAll('.source-annotation', evidence);
    const selectedIndex = buttons.indexOf(button);
    buttons.forEach(item => item.setAttribute('aria-pressed', String(Boolean(active && item === button))));
    const start = Number(button.dataset.lineStart), end = Number(button.dataset.lineEnd);
    queryAll('.code-line', evidence).forEach(line => {
      const selected = Boolean(active && Number(line.dataset.line) >= start && Number(line.dataset.line) <= end);
      line.classList.toggle('is-annotated', selected);
    });
    queryAll('.source-annotation-text', evidence).forEach((note, index) => {
      note.classList.toggle('search-hit', Boolean(searchHit && active && index === selectedIndex));
    });
    return Boolean(active);
  }

  function revealSourceRoute(route, { focus = false, scroll = false } = {}) {
    const evidence = route.evidence || document.getElementById(route.sourceId);
    if (!evidence) return;
    clearSearchHighlights();
    for (let ancestor = evidence; ancestor; ancestor = ancestor.parentElement) {
      if (ancestor.matches('details')) ancestor.open = true;
    }
    const summary = query('summary', evidence);
    let target = summary;
    if (route.targetType === 'line') {
      target = query(`.code-line[data-line="${route.line}"]`, evidence) || target;
      if (target && target.matches('.code-line')) target.classList.add('search-hit');
    } else if (route.targetType === 'note') {
      const buttons = queryAll('.source-annotation', evidence);
      const button = buttons[route.note - 1];
      if (button) {
        setSourceAnnotation(button, true, { searchHit: true });
        target = queryAll('.source-annotation-text', evidence)[route.note - 1] || button;
      }
    }
    if (!target) return;
    if (target === summary) target.classList.add('search-hit');
    if (!target.matches('summary, button, a[href]')) target.tabIndex = -1;
    if (focus) focusWithoutScroll(target);
    if (scroll) scrollToElement(target);
  }

  function setupReadingDiagrams() {
    const selector = query('#map-path');
    const graph = query('.architecture');
    if (selector && graph) {
      selector.addEventListener('change', () => {
        updateMap('');
        const description = queryAll('[data-map-path]').find(item => item.dataset.mapPath === selector.value);
        const indices = description ? JSON.parse(description.dataset.pathEdges) : [];
        const participants = new Set();
        graph.classList.toggle('has-path', indices.length > 0);
        queryAll('[data-map-path]').forEach(item => { item.hidden = item !== description; });
        queryAll('[data-edge-index]', graph).forEach(edge => {
          const order = indices.indexOf(Number(edge.dataset.edgeIndex));
          edge.classList.toggle('on-path', order >= 0);
          const number = query('.path-order text', edge);
          if (number) number.textContent = order >= 0 ? String(order + 1) : '';
          if (order >= 0) {
            participants.add(edge.dataset.edgeFrom);
            participants.add(edge.dataset.edgeTo);
          }
        });
        nodes.forEach(node => node.classList.toggle('on-path', participants.has(node.dataset.node)));
      });
    }
    queryAll('.source-annotation').forEach(button => {
      button.addEventListener('click', () => {
        const wasActive = button.getAttribute('aria-pressed') === 'true';
        const evidence = button.closest('.evidence');
        setSourceAnnotation(button, !wasActive);
        if (!wasActive) {
          const start = Number(button.dataset.lineStart);
          const line = query(`.code-line[data-line="${start}"]`, evidence);
          if (line) scrollToElement(line);
        }
      });
    });
  }

  function setupCopyButtons() {
    queryAll('.copy-source').forEach(button => {
      const evidence = button.closest('.evidence');
      const excerpt = evidence ? sourceExcerpt(evidence) : '';
      if (!excerpt) {
        button.hidden = true;
        button.disabled = true;
        return;
      }
      button.addEventListener('click', () => copyText(excerpt, statusFor(button)));
    });
    queryAll('.copy-question').forEach(button => {
      button.addEventListener('click', () => copyText(currentQuestionContext(), query('.copy-status', button.parentElement || document)));
    });
  }

  function trackStepFromScroll() {
    scrollFrame = 0;
    if (routeFromHash().type === 'source') return;
    const view = viewById.get(currentViewId);
    if (!view || !view.classList.contains('mechanism') || location.hash.startsWith('#term/')) return;
    const steps = stepsFor(view);
    if (!steps.length) return;
    const anchor = (topbar ? topbar.offsetHeight : 0) + 32;
    let selected = steps[0];
    steps.forEach(step => {
      if (step.getBoundingClientRect().top <= anchor) selected = step;
    });
    const selectedId = selected.dataset.step;
    if (pendingStepId) {
      if (selectedId === pendingStepId || Date.now() >= pendingStepUntil) pendingStepId = '';
      else return;
    }
    if (selectedId === currentStepId) return;
    setActiveStep(view, selected);
    const hash = `#mechanism/${encodePart(currentViewId)}/step/${encodePart(selectedId)}`;
    if (location.hash !== hash) history.replaceState(null, '', hash);
    lastMainHash = hash;
    scheduleResumeSave();
  }

  function requestStepTracking() {
    if (scrollFrame) return;
    const raf = window.requestAnimationFrame || (callback => window.setTimeout(callback, 16));
    scrollFrame = raf(trackStepFromScroll);
  }

  function handleRouteEvent() { navigate({ scroll: true, focus: true }); }

  document.addEventListener('click', event => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const stateButton = target.closest('button[data-reading-state]');
    if (stateButton) {
      const view = stateButton.closest('.view[data-view]');
      if (view) setReadingState(view, stateButton.dataset.readingState);
      return;
    }
    const link = target.closest('a[href^="#"]');
    if (!link || link.classList.contains('resume-link') || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    if (link.classList.contains('map-clear')) {
      const selector = query('#map-path');
      if (selector) { selector.value = ''; selector.dispatchEvent(new Event('change')); }
    }
    const route = routeFromHash(link.getAttribute('href'));
    if (route.type === 'unknown') return;
    event.preventDefault();
    if (link.closest('.search-results')) closeSearch();
    if (route.type === 'term') {
      openTerm(route.termId);
      return;
    }
    writeHash(link.getAttribute('href'), 'push');
    navigate({ scroll: true, focus: true });
  });

  if (searchDialog) {
    queryAll('[data-close-search]', searchDialog).forEach(button => button.addEventListener('click', closeSearch));
    searchDialog.addEventListener('cancel', event => { event.preventDefault(); closeSearch(); });
  }
  if (termDialog) {
    queryAll('[data-close-term]', termDialog).forEach(button => button.addEventListener('click', () => closeTerm()));
    termDialog.addEventListener('cancel', event => { event.preventDefault(); closeTerm(); });
  }
  if (searchInput) searchInput.addEventListener('input', () => renderSearchResults(searchInput.value));
  const searchButton = query('.search-button');
  if (searchButton) searchButton.addEventListener('click', openSearch);
  const printButton = query('.print-button');
  if (printButton) printButton.addEventListener('click', () => window.print());
  if (resumeLink) {
    resumeLink.addEventListener('click', event => {
      if (!validResume(resumeRecord)) return;
      event.preventDefault();
      const record = resumeRecord;
      writeHash(record.hash, 'push');
      pendingStepId = '';
      navigate({ scroll: false, focus: true });
      window.setTimeout(() => {
        const max = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        try { window.scrollTo({ top: Math.min(max, Math.max(0, record.scrollY || 0)), behavior: 'auto' }); }
        catch (_error) { window.scrollTo(0, Math.min(max, Math.max(0, record.scrollY || 0))); }
      }, 0);
    });
  }
  window.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      openSearch();
    }
    if (event.key === 'Escape' && termDialog && termDialog.open) closeTerm();
  });
  window.addEventListener('hashchange', handleRouteEvent);
  window.addEventListener('popstate', handleRouteEvent);
  window.addEventListener('scroll', () => {
    requestStepTracking();
    scheduleResumeSave();
  }, { passive: true });
  window.addEventListener('resize', requestStepTracking);

  let closedDetails = [];
  window.addEventListener('beforeprint', () => {
    closedDetails = queryAll('details').filter(detail => !detail.open);
    closedDetails.forEach(detail => { detail.open = true; });
  });
  window.addEventListener('afterprint', () => {
    closedDetails.forEach(detail => { detail.open = false; });
    closedDetails = [];
  });

  resumeRecord = readResume();
  updateResumeLink();
  updateReadingStateUi();
  setupCopyButtons();
  setupReadingDiagrams();
  root.classList.add('enhanced');
  navigate({ initial: true, scroll: false, focus: false });
  if (location.hash.startsWith('#mechanism/') || location.hash.startsWith('#node/') || location.hash.startsWith('#relationship/') || location.hash.startsWith('#source/')) {
    requestAnimationFrame(() => navigate({ initial: true, scroll: true, focus: false }));
  }
  window.addEventListener('pagehide', () => { if (resumeTimer) saveResume(); });
})();
