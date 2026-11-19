@if (session('new_logins'))
<section class="slips">
    <div class="slips-head">
        <h2>Login slips</h2>
        <button type="button" class="btn" onclick="window.print()">Print slips</button>
    </div>
    <p class="muted no-print">These passwords are shown only once. Print them or write them down now.</p>
    <div class="slip-grid">
        @foreach (session('new_logins') as $login)
            <div class="slip">
                <div class="slip-title">PythonIDE: {{ request()->getHost() }}</div>
                <div class="slip-name">{{ $login['name'] }}</div>
                <div>Username: <b>{{ $login['username'] }}</b></div>
                <div>Password: <b>{{ $login['password'] }}</b></div>
            </div>
        @endforeach
    </div>
</section>
@endif
