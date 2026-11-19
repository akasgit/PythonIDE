@extends('layouts.app')
@section('title', 'PythonIDE')
@section('body_class', 'ide-page')
@push('head')
    <link rel="stylesheet" href="{{ asset('lib/codemirror/codemirror.css') }}">
@endpush
@section('full')
<div class="ide" id="ide">
    <div class="toolbar">
        <button class="tb" id="btn-new" title="Start a new program">New</button>
        <div class="menu-wrap">
            <button class="tb" id="btn-open" title="Open a saved program">Open ▾</button>
            <div class="menu" id="open-menu"></div>
        </div>
        <button class="tb" id="btn-save" title="Save (Ctrl+S)">Save</button>
        <input class="title-box" id="title" maxlength="100" placeholder="Program name" aria-label="Program name">
        <div class="menu-wrap">
            <button class="tb" id="btn-examples">Examples ▾</button>
            <div class="menu" id="examples-menu"></div>
        </div>
        <span class="gap"></span>
        <button class="tb run" id="btn-run" title="Run (F5)">Run (F5)</button>
        <button class="tb stop" id="btn-stop" title="Stop (Shift+F5)" disabled>Stop</button>
        <span class="gap"></span>
        <button class="tb step" id="btn-step" title="Run one line at a time (F6)">Step (F6)</button>
        <button class="tb step" id="btn-next" title="Next step (F7)" disabled>Next (F7)</button>
        <button class="tb step" id="btn-end" title="Run to the end (F8)" disabled>To end</button>
        <label class="tb-label" title="Go to the next step by itself"><input type="checkbox" id="auto"> Auto</label>
        <input type="range" id="speed" min="150" max="1500" step="50" value="700" title="Auto speed: slow ← → fast" style="direction: rtl" hidden>
        <span class="spacer"></span>
        <div class="menu-wrap">
            <button class="tb" id="btn-view" title="Colours, help language and text size">View ▾</button>
            <div class="menu menu-right" id="view-menu">
                <div class="group">Colours (F9)</div>
                <button data-theme="light">Light</button>
                <button data-theme="dark">Dark</button>
                <button data-theme="projector">Projector (big, high contrast)</button>
                <div class="group">Error help</div>
                <button data-lang="both">English + नेपाली</button>
                <button data-lang="en">English only</button>
                <button data-lang="ne">नेपाली मात्र</button>
                <div class="group">Text size</div>
                <div class="menu-row"><button id="btn-smaller">A−  Smaller</button><button id="btn-bigger">A+  Bigger</button></div>
            </div>
        </div>
    </div>
    <div class="workspace" id="workspace">
        <div class="left" id="left">
            <div class="editor-wrap"><textarea id="code"></textarea></div>
            <div class="sash-h" id="sash-h" title="Drag to resize"></div>
            <div class="panel">
                <div class="panel-head">Output<span class="spacer"></span>
                    <button id="btn-download" title="Download this program as a .py file">Download .py</button>
                    <button id="btn-upload" title="Open a .py file from this computer">Open file…</button>
                    <input type="file" id="file-input" accept=".py,.txt" hidden>
                    <button id="btn-clear">Clear</button></div>
                <pre class="output" id="output" tabindex="0"></pre>
                <div class="input-row" id="input-row">
                    <label for="input">Input:</label>
                    <input id="input" disabled autocomplete="off">
                    <button id="btn-enter" disabled>Enter</button>
                </div>
            </div>
        </div>
        <div class="sash-v" id="sash-v" title="Drag to resize"></div>
        <div class="panel side">
            <div class="panel-head">
                <button id="tab-vars" class="active">Variables</button>
                <button id="tab-draw">Drawing</button>
            </div>
            <div id="vars-panel" class="panel" style="flex:1">
                <div class="vars-hint" id="vars-hint">Run or Step your program to see its variables here.</div>
                <div class="vars-wrap">
                    <table class="vars"><thead><tr><th>Name</th><th>Value</th><th>Type</th></tr></thead>
                        <tbody id="vars"></tbody></table>
                </div>
            </div>
            <div id="draw-panel" class="drawing-wrap" hidden>
                <div style="position:relative">
                    <canvas id="canvas" width="600" height="600"></canvas>
                    <canvas id="sprites" width="600" height="600" style="position:absolute;left:0;top:0;background:transparent;border-color:transparent"></canvas>
                </div>
            </div>
        </div>
    </div>
    <div class="statusbar" id="status">Starting…</div>
    <div class="loading" id="loading">
        <div class="box"><b>Getting Python ready…</b><br>
            <span class="muted small" id="loading-text">The first time can take a minute on a slow connection. After that it is quick.</span></div>
    </div>
</div>
@endsection
@push('scripts')
    <script>window.IDE_CONFIG = @json($config);</script>
    <script src="{{ asset('lib/codemirror/codemirror.js') }}"></script>
    <script src="{{ asset('lib/codemirror/mode/python/python.js') }}"></script>
    <script src="{{ asset('lib/codemirror/addon/matchbrackets.js') }}"></script>
    <script src="{{ asset('lib/codemirror/addon/active-line.js') }}"></script>
    <script src="{{ asset('lib/codemirror/addon/comment.js') }}"></script>
    <script src="{{ asset('ide-assets/ide.js') }}?v={{ $config['version'] }}"></script>
@endpush
