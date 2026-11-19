<?php

namespace App\Support;

use App\Models\User;
use Illuminate\Support\Str;

/** Easy usernames and passwords for school students. */
class Credentials
{
    private const WORDS = [
        'apple', 'bird', 'cloud', 'dragon', 'eagle', 'flower', 'garden', 'hill', 'island',
        'jungle', 'kite', 'lake', 'mango', 'moon', 'river', 'star', 'tiger', 'tree', 'yak',
        'panda', 'rhino', 'lotus', 'peak', 'sun', 'rain', 'snow', 'road', 'boat', 'book',
    ];

    public static function password(): string
    {
        return self::WORDS[random_int(0, count(self::WORDS) - 1)].random_int(10, 99);
    }

    /** "Sita Sharma" -> "sita.sharma", with a number added if it is taken. */
    public static function username(string $name): string
    {
        $base = Str::slug(Str::ascii($name), '.');
        $base = substr(preg_replace('/[^a-z0-9.]/', '', $base), 0, 30);
        if ($base === '') {
            $base = 'student';
        }
        $username = $base;
        $n = 1;
        while (User::where('username', $username)->exists()) {
            $n++;
            $username = $base.$n;
        }

        return $username;
    }
}
