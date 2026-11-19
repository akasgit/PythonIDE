@extends('layouts.app')
@section('title', $classroom->name.' - PythonIDE')
@section('content')
<p class="no-print"><a href="{{ route('classes.index') }}">← All classes</a></p>
<div class="row-head no-print">
    <h1>{{ $classroom->name }}</h1>
    <form method="post" action="{{ url('/classes/'.$classroom->id) }}" class="form inline">
        @csrf @method('put')
        <input name="name" value="{{ $classroom->name }}" maxlength="60" required>
        <button class="btn small">Rename</button>
    </form>
</div>

<div class="no-print">
@if ($students->isEmpty())
    <p class="muted">No students yet. Add them below.</p>
@else
<table class="table">
    <thead><tr><th>Student</th><th>Username</th><th>Programs</th><th>Last saved</th><th></th></tr></thead>
    <tbody>
    @foreach ($students as $s)
        <tr>
            <td><a href="{{ route('students.show', $s) }}">{{ $s->name }}</a></td>
            <td><code>{{ $s->username }}</code></td>
            <td>{{ $s->programs_count }}</td>
            <td class="muted">{{ $s->programs_max_updated_at ? \Illuminate\Support\Carbon::parse($s->programs_max_updated_at)->diffForHumans() : '-' }}</td>
            <td class="actions">
                <a class="btn small" href="{{ route('students.show', $s) }}">View work</a>
                <form method="post" action="{{ url('/students/'.$s->id.'/password') }}" onsubmit="return confirm('Give {{ addslashes($s->name) }} a new password?')">
                    @csrf<button class="btn small">New password</button>
                </form>
                <form method="post" action="{{ url('/students/'.$s->id) }}" onsubmit="return confirm('Delete {{ addslashes($s->name) }} and all their programs?')">
                    @csrf @method('delete')<button class="btn small danger">Delete</button>
                </form>
            </td>
        </tr>
    @endforeach
    </tbody>
</table>
@endif

<div class="card">
    <h2>Add students</h2>
    <p class="muted">Type one name per line. Each student gets a username and an easy password,
        shown on printable login slips.</p>
    <form method="post" action="{{ url('/classes/'.$classroom->id.'/students') }}" class="form">
        @csrf
        <textarea name="names" rows="8" placeholder="Sita Sharma&#10;Ram Thapa&#10;Gita Karki" required></textarea>
        <button class="btn primary">Add students</button>
    </form>
</div>

@if ($students->isEmpty())
<form method="post" action="{{ url('/classes/'.$classroom->id) }}" onsubmit="return confirm('Delete this class?')">
    @csrf @method('delete')<button class="btn small danger">Delete this class</button>
</form>
@endif
</div>
@endsection
