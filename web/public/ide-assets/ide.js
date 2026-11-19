/*
 * PythonIDE online: the editor page.
 *
 * Python runs in a Web Worker (resources/ide/worker.js) using Pyodide.
 * This file handles the editor, the buttons, output, input(), step mode,
 * the Variables panel, turtle drawing, themes and saving programs.
 */
(function () {
    'use strict';

    const CONFIG = window.IDE_CONFIG;
    const CMD = { NEXT: 1, TO_END: 2, STOP: 3, INPUT: 4 };
    const MAX_OUTPUT = 200000; // characters kept in the Output box
    const store = {
        get(key, fallback) {
            try { const v = localStorage.getItem('pythonide.' + key); return v === null ? fallback : v; } catch (e) { return fallback; }
        },
        set(key, value) { try { localStorage.setItem('pythonide.' + key, value); } catch (e) { /* private mode */ } },
    };
    const $ = (id) => document.getElementById(id);
    const el = {
        output: $('output'), input: $('input'), inputRow: $('input-row'), enter: $('btn-enter'),
        status: $('status'), vars: $('vars'), varsHint: $('vars-hint'), title: $('title'),
        run: $('btn-run'), stop: $('btn-stop'), step: $('btn-step'), next: $('btn-next'), end: $('btn-end'),
        auto: $('auto'), speed: $('speed'), loading: $('loading'), loadingText: $('loading-text'),
    };
    let themeName = 'light';
    let language = store.get('language', 'both');

    // ------------------------------------------------------------------ editor
    const editor = CodeMirror.fromTextArea($('code'), {
        mode: { name: 'python', version: 3 },
        theme: 'pyide',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        smartIndent: true,
        matchBrackets: true,
        styleActiveLine: true,
        extraKeys: {
            Tab: (cm) => {
                if (cm.somethingSelected()) cm.indentSelection('add');
                else cm.replaceSelection('    '.slice(cm.getCursor().ch % 4), 'end');
            },
            'Shift-Tab': (cm) => cm.indentSelection('subtract'),
            Backspace: (cm) => {
                // Remove a whole indent level at once, like the desktop app.
                const cur = cm.getCursor();
                const before = cm.getLine(cur.line).slice(0, cur.ch);
                if (!cm.somethingSelected() && before.length && /^ +$/.test(before)) {
                    const n = before.length % 4 || 4;
                    cm.replaceRange('', { line: cur.line, ch: cur.ch - n }, cur);
                } else {
                    return CodeMirror.Pass;
                }
            },
            'Ctrl-/': 'toggleComment',
            'Cmd-/': 'toggleComment',
        },
    });

    let marked = { step: null, error: null };
    function markLine(kind, line) {
        const old = marked[kind];
        if (old !== null) {
            editor.removeLineClass(old, 'background', 'line-' + kind);
            editor.removeLineClass(old, 'gutter', 'gutter-' + kind);
        }
        marked[kind] = null;
        if (line) {
            const handle = editor.addLineClass(line - 1, 'background', 'line-' + kind);
            editor.addLineClass(line - 1, 'gutter', 'gutter-' + kind);
            marked[kind] = handle;
            editor.scrollIntoView({ line: line - 1, ch: 0 }, 80);
        }
    }

    // ------------------------------------------------------------- the worker
    const canRun = typeof SharedArrayBuffer !== 'undefined' && self.crossOriginIsolated;
    const shared = canRun ? {
        sync: new SharedArrayBuffer(16),
        data: new SharedArrayBuffer(64 * 1024),
        interrupt: new SharedArrayBuffer(1),
    } : null;
    const sync = shared && new Int32Array(shared.sync);
    const data = shared && new Uint8Array(shared.data);
    const interrupt = shared && new Uint8Array(shared.interrupt);
    const encoder = new TextEncoder();
    let worker = null;
    let ready = false;
    let pendingRun = null;
    let stopTimer = null;

    function startWorker() {
        ready = false;
        worker = new Worker(CONFIG.workerUrl);
        worker.onmessage = (e) => handle(JSON.parse(e.data));
        worker.onerror = (e) => {
            status('Python could not start: ' + (e.message || 'unknown problem') + '. Try reloading the page.');
        };
        worker.postMessage({
            type: 'init', pyodideUrl: CONFIG.pyodideUrl, assetBase: CONFIG.assetBase,
            version: CONFIG.version, sync: shared.sync, data: shared.data, interrupt: shared.interrupt,
        });
    }

    function command(cmd, text) {
        let len = 0;
        if (text) {
            const bytes = encoder.encode(text).slice(0, data.length);
            data.set(bytes);
            len = bytes.length;
        }
        Atomics.store(sync, 1, cmd);
        Atomics.store(sync, 2, len);
        Atomics.store(sync, 0, 1);
        Atomics.notify(sync, 0);
    }

    // ------------------------------------------------------------- running
    let mode = 'idle'; // idle | run | step
    let waitingInput = false;
    let hadError = false;
    let steps = 0;
    let prevValues = {};
    let autoTimer = null;
    let currentSource = '';

    function startProgram(step) {
        if (!canRun) return;
        if (mode !== 'idle') {
            stopProgram();
            return;
        }
        clearOutput();
        markLine('error', null);
        markLine('step', null);
        clearVars();
        turtleReset();
        hadError = false;
        steps = 0;
        prevValues = {};
        currentSource = editor.getValue();
        showTab('vars');
        setMode(step ? 'step' : 'run');
        if (step) {
            el.varsHint.textContent = 'Green rows changed in the last step.';
            showTab('vars');
        }
        const run = { type: 'run', code: currentSource, step: !!step };
        if (ready) {
            worker.postMessage(run);
            status(step ? 'Step mode: the yellow line runs next. Press Next (F7).' : 'Running…  Press Stop (Shift+F5) to stop it.');
        } else {
            pendingRun = run;
            status('Python is still loading. Your program will start in a moment…');
        }
    }

    function stopProgram() {
        if (mode === 'idle') return;
        cancelAuto();
        if (pendingRun) {
            pendingRun = null;
            appendText('\nProgram stopped.\n', 'info');
            finish();
            return;
        }
        interrupt[0] = 2; // raises KeyboardInterrupt in running Python
        command(CMD.STOP); // wakes it up if it is waiting for input or a step
        clearTimeout(stopTimer);
        stopTimer = setTimeout(() => {
            // Still busy (e.g. a very long calculation): restart Python.
            if (mode !== 'idle') {
                worker.terminate();
                appendText('\nProgram stopped.\n', 'info');
                hadError = true;
                finish();
                el.loading.hidden = false;
                el.loadingText.textContent = 'Restarting Python…';
                startWorker();
            }
        }, 2000);
    }

    function handle(msg) {
        switch (msg.t) {
            case 'status':
                el.loadingText.textContent = msg.text;
                break;
            case 'ready':
                ready = true;
                el.loading.hidden = true;
                if (pendingRun) {
                    worker.postMessage(pendingRun);
                    pendingRun = null;
                    status(mode === 'step' ? 'Step mode: the yellow line runs next. Press Next (F7).' : 'Running…');
                } else if (mode === 'idle') {
                    status(viewingNote || 'Ready (Python ' + msg.python + '). Press Run (F5) to run your program.');
                }
                break;
            case 'fatal':
                el.loadingText.textContent = 'Python could not start: ' + msg.text;
                status('Python could not start. Check your internet connection and reload the page.');
                break;
            case 'out':
                appendText(msg.text);
                break;
            case 'err':
                appendText(msg.text, 'stderr');
                break;
            case 'input':
                cancelAuto();
                setWaiting(true);
                break;
            case 'line':
                steps += 1;
                markLine('step', msg.line);
                showScopes(msg.scopes);
                status('Step ' + steps + ': line ' + msg.line + ' (yellow) runs next.  Press Next (F7).');
                if (el.auto.checked) scheduleAuto();
                break;
            case 'error':
                hadError = true;
                showError(msg.info, msg.help);
                break;
            case 'stopped':
                hadError = true;
                appendText('\nProgram stopped.\n', 'info');
                status('Program stopped.');
                break;
            case 'vars':
                showFinalVars(msg.vars);
                break;
            case 'turtle':
                turtleCommands(msg.cmds);
                break;
            case 'internal':
                appendText('\n[PythonIDE problem: ' + msg.text + ']\n', 'stderr');
                break;
            case 'done':
                if (!hadError) {
                    appendText('\n--- Program finished (' + Number(msg.seconds).toFixed(1) + ' s) ---\n', 'info');
                    status('Program finished.');
                }
                finish();
                break;
        }
    }

    function finish() {
        clearTimeout(stopTimer);
        cancelAuto();
        markLine('step', null);
        setMode('idle');
    }

    function setMode(newMode) {
        mode = newMode;
        el.run.disabled = false;
        el.stop.disabled = mode === 'idle';
        el.step.disabled = mode === 'run';
        el.next.disabled = mode !== 'step';
        el.end.disabled = mode !== 'step';
        editor.setOption('readOnly', mode === 'step');
        setWaiting(false);
    }

    function setWaiting(waiting) {
        waitingInput = waiting;
        el.input.disabled = !waiting;
        el.enter.disabled = !waiting;
        el.inputRow.classList.toggle('waiting', waiting);
        el.inputRow.querySelector('label').textContent = waiting ? 'Type here and press Enter:' : 'Input:';
        if (waiting) {
            el.input.focus();
            status('Your program is waiting for you to type something below and press Enter.');
        }
    }

    function sendInput() {
        if (!waitingInput) return;
        const text = el.input.value;
        el.input.value = '';
        appendText(text + '\n', 'typed');
        setWaiting(false);
        command(CMD.INPUT, text);
        if (mode === 'step') {
            status('Step mode: press Next (F7).');
            if (el.auto.checked) scheduleAuto();
        } else {
            status('Running…');
        }
    }

    function nextStep() {
        if (mode === 'idle') { startProgram(true); return; }
        if (mode !== 'step') return;
        if (waitingInput) { el.input.focus(); return; }
        command(CMD.NEXT);
    }

    function toEnd() {
        if (mode !== 'step') return;
        el.auto.checked = false;
        cancelAuto();
        markLine('step', null);
        command(CMD.TO_END);
    }

    function scheduleAuto() {
        cancelAuto();
        autoTimer = setTimeout(() => {
            autoTimer = null;
            if (mode === 'step' && el.auto.checked && !waitingInput) command(CMD.NEXT);
        }, Number(el.speed.value));
    }

    function cancelAuto() {
        clearTimeout(autoTimer);
        autoTimer = null;
    }

    // ------------------------------------------------------------- output
    function appendText(text, cls) {
        const out = el.output;
        const atBottom = out.scrollHeight - out.scrollTop - out.clientHeight < 40;
        if (cls) {
            const span = document.createElement('span');
            span.className = cls;
            span.textContent = text;
            out.appendChild(span);
        } else if (out.lastChild && out.lastChild.nodeType === 3) {
            out.lastChild.appendData(text);
        } else {
            out.appendChild(document.createTextNode(text));
        }
        // Keep the page fast when a program prints forever.
        if (out.textContent.length > MAX_OUTPUT * 1.2) {
            while (out.firstChild && out.textContent.length > MAX_OUTPUT) out.removeChild(out.firstChild);
        }
        if (atBottom) out.scrollTop = out.scrollHeight;
    }

    function clearOutput() {
        el.output.textContent = '';
    }

    function showError(info, help) {
        const lang = language;
        const box = document.createElement('div');
        box.className = 'help';
        const add = (cls, text) => {
            if (!text) return;
            const div = document.createElement('div');
            div.className = cls;
            div.textContent = text;
            box.appendChild(div);
        };
        add('title', (info.line ? 'Error on line ' + info.line + ': ' : 'Error: ') + help.title);
        if (lang !== 'ne') add('text', help.en);
        if (lang !== 'en') add('text ne', help.ne);
        if (lang !== 'ne' && help.hint_en) add('hint', 'Tip: ' + help.hint_en);
        if (lang !== 'en' && help.hint_ne) add('hint ne', 'सुझाव: ' + help.hint_ne);
        add('tech', 'Python says: ' + info.type + ': ' + info.msg);
        el.output.appendChild(box);
        box.scrollIntoView({ block: 'nearest' });
        if (info.line) {
            markLine('step', null);
            markLine('error', info.line);
        }
        status(info.line ? 'There is an error on line ' + info.line + '. Read the help in the Output box.'
            : 'Your program has an error.');
    }

    // ------------------------------------------------------------- variables
    function clearVars() {
        el.vars.textContent = '';
        el.varsHint.textContent = 'Run or Step your program to see its variables here.';
    }

    function row(cells, cls) {
        const tr = document.createElement('tr');
        if (cls) tr.className = cls;
        cells.forEach((text, i) => {
            const td = document.createElement('td');
            td.textContent = text;
            if (i === 1) td.className = 'value';
            tr.appendChild(td);
        });
        if (cells.length === 1) tr.firstChild.colSpan = 3;
        el.vars.appendChild(tr);
    }

    function showFinalVars(rows) {
        if (mode === 'step') {
            showScopes([['Main program (finished)', rows]]);
            return;
        }
        el.vars.textContent = '';
        el.varsHint.textContent = rows.length ? 'Variables when the program ended:' : 'Your program has no variables.';
        rows.forEach(([name, type, value]) => row([name, value, type]));
    }

    function showScopes(scopes) {
        el.vars.textContent = '';
        const values = {};
        scopes.forEach(([title, rows]) => {
            row([title], 'scope');
            rows.forEach(([name, type, value]) => {
                const key = title + '\u0000' + name;
                values[key] = value;
                row(['  ' + name, value, type], prevValues[key] !== value ? 'changed' : '');
            });
        });
        prevValues = values;
    }

    // ------------------------------------------------------------- turtle
    const canvas = $('canvas');
    const sprites = $('sprites');
    const ctx = canvas.getContext('2d');
    const sctx = sprites.getContext('2d');
    let tQueue = [];
    let tPoses = {};
    let tBg = '#ffffff';
    let tAnimating = false;
    let tTracer = true;

    function tx(x) { return canvas.width / 2 + x; }
    function ty(y) { return canvas.height / 2 - y; }

    function turtleReset() {
        tQueue = [];
        tPoses = {};
        tBg = '#ffffff';
        tTracer = true;
        ctx.fillStyle = tBg;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        sctx.clearRect(0, 0, sprites.width, sprites.height);
    }

    function turtleCommands(cmds) {
        if (!tQueue.length && !tAnimating) showTab('draw');
        tQueue.push(...cmds);
        if (!tAnimating) {
            tAnimating = true;
            requestAnimationFrame(turtleFrame);
        }
    }

    function turtleFrame() {
        // Draw a few commands per frame so students can watch it draw.
        let budget = 1;
        let drawn = 0;
        while (tQueue.length && drawn < 4000) {
            const c = tQueue[0];
            if (c.op === 'line' || c.op === 'move') {
                const speed = tTracer ? c.speed : 0;
                if (speed > 0) {
                    if (budget <= 0) break;
                    budget -= 1 / Math.max(1, speed * 2);
                }
            }
            tQueue.shift();
            drawCommand(c);
            drawn++;
        }
        drawSprites();
        if (tQueue.length) requestAnimationFrame(turtleFrame);
        else tAnimating = false;
    }

    function drawCommand(c) {
        switch (c.op) {
            case 'line':
                ctx.strokeStyle = c.color;
                ctx.lineWidth = c.width;
                ctx.lineCap = 'round';
                ctx.beginPath();
                ctx.moveTo(tx(c.x1), ty(c.y1));
                ctx.lineTo(tx(c.x2), ty(c.y2));
                ctx.stroke();
                break;
            case 'fill':
                ctx.fillStyle = c.color;
                ctx.beginPath();
                c.points.forEach(([x, y], i) => (i ? ctx.lineTo(tx(x), ty(y)) : ctx.moveTo(tx(x), ty(y))));
                ctx.closePath();
                ctx.fill();
                break;
            case 'dot':
                ctx.fillStyle = c.color;
                ctx.beginPath();
                ctx.arc(tx(c.x), ty(c.y), c.size / 2, 0, Math.PI * 2);
                ctx.fill();
                break;
            case 'text':
                ctx.fillStyle = c.color;
                ctx.font = c.font;
                ctx.textAlign = c.align;
                ctx.fillText(c.text, tx(c.x), ty(c.y));
                break;
            case 'stamp':
                drawArrow(ctx, c.x, c.y, c.h, c.color);
                break;
            case 'bg':
                tBg = c.color;
                // Repaint the background behind what is already drawn.
                ctx.save();
                ctx.globalCompositeOperation = 'destination-over';
                ctx.fillStyle = tBg;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.restore();
                break;
            case 'clear':
                ctx.fillStyle = tBg;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                break;
            case 'tracer':
                tTracer = c.on;
                break;
            case 'pose':
                tPoses[c.id] = c;
                break;
        }
    }

    function drawArrow(g, x, y, heading, color) {
        const a = (heading * Math.PI) / 180;
        const pts = [[10, 0], [-6, 6], [-3, 0], [-6, -6]].map(([px, py]) => [
            tx(x + px * Math.cos(a) - py * Math.sin(a)),
            ty(y + px * Math.sin(a) + py * Math.cos(a)),
        ]);
        g.fillStyle = color;
        g.strokeStyle = '#000';
        g.lineWidth = 1;
        g.beginPath();
        pts.forEach(([px, py], i) => (i ? g.lineTo(px, py) : g.moveTo(px, py)));
        g.closePath();
        g.fill();
        g.stroke();
    }

    function drawSprites() {
        sctx.clearRect(0, 0, sprites.width, sprites.height);
        Object.values(tPoses).forEach((p) => p.visible && drawArrow(sctx, p.x, p.y, p.h, p.color));
    }

    function showTab(which) {
        $('tab-vars').classList.toggle('active', which === 'vars');
        $('tab-draw').classList.toggle('active', which === 'draw');
        $('vars-panel').hidden = which !== 'vars';
        $('draw-panel').hidden = which !== 'draw';
    }

    // ------------------------------------------------------------- programs
    let program = CONFIG.program; // {id, title, code, owner, mine} or null
    let viewingNote = '';
    let dirty = false;
    let loadingCode = false;

    function setCode(code, title, prog) {
        loadingCode = true;
        editor.setValue(code);
        editor.clearHistory();
        loadingCode = false;
        program = prog || null;
        el.title.value = title || '';
        markLine('error', null);
        markLine('step', null);
        setDirty(false);
        editor.focus();
    }

    function setDirty(value) {
        dirty = value;
        document.title = (dirty ? '* ' : '') + (el.title.value || 'Untitled') + ' - PythonIDE';
    }

    function confirmDiscard() {
        return !dirty || confirm('Your program has changes that are not saved. Continue anyway?');
    }

    async function api(method, url, body) {
        const response = await fetch(url, {
            method,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name=csrf-token]').content,
            },
            credentials: 'same-origin',
            body: body ? JSON.stringify(body) : undefined,
        });
        if (response.status === 401 || response.status === 419) {
            throw new Error('You have been logged out. Log in again in another tab, then press Save again.');
        }
        if (!response.ok) {
            let message = 'Saving failed (' + response.status + ').';
            try { const j = await response.json(); if (j.message) message = j.message; } catch (e) { /* ignore */ }
            throw new Error(message);
        }
        return response.status === 204 ? null : response.json();
    }

    function guestPrograms() {
        try { return JSON.parse(store.get('guest.programs', '[]')); } catch (e) { return []; }
    }

    async function save() {
        let title = el.title.value.trim();
        if (!title) {
            title = (prompt('Give your program a name:', 'My program') || '').trim();
            if (!title) return;
            el.title.value = title;
        }
        const code = editor.getValue();
        if (!CONFIG.user) {
            // Not logged in: keep it in this browser.
            const list = guestPrograms().filter((p) => p.title !== title);
            list.unshift({ title, code, updated: Date.now() });
            store.set('guest.programs', JSON.stringify(list.slice(0, 50)));
            setDirty(false);
            status('Saved "' + title + '" in this browser. Log in to save it online, or use Download .py.');
            return;
        }
        try {
            if (program && program.id && program.mine) {
                await api('PUT', '/api/programs/' + program.id, { title, code });
            } else {
                const copyOf = program && !program.mine;
                if (copyOf && title === program.title) title = 'Copy of ' + title;
                const created = await api('POST', '/api/programs', { title, code });
                program = { id: created.id, title, mine: true };
                el.title.value = title;
                history.replaceState(null, '', '?program=' + created.id);
            }
            setDirty(false);
            status('Saved "' + title + '".');
        } catch (err) {
            status(err.message);
            alert(err.message);
        }
    }

    async function fillOpenMenu() {
        const menu = $('open-menu');
        menu.textContent = '';
        const heading = (text) => {
            const d = document.createElement('div');
            d.className = 'group';
            d.textContent = text;
            menu.appendChild(d);
        };
        const item = (label, action) => {
            const b = document.createElement('button');
            b.textContent = label;
            b.onclick = () => { closeMenus(); action(); };
            menu.appendChild(b);
        };
        if (CONFIG.user) {
            heading('My programs');
            try {
                const list = await api('GET', '/api/programs');
                if (!list.length) {
                    const d = document.createElement('div');
                    d.className = 'empty';
                    d.textContent = 'No saved programs yet.';
                    menu.appendChild(d);
                }
                list.slice(0, 40).forEach((p) => item(p.title + '  ·  ' + p.updated, () => openProgram(p.id)));
            } catch (err) {
                heading(err.message);
            }
        } else {
            heading('Saved in this browser');
            const list = guestPrograms();
            if (!list.length) {
                const d = document.createElement('div');
                d.className = 'empty';
                d.textContent = 'Nothing saved yet.';
                menu.appendChild(d);
            }
            list.forEach((p) => item(p.title, () => { if (confirmDiscard()) setCode(p.code, p.title, null); }));
        }
        heading('From this computer');
        item('Open a .py file…', () => $('file-input').click());
    }

    async function openProgram(id) {
        if (!confirmDiscard()) return;
        try {
            const p = await api('GET', '/api/programs/' + id);
            setCode(p.code, p.title, { id: p.id, title: p.title, mine: true });
            history.replaceState(null, '', '?program=' + p.id);
            status('Opened "' + p.title + '".');
        } catch (err) {
            status(err.message);
        }
    }

    function newProgram() {
        if (!confirmDiscard()) return;
        if (mode !== 'idle') stopProgram();
        setCode('', '', null);
        history.replaceState(null, '', location.pathname);
        clearOutput();
        clearVars();
        status('New program. Write your code, then press Run (F5).');
    }

    function download() {
        const name = (el.title.value.trim() || 'my_program').replace(/[^\w\- ]+/g, '').replace(/ +/g, '_') + '.py';
        const blob = new Blob([editor.getValue()], { type: 'text/x-python' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = name;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    }

    $('file-input').addEventListener('change', (e) => {
        const file = e.target.files[0];
        e.target.value = '';
        if (!file || !confirmDiscard()) return;
        file.text().then((text) => {
            setCode(text.replace(/\r\n/g, '\n'), file.name.replace(/\.py$/i, ''), null);
            status('Opened ' + file.name + '. Press Save to keep it.');
        });
    });

    // ------------------------------------------------------------- examples
    async function fillExamples() {
        const menu = $('examples-menu');
        const response = await fetch(CONFIG.assetBase + '/examples.json?v=' + CONFIG.version);
        const examples = await response.json();
        examples.sections.forEach((section) => {
            if (section.title) {
                const h = document.createElement('div');
                h.className = 'group big';
                h.textContent = section.title;
                menu.appendChild(h);
            }
            section.groups.forEach((group) => {
                const details = document.createElement('details');
                details.className = 'menu-group';
                const summary = document.createElement('summary');
                summary.textContent = group.title;
                details.appendChild(summary);
                group.items.forEach((ex) => {
                    const b = document.createElement('button');
                    b.textContent = ex.title;
                    b.onclick = () => {
                        closeMenus();
                        if (!confirmDiscard()) return;
                        if (mode !== 'idle') stopProgram();
                        setCode(ex.code, ex.title, null);
                        status('Example loaded: ' + ex.title + '. Press Run (F5) or Step (F6).');
                    };
                    details.appendChild(b);
                });
                menu.appendChild(details);
            });
        });
        return examples;
    }

    function closeMenus() {
        document.querySelectorAll('.menu.open').forEach((m) => m.classList.remove('open'));
    }

    function toggleMenu(id, fill) {
        const menu = $(id);
        const open = !menu.classList.contains('open');
        closeMenus();
        if (open) {
            menu.classList.add('open');
            if (fill) fill();
        }
    }

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.menu-wrap')) closeMenus();
    });

    // ------------------------------------------------------------- appearance
    const THEMES = ['light', 'dark', 'projector'];
    const BASE_SIZE = { light: 15, dark: 15, projector: 22 };

    const THEME_LABELS = { light: 'Light', dark: 'Dark', projector: 'Projector' };

    function applyTheme(name) {
        if (!THEMES.includes(name)) name = 'light';
        themeName = name;
        document.documentElement.dataset.theme = name;
        store.set('theme', name);
        markChoices();
        applySize();
    }

    function setLanguage(lang) {
        language = lang;
        store.set('language', lang);
        markChoices();
    }

    function markChoices() {
        document.querySelectorAll('#view-menu [data-theme]').forEach((b) => b.classList.toggle('on', b.dataset.theme === themeName));
        document.querySelectorAll('#view-menu [data-lang]').forEach((b) => b.classList.toggle('on', b.dataset.lang === language));
    }

    function applySize() {
        const zoom = Number(store.get('zoom', '0'));
        const size = Math.max(10, Math.min(40, BASE_SIZE[themeName] + zoom));
        document.documentElement.style.setProperty('--code-size', size + 'px');
        document.documentElement.style.setProperty('--help-size', Math.round(size * 0.9) + 'px');
        editor.refresh();
    }

    function zoom(delta) {
        store.set('zoom', String(Number(store.get('zoom', '0')) + delta));
        applySize();
    }

    function nextTheme() {
        applyTheme(THEMES[(THEMES.indexOf(themeName) + 1) % THEMES.length]);
        status('Colours: ' + THEME_LABELS[themeName]);
    }

    // Draggable dividers between the editor, output and side panel.
    function dragSash(sash, onMove) {
        sash.addEventListener('mousedown', (e) => {
            e.preventDefault();
            const move = (ev) => onMove(ev);
            const up = () => {
                document.removeEventListener('mousemove', move);
                document.removeEventListener('mouseup', up);
                editor.refresh();
            };
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', up);
        });
    }
    const workspace = $('workspace');
    dragSash($('sash-v'), (e) => {
        const rect = workspace.getBoundingClientRect();
        const width = Math.max(220, Math.min(rect.width - 320, rect.right - e.clientX));
        workspace.style.setProperty('--side-width', width + 'px');
    });
    dragSash($('sash-h'), (e) => {
        const rect = $('left').getBoundingClientRect();
        const pct = Math.max(20, Math.min(85, ((e.clientY - rect.top) / rect.height) * 100));
        $('left').style.setProperty('--editor-height', pct + '%');
    });

    function status(text) {
        el.status.textContent = text;
    }

    // ------------------------------------------------------------- wiring
    el.run.onclick = () => startProgram(false);
    el.stop.onclick = stopProgram;
    el.step.onclick = () => (mode === 'step' ? nextStep() : startProgram(true));
    el.next.onclick = nextStep;
    el.end.onclick = toEnd;
    el.auto.onchange = () => {
        el.speed.hidden = !el.auto.checked; // the speed slider is only needed with Auto
        if (el.auto.checked && mode === 'step' && !waitingInput) scheduleAuto();
        else cancelAuto();
    };
    el.enter.onclick = sendInput;
    el.input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); sendInput(); } });
    $('btn-new').onclick = newProgram;
    $('btn-save').onclick = save;
    $('btn-open').onclick = () => toggleMenu('open-menu', fillOpenMenu);
    $('btn-examples').onclick = () => toggleMenu('examples-menu');
    $('btn-download').onclick = download;
    $('btn-upload').onclick = () => $('file-input').click();
    $('btn-clear').onclick = clearOutput;
    $('btn-bigger').onclick = () => zoom(1);
    $('btn-smaller').onclick = () => zoom(-1);
    $('tab-vars').onclick = () => showTab('vars');
    $('tab-draw').onclick = () => showTab('draw');
    $('btn-view').onclick = () => toggleMenu('view-menu');
    document.querySelectorAll('#view-menu [data-theme]').forEach((b) => { b.onclick = () => applyTheme(b.dataset.theme); });
    document.querySelectorAll('#view-menu [data-lang]').forEach((b) => { b.onclick = () => setLanguage(b.dataset.lang); });
    el.speed.value = store.get('speed', '700');
    el.speed.onchange = () => store.set('speed', el.speed.value);
    el.title.addEventListener('input', () => setDirty(true));

    editor.on('change', () => {
        if (loadingCode) return;
        setDirty(true);
        if (mode === 'idle') markLine('error', null);
        if (!CONFIG.program) store.set('draft', JSON.stringify({ code: editor.getValue(), title: el.title.value }));
    });

    document.addEventListener('keydown', (e) => {
        const key = e.key;
        if (key === 'F5' && e.shiftKey) { e.preventDefault(); stopProgram(); }
        else if (key === 'F5') { e.preventDefault(); startProgram(false); }
        else if (key === 'F6') { e.preventDefault(); el.step.onclick(); }
        else if (key === 'F7') { e.preventDefault(); nextStep(); }
        else if (key === 'F8') { e.preventDefault(); toEnd(); }
        else if (key === 'F9') { e.preventDefault(); nextTheme(); }
        else if ((e.ctrlKey || e.metaKey) && key.toLowerCase() === 's') { e.preventDefault(); save(); }
        else if (key === 'Escape') closeMenus();
    });

    window.addEventListener('beforeunload', (e) => {
        if (dirty && (CONFIG.user || CONFIG.program)) { e.preventDefault(); e.returnValue = ''; }
    });

    // ------------------------------------------------------------- start
    applyTheme(store.get('theme', 'light'));
    setMode('idle');
    fillExamples().then((examples) => {
        if (program) return;
        const params = new URLSearchParams(location.search);
        let draft = null;
        try { draft = JSON.parse(store.get('draft', 'null')); } catch (e) { /* ignore */ }
        if (params.has('new')) setCode('', '', null);
        else if (draft && draft.code) setCode(draft.code, draft.title, null);
        else setCode(examples.welcome, '', null);
    }).catch(() => status('Could not load the examples.'));

    if (program) {
        const title = program.mine ? program.title : program.owner + ': ' + program.title;
        setCode(program.code, program.mine ? program.title : program.title, program);
        if (!program.mine) {
            viewingNote = 'You are viewing ' + program.owner + '\'s program. Saving makes a copy in your programs.';
            status(viewingNote);
        }
        document.title = title + ' - PythonIDE';
    }

    if (canRun) {
        startWorker();
    } else {
        el.loading.hidden = true;
        el.run.disabled = el.step.disabled = true;
        appendText('This browser cannot run Python here.\nPlease use a recent Google Chrome, Microsoft Edge or Firefox.\n', 'stderr');
        status('This browser cannot run Python. Please use a recent Chrome, Edge or Firefox.');
    }
})();
