<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Foundation\Auth\User as Authenticatable;

class User extends Authenticatable
{
    protected $fillable = ['name', 'username', 'email', 'password', 'role', 'is_admin', 'classroom_id'];

    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return [
            'password' => 'hashed',
            'is_admin' => 'boolean',
        ];
    }

    public function isTeacher(): bool
    {
        return $this->role === 'teacher';
    }

    public function programs(): HasMany
    {
        return $this->hasMany(Program::class);
    }

    /** The class a student belongs to. */
    public function classroom(): BelongsTo
    {
        return $this->belongsTo(Classroom::class);
    }

    /** The classes a teacher runs. */
    public function classrooms(): HasMany
    {
        return $this->hasMany(Classroom::class, 'teacher_id');
    }

    /** Can this user see the given student's programs? */
    public function canSeeWorkOf(User $student): bool
    {
        if ($this->id === $student->id) {
            return true;
        }
        if (! $this->isTeacher()) {
            return false;
        }
        if ($this->is_admin) {
            return true;
        }

        return $student->classroom && $student->classroom->teacher_id === $this->id;
    }
}
