@extends('layouts.app')
@section('title', 'Log in - PythonIDE')
@section('content')
<div class="card narrow">
    <h1>Log in</h1>
    <form method="post" action="{{ url('/login') }}" class="form">
        @csrf
        <label>Username <input name="username" value="{{ old('username') }}" autocomplete="username" autocapitalize="none" required autofocus></label>
        <label>Password <input type="password" name="password" autocomplete="current-password" required></label>
        <label class="check"><input type="checkbox" name="remember" value="1"> Keep me logged in on this computer</label>
        <button class="btn primary">Log in</button>
    </form>
    <p class="muted">Your teacher gives you your username and password.</p>
    <p><a href="{{ route('ide') }}">Use the editor without logging in →</a><br>
       <span class="muted small">Your programs are then kept only in this browser.</span></p>
</div>
@endsection
