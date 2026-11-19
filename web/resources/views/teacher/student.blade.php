@extends('layouts.app')
@section('title', $student->name.' - PythonIDE')
@section('content')
<p><a href="{{ route('classes.show', $classroom) }}">← {{ $classroom->name }}</a></p>
<h1>{{ $student->name }}</h1>
<p class="muted">Username <code>{{ $student->username }}</code> · {{ $programs->count() }} programs</p>
@if ($programs->isEmpty())
    <p class="muted">{{ $student->name }} has not saved any programs yet.</p>
@else
<table class="table">
    <thead><tr><th>Program</th><th>Last saved</th><th></th></tr></thead>
    <tbody>
    @foreach ($programs as $p)
        <tr>
            <td data-label="Program" class="main">{{ $p->title }}</td>
            <td class="muted" data-label="Last saved">{{ $p->updated_at->diffForHumans() }} <span class="small">({{ $p->updated_at->format('Y-m-d H:i') }})</span></td>
            <td class="actions"><a class="btn small" href="{{ route('ide') }}?program={{ $p->id }}">Open and run</a></td>
        </tr>
    @endforeach
    </tbody>
</table>
<p class="muted small">Opening a student's program never changes it. If you press Save, a copy is saved in your own programs.</p>
@endif
@endsection
