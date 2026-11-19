<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Program extends Model
{
    protected $fillable = ['title', 'code'];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
