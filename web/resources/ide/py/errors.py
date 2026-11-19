"""Explain Python errors in simple words (English and Nepali).

``explain(info, source)`` takes the dict made by ``_shared.exception_info``
and the program's source code, and returns a ``Help`` with a short title,
an explanation and a hint in both languages.
"""

import builtins
import difflib
import re

BLOCK_WORDS = ("if", "elif", "else", "for", "while", "def", "class", "try", "except", "finally", "with")


class Help:
    def __init__(self, title, en, ne, hint_en="", hint_ne=""):
        self.title = title
        self.en = en
        self.ne = ne
        self.hint_en = hint_en
        self.hint_ne = hint_ne

    def __repr__(self):
        return "Help({!r})".format(self.title)


def _names_in(source):
    names = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source))
    names.update(dir(builtins))
    return names


def _did_you_mean(name, source):
    choices = [n for n in _names_in(source) if n != name and not n.startswith("_")]
    lower = [n for n in choices if n.lower() == name.lower()]
    if lower:
        return lower[0]
    close = difflib.get_close_matches(name, choices, n=1, cutoff=0.75)
    return close[0] if close else None


def _line(source, lineno):
    if not lineno:
        return ""
    lines = source.splitlines()
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1]
    return ""


def explain(info, source=""):
    kind = info.get("type", "")
    msg = info.get("msg", "") or ""
    text = info.get("text")
    if text is None:
        text = _line(source, info.get("line"))
    text = text or ""
    handler = _HANDLERS.get(kind)
    result = handler(msg, text, source, info) if handler else None
    return result or _generic(kind, msg)


# -- syntax --------------------------------------------------------------------


def _syntax(msg, text, source, info):
    stripped = text.strip()
    first_word = re.match(r"[A-Za-z_]+", stripped)
    first_word = first_word.group(0) if first_word else ""
    m = msg.lower()

    if re.search(r"[“”‘’]", text) or "invalid character" in m:
        return Help(
            "Strange character in your code",
            "There is a character Python does not understand. Curly quotes "
            "“ ” or ‘ ’ often come from copying code from Word "
            "or a website.",
            "तपाईंको कोडमा Python ले नबुझ्ने अक्षर छ। Word वा वेबसाइटबाट कपी गर्दा यस्तो हुन्छ।",
            'Delete the quotes and type them again with the keyboard: " or \'',
            'उद्धरण चिन्ह मेटाएर किबोर्डबाट फेरि टाइप गर्नुहोस्: " वा \'',
        )

    if "missing parentheses in call to 'print'" in m or (
        first_word == "print" and not stripped[5:].lstrip().startswith("(")
    ):
        return Help(
            "print needs brackets ( )",
            "In Python 3, print is a function, so what you want to print must "
            "go inside round brackets.",
            "Python 3 मा print एउटा function हो, त्यसैले छाप्नुपर्ने कुरा ( ) भित्र लेख्नुपर्छ।",
            'Write it like this: print("Hello")',
            'यसरी लेख्नुहोस्: print("Hello")',
        )

    if "string literal" in m or "eol while scanning" in m or "eof while scanning triple" in m:
        return Help(
            "A text (string) is not closed",
            "Text in Python starts and ends with a quote mark. One of your "
            "quote marks is missing its partner.",
            "Python मा कुनै पनि text उद्धरण चिन्ह (\" \") भित्र हुनुपर्छ। एउटा उद्धरण चिन्ह बन्द गरिएको छैन।",
            'Check that every " has a closing ", like "Namaste"',
            'हरेक " को बन्द गर्ने " छ कि हेर्नुहोस्, जस्तै "Namaste"',
        )

    if "was never closed" in m or "unexpected eof" in m or "'(' was never closed" in m:
        return Help(
            "A bracket is not closed",
            "You opened a bracket ( [ or { but did not close it. Every opening "
            "bracket needs a closing bracket.",
            "तपाईंले ( [ वा { खोल्नुभयो तर बन्द गर्नुभएन। हरेक खुल्ने कोष्ठकको बन्द गर्ने कोष्ठक चाहिन्छ।",
            "Count the ( and ) on this line and the line above. They must be equal.",
            "यो र माथिको लाइनमा ( र ) गन्नुहोस्। दुवै बराबर हुनुपर्छ।",
        )

    if "unmatched" in m or "does not match opening" in m:
        return Help(
            "Brackets do not match",
            "There is a closing bracket ) ] or } without a matching opening "
            "bracket, or the bracket types are mixed up.",
            "बन्द गर्ने कोष्ठकको जोडी मिलेन, वा फरक किसिमका कोष्ठक मिसिएका छन्।",
            "( goes with ), [ goes with ], { goes with }",
            "( को जोडी ), [ को जोडी ], { को जोडी }",
        )

    if first_word in BLOCK_WORDS and ":" not in stripped.split("#")[0]:
        return Help(
            "Colon : is missing",
            "Lines that start with {} must end with a colon :".format(first_word),
            "{} बाट सुरु हुने लाइनको अन्त्यमा कोलन : हुनुपर्छ।".format(first_word),
            "Example:  if age >= 18:",
            "उदाहरण:  if age >= 18:",
        )

    if first_word in ("if", "elif", "while") and re.search(r"[^=!<>]=[^=]", stripped):
        return Help(
            "Use == to compare",
            "A single = puts a value into a variable. To check if two things "
            "are equal, use two equal signs ==",
            "एउटा = ले variable मा मान राख्छ। दुई चीज बराबर छ कि हेर्न == प्रयोग गर्नुहोस्।",
            "Example:  if marks == 100:",
            "उदाहरण:  if marks == 100:",
        )

    if "cannot assign" in m or "can't assign" in m:
        return Help(
            "Wrong side of =",
            "The variable name must be on the left of = and the value on the "
            "right. You also cannot store a value into a number or a text.",
            "= को बायाँ variable को नाम र दायाँ मान हुनुपर्छ।",
            "Example:  total = a + b   (not  a + b = total)",
            "उदाहरण:  total = a + b   (a + b = total होइन)",
        )

    if re.search(r"\b\d+[A-Za-z_]", stripped) and "invalid" in m:
        return Help(
            "A name cannot start with a number",
            "Variable names can have letters, numbers and _ but must not start "
            "with a number. Also, Python needs * to multiply: write 2*x, not 2x.",
            "Variable को नाम अङ्कबाट सुरु हुन सक्दैन। गुणा गर्न * चाहिन्छ: 2x होइन 2*x लेख्नुहोस्।",
        )

    return Help(
        "Python cannot understand this line",
        "Something in this line is not written the way Python expects. Look "
        "carefully for a missing comma, bracket, quote or colon.",
        "यो लाइन Python ले बुझ्ने तरिकाले लेखिएको छैन। कमा (,), कोष्ठक, उद्धरण चिन्ह वा कोलन (:) छुटेको छ कि हेर्नुहोस्।",
        "The mistake is often at the end of the line above.",
        "गल्ती धेरैजसो माथिको लाइनको अन्त्यमा हुन्छ।",
    )


def _indentation(msg, text, source, info):
    m = msg.lower()
    if "expected an indented block" in m:
        return Help(
            "Space missing at the start of the line",
            "After a line that ends with a colon :, the next lines must move "
            "to the right (indent) by 4 spaces.",
            "कोलन (:) भएको लाइनपछिका लाइनहरू ४ स्पेस दायाँ सार्नुपर्छ (indent)।",
            "Press Tab at the start of the line to add 4 spaces.",
            "लाइनको सुरुमा Tab थिच्नुहोस्।",
        )
    if "unexpected indent" in m:
        return Help(
            "Extra space at the start of the line",
            "This line starts further to the right than it should. Only lines "
            "inside if, for, while or def should have spaces in front.",
            "यो लाइनको सुरुमा अनावश्यक स्पेस छ। if, for, while वा def भित्रका लाइनमा मात्र स्पेस हुन्छ।",
            "Remove the spaces at the start of this line.",
            "यो लाइनको सुरुको स्पेस मेटाउनुहोस्।",
        )
    return Help(
        "Spaces at the start of lines do not line up",
        "Lines in the same block must start at exactly the same place. "
        "Mixing Tab and spaces can also cause this.",
        "एउटै भागका लाइनहरू एकै ठाउँबाट सुरु हुनुपर्छ।",
        "Use 4 spaces for each level.",
        "हरेक तहमा ४ स्पेस प्रयोग गर्नुहोस्।",
    )


# -- runtime -------------------------------------------------------------------


def _name(msg, text, source, info):
    m = re.search(r"name '([^']+)' is not defined", msg)
    if not m:
        return None
    name = m.group(1)
    guess = _did_you_mean(name, source)
    if guess and guess.lower() == name.lower():
        hint_en = "Python cares about capital letters. Did you mean {}?".format(guess)
        hint_ne = "Python मा ठूलो र सानो अक्षर फरक हुन्छ। के तपाईंले {} भन्न खोज्नुभएको?".format(guess)
    elif guess:
        hint_en = "Did you mean {}? Check the spelling.".format(guess)
        hint_ne = "के तपाईंले {} भन्न खोज्नुभएको? हिज्जे हेर्नुहोस्।".format(guess)
    else:
        hint_en = ('If {0} is meant to be text, put it in quotes: "{0}". If it is a '
                   "variable, give it a value first, e.g. {0} = 0").format(name)
        hint_ne = ('{0} text हो भने उद्धरण चिन्हमा राख्नुहोस्: "{0}"। Variable हो भने पहिले मान दिनुहोस्, जस्तै {0} = 0').format(name)
    return Help(
        "Python does not know '{}'".format(name),
        "You used the name {} but Python has never seen it before. Maybe it "
        "is spelled wrongly, or you used it before giving it a value.".format(name),
        "तपाईंले {} प्रयोग गर्नुभयो तर Python ले यो नाम चिन्दैन। हिज्जे गलत भयो, वा मान नदिई प्रयोग गर्नुभयो।".format(name),
        hint_en,
        hint_ne,
    )


def _unbound(msg, text, source, info):
    m = re.search(r"'([^']+)'", msg)
    name = m.group(1) if m else "?"
    return Help(
        "'{}' is used before it has a value".format(name),
        "Inside this function, {0} is changed, so Python treats it as a new "
        "variable of the function. But it is used before it gets a value.".format(name),
        "यो function भित्र {0} लाई मान नदिई प्रयोग गरियो।".format(name),
        "Give {0} a value at the start of the function, or pass it in as a "
        "parameter.".format(name),
        "Function को सुरुमा {0} लाई मान दिनुहोस्, वा parameter को रूपमा पठाउनुहोस्।".format(name),
    )


def _type(msg, text, source, info):
    m = msg.lower()
    if "can only concatenate str" in m or ("unsupported operand" in m and "str" in m) or (
        "not supported between instances of 'str'" in m
    ) or ("not supported between instances of" in m and "'str'" in m):
        return Help(
            "Mixing text and numbers",
            "You tried to join or compare text with a number. Remember: input() "
            "always gives text, even when you type a number.",
            "तपाईंले text र संख्या मिसाउनुभयो। याद राख्नुहोस्: input() ले सधैं text दिन्छ, अङ्क टाइप गरे पनि।",
            "Use int(input()) or float(input()) to get a number. To join a number "
            "to text use str(number), or use a comma in print: print(\"Total:\", total)",
            "संख्या चाहिए int(input()) वा float(input()) प्रयोग गर्नुहोस्। print मा कमा प्रयोग गर्न सक्नुहुन्छ: print(\"Total:\", total)",
        )
    if "unsupported operand" in m:
        return Help(
            "These values cannot be used together",
            "The math sign (+ - * /) does not work with these kinds of values.",
            "यी मानहरूसँग यो गणितको चिन्ह (+ - * /) काम गर्दैन।",
            "Check what is inside each variable in the Variables panel.",
            "Variables प्यानलमा हरेक variable मा के छ हेर्नुहोस्।",
        )
    if "object is not callable" in m:
        return Help(
            "This is not a function",
            "You put ( ) after something that is not a function. Maybe you used "
            "a function name (like print or sum) as a variable name.",
            "तपाईंले function नभएको चीजपछि ( ) लगाउनुभयो। सायद print वा sum जस्ता नामलाई variable बनाउनुभयो।",
            "Don't name your variables print, input, sum, max, min, list or str.",
            "print, input, sum, max, min, list, str जस्ता नाम variable लाई नदिनुहोस्।",
        )
    if "positional argument" in m or "required" in m:
        return Help(
            "Wrong number of values given to a function",
            "The function needs a different number of values inside its "
            "brackets than you gave it.",
            "Function लाई चाहिने भन्दा फरक संख्यामा मान दिनुभयो।",
            "Look at the def line of the function to see how many it needs.",
            "Function को def लाइन हेरेर कति चाहिन्छ थाहा पाउनुहोस्।",
        )
    return None


def _value(msg, text, source, info):
    m = re.search(r"invalid literal for int\(\) with base 10: (.*)", msg)
    if m or "could not convert string to float" in msg:
        typed = m.group(1) if m else msg.split(":", 1)[-1].strip()
        return Help(
            "That is not a number",
            "The program wanted a number, but got {}.".format(typed),
            "प्रोग्रामलाई अङ्क चाहिएको थियो, तर {} पायो।".format(typed),
            "Type only digits like 25. For decimal numbers like 2.5 use "
            "float(input()) instead of int(input()).",
            "25 जस्ता अङ्क मात्र टाइप गर्नुहोस्। 2.5 जस्ता दशमलव संख्याको लागि float(input()) प्रयोग गर्नुहोस्।",
        )
    return None


def _zero(msg, text, source, info):
    return Help(
        "Cannot divide by zero",
        "You divided a number by 0. That is not possible in maths, so Python stops.",
        "कुनै पनि संख्यालाई शून्य (0) ले भाग गर्न मिल्दैन।",
        "Use an if to check that the number is not 0 before dividing.",
        "भाग गर्नुअघि if ले संख्या 0 होइन भनी जाँच गर्नुहोस्।",
    )


def _index(msg, text, source, info):
    return Help(
        "Position is outside the list",
        "You asked for an item at a position that does not exist. In a list "
        "of 5 items, the positions are 0, 1, 2, 3 and 4.",
        "लिस्टमा नभएको स्थानको वस्तु माग्नुभयो। ५ वटा वस्तु भएको लिस्टमा स्थान 0 देखि 4 सम्म हुन्छ।",
        "Counting starts at 0. The last position is len(list) - 1.",
        "गन्ती 0 बाट सुरु हुन्छ। अन्तिम स्थान len(list) - 1 हो।",
    )


def _key(msg, text, source, info):
    return Help(
        "Key {} is not in the dictionary".format(msg),
        "You looked up a key that the dictionary does not have.",
        "Dictionary मा नभएको key खोज्नुभयो।",
        "Check the spelling and capital letters of the key.",
        "Key को हिज्जे र ठूलो/सानो अक्षर हेर्नुहोस्।",
    )


def _attribute(msg, text, source, info):
    m = re.search(r"'(\w+)' object has no attribute '(\w+)'", msg)
    what = "'{}' cannot do '{}'".format(m.group(1), m.group(2)) if m else "Unknown action"
    return Help(
        what,
        "You used a dot . to do something this kind of value cannot do. "
        "Maybe the name after the dot is misspelled.",
        "डट (.) पछि लेखेको काम यो मानले गर्न सक्दैन। हिज्जे गलत हुन सक्छ।",
        "Example: \"hello\".upper() works, but \"hello\".uper() does not.",
        "उदाहरण: \"hello\".upper() चल्छ, \"hello\".uper() चल्दैन।",
    )


def _module(msg, text, source, info):
    m = re.search(r"No module named '([^']+)'", msg)
    name = m.group(1) if m else "?"
    return Help(
        "Module '{}' is not installed".format(name),
        "Python could not find a module called {}. Maybe the name is spelled "
        "wrongly, or it is not installed on this computer.".format(name),
        "{} नामको module भेटिएन। हिज्जे गलत छ, वा यो कम्प्युटरमा इन्स्टल छैन।".format(name),
        "Modules that are always available: math, random, turtle, time.",
        "सधैं उपलब्ध module: math, random, turtle, time।",
    )


def _recursion(msg, text, source, info):
    return Help(
        "A function keeps calling itself forever",
        "Your function calls itself again and again and never stops.",
        "तपाईंको function ले आफैंलाई बारम्बार बोलाइरहेको छ र कहिल्यै रोकिँदैन।",
        "Add an if that stops it, for example: if n == 0: return 1",
        "रोक्ने if थप्नुहोस्, जस्तै: if n == 0: return 1",
    )


def _eof(msg, text, source, info):
    return Help(
        "No input was given",
        "The program was waiting for you to type something, but the input ended.",
        "प्रोग्रामले तपाईंले टाइप गर्ने पर्खाइमा थियो, तर input समाप्त भयो।",
    )


def _file(msg, text, source, info):
    return Help(
        "File not found",
        "Python could not find the file. The file must be in the same folder "
        "as your program, and the name must match exactly.",
        "Python ले फाइल भेट्टाएन। फाइल तपाईंको प्रोग्राम भएकै फोल्डरमा हुनुपर्छ।",
        "Save your program first, then put the file next to it.",
        "पहिले प्रोग्राम Save गर्नुहोस्, अनि फाइल सोही फोल्डरमा राख्नुहोस्।",
    )


def _generic(kind, msg):
    return Help(
        "Error: {}".format(kind or "unknown"),
        "Python stopped your program because something went wrong on this line.",
        "यो लाइनमा केही गल्ती भएकोले Python ले प्रोग्राम रोक्यो।",
        "Read the line carefully, or try Step mode to watch what happens.",
        "लाइन ध्यानले पढ्नुहोस्, वा Step mode मा के हुन्छ हेर्नुहोस्।",
    )


_HANDLERS = {
    "SyntaxError": _syntax,
    "IndentationError": _indentation,
    "TabError": _indentation,
    "NameError": _name,
    "UnboundLocalError": _unbound,
    "TypeError": _type,
    "ValueError": _value,
    "ZeroDivisionError": _zero,
    "IndexError": _index,
    "KeyError": _key,
    "AttributeError": _attribute,
    "ModuleNotFoundError": _module,
    "ImportError": _module,
    "RecursionError": _recursion,
    "EOFError": _eof,
    "FileNotFoundError": _file,
}

