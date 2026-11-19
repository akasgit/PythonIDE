<?php

namespace App\Http\Controllers\Teacher;

use App\Http\Controllers\Controller;
use App\Models\Classroom;
use App\Models\User;
use App\Support\Credentials;
use Illuminate\Http\Request;

class ClassroomController extends Controller
{
    public function index(Request $request)
    {
        $user = $request->user();
        $query = Classroom::withCount('students')->with('teacher')->orderBy('name');
        if (! $user->is_admin) {
            $query->where('teacher_id', $user->id);
        }

        return view('teacher.classes', ['classrooms' => $query->get()]);
    }

    public function store(Request $request)
    {
        $data = $request->validate(['name' => 'required|string|max:60']);
        $classroom = $request->user()->classrooms()->create($data);

        return redirect()->route('classes.show', $classroom)
            ->with('status', 'Class created. Now add your students.');
    }

    public function show(Request $request, Classroom $classroom)
    {
        $this->authorizeClass($request, $classroom);
        $students = $classroom->students()
            ->withCount('programs')
            ->withMax('programs', 'updated_at')
            ->get();

        return view('teacher.class', ['classroom' => $classroom, 'students' => $students]);
    }

    public function update(Request $request, Classroom $classroom)
    {
        $this->authorizeClass($request, $classroom);
        $classroom->update($request->validate(['name' => 'required|string|max:60']));

        return back()->with('status', 'Class renamed.');
    }

    public function destroy(Request $request, Classroom $classroom)
    {
        $this->authorizeClass($request, $classroom);
        if ($classroom->students()->exists()) {
            return back()->withErrors(['class' => 'Remove the students from this class first.']);
        }
        $classroom->delete();

        return redirect()->route('classes.index')->with('status', 'Class deleted.');
    }

    /** Add many students at once: one name per line. */
    public function addStudents(Request $request, Classroom $classroom)
    {
        $this->authorizeClass($request, $classroom);
        $data = $request->validate(['names' => 'required|string|max:20000']);
        $names = array_values(array_filter(array_map(
            fn ($line) => trim(preg_replace('/\s+/', ' ', $line)),
            preg_split('/\r\n|\r|\n/', $data['names'])
        )));
        if (count($names) > 200) {
            return back()->withErrors(['names' => 'Add at most 200 students at a time.']);
        }

        $created = [];
        foreach ($names as $name) {
            $name = mb_substr($name, 0, 100);
            $password = Credentials::password();
            $student = User::create([
                'name' => $name,
                'username' => Credentials::username($name),
                'password' => $password,
                'role' => 'student',
                'classroom_id' => $classroom->id,
            ]);
            $created[] = ['name' => $student->name, 'username' => $student->username, 'password' => $password];
        }

        return redirect()->route('classes.show', $classroom)
            ->with('new_logins', $created)
            ->with('status', count($created).' students added. Print their login slips now: '
                .'the passwords are shown only once.');
    }

    public function resetPassword(Request $request, User $student)
    {
        $classroom = $this->studentClass($request, $student);
        $password = Credentials::password();
        $student->update(['password' => $password]);

        return redirect()->route('classes.show', $classroom)
            ->with('new_logins', [['name' => $student->name, 'username' => $student->username, 'password' => $password]])
            ->with('status', 'New password for '.$student->name.'.');
    }

    public function removeStudent(Request $request, User $student)
    {
        $classroom = $this->studentClass($request, $student);
        $student->delete();

        return redirect()->route('classes.show', $classroom)
            ->with('status', $student->name.' and their programs were deleted.');
    }

    public function studentWork(Request $request, User $student)
    {
        $classroom = $this->studentClass($request, $student);

        return view('teacher.student', [
            'classroom' => $classroom,
            'student' => $student,
            'programs' => $student->programs()->latest('updated_at')->get(['id', 'title', 'updated_at']),
        ]);
    }

    private function authorizeClass(Request $request, Classroom $classroom): void
    {
        $user = $request->user();
        abort_unless($user->is_admin || $classroom->teacher_id === $user->id, 403);
    }

    private function studentClass(Request $request, User $student): Classroom
    {
        abort_unless($student->role === 'student' && $student->classroom, 404);
        $this->authorizeClass($request, $student->classroom);

        return $student->classroom;
    }
}
