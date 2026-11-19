<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;

class EnvWriterTest extends TestCase
{
    public function test_first_visit_creates_env_with_a_key(): void
    {
        $dir = sys_get_temp_dir().'/pyide'.uniqid();
        mkdir($dir.'/bootstrap', 0777, true);
        copy(__DIR__.'/../../bootstrap/ensure-env.php', $dir.'/bootstrap/ensure-env.php');
        file_put_contents($dir.'/.env.example', "APP_NAME=PythonIDE\nAPP_KEY=\nDB_CONNECTION=mysql\n");
        require $dir.'/bootstrap/ensure-env.php';
        $env = file_get_contents($dir.'/.env');
        $this->assertMatchesRegularExpression('/^APP_KEY=base64:[A-Za-z0-9+\/=]{44}$/m', $env);
        $this->assertStringContainsString('DB_CONNECTION=mysql', $env);

        // A second visit keeps the same key.
        require $dir.'/bootstrap/ensure-env.php';
        $this->assertSame($env, file_get_contents($dir.'/.env'));
    }
}
