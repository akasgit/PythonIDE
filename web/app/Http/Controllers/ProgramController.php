<?php

namespace App\Http\Controllers;

use App\Models\Program;
use Illuminate\Http\Request;

class ProgramController extends Controller
{
    public function index(Request $request)
    {
        return view('programs', [
            'programs' => $request->user()->programs()->latest('updated_at')->get(['id', 'title', 'updated_at']),
        ]);
    }

    public function list(Request $request)
    {
        return $request->user()->programs()->latest('updated_at')
            ->get(['id', 'title', 'updated_at'])
            ->map(fn ($p) => ['id' => $p->id, 'title' => $p->title, 'updated' => $p->updated_at->diffForHumans()]);
    }

    public function get(Request $request, Program $program)
    {
        $this->own($request, $program);

        return ['id' => $program->id, 'title' => $program->title, 'code' => $program->code];
    }

    public function store(Request $request)
    {
        $program = $request->user()->programs()->create($this->validated($request));

        return response()->json(['id' => $program->id, 'title' => $program->title], 201);
    }

    public function update(Request $request, Program $program)
    {
        $this->own($request, $program);
        $program->update($this->validated($request));

        return ['id' => $program->id, 'title' => $program->title];
    }

    public function destroy(Request $request, Program $program)
    {
        $this->own($request, $program);
        $program->delete();

        return $request->expectsJson() ? response()->noContent() : back()->with('status', 'Program deleted.');
    }

    private function own(Request $request, Program $program): void
    {
        abort_unless($program->user_id === $request->user()->id, 404);
    }

    private function validated(Request $request): array
    {
        return $request->validate([
            'title' => 'required|string|max:100',
            'code' => 'present|nullable|string|max:200000',
        ]) + ['code' => ''];
    }
}
