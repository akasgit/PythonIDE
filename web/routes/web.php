<?php

use App\Http\Controllers\AccountController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\IdeController;
use App\Http\Controllers\InstallController;
use App\Http\Controllers\ProgramController;
use App\Http\Controllers\Teacher\ClassroomController;
use App\Http\Controllers\Teacher\TeacherController;
use Illuminate\Support\Facades\Route;

Route::get('/', fn () => redirect(auth()->check() ? '/ide' : '/login'));

// One-time setup
Route::get('/install', [InstallController::class, 'show']);
Route::post('/install/database', [InstallController::class, 'saveDatabase']);
Route::post('/install/admin', [InstallController::class, 'createAdmin']);

// Login
Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
    Route::post('/login', [AuthController::class, 'login'])->middleware('throttle:10,1');
});
Route::post('/logout', [AuthController::class, 'logout'])->middleware('auth')->name('logout');

// The IDE works without logging in too (programs are then kept in the browser).
Route::get('/ide', [IdeController::class, 'show'])->name('ide');
Route::get('/ide/worker.js', [IdeController::class, 'worker']);

Route::middleware('auth')->group(function () {
    Route::get('/programs', [ProgramController::class, 'index'])->name('programs');
    Route::delete('/programs/{program}', [ProgramController::class, 'destroy'])->name('programs.destroy');

    Route::prefix('api')->group(function () {
        Route::get('/programs', [ProgramController::class, 'list']);
        Route::post('/programs', [ProgramController::class, 'store']);
        Route::get('/programs/{program}', [ProgramController::class, 'get']);
        Route::put('/programs/{program}', [ProgramController::class, 'update']);
        Route::delete('/programs/{program}', [ProgramController::class, 'destroy']);
    });

    Route::get('/account', [AccountController::class, 'show'])->name('account');
    Route::post('/account/password', [AccountController::class, 'updatePassword']);

    Route::middleware('teacher')->group(function () {
        Route::get('/classes', [ClassroomController::class, 'index'])->name('classes.index');
        Route::post('/classes', [ClassroomController::class, 'store']);
        Route::get('/classes/{classroom}', [ClassroomController::class, 'show'])->name('classes.show');
        Route::put('/classes/{classroom}', [ClassroomController::class, 'update']);
        Route::delete('/classes/{classroom}', [ClassroomController::class, 'destroy']);
        Route::post('/classes/{classroom}/students', [ClassroomController::class, 'addStudents']);
        Route::get('/students/{student}', [ClassroomController::class, 'studentWork'])->name('students.show');
        Route::post('/students/{student}/password', [ClassroomController::class, 'resetPassword']);
        Route::delete('/students/{student}', [ClassroomController::class, 'removeStudent']);

        Route::middleware('teacher:admin')->group(function () {
            Route::get('/teachers', [TeacherController::class, 'index'])->name('teachers');
            Route::post('/teachers', [TeacherController::class, 'store']);
            Route::post('/teachers/{teacher}/password', [TeacherController::class, 'resetPassword']);
            Route::delete('/teachers/{teacher}', [TeacherController::class, 'destroy']);
        });
    });
});
