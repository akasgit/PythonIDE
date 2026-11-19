"""Class 10 example programs, shown under Examples > Class 10."""

CLASS10 = [
    ("Functions (modular programming)", [
        ("SUB and FUNCTION in Python", '''\
# In QBASIC you used SUB (does a job) and FUNCTION (gives back a value).
# In Python both are written with def.

# Like a SUB: it only does a job (prints), it gives nothing back.
def show_line():
    print("-" * 30)

# Like a FUNCTION: it gives back (returns) a value.
def square(n):
    return n * n

show_line()
print("Square of 7 is", square(7))
show_line()
'''),
        ("Simple interest (function)", '''\
def simple_interest(p, t, r):
    return p * t * r / 100

p = float(input("Principal (Rs): "))
t = float(input("Time (years): "))
r = float(input("Rate (%): "))

i = simple_interest(p, t, r)
print("Simple interest = Rs", round(i, 2))
print("Amount = Rs", round(p + i, 2))
'''),
        ("Area and volume of a cylinder", '''\
import math

def curved_area(r, h):
    return 2 * math.pi * r * h

def volume(r, h):
    return math.pi * r * r * h

r = float(input("Radius (cm): "))
h = float(input("Height (cm): "))

print("Curved surface area =", round(curved_area(r, h), 2), "sq. cm")
print("Volume =", round(volume(r, h), 2), "cubic cm")
'''),
        ("Total and average (two return values)", '''\
def total_and_average(a, b, c):
    total = a + b + c
    average = total / 3
    return total, average          # a function can return two values

english = float(input("Marks in English: "))
maths = float(input("Marks in Maths: "))
science = float(input("Marks in Science: "))

t, avg = total_and_average(english, maths, science)
print("Total =", t)
print("Average =", round(avg, 2))
'''),
        ("Default value: rupees to dollars", '''\
# rate has a default value. If we don't give a rate, 133.5 is used.
def to_dollars(rupees, rate=133.5):
    return rupees / rate

rs = float(input("Amount in Nepali rupees: "))
print("At the usual rate: $", round(to_dollars(rs), 2))
print("At rate 135:       $", round(to_dollars(rs, 135), 2))
'''),
        ("Local and global variables", '''\
school = "Shree Secondary School"     # global: usable everywhere

def greet(name):
    message = "Welcome, " + name       # local: only inside greet()
    print(message, "to", school)

greet("Sita")
greet("Hari")
print(school)
# print(message)   <- remove the # to see the error: message is local
'''),
        ("Recursion: factorial", '''\
# A recursive function calls itself with a smaller value.
def factorial(n):
    if n == 0:
        return 1                    # stopping condition
    return n * factorial(n - 1)

n = int(input("Enter a number: "))
print(n, "! =", factorial(n))
'''),
    ]),
    ("Number programs", [
        ("Armstrong number", '''\
# 153 is an Armstrong number: 1*1*1 + 5*5*5 + 3*3*3 = 153
n = int(input("Enter a 3-digit number: "))

temp = n
total = 0
while temp > 0:
    digit = temp % 10
    total = total + digit ** 3
    temp = temp // 10

if total == n:
    print(n, "is an Armstrong number")
else:
    print(n, "is not an Armstrong number")
'''),
        ("Palindrome number", '''\
n = int(input("Enter a number: "))

temp = n
reverse = 0
while temp > 0:
    reverse = reverse * 10 + temp % 10
    temp = temp // 10

if reverse == n:
    print(n, "is a palindrome number")
else:
    print(n, "is not a palindrome number")
'''),
        ("Perfect number", '''\
# 28 is perfect: its factors 1 + 2 + 4 + 7 + 14 = 28
n = int(input("Enter a number: "))

total = 0
for i in range(1, n):
    if n % i == 0:
        total = total + i

if total == n:
    print(n, "is a perfect number")
else:
    print(n, "is not a perfect number")
'''),
        ("Prime numbers from 1 to 100", '''\
print("Prime numbers from 1 to 100:")
for n in range(2, 101):
    is_prime = True
    for i in range(2, n):
        if n % i == 0:
            is_prime = False
            break
    if is_prime:
        print(n, end=" ")
print()
'''),
        ("HCF and LCM", '''\
a = int(input("First number: "))
b = int(input("Second number: "))

x, y = a, b
while y != 0:
    x, y = y, x % y          # Euclid's method
hcf = x
lcm = a * b // hcf

print("HCF =", hcf)
print("LCM =", lcm)
'''),
        ("Decimal to binary", '''\
n = int(input("Enter a decimal number: "))

if n == 0:
    binary = "0"
else:
    binary = ""
    temp = n
    while temp > 0:
        binary = str(temp % 2) + binary
        temp = temp // 2

print("Binary of", n, "is", binary)
'''),
        ("Binary to decimal", '''\
binary = input("Enter a binary number (only 0 and 1): ")

decimal = 0
for digit in binary:
    decimal = decimal * 2 + int(digit)

print("Decimal value is", decimal)
'''),
        ("Multiplication tables 1 to 10", '''\
# A loop inside a loop (nested loop)
for row in range(1, 11):
    for col in range(1, 11):
        print(str(row * col).rjust(4), end="")
    print()
'''),
    ]),
    ("Series and patterns", [
        ("1, 4, 9, 16 ... (squares)", '''\
n = int(input("How many terms? "))
for i in range(1, n + 1):
    print(i * i, end=" ")
print()
'''),
        ("2, 4, 8, 16 ... (doubling)", '''\
n = int(input("How many terms? "))
term = 2
for i in range(n):
    print(term, end=" ")
    term = term * 2
print()
'''),
        ("1, 2, 4, 7, 11 ...", '''\
# The gap grows by one each time: +1, +2, +3, +4 ...
n = int(input("How many terms? "))
term = 1
for gap in range(1, n + 1):
    print(term, end=" ")
    term = term + gap
print()
'''),
        ("5, 55, 555, 5555 ...", '''\
n = int(input("How many terms? "))
term = 0
for i in range(n):
    term = term * 10 + 5
    print(term, end=" ")
print()
'''),
        ("100, 95, 90 ... 5", '''\
for n in range(100, 4, -5):
    print(n, end=" ")
print()
'''),
        ("Sum of 1 + 1/2 + 1/3 ... + 1/n", '''\
n = int(input("Enter n: "))
total = 0
for i in range(1, n + 1):
    total = total + 1 / i
print("Sum =", round(total, 4))
'''),
        ("Star triangle", '''\
rows = int(input("How many rows? "))
for i in range(1, rows + 1):
    print("*" * i)
'''),
        ("Number triangle", '''\
# 1
# 1 2
# 1 2 3
rows = int(input("How many rows? "))
for i in range(1, rows + 1):
    for j in range(1, i + 1):
        print(j, end=" ")
    print()
'''),
        ("Star pyramid", '''\
rows = int(input("How many rows? "))
for i in range(1, rows + 1):
    spaces = " " * (rows - i)
    stars = "*" * (2 * i - 1)
    print(spaces + stars)
'''),
        ("NEPAL word pattern", '''\
word = "NEPAL"

# N, NE, NEP, NEPA, NEPAL
for i in range(1, len(word) + 1):
    print(word[:i])

print()

# NEPAL, NEPA, NEP, NE, N
for i in range(len(word), 0, -1):
    print(word[:i])
'''),
    ]),
    ("String handling", [
        ("Vowels and consonants", '''\
text = input("Enter a sentence: ")

vowels = 0
consonants = 0
for ch in text.lower():
    if ch in "aeiou":
        vowels = vowels + 1
    elif ch.isalpha():
        consonants = consonants + 1

print("Vowels:", vowels)
print("Consonants:", consonants)
'''),
        ("Count words", '''\
sentence = input("Enter a sentence: ")
words = sentence.split()      # split at spaces into a list of words

print("Number of words:", len(words))
for w in words:
    print(w)
'''),
        ("Capital and small letters", '''\
text = input("Enter some text: ")

capital = 0
small = 0
for ch in text:
    if ch.isupper():
        capital = capital + 1
    elif ch.islower():
        small = small + 1

print("Capital letters:", capital)
print("Small letters:", small)
print("All capital:", text.upper())
print("All small:", text.lower())
'''),
        ("Reverse a sentence", '''\
sentence = input("Enter a sentence: ")

print("Letters reversed:", sentence[::-1])

words = sentence.split()
words.reverse()
print("Words reversed:  ", " ".join(words))
'''),
        ("Initials of a name", '''\
# Ram Bahadur Thapa  ->  R. B. Thapa
name = input("Enter your full name: ").title()
parts = name.split()

short = ""
for part in parts[:-1]:
    short = short + part[0] + ". "
short = short + parts[-1]

print(short)
'''),
        ("How often each letter appears", '''\
text = input("Enter a word: ").lower()

count = {}                       # a dictionary: letter -> how many
for ch in text:
    if ch.isalpha():
        count[ch] = count.get(ch, 0) + 1

for letter in sorted(count):
    print(letter, ":", count[letter])
'''),
    ]),
    ("Lists, tuples and dictionaries", [
        ("Largest and smallest (without max)", '''\
numbers = []
n = int(input("How many numbers? "))
for i in range(n):
    numbers.append(int(input("Number " + str(i + 1) + ": ")))

largest = numbers[0]
smallest = numbers[0]
for x in numbers:
    if x > largest:
        largest = x
    if x < smallest:
        smallest = x

print("Largest:", largest)
print("Smallest:", smallest)
'''),
        ("Search in a list", '''\
districts = ["Kathmandu", "Lalitpur", "Bhaktapur", "Kaski", "Chitwan", "Jhapa"]

name = input("Enter a district to search: ").title()

found = False
for position in range(len(districts)):
    if districts[position] == name:
        print(name, "found at position", position)
        found = True

if not found:
    print(name, "is not in the list")
'''),
        ("Bubble sort", '''\
marks = [67, 45, 89, 32, 78, 55]
print("Before:", marks)

n = len(marks)
for i in range(n - 1):
    for j in range(n - 1 - i):
        if marks[j] > marks[j + 1]:
            marks[j], marks[j + 1] = marks[j + 1], marks[j]   # swap

print("After: ", marks)
# Python can also do it in one line: sorted(marks)
'''),
        ("Remove repeated items", '''\
numbers = [4, 7, 4, 2, 7, 9, 2, 4]

unique = []
for x in numbers:
    if x not in unique:
        unique.append(x)

print("Original:", numbers)
print("Without repeats:", unique)
'''),
        ("Tuple: days of the week", '''\
# A tuple is like a list, but it cannot be changed.
days = ("Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday")

n = int(input("Enter day number (1-7): "))
if 1 <= n <= 7:
    print("Day", n, "is", days[n - 1])
else:
    print("Please enter a number from 1 to 7")
'''),
        ("Dictionary: find the topper", '''\
marks = {"Sita": 87, "Ram": 74, "Gita": 92, "Hari": 68}

for name in marks:
    print(name, "got", marks[name])

topper = max(marks, key=marks.get)
print("Topper:", topper, "with", marks[topper], "marks")
'''),
        ("Dictionary: phone book", '''\
phone = {}

n = int(input("How many contacts? "))
for i in range(n):
    name = input("Name: ").title()
    number = input("Phone number: ")
    phone[name] = number

search = input("Whose number do you want? ").title()
if search in phone:
    print(search, ":", phone[search])
else:
    print(search, "is not in the phone book")
'''),
    ]),
    ("File handling (student records)", [
        ("1. Write records to a file", '''\
# Saves student records in students.txt, one student per line:
#   name,class,english,maths,science
# Save your program first so you know which folder the file goes into.

f = open("students.txt", "w")      # "w" = write (starts a new file)

n = int(input("How many students? "))
for i in range(n):
    print("Student", i + 1)
    name = input("  Name: ")
    grade = input("  Class: ")
    english = input("  English marks: ")
    maths = input("  Maths marks: ")
    science = input("  Science marks: ")
    f.write(name + "," + grade + "," + english + "," + maths + "," + science + "\\n")

f.close()
print("Saved", n, "records in students.txt")
'''),
        ("2. Read and show all records", '''\
# Run "1. Write records to a file" first.
f = open("students.txt", "r")      # "r" = read

print("Name".ljust(12), "Class", "Eng", "Maths", "Sci", "Total", sep="\\t")
for line in f:
    name, grade, eng, maths, sci = line.strip().split(",")
    total = int(eng) + int(maths) + int(sci)
    print(name.ljust(12), grade, eng, maths, sci, total, sep="\\t")

f.close()
'''),
        ("3. Add more records", '''\
f = open("students.txt", "a")      # "a" = append (adds to the end)

name = input("Name: ")
grade = input("Class: ")
english = input("English marks: ")
maths = input("Maths marks: ")
science = input("Science marks: ")
f.write(name + "," + grade + "," + english + "," + maths + "," + science + "\\n")

f.close()
print("Record added.")
'''),
        ("4. Show students who passed", '''\
# Pass = 35 or more in every subject.
f = open("students.txt", "r")

print("Students who passed:")
for line in f:
    name, grade, eng, maths, sci = line.strip().split(",")
    if int(eng) >= 35 and int(maths) >= 35 and int(sci) >= 35:
        print(" -", name)

f.close()
'''),
        ("5. Search a student", '''\
search = input("Enter the name to search: ").lower()

found = False
with open("students.txt", "r") as f:   # "with" closes the file for you
    for line in f:
        name, grade, eng, maths, sci = line.strip().split(",")
        if name.lower() == search:
            print("Found:", name, "| Class", grade, "| Marks:", eng, maths, sci)
            found = True

if not found:
    print("No student called", search)
'''),
        ("6. Count records", '''\
count = 0
with open("students.txt", "r") as f:
    for line in f:
        if line.strip() != "":
            count = count + 1

print("There are", count, "records in students.txt")
'''),
    ]),
    ("Handling errors (try / except)", [
        ("Ask again until a number is typed", '''\
while True:
    try:
        age = int(input("Enter your age: "))
        break                         # it worked, leave the loop
    except ValueError:
        print("That is not a whole number. Please try again.")

print("Next year you will be", age + 1)
'''),
        ("Safe division", '''\
try:
    a = float(input("First number: "))
    b = float(input("Second number: "))
    print("Answer:", a / b)
except ValueError:
    print("Please type numbers only.")
except ZeroDivisionError:
    print("You cannot divide by zero.")
finally:
    print("Thank you!")              # finally runs every time
'''),
        ("File that may not exist", '''\
try:
    f = open("students.txt", "r")
    print(f.read())
    f.close()
except FileNotFoundError:
    print("students.txt does not exist yet.")
    print("Run the example 'Write records to a file' first.")
'''),
    ]),
]
