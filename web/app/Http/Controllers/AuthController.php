<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class AuthController extends Controller
{
    public function showLogin()
    {
        return view('login');
    }

    public function login(Request $request)
    {
        $data = $request->validate([
            'username' => 'required|string',
            'password' => 'required|string',
        ]);
        if (! Auth::attempt(['username' => strtolower(trim($data['username'])), 'password' => $data['password']],
            $request->boolean('remember'))) {
            return back()->withInput($request->only('username'))
                ->withErrors(['username' => 'Wrong username or password.']);
        }
        $request->session()->regenerate();

        return redirect()->intended('/ide');
    }

    public function logout(Request $request)
    {
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect('/login');
    }
}
