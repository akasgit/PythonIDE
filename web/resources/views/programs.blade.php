@extends('layouts.app')
@section('title', 'My programs - PythonIDE')
@section('content')
<div class="row-head">
    <h1>My programs</h1>
    <a class="btn primary" href="{{ route('ide') }}?new=1">New program</a>
</div>
@if ($programs->isEmpty())
    <p class="muted">You have not saved any programs yet. Write one in the editor and press <b>Save</b>.</p>
@else
<table class="table">
    <thead><tr><th>Name</th><th>Last saved</th><th></th></tr></thead>
    <tbody>
    @foreach ($programs as $p)
        <tr>
            <td data-label="Name"><a href="{{ route('ide') }}?program={{ $p->id }}">{{ $p->title }}</a></td>
            <td class="muted" data-label="Last saved">{{ $p->updated_at->diffForHumans() }}</td>
            <td class="actions">
                <a class="btn small" href="{{ route('ide') }}?program={{ $p->id }}">Open</a>
                <form method="post" action="{{ route('programs.destroy', $p) }}" onsubmit="return confirm('Delete {{ addslashes($p->title) }}?')">
                    @csrf @method('delete')<button class="btn small danger">Delete</button>
                </form>
            </td>
        </tr>
    @endforeach
    </tbody>
</table>
@endif
@endsection
