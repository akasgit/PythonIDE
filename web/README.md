# PythonIDE Online

The PythonIDE editor in a web browser, with teacher and student accounts. It's built
with Laravel and made for ordinary **cPanel shared hosting**. You don't need a
terminal, Composer or Node on the server.

Students' Python runs **inside their own browser**, using Pyodide (real Python 3.12
compiled for the web). Nothing a student types ever runs on your server, so a
mistaken or mischievous program cannot harm it, and the site stays fast however
many students use it.

## What it does

- **Editor:** line numbers, Python colours, auto-indent and Tab handling, like the
  desktop app.
- **Run, Stop, Step:** `input()` works with a yellow input box. **Step** runs one line
  at a time and shows the variables, with changed ones in green. **Stop** ends endless
  loops.
- **Error help** in English and Nepali. It uses the same code as the desktop app.
- **All 80 examples**, including the Class 10 section. **Turtle** drawings appear in
  the Drawing panel.
- **Themes:** Light, Dark and Projector (View menu or F9).
- **Accounts:**
  - Teachers create classes and add students by typing their names. Each student
    gets a username and an easy password on a printable **login slip**.
  - Students **save their programs online** and open them on any computer.
  - Teachers see each student's programs and can open and run them. A teacher can
    never change a student's program: Save makes the teacher a copy.
  - The first teacher is the **admin** and can add more teachers.
- **No login needed** to try it: open `/ide` and programs are kept in that browser,
  or downloaded as `.py` files.

## Putting it on pythonide.aryalakash.com.np (cPanel)

You need **PHP 8.2 or newer**, a **MySQL database** and **HTTPS**. Most cPanel hosts
have all three.

1. **Download** `PythonIDE-Web-<version>.zip` from the
   [Releases page](https://github.com/akasgit/PythonIDE/releases). It already
   contains Laravel's `vendor` folder and Python for the browser.
2. **PHP version:** in cPanel → *Select PHP Version* (or *MultiPHP Manager*), choose
   **8.2 or newer** for the domain. If there is a list of extensions, make sure
   `pdo_mysql`, `mbstring`, `openssl`, `fileinfo`, `tokenizer`, `xml` and `ctype`
   are ticked. They usually are.
3. **Database:** in cPanel → *MySQL Databases*:
   - create a database, for example `pythonide`;
   - create a user with a strong password;
   - under *Add User To Database*, add the user to the database with **All Privileges**.
   - Write down the full names cPanel shows, for example `cpuser_pythonide`.
4. **Upload:** in cPanel → *File Manager*, open your **home folder** (the one that
   *contains* `public_html`, not `public_html` itself). Upload the zip, then right-click
   it and choose **Extract**. You now have a folder `pythonide-web`.
5. **Point the subdomain at it:** in cPanel → *Domains* (or *Subdomains*), create
   `pythonide.aryalakash.com.np`, or edit it if it already exists. Set its
   **Document Root** to `pythonide-web/public`.
6. **HTTPS:** in cPanel → *SSL/TLS Status*, run **AutoSSL** for the subdomain (it's
   free). If there's a *Force HTTPS Redirect* switch under *Domains*, turn it on.
   Browsers only allow Python's `input()`, Step and Stop on `https://` pages.
7. **Finish setup:** open **https://pythonide.aryalakash.com.np/install**:
   - *Step 1:* enter the database name, user and password from step 3.
   - *Step 2:* create your teacher account. For safety, it asks for the database
     password again, so a stranger can't take over a site that isn't set up yet.
     Do this step soon after uploading.

Then log in, go to **Classes**, create a class and add your students.

### If you can't change the Document Root

Some hosts don't let you change it. In that case extract the zip so that the
contents of `pythonide-web` are *inside the subdomain's folder*. The included
`.htaccess` then forwards everything to `public/` and keeps `.env` and the code
private. Changing the Document Root (step 5) is cleaner, so use that when you can.

### Updating to a new version

Download the new zip and extract it **over** the old `pythonide-web` folder, replacing
files. Your `.env` (database settings) and everything in `storage` stay as they are,
because the zip contains neither. Any new database tables are created automatically
on the next visit.

### Backups

All accounts and saved programs are in the MySQL database. Use cPanel → *Backup* (or
*phpMyAdmin → Export*) now and then.

## How it works (for developers)

| Part | Where |
|---|---|
| Laravel app (accounts, classes, saved programs, install page) | `app/`, `routes/web.php`, `resources/views/` |
| The editor page | `resources/views/ide.blade.php`, `public/ide-assets/ide.js`, `public/css/app.css` |
| Runs Python in a Web Worker | `resources/ide/worker.js` (served by Laravel so it always gets the right headers) |
| Python that runs a student's program, plus step mode | `resources/ide/py/runner.py` |
| Browser version of `turtle` | `resources/ide/py/turtle.py` |
| Error help and examples | Copied from the desktop app by `tools/export_web_assets.py` |
| CodeMirror 5 (the code editor) | `public/lib/codemirror/` |
| Pyodide 0.26.4 (Python 3.12) | `public/pyodide/`, downloaded by `tools/fetch-pyodide.sh` |

`input()`, Step and Stop need `SharedArrayBuffer`, so every page is sent with
`Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy:
require-corp` (`app/Http/Middleware/CrossOriginIsolation.php`). This only works on
HTTPS (or `localhost`).

Run it locally:

```bash
cd web && composer install && ../tools/fetch-pyodide.sh
```

```bash
cp .env.example .env && php artisan key:generate
```

Set `DB_CONNECTION=sqlite` and a `DB_DATABASE` path in `.env`, then:

```bash
php artisan migrate && php artisan serve
```

Open http://127.0.0.1:8000/install (with SQLite, create the lock file
`storage/app/installed.lock` and a teacher through `php artisan tinker` instead).

Tests:

```bash
php artisan test
```

The browser test in `tests/e2e/ide.e2e.cjs` runs in GitHub Actions; see
`.github/workflows/build-installer.yml`.
