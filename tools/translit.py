#!/usr/bin/env python3
"""Транслитерация названий из узбекской кириллицы в латиницу.

to_latin(text)                    - узбекская латиница (алфавит 1995, с oʻ и gʻ через U+02BB, tutuq belgisi U+02BC);
to_latin(text, karakalpak=True)   - каракалпакская латиница (á ó ú ń ǵ ı w) для названий в Каракалпакстане.
Латинские буквы, цифры и знаки проходят без изменений. Код распространяется по лицензии MIT (см. LICENSE).
"""

OKINA = "ʻ"   # ʻ  (oʻ, gʻ)
TUTUQ = "ʼ"   # ʼ  (tutuq belgisi)

UZ = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": TUTUQ, "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya", "ў": "o" + OKINA, "қ": "q", "ғ": "g" + OKINA, "ҳ": "h",
    # буквы каракалпакской кириллицы в узбекском тексте: ближайшие узбекские буквы
    "ә": "a", "ө": "o" + OKINA, "ү": "u", "ң": "ng",
}
KK = dict(UZ, **{"ә": "á", "ө": "ó", "ү": "ú", "ң": "ń", "ғ": "ǵ", "ў": "w", "ы": "ı"})
VOWELS = set("аеёиоуўэюяыәөү")


def _letter(ch):
    return ch.isalpha()


def to_latin(text, karakalpak=False):
    table = KK if karakalpak else UZ
    out = []
    for i, ch in enumerate(text):
        low = ch.lower()
        if low not in table:
            out.append(ch)
            continue
        lat = table[low]
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if low == "е" and (not _letter(prev) or prev.lower() in VOWELS or prev.lower() in "ъь"):
            lat = "ye"
        if karakalpak and low == "и" and ch.isupper():
            lat = "i"
        if ch.isupper() and lat:
            if len(lat.replace(OKINA, "").replace(TUTUQ, "")) == 1:
                lat = lat[0].upper() + lat[1:]
            elif (_letter(prev) and prev.isupper()) or (_letter(nxt) and nxt.isupper()):
                lat = lat.upper()
            else:
                lat = lat[0].upper() + lat[1:]
            if karakalpak and low == "и":
                lat = "İ"
        out.append(lat)
    return "".join(out)
