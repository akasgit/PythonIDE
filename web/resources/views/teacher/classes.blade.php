@extends('layouts.app')
@section('title', 'Classes - PythonIDE')
@section('content')
<h1>Classes</h1>
@if ($classrooms->isEmpty())
    <p class="muted">No classes yet. Create one below, then add your students to it.</p>
@else
<table class="table">
    <thead><tr><th>Class</th><th>Students</th>@if (auth()->user()->is_admin)<th>Teacher</th>@endif</tr></thead>
    <tbody>
    @foreach ($classrooms as $c)
        <tr>
            <td><a href="{{ route('classes.show', $c) }}">{{ $c->name }}</a></td>
            <td>{{ $c->students_count }}</td>
            @if (auth()->user()->is_admin)<td class="muted">{{ $c->teacher->name }}</td>@endif
        </tr>
    @endforeach
    </tbody>
</table>
@endif
<div class="card">
    <h2>New class</h2>
    <form method="post" action="{{ url('/classes') }}" class="form inline">
        @csrf
        <input name="name" placeholder="e.g. Class 10 A" required maxlength="60">
        <button class="btn primary">Create class</button>
    </form>
</div>
@endsection
