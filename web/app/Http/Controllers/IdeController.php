<?php

namespace App\Http\Controllers;

use App\Models\Program;
use Illuminate\Http\Request;

class IdeController extends Controller
{
    public function show(Request $request)
    {
        $user = $request->user();
        $program = null;
        if ($user && $request->filled('program')) {
            $found = Program::with('user')->find($request->integer('program'));
            if (! $found || ! $user->canSeeWorkOf($found->user)) {
                abort(404);
            }
            $program = [
                'id' => $found->id,
                'title' => $found->title,
                'code' => $found->code,
                'owner' => $found->user->name,
                // A teacher looking at a student's work saves a copy, never over it.
                'mine' => $found->user_id === $user->id,
            ];
        }

        return view('ide', [
            'config' => [
                'user' => $user ? ['name' => $user->name, 'teacher' => $user->isTeacher()] : null,
                'program' => $program,
                'workerUrl' => url('/ide/worker.js').'?v='.$this->version(),
                'assetBase' => url('/ide-assets'),
                'pyodideUrl' => url('/pyodide').'/',
                'version' => $this->version(),
            ],
        ]);
    }

    /**
     * The worker script is served by Laravel (not as a plain file) so it
     * always gets the cross-origin isolation headers, even on hosting where
     * .htaccess cannot set headers.
     */
    public function worker()
    {
        return response()->file(resource_path('ide/worker.js'), [
            'Content-Type' => 'text/javascript; charset=utf-8',
            'Cache-Control' => 'public, max-age=3600',
        ]);
    }

    private function version(): string
    {
        return substr(md5((string) @filemtime(resource_path('ide/worker.js'))
            .@filemtime(public_path('ide-assets/ide.js')).@filemtime(public_path('ide-assets/py/runner.py'))), 0, 8);
    }
}
