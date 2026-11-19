<?php

namespace Tests\Feature;

use App\Models\Classroom;
use App\Models\Program;
use App\Models\User;
use App\Support\Installer;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class PythonIdeTest extends TestCase
{
    use RefreshDatabase;

    private ?string $savedLock = null;

    protected function setUp(): void
    {
        parent::setUp();
        $lock = Installer::lockFile();
        $this->savedLock = is_file($lock) ? file_get_contents($lock) : null;
        Installer::markInstalled();
    }

    protected function tearDown(): void
    {
        $lock = Installer::lockFile();
        if ($this->savedLock === null) {
            @unlink($lock);
        } else {
            file_put_contents($lock, $this->savedLock);
        }
        parent::tearDown();
    }

    private function teacher(array $extra = []): User
    {
        return User::create($extra + ['name' => 'Teacher', 'username' => 'teacher'.uniqid(), 'password' => 'secret123', 'role' => 'teacher']);
    }

    private function student(?Classroom $classroom = null, string $name = 'Sita'): User
    {
        return User::create(['name' => $name, 'username' => strtolower($name).uniqid(), 'password' => 'mango42',
            'role' => 'student', 'classroom_id' => $classroom?->id]);
    }

    public function test_everything_goes_to_install_until_set_up(): void
    {
        @unlink(Installer::lockFile());
        $this->get('/ide')->assertRedirect('/install');
        $this->get('/install')->assertOk()->assertSee('Your teacher account');
    }

    public function test_install_creates_admin_and_finishes(): void
    {
        @unlink(Installer::lockFile());
        $this->post('/install/admin', [
            'name' => 'Akash Aryal', 'username' => 'Akash', 'password' => 'secret123',
            'password_confirmation' => 'secret123', 'db_password' => '',
        ])->assertRedirect('/classes');
        $admin = User::where('username', 'akash')->first();
        $this->assertTrue($admin->is_admin && $admin->isTeacher());
        $this->assertTrue(Installer::isInstalled());
        $this->get('/install')->assertRedirect('/login');
        $this->post('/install/admin', [])->assertNotFound();
    }

    public function test_install_needs_the_database_password(): void
    {
        @unlink(Installer::lockFile());
        config(['database.connections.sqlite.password' => 'real-db-password']);
        $this->post('/install/admin', [
            'name' => 'Stranger', 'username' => 'hacker', 'password' => 'secret123',
            'password_confirmation' => 'secret123', 'db_password' => 'guess',
        ])->assertSessionHasErrors('db_password');
        $this->assertFalse(Installer::isInstalled());
    }

    public function test_ide_page_is_cross_origin_isolated_and_open_to_guests(): void
    {
        $this->get('/ide')->assertOk()
            ->assertHeader('Cross-Origin-Opener-Policy', 'same-origin')
            ->assertHeader('Cross-Origin-Embedder-Policy', 'require-corp')
            ->assertSee('IDE_CONFIG', false);
        $this->get('/ide/worker.js')->assertOk()
            ->assertHeader('Cross-Origin-Embedder-Policy', 'require-corp')
            ->assertHeader('Content-Type', 'text/javascript; charset=utf-8');
    }

    public function test_login_with_username(): void
    {
        $student = $this->student();
        $this->post('/login', ['username' => strtoupper($student->username), 'password' => 'wrong'])
            ->assertSessionHasErrors('username');
        $this->post('/login', ['username' => ' '.$student->username, 'password' => 'mango42'])
            ->assertRedirect('/ide');
        $this->assertAuthenticatedAs($student);
    }

    public function test_student_saves_and_updates_own_programs(): void
    {
        $student = $this->student();
        $id = $this->actingAs($student)->postJson('/api/programs', ['title' => 'Area', 'code' => 'print(1)'])
            ->assertCreated()->json('id');
        $this->putJson("/api/programs/$id", ['title' => 'Area 2', 'code' => 'print(2)'])->assertOk();
        $this->getJson("/api/programs/$id")->assertJson(['title' => 'Area 2', 'code' => 'print(2)']);
        $this->getJson('/api/programs')->assertJsonCount(1);
        $this->get('/programs')->assertSee('Area 2');
    }

    public function test_students_cannot_touch_each_others_programs(): void
    {
        $sita = $this->student(null, 'Sita');
        $ram = $this->student(null, 'Ram');
        $program = $sita->programs()->create(['title' => 'Secret', 'code' => 'x = 1']);
        $this->actingAs($ram);
        $this->getJson("/api/programs/{$program->id}")->assertNotFound();
        $this->putJson("/api/programs/{$program->id}", ['title' => 'Hacked', 'code' => ''])->assertNotFound();
        $this->deleteJson("/api/programs/{$program->id}")->assertNotFound();
        $this->get("/ide?program={$program->id}")->assertNotFound();
        $this->assertSame('Secret', $program->fresh()->title);
    }

    public function test_guests_cannot_use_the_api_or_teacher_pages(): void
    {
        $this->getJson('/api/programs')->assertUnauthorized();
        $this->get('/classes')->assertRedirect('/login');
        $this->actingAs($this->student())->get('/classes')->assertForbidden();
    }

    public function test_teacher_adds_students_and_sees_their_work_only_in_own_class(): void
    {
        $teacher = $this->teacher();
        $other = $this->teacher();
        $this->actingAs($teacher)->post('/classes', ['name' => 'Class 10 A']);
        $classroom = Classroom::where('name', 'Class 10 A')->first();
        $this->post("/classes/{$classroom->id}/students", ['names' => "Sita Sharma\nRam Thapa\n\nSita Sharma"])
            ->assertSessionHas('new_logins', fn ($logins) => count($logins) === 3
                && $logins[0]['username'] === 'sita.sharma' && $logins[2]['username'] === 'sita.sharma2');
        $sita = User::where('username', 'sita.sharma')->first();
        $program = $sita->programs()->create(['title' => 'Loops', 'code' => 'print(1)']);

        $this->get("/students/{$sita->id}")->assertOk()->assertSee('Loops');
        $this->get("/ide?program={$program->id}")->assertOk()->assertSee('"mine":false', false);

        $this->actingAs($other)->get("/students/{$sita->id}")->assertForbidden();
        $this->get("/ide?program={$program->id}")->assertNotFound();
        $this->get("/classes/{$classroom->id}")->assertForbidden();
    }

    public function test_reset_password_and_remove_student(): void
    {
        $teacher = $this->teacher();
        $classroom = $teacher->classrooms()->create(['name' => '9B']);
        $student = $this->student($classroom);
        $this->actingAs($teacher)->post("/students/{$student->id}/password")
            ->assertSessionHas('new_logins');
        $this->assertFalse(password_verify('mango42', $student->fresh()->password));
        $student->programs()->create(['title' => 'x', 'code' => '']);
        $this->delete("/students/{$student->id}")->assertRedirect();
        $this->assertNull(User::find($student->id));
        $this->assertSame(0, Program::count());
    }

    public function test_only_admins_manage_teachers(): void
    {
        $admin = $this->teacher(['is_admin' => true]);
        $this->actingAs($this->teacher())->get('/teachers')->assertForbidden();
        $this->actingAs($admin)->post('/teachers', ['name' => 'New Teacher', 'username' => 'NewT'])
            ->assertSessionHas('new_logins');
        $this->assertTrue(User::where('username', 'newt')->first()->isTeacher());
        $this->delete("/teachers/{$admin->id}")->assertSessionHasErrors('teacher');
    }

    public function test_change_password(): void
    {
        $student = $this->student();
        $this->actingAs($student)->post('/account/password', [
            'current_password' => 'mango42', 'password' => 'newpass1', 'password_confirmation' => 'newpass1',
        ])->assertSessionHas('status');
        $this->assertTrue(password_verify('newpass1', $student->fresh()->password));
    }
}
