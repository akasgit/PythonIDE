"""Example programs for Class 9 and 10, grouped by topic.

Teachers can add their own: put any .py file in the "examples" folder next
to the program's folder (see README) and it appears under "My examples".
"""

EXAMPLES = [
    ("1. Getting started", [
        ("Hello, Nepal!", '''\
# print() shows something on the screen.
print("Namaste!")
print("Hello, Nepal!")

# Text goes inside quotes. Numbers do not need quotes.
print("Height of Mount Everest:", 8848.86, "metres")
'''),
        ("Variables", '''\
# A variable is a box with a name that stores a value.
name = "Sita"
age = 15
height = 1.52

print("Name:", name)
print("Age:", age)
print("Height:", height, "m")

# A variable can change. Watch it in the Variables panel.
age = age + 1
print("Next year", name, "will be", age)
'''),
        ("Maths with Python", '''\
a = 17
b = 5

print("a + b =", a + b)    # add
print("a - b =", a - b)    # subtract
print("a * b =", a * b)    # multiply
print("a / b =", a / b)    # divide (gives a decimal)
print("a // b =", a // b)  # whole-number division
print("a % b =", a % b)    # remainder
print("a ** 2 =", a ** 2)  # power (a squared)
'''),
    ]),
    ("2. Input and output", [
        ("Ask your name", '''\
# input() waits for you to type something and press Enter.
name = input("What is your name? ")
school = input("Which school do you study in? ")

print("Namaste,", name + "!")
print("Welcome to Python at", school)
'''),
        ("Sum of two numbers", '''\
# input() always gives TEXT. int() changes the text into a number.
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))

total = a + b
print("Sum =", total)
'''),
        ("Simple interest", '''\
# Simple Interest  I = (P x T x R) / 100
p = float(input("Principal (Rs): "))
t = float(input("Time (years): "))
r = float(input("Rate (% per year): "))

i = (p * t * r) / 100
amount = p + i

print("Simple interest = Rs", i)
print("Total amount   = Rs", amount)
'''),
        ("Area of a circle", '''\
import math

r = float(input("Radius of the circle (cm): "))
area = math.pi * r ** 2
circumference = 2 * math.pi * r

# round(x, 2) keeps 2 digits after the decimal point.
print("Area =", round(area, 2), "sq. cm")
print("Circumference =", round(circumference, 2), "cm")
'''),
        ("Celsius to Fahrenheit", '''\
c = float(input("Temperature in Celsius: "))
f = c * 9 / 5 + 32
print(c, "C =", f, "F")
'''),
    ]),
    ("3. Decisions (if / else)", [
        ("Even or odd", '''\
n = int(input("Enter a number: "))

# % gives the remainder. Even numbers have remainder 0 when divided by 2.
if n % 2 == 0:
    print(n, "is EVEN")
else:
    print(n, "is ODD")
'''),
        ("Positive, negative or zero", '''\
n = float(input("Enter a number: "))

if n > 0:
    print("Positive")
elif n < 0:
    print("Negative")
else:
    print("Zero")
'''),
        ("Greatest of three numbers", '''\
a = int(input("First number: "))
b = int(input("Second number: "))
c = int(input("Third number: "))

if a >= b and a >= c:
    greatest = a
elif b >= a and b >= c:
    greatest = b
else:
    greatest = c

print("Greatest number is", greatest)
'''),
        ("Grade from marks", '''\
marks = float(input("Enter your marks (out of 100): "))

if marks >= 90:
    grade = "A+"
elif marks >= 80:
    grade = "A"
elif marks >= 70:
    grade = "B+"
elif marks >= 60:
    grade = "B"
elif marks >= 50:
    grade = "C+"
elif marks >= 40:
    grade = "C"
elif marks >= 35:
    grade = "D"
else:
    grade = "NG (Not Graded)"

print("Your grade is", grade)
'''),
        ("Can you vote?", '''\
age = int(input("Enter your age: "))

if age >= 18:
    print("You can vote in Nepal.")
else:
    years_left = 18 - age
    print("You can vote after", years_left, "years.")
'''),
    ]),
    ("4. Loops (for / while)", [
        ("Count 1 to 10", '''\
# range(1, 11) gives 1, 2, 3 ... 10  (it stops BEFORE 11)
for i in range(1, 11):
    print(i)

print("Done!")
'''),
        ("Multiplication table", '''\
n = int(input("Which table? "))

for i in range(1, 11):
    print(n, "x", i, "=", n * i)
'''),
        ("Sum of 1 to N", '''\
n = int(input("Enter N: "))

total = 0
for i in range(1, n + 1):
    total = total + i

print("Sum of 1 to", n, "is", total)
'''),
        ("Factorial", '''\
n = int(input("Enter a number: "))

fact = 1
for i in range(1, n + 1):
    fact = fact * i

print(n, "! =", fact)
'''),
        ("Fibonacci series", '''\
n = int(input("How many terms? "))

a, b = 0, 1
for i in range(n):
    print(a, end=" ")
    a, b = b, a + b
print()
'''),
        ("Prime or not", '''\
n = int(input("Enter a number: "))

is_prime = n > 1
for i in range(2, n):
    if n % i == 0:
        is_prime = False
        break

if is_prime:
    print(n, "is a PRIME number")
else:
    print(n, "is NOT a prime number")
'''),
        ("Reverse a number (while)", '''\
n = int(input("Enter a number: "))

reverse = 0
while n > 0:
    digit = n % 10          # last digit
    reverse = reverse * 10 + digit
    n = n // 10             # remove last digit

print("Reversed number:", reverse)
'''),
        ("Sum of digits (while)", '''\
n = int(input("Enter a number: "))

total = 0
while n > 0:
    total = total + n % 10
    n = n // 10

print("Sum of digits:", total)
'''),
        ("Guess the number", '''\
import random

secret = random.randint(1, 20)
tries = 0
guess = 0

print("I am thinking of a number between 1 and 20.")
while guess != secret:
    guess = int(input("Your guess: "))
    tries = tries + 1
    if guess < secret:
        print("Too small!")
    elif guess > secret:
        print("Too big!")

print("Correct! You got it in", tries, "tries.")
'''),
    ]),
    ("5. Strings (text)", [
        ("Text functions", '''\
word = "Kathmandu"

print(word.upper())     # KATHMANDU
print(word.lower())     # kathmandu
print(len(word))        # number of letters
print(word[0])          # first letter (position 0)
print(word[-1])         # last letter
print(word[0:5])        # letters 0 to 4
'''),
        ("Count vowels", '''\
text = input("Enter a sentence: ")

count = 0
for letter in text.lower():
    if letter in "aeiou":
        count = count + 1

print("Number of vowels:", count)
'''),
        ("Palindrome", '''\
word = input("Enter a word: ").lower()

if word == word[::-1]:
    print(word, "is a palindrome")
else:
    print(word, "is not a palindrome")
'''),
    ]),
    ("6. Lists", [
        ("List basics", '''\
districts = ["Kathmandu", "Lalitpur", "Bhaktapur"]

print(districts)
print("First:", districts[0])
print("How many:", len(districts))

districts.append("Kaski")
print("After adding:", districts)

for d in districts:
    print("-", d)
'''),
        ("Average marks", '''\
marks = []
n = int(input("How many subjects? "))

for i in range(n):
    m = float(input("Marks of subject " + str(i + 1) + ": "))
    marks.append(m)

print("Marks:", marks)
print("Total:", sum(marks))
print("Average:", sum(marks) / n)
print("Highest:", max(marks))
print("Lowest:", min(marks))
'''),
    ]),
    ("7. Functions", [
        ("My first function", '''\
def greet(name):
    print("Namaste,", name + "!")

greet("Ram")
greet("Gita")
greet("Hari")
'''),
        ("Function that returns", '''\
def area_of_rectangle(length, breadth):
    return length * breadth

l = float(input("Length: "))
b = float(input("Breadth: "))

a = area_of_rectangle(l, b)
print("Area =", a)
'''),
        ("Is it a leap year?", '''\
def is_leap(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0

y = int(input("Enter a year (AD): "))
if is_leap(y):
    print(y, "is a leap year")
else:
    print(y, "is not a leap year")
'''),
    ]),
    ("8. Turtle drawing", [
        ("Draw a square", '''\
import turtle

t = turtle.Turtle()
t.pensize(3)
t.color("blue")

for i in range(4):
    t.forward(150)
    t.left(90)
'''),
        ("Draw a star", '''\
import turtle

t = turtle.Turtle()
t.color("red")
t.pensize(2)
t.speed(3)

for i in range(5):
    t.forward(200)
    t.right(144)
'''),
        ("Colourful spiral", '''\
import turtle

t = turtle.Turtle()
t.speed(0)
colours = ["red", "blue", "green", "orange", "purple"]

for i in range(100):
    t.color(colours[i % 5])
    t.forward(i * 3)
    t.left(91)
'''),
    ]),
]

WELCOME = '''\
# Welcome to PythonIDE!
#
#   Run  (F5)  runs your program
#   Step (F6)  runs it one line at a time so you can watch the variables
#   Examples   menu has ready-made programs to try
#
# Lines starting with # are comments. Python ignores them.

name = input("What is your name? ")
print("Namaste,", name + "!")
'''
