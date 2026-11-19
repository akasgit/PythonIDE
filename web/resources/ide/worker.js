/*
 * PythonIDE online: runs Python (Pyodide) in a Web Worker, so a student's
 * endless loop never freezes the page.
 *
 * Waiting for input() and for "Next step" uses a SharedArrayBuffer:
 *   sync[0]  1 when the page has sent a command, 0 after the worker read it
 *   sync[1]  the command: 1 next step, 2 run to end, 3 stop, 4 input line
 *   sync[2]  length in bytes of the input text in `data`
 * Stop also sets the Pyodide interrupt buffer, which raises
 * KeyboardInterrupt in running Python code.
 */
/* eslint-env worker */
'use strict';

let pyodide = null;
let sync = null;
let data = null;
let runner = null;
let interrupt = null;
const decoder = new TextDecoder();

function post(json) {
    self.postMessage(json);
}

function readCommand() {
    const cmd = Atomics.load(sync, 1);
    const len = Atomics.load(sync, 2);
    // decode() refuses views on shared memory, so copy the bytes first.
    const text = len ? decoder.decode(data.slice(0, len)) : '';
    Atomics.store(sync, 0, 0);
    return { cmd, text };
}

const ide = {
    post,
    wait() {
        Atomics.wait(sync, 0, 0);
        return JSON.stringify(readCommand());
    },
    sleep(seconds) {
        const result = Atomics.wait(sync, 0, 0, Math.max(0, seconds * 1000));
        if (result !== 'timed-out' && Atomics.load(sync, 0) === 1) {
            return readCommand().cmd;
        }
        return 0;
    },
};

async function init(msg) {
    sync = new Int32Array(msg.sync);
    data = new Uint8Array(msg.data);
    post(JSON.stringify({ t: 'status', text: 'Loading Python…' }));
    importScripts(msg.pyodideUrl + 'pyodide.js');
    pyodide = await self.loadPyodide({ indexURL: msg.pyodideUrl });
    interrupt = new Uint8Array(msg.interrupt);
    pyodide.setInterruptBuffer(interrupt);
    pyodide.registerJsModule('ide', ide);
    for (const name of ['_shared.py', 'errors.py', 'runner.py', 'turtle.py']) {
        // Fetched without ".py" in the address (see routes/web.php).
        const response = await fetch(msg.pythonUrl + '/' + name.replace(/\.py$/, '') + '?v=' + msg.version);
        if (!response.ok) throw new Error('Could not load ' + name + ' (HTTP ' + response.status + ')');
        pyodide.FS.writeFile('/home/pyodide/' + name, await response.text());
    }
    pyodide.runPython('import sys; sys.path.insert(0, "/home/pyodide")');
    runner = pyodide.pyimport('runner');
    post(JSON.stringify({ t: 'ready', python: pyodide.runPython('import sys; sys.version.split()[0]') }));
}

self.onmessage = async (event) => {
    const msg = event.data;
    if (msg.type === 'init') {
        try {
            await init(msg);
        } catch (err) {
            post(JSON.stringify({ t: 'fatal', text: String(err && err.message || err) }));
        }
    } else if (msg.type === 'run') {
        // Forget a Stop that arrived after the previous program had ended.
        Atomics.store(sync, 0, 0);
        interrupt[0] = 0;
        try {
            runner.run(msg.code, msg.step);
        } catch (err) {
            // A problem in PythonIDE itself, not in the student's program.
            post(JSON.stringify({ t: 'internal', text: String(err && err.message || err) }));
            post(JSON.stringify({ t: 'done', seconds: 0, steps: 0 }));
        }
    }
};
