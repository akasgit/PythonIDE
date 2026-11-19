<?php

/*
 * Shared hosting has no terminal to run "php artisan key:generate", so on the
 * first request we create .env from .env.example and give it a secret key.
 */
(function () {
    $base = dirname(__DIR__);
    $env = $base.'/.env';
    if (! is_file($env)) {
        if (! is_file($base.'/.env.example') || ! @copy($base.'/.env.example', $env)) {
            return;
        }
    }
    $contents = (string) file_get_contents($env);
    if (preg_match('/^APP_KEY=\s*$/m', $contents)) {
        $key = 'base64:'.base64_encode(random_bytes(32));
        $contents = preg_replace('/^APP_KEY=\s*$/m', 'APP_KEY='.$key, $contents);
        @file_put_contents($env, $contents);
    }
})();
