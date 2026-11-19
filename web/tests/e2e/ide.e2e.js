/*
 * Browser test of the online IDE (run by GitHub Actions).
 *   1. php artisan serve, with a teacher "teacher"/"secret123", a class
 *      "Class 10 A" and a student "sita"/"mango42" (see the workflow)
 *   2. node tests/e2e/ide.e2e.js
 */
const { chromium } = require('playwright');
const SHOTS = process.env.SHOTS || __dirname;
const BASE = process.env.BASE_URL || 'http://127.0.0.1:8000';
let failures = 0;
function check(name, ok, extra) { console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')); if (!ok) failures++; }

async function setCode(page, code) {
  await page.evaluate((c) => document.querySelector('.CodeMirror').CodeMirror.setValue(c), code);
}
const output = (page) => page.$eval('#output', (e) => e.textContent);
const finished = (page, text, timeout) => page.waitForFunction((t) => document.getElementById('output').textContent.includes(t), text, { timeout: timeout || 15000 });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  page.on('dialog', (d) => d.accept('Area program'));
  await page.goto(BASE + '/ide');
  check('cross-origin isolated', await page.evaluate(() => self.crossOriginIsolated));
  const t0 = Date.now();
  await page.waitForSelector('#loading', { state: 'hidden', timeout: 90000 });
  console.log('Python ready in', Date.now() - t0, 'ms; status:', await page.textContent('#status'));

  // 1. Run with input
  await setCode(page, 'a = int(input("A: "))\nb = int(input("B: "))\nprint("Sum =", a + b)\n');
  await page.click('#btn-run');
  await page.waitForSelector('#input-row.waiting', { timeout: 15000 });
  await page.fill('#input', '20'); await page.keyboard.press('Enter');
  await finished(page, 'B: ');
  await page.waitForSelector('#input-row.waiting');
  await page.fill('#input', '22'); await page.keyboard.press('Enter');
  await finished(page, 'Program finished');
  const out1 = await output(page);
  check('run with input', out1.includes('A: 20\nB: 22\nSum = 42'), JSON.stringify(out1.slice(0, 80)));
  const vars1 = await page.$$eval('#vars tr', (rows) => rows.map((r) => r.textContent));
  check('final variables', vars1.some((r) => r.startsWith('a') && r.includes('20')), JSON.stringify(vars1));

  // 2. Syntax error help
  await setCode(page, 'marks = 50\nif marks >= 40\n    print("Pass")\n');
  await page.click('#btn-run');
  await page.waitForSelector('#output .help', { timeout: 15000 });
  const help = await page.textContent('#output .help .title');
  check('syntax error explained', help.includes('line 2') && help.includes('Colon'), help);
  check('error line marked', (await page.$$('.line-error')).length === 1);
  await page.screenshot({ path: SHOTS + '/web_error.png' });

  // 3. NameError with suggestion
  await setCode(page, 'total = 5\nprint(totl)\n');
  await page.click('#btn-run');
  await page.waitForSelector('#output .help');
  check('name error suggestion', (await page.textContent('#output .help')).includes('Did you mean total'));

  // 4. Step mode
  await setCode(page, 'total = 0\nfor i in range(1, 4):\n    total = total + i\nprint("Sum:", total)\n');
  await page.click('#btn-step');
  await page.waitForSelector('.line-step', { timeout: 15000 });
  for (let k = 0; k < 4; k++) { await page.click('#btn-next'); await page.waitForTimeout(300); }
  const stepStatus = await page.textContent('#status');
  const changed = await page.$$eval('#vars tr.changed', (rows) => rows.map((r) => r.textContent));
  check('step mode moves and shows changes', /Step 5: line \d/.test(stepStatus) && changed.length > 0, stepStatus + ' ' + JSON.stringify(changed));
  await page.screenshot({ path: SHOTS + '/web_step.png' });
  await page.click('#btn-end');
  await finished(page, 'Sum: 6', 10000);
  check('step to end', true);

  // 5. Stop an endless loop
  await setCode(page, 'n = 0\nwhile True:\n    n = n + 1\n');
  await page.click('#btn-run');
  await page.waitForTimeout(1500);
  const ts = Date.now();
  await page.click('#btn-stop');
  await finished(page, 'Program stopped', 5000);
  check('stop endless loop', true, (Date.now() - ts) + ' ms');
  await page.waitForFunction(() => document.getElementById('btn-stop').disabled);
  await setCode(page, 'print("again")\n');
  await page.click('#btn-run');
  await finished(page, 'Program finished', 10000);
  check('runs again after stop', (await output(page)).startsWith('again'));

  // 6. Stop while waiting for input
  await setCode(page, 'x = input("?")\n');
  await page.click('#btn-run');
  await page.waitForSelector('#input-row.waiting');
  await page.click('#btn-stop');
  await finished(page, 'Program stopped', 5000);
  check('stop while waiting for input', true);

  // 7. Turtle
  await setCode(page, 'import turtle\nt = turtle.Turtle()\nt.color("red")\nt.pensize(4)\nt.speed(0)\nfor i in range(4):\n    t.forward(150)\n    t.left(90)\nt.circle(50)\n');
  await page.click('#btn-run');
  await finished(page, 'Program finished');
  await page.waitForTimeout(800);
  const red = await page.evaluate(() => {
    const d = document.getElementById('canvas').getContext('2d').getImageData(0, 0, 600, 600).data;
    let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i] > 200 && d[i + 1] < 80) n++; return n;
  });
  check('turtle draws', red > 500 && !(await page.isHidden('#draw-panel')), red + ' red pixels');
  await page.screenshot({ path: SHOTS + '/web_turtle.png' });

  // 8. time.sleep and the examples menu
  await setCode(page, 'import time\nfor i in range(3):\n    print(i)\n    time.sleep(0.2)\n');
  await page.click('#btn-run');
  await finished(page, 'Program finished', 10000);
  check('time.sleep', (await output(page)).startsWith('0\n1\n2'));
  await page.click('#btn-examples');
  await page.click('summary:has-text("Number programs")');
  await page.click('button:has-text("Armstrong number")');
  check('example loads', (await page.evaluate(() => document.querySelector('.CodeMirror').CodeMirror.getValue())).includes('Armstrong'));

  // 9. Projector theme with an error
  await page.click('#btn-view'); await page.click('#view-menu [data-theme=projector]'); await page.keyboard.press('Escape');
  await setCode(page, 'name = input("Name: ")\nprint("Namaste,", nme)\n');
  await page.click('#btn-run');
  await page.waitForSelector('#input-row.waiting');
  await page.fill('#input', 'Sita'); await page.keyboard.press('Enter');
  await page.waitForSelector('#output .help');
  check('projector theme', (await page.evaluate(() => document.documentElement.dataset.theme)) === 'projector');
  await page.screenshot({ path: SHOTS + '/web_projector.png' });
  await page.keyboard.press('F9');

  // 10. Student logs in and saves; teacher sees it
  const student = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  student.on('dialog', (d) => d.accept('Area program'));
  await student.goto(BASE + '/login');
  await student.fill('input[name=username]', 'sita'); await student.fill('input[name=password]', 'mango42');
  await student.click('button:has-text("Log in")');
  await student.waitForURL('**/ide');
  await student.waitForSelector('.CodeMirror');
  await setCode(student, 'l = 5\nb = 3\nprint("Area =", l * b)\n');
  await student.click('#btn-save');
  await student.waitForFunction(() => document.getElementById('status').textContent.startsWith('Saved'), null, { timeout: 10000 });
  check('student saves online', /program=\d+/.test(student.url()), student.url());
  await student.goto(BASE + '/programs');
  check('appears in My programs', (await student.textContent('table')).includes('Area program'));

  const teacher = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await teacher.goto(BASE + '/login');
  await teacher.fill('input[name=username]', 'teacher'); await teacher.fill('input[name=password]', 'secret123');
  await teacher.click('button:has-text("Log in")');
  await teacher.goto(BASE + '/classes');
  await teacher.click('text=Class 10 A');
  await teacher.fill('textarea[name=names]', 'Ram Thapa\nGita Karki');
  await teacher.click('button:has-text("Add students")');
  const slips = await teacher.$$eval('.slip', (s) => s.map((x) => x.textContent.replace(/\s+/g, ' ').trim()));
  check('teacher adds students with slips', slips.length === 2, JSON.stringify(slips));
  await teacher.screenshot({ path: SHOTS + '/web_class.png', fullPage: true });
  await teacher.click('a:has-text("Sita Sharma")');
  await teacher.click('a:has-text("Open and run")');
  await teacher.waitForSelector('#loading', { state: 'hidden', timeout: 90000 });
  check('teacher opens student program', (await teacher.textContent('#status')).includes("Sita Sharma's program"));
  await teacher.click('#btn-run');
  await finished(teacher, 'Area = 15');
  check('teacher runs it', true);

  await browser.close();
  console.log(failures ? failures + ' FAILED' : 'ALL PASSED');
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error('CRASH', e); process.exit(2); });
