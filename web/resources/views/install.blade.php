@extends('layouts.app')
@section('title', 'Install PythonIDE')
@section('content')
<div class="card">
    <h1>Set up PythonIDE</h1>
    @unless ($secure)
        <div class="flash bad"><b>This site is not using HTTPS.</b> Python in the browser only works on
            <code>https://</code> addresses. In cPanel, turn on <b>SSL/TLS Status → AutoSSL</b> (free) for this
            domain, then open <code>https://{{ request()->getHost() }}/install</code>.</div>
    @endunless
    <ul class="checks">
        @foreach ($checks as $label => $ok)
            <li class="{{ $ok ? 'ok' : 'bad' }}">{{ $ok ? '✓' : '✗' }} {{ $label }}</li>
        @endforeach
    </ul>

    @if ($step === 'database')
        <h2>Step 1 of 2: Database</h2>
        <p>Create a MySQL database and user in <b>cPanel → MySQL Databases</b> (give the user
           <i>All privileges</i> on the database), then enter them here.</p>
        @if ($dbError && $dbError !== 'No database is set yet.')
            <p class="muted small">Current problem: {{ $dbError }}</p>
        @endif
        <form method="post" action="{{ url('/install/database') }}" class="form">
            @csrf
            <label>Database host <input name="host" value="{{ old('host', $db['host'] ?: 'localhost') }}" required></label>
            <label>Port <input name="port" value="{{ old('port', $db['port'] ?: 3306) }}" required></label>
            <label>Database name <input name="database" value="{{ old('database', $db['database']) }}" placeholder="e.g. cpaneluser_pythonide" required></label>
            <label>Database username <input name="username" value="{{ old('username', $db['username']) }}" required></label>
            <label>Database password <input type="password" name="password"></label>
            <button class="btn primary">Save and continue</button>
        </form>
    @else
        <h2>Step 2 of 2: Your teacher account</h2>
        <p>The database is connected. This creates the tables and your account. You will be the
           <b>admin</b>: you can add other teachers later.</p>
        <form method="post" action="{{ url('/install/admin') }}" class="form">
            @csrf
            <label>Your name <input name="name" value="{{ old('name') }}" required></label>
            <label>Username <input name="username" value="{{ old('username') }}" autocapitalize="none" required>
                <span class="muted small">Letters, numbers, - and _ only.</span></label>
            <label>Password <input type="password" name="password" required minlength="6"></label>
            <label>Password again <input type="password" name="password_confirmation" required minlength="6"></label>
            <label>Database password (to prove you own this site) <input type="password" name="db_password"></label>
            <button class="btn primary">Finish setup</button>
        </form>
    @endif
</div>
@endsection
