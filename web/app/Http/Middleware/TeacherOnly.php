<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class TeacherOnly
{
    public function handle(Request $request, Closure $next, string $level = 'teacher')
    {
        $user = $request->user();
        if (! $user || ! $user->isTeacher() || ($level === 'admin' && ! $user->is_admin)) {
            abort(403);
        }

        return $next($request);
    }
}
