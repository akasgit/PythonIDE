@extends('layouts.app')
@section('title', 'Account - PythonIDE')
@section('content')
<div class="card narrow">
    <h1>{{ auth()->user()->name }}</h1>
    <p class="muted">Username: <b>{{ auth()->user()->username }}</b>
        @if (auth()->user()->classroom) · Class: {{ auth()->user()->classroom->name }} @endif</p>
    <h2>Change password</h2>
    <form method="post" action="{{ url('/account/password') }}" class="form">
        @csrf
        <label>Current password <input type="password" name="current_password" required autocomplete="current-password"></label>
        <label>New password <input type="password" name="password" required minlength="6" autocomplete="new-password"></label>
        <label>New password again <input type="password" name="password_confirmation" required minlength="6" autocomplete="new-password"></label>
        <button class="btn primary">Change password</button>
    </form>
</div>
@endsection
