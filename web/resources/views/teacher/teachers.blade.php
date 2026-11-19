@extends('layouts.app')
@section('title', 'Teachers - PythonIDE')
@section('content')
<h1>Teachers</h1>
<table class="table">
    <thead><tr><th>Name</th><th>Username</th><th>Classes</th><th></th></tr></thead>
    <tbody>
    @foreach ($teachers as $t)
        <tr>
            <td data-label="Name" class="main">{{ $t->name }} @if ($t->is_admin)<span class="tag">admin</span>@endif</td>
            <td data-label="Username"><code>{{ $t->username }}</code></td>
            <td data-label="Classes">{{ $t->classrooms_count }}</td>
            <td class="actions">
                @if ($t->id !== auth()->id())
                <form method="post" action="{{ url('/teachers/'.$t->id.'/password') }}" onsubmit="return confirm('Give {{ addslashes($t->name) }} a new password?')">
                    @csrf<button class="btn small">New password</button>
                </form>
                <form method="post" action="{{ url('/teachers/'.$t->id) }}" onsubmit="return confirm('Delete {{ addslashes($t->name) }}?')">
                    @csrf @method('delete')<button class="btn small danger">Delete</button>
                </form>
                @endif
            </td>
        </tr>
    @endforeach
    </tbody>
</table>
<div class="card">
    <h2>Add a teacher</h2>
    <form method="post" action="{{ url('/teachers') }}" class="form">
        @csrf
        <label>Name <input name="name" value="{{ old('name') }}" required></label>
        <label>Username <input name="username" value="{{ old('username') }}" autocapitalize="none" required></label>
        <label class="check"><input type="checkbox" name="is_admin" value="1"> Admin (can add and remove teachers)</label>
        <button class="btn primary">Add teacher</button>
    </form>
</div>
@endsection
