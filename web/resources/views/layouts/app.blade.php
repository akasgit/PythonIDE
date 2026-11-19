<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'PythonIDE')</title>
    <link rel="icon" href="{{ asset('favicon.ico') }}">
    <script>
        // Apply the saved colour theme before the page is drawn.
        try { document.documentElement.dataset.theme = localStorage.getItem('pythonide.theme') || 'light'; } catch (e) {}
    </script>
    <link rel="stylesheet" href="{{ asset('css/app.css') }}?v={{ @filemtime(public_path('css/app.css')) }}">
    @stack('head')
</head>
<body class="@yield('body_class')">
<header class="site-header">
    <a class="brand" href="{{ url('/') }}"><span class="logo">Py</span> PythonIDE</a>
    <nav>
        <a href="{{ route('ide') }}" @class(['active' => request()->routeIs('ide')])>Editor</a>
        @auth
            <a href="{{ route('programs') }}" @class(['active' => request()->routeIs('programs')])>My programs</a>
            @if (auth()->user()->isTeacher())
                <a href="{{ route('classes.index') }}" @class(['active' => request()->is('classes*', 'students*')])>Classes</a>
                @if (auth()->user()->is_admin)
                    <a href="{{ route('teachers') }}" @class(['active' => request()->routeIs('teachers')])>Teachers</a>
                @endif
            @endif
        @endauth
    </nav>
    <div class="who">
        @auth
            <a href="{{ route('account') }}" title="Account" class="me">{{ auth()->user()->name }}</a>
            <form method="post" action="{{ route('logout') }}">@csrf<button class="link">Log out</button></form>
        @else
            <a href="{{ route('login') }}">Log in</a>
        @endauth
    </div>
</header>
@hasSection('full')
    @yield('full')
@else
    <main class="page">
        @if (session('status'))<div class="flash ok">{{ session('status') }}</div>@endif
        @if ($errors->any())
            <div class="flash bad">@foreach ($errors->all() as $e)<div>{{ $e }}</div>@endforeach</div>
        @endif
        @include('partials.new-logins')
        @yield('content')
    </main>
@endif
@stack('scripts')
</body>
</html>
