<?php

namespace App\Http\Middleware;

use App\Support\Installer;
use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Artisan;

/**
 * Send every visitor to /install until setup is finished. After an update
 * (new files uploaded over the old ones), create any new database tables
 * on the next visit, because shared hosting has no terminal for "migrate".
 */
class RequireInstalled
{
    public function handle(Request $request, Closure $next)
    {
        if (! Installer::isInstalled()) {
            if (! $request->is('install', 'install/*', 'up')) {
                return redirect('/install');
            }

            return $next($request);
        }

        $stamp = storage_path('app/migrations.stamp');
        $current = (string) count(glob(database_path('migrations/*.php')));
        if (! is_file($stamp) || trim((string) file_get_contents($stamp)) !== $current) {
            Artisan::call('migrate', ['--force' => true]);
            @file_put_contents($stamp, $current);
        }

        return $next($request);
    }
}
