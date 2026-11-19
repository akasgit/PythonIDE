<?php

namespace App\Support;

class Installer
{
    public static function lockFile(): string
    {
        return storage_path('app/installed.lock');
    }

    public static function isInstalled(): bool
    {
        return is_file(self::lockFile());
    }

    public static function markInstalled(): void
    {
        file_put_contents(self::lockFile(), date('c')."\n");
    }

    /** Set KEY=value lines in .env, keeping everything else. */
    public static function writeEnv(array $values): bool
    {
        $path = base_path('.env');
        $contents = is_file($path) ? (string) file_get_contents($path) : '';
        foreach ($values as $key => $value) {
            $value = (string) $value;
            if ($value !== '' && preg_match('/[\s#"\'$\\\\]/', $value)) {
                $value = '"'.str_replace(['\\', '"', '$'], ['\\\\', '\"', '\$'], $value).'"';
            }
            $line = $key.'='.$value;
            $pattern = '/^'.preg_quote($key, '/').'=.*$/m';
            if (preg_match($pattern, $contents)) {
                $contents = preg_replace_callback($pattern, fn () => $line, $contents);
            } else {
                $contents = rtrim($contents)."\n".$line."\n";
            }
        }

        return file_put_contents($path, $contents) !== false;
    }
}
