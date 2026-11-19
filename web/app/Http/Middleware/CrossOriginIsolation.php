<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

/**
 * Python runs in the browser in a Web Worker. To let the program wait for
 * input() and for "Next step", the page needs SharedArrayBuffer, which
 * browsers only allow on "cross-origin isolated" pages with these headers.
 */
class CrossOriginIsolation
{
    public function handle(Request $request, Closure $next)
    {
        $response = $next($request);
        $response->headers->set('Cross-Origin-Opener-Policy', 'same-origin');
        $response->headers->set('Cross-Origin-Embedder-Policy', 'require-corp');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('Referrer-Policy', 'same-origin');

        return $response;
    }
}
