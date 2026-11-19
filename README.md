# PythonIDE

A simple Python editor for Class 9 and 10 students. It runs well on old school-lab
computers (3rd-gen Core i3, 2–4 GB RAM) and works offline. It needs only Python,
nothing else to install.

## What it does for students

- **Run (F5).** Runs the program. When the program asks for input, the input box
  turns yellow and says *"Type here and press Enter"*.
- **Easy error messages.** Errors are explained in simple English **and Nepali**,
  with a tip on how to fix them. The wrong line turns red. Some examples:
  - missing `:` after `if` / `for`
  - writing `=` instead of `==`
  - a quote or bracket that is not closed
  - `Print` instead of `print`
  - joining text and a number (`"Age " + 15`)
  - forgetting `int(input())`
- **Step mode (F6 / F7).** Runs the program one line at a time. The line that runs
  next is yellow. The **Variables** panel shows every variable's value and type,
  and the ones that just changed turn green. *Auto* plays the steps by itself, and
  the slider sets the speed.
- **Variables panel.** After a normal run it shows the final values, so students
  see what their program did.
- **Examples menu.** 33 ready-made programs following the Class 9–10
  syllabus: input/output, simple interest, if/elif, loops, factorial, prime,
  Fibonacci, strings, lists, functions and turtle drawing.
- **Cheat sheet (F1).** A one-page Python reference.
- **Big text for projectors.** Use **A+ / A-** or Ctrl + mouse wheel.
- **Turtle graphics.** Turtle programs work with Run, and the drawing window stays
  open until it is closed.

## Installing in a school lab

1. Install Python on each computer from <https://www.python.org/downloads/>:
   - **Windows 7:** use **Python 3.8.10**, the last version that supports Windows 7
     ([32-bit](https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe) /
     [64-bit](https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe)).
   - **Windows 10/11:** any Python 3.8 or newer.
   - During installation, tick **"Add Python to PATH"**. Keep the default options:
     they include *tcl/tk*, which PythonIDE needs.
2. Download this repository (*Code → Download ZIP* on GitHub) and unzip it, for
   example to `C:\PythonIDE`.
3. Double-click **`Start PythonIDE.bat`**. If `.pyw` files open with Python, you can
   double-click **`start.pyw`** instead.
4. For a desktop shortcut, right-click `Start PythonIDE.bat` → *Send to → Desktop
   (create shortcut)*.

The installer files can be copied to each lab computer with a pen drive. No
internet connection is needed after that.

**Ubuntu / Linux labs:** run `sudo apt install python3-tk` once, then run `./start.sh`.

## Where programs are saved

Programs are saved in **Documents\PythonIDE Programs** by default. Settings (text
size, error-help language) are stored in a `.pythonide` folder in the user's home
folder.

## For teachers: adding your own examples

Put `.py` files in a folder named **`examples`** next to `start.pyw`. They appear
under **Examples → My examples (from teacher)**. In file names, `_` is shown as a
space: `class9_area_of_triangle.py` appears as *class9 area of triangle*.

The error-help language can be set to English, Nepali or both from the **View** menu.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| F5 | Run |
| Shift+F5 | Stop |
| F6 | Start step mode |
| F7 | Next step |
| F8 | Run to the end (in step mode) |
| F1 | Cheat sheet |
| Ctrl+S / Ctrl+O / Ctrl+N | Save / Open / New |
| Ctrl+/ | Comment or uncomment lines |
| Tab / Shift+Tab | Indent / un-indent (also works on selected lines) |
| Ctrl + / Ctrl − | Bigger / smaller text |

## For developers

- Only the Python standard library (Tkinter) is used. The code is kept compatible
  with **Python 3.8**.
- `pythonide/runner.py` runs programs in a separate Python process, so a crash or an
  endless loop never freezes the editor.
- `pythonide/stepper.py` runs step mode using `sys.settrace`.
- `pythonide/errors.py` contains the friendly error explanations. To improve a
  message or the Nepali text, edit it there.
- `pythonide/examples.py` holds the built-in examples.

Run the tests:

```bash
python -m unittest discover -s tests
```
