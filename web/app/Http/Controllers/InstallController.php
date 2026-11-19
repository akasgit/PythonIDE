<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Support\Installer;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use PDO;
use Throwable;

/**
 * One-time setup for shared hosting (no terminal): save the database
 * details, create the tables and the first (admin) teacher.
 */
class InstallController extends Controller
{
    public function show()
    {
        if (Installer::isInstalled()) {
            return redirect('/login');
        }
        $dbError = $this->databaseError();

        return view('install', [
            'step' => $dbError === null ? 'admin' : 'database',
            'dbError' => $dbError,
            'db' => [
                'host' => config('database.connections.mysql.host', 'localhost'),
                'port' => config('database.connections.mysql.port', 3306),
                'database' => config('database.connections.mysql.database'),
                'username' => config('database.connections.mysql.username'),
            ],
            'checks' => $this->checks(),
            'secure' => request()->isSecure() || in_array(request()->getHost(), ['localhost', '127.0.0.1'], true),
        ]);
    }

    public function saveDatabase(Request $request)
    {
        abort_if(Installer::isInstalled(), 404);
        // Once a working database is saved, it cannot be changed from here.
        abort_if($this->databaseError() === null, 403, 'The database is already set up.');

        $data = $request->validate([
            'host' => 'required|string|max:255',
            'port' => 'required|integer|min:1|max:65535',
            'database' => 'required|string|max:64',
            'username' => 'required|string|max:64',
            'password' => 'nullable|string|max:255',
        ]);
        try {
            new PDO(
                "mysql:host={$data['host']};port={$data['port']};dbname={$data['database']}",
                $data['username'],
                $data['password'] ?? '',
                [PDO::ATTR_TIMEOUT => 5, PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
            );
        } catch (Throwable $e) {
            return back()->withInput()->withErrors([
                'database' => 'Could not connect to the database: '.$e->getMessage(),
            ]);
        }
        $saved = Installer::writeEnv([
            'DB_CONNECTION' => 'mysql',
            'DB_HOST' => $data['host'],
            'DB_PORT' => $data['port'],
            'DB_DATABASE' => $data['database'],
            'DB_USERNAME' => $data['username'],
            'DB_PASSWORD' => $data['password'] ?? '',
            'APP_URL' => $request->getSchemeAndHttpHost(),
        ]);
        if (! $saved) {
            return back()->withInput()->withErrors([
                'database' => 'Could not write the .env file. Check that the PythonIDE folder is writable.',
            ]);
        }

        return redirect('/install');
    }

    public function createAdmin(Request $request)
    {
        abort_if(Installer::isInstalled(), 404);
        abort_if($this->databaseError() !== null, 400, 'Set up the database first.');

        $data = $request->validate([
            'name' => 'required|string|max:100',
            'username' => 'required|alpha_dash|max:50',
            'password' => 'required|string|min:6|confirmed',
            'db_password' => 'nullable|string',
        ]);
        // Only the site owner knows the database password, so a stranger who
        // finds /install before you cannot make themselves the admin.
        if ((string) ($data['db_password'] ?? '') !== (string) config('database.connections.'.config('database.default').'.password')) {
            return back()->withInput()->withErrors(['db_password' => 'This is not the database password.']);
        }

        $data['username'] = strtolower($data['username']);
        Artisan::call('migrate', ['--force' => true]);
        if (User::where('username', $data['username'])->exists()) {
            return back()->withInput()->withErrors(['username' => 'This username is taken.']);
        }
        $user = User::create([
            'name' => $data['name'],
            'username' => $data['username'],
            'password' => $data['password'],
            'role' => 'teacher',
            'is_admin' => true,
        ]);
        Installer::markInstalled();
        Auth::login($user);
        $request->session()->regenerate();

        return redirect('/classes')->with('status', 'PythonIDE is ready. Create your first class below.');
    }

    private function databaseError(): ?string
    {
        if (! config('database.connections.'.config('database.default').'.database')) {
            return 'No database is set yet.';
        }
        try {
            DB::connection()->getPdo();

            return null;
        } catch (Throwable $e) {
            return $e->getMessage();
        }
    }

    private function checks(): array
    {
        return [
            'PHP 8.2 or newer' => version_compare(PHP_VERSION, '8.2.0', '>='),
            'PDO MySQL extension' => extension_loaded('pdo_mysql'),
            'storage folder is writable' => is_writable(storage_path()),
            '.env file is writable' => is_writable(base_path('.env')),
        ];
    }
}
