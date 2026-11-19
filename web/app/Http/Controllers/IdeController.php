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
                'pythonUrl' => url('/ide/python'),
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

    /**
     * The Python files that run inside the browser. They are sent by Laravel
     * because many shared hosts block or try to execute .py files.
     */
    public function python(string $name)
    {
        abort_unless(in_array($name.'.py', self::PYTHON_FILES, true), 404);

        return response()->file(resource_path('ide/py/'.$name.'.py'), [
            'Content-Type' => 'text/plain; charset=utf-8',
            'Cache-Control' => 'public, max-age=3600',
        ]);
    }

    public const PYTHON_FILES = ['_shared.py', 'errors.py', 'runner.py', 'turtle.py'];

    private function version(): string
    {
        return substr(md5((string) @filemtime(resource_path('ide/worker.js'))
            .@filemtime(public_path('ide-assets/ide.js')).@filemtime(resource_path('ide/py/runner.py')).@filemtime(resource_path('ide/py/errors.py'))), 0, 8);
    }
}
