<?php

namespace App\Http\Controllers\Teacher;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Support\Credentials;
use Illuminate\Http\Request;

/** Admin only: add and remove teacher accounts. */
class TeacherController extends Controller
{
    public function index()
    {
        return view('teacher.teachers', [
            'teachers' => User::where('role', 'teacher')->withCount('classrooms')->orderBy('name')->get(),
        ]);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:100',
            'username' => 'required|alpha_dash|max:50|unique:users,username',
            'is_admin' => 'nullable|boolean',
        ]);
        $password = Credentials::password();
        $teacher = User::create([
            'name' => $data['name'],
            'username' => strtolower($data['username']),
            'password' => $password,
            'role' => 'teacher',
            'is_admin' => $request->boolean('is_admin'),
        ]);

        return back()->with('new_logins', [['name' => $teacher->name, 'username' => $teacher->username, 'password' => $password]])
            ->with('status', 'Teacher added. Give them this login; they can change the password under Account.');
    }

    public function resetPassword(User $teacher)
    {
        abort_unless($teacher->isTeacher(), 404);
        $password = Credentials::password();
        $teacher->update(['password' => $password]);

        return back()->with('new_logins', [['name' => $teacher->name, 'username' => $teacher->username, 'password' => $password]])
            ->with('status', 'New password for '.$teacher->name.'.');
    }

    public function destroy(Request $request, User $teacher)
    {
        abort_unless($teacher->isTeacher(), 404);
        if ($teacher->id === $request->user()->id) {
            return back()->withErrors(['teacher' => 'You cannot delete your own account.']);
        }
        if ($teacher->classrooms()->exists()) {
            return back()->withErrors(['teacher' => 'This teacher still has classes. Delete or move them first.']);
        }
        $teacher->delete();

        return back()->with('status', 'Teacher deleted.');
    }
}
