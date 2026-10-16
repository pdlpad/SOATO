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


KK_ONLY = set("әөүңы")  # буквы, которых нет в узбекском: признак каракалпакского слова


def _word_has_kk_letters(text, i):
    a = i
    while a > 0 and _letter(text[a - 1]):
        a -= 1
    b = i
    while b < len(text) and _letter(text[b]):
        b += 1
    return any(c.lower() in KK_ONLY for c in text[a:b])


def to_latin(text, karakalpak=False):
    """Кириллица -> латиница. В режиме karakalpak буква ў читается как w только рядом с гласной
    (таў, Наўрыз), между согласными это узбекское oʻ (Дўстлик -> Doʻstlik); заглавная И даёт İ
    только в слове с каракалпакскими буквами (ә ө ү ң ы)."""
    table = KK if karakalpak else UZ
    out = []
    prev_w = False
    for i, ch in enumerate(text):
        low = ch.lower()
        if low not in table:
            out.append(ch)
            prev_w = False
            continue
        lat = table[low]
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""
        is_w = False
        if karakalpak and low == "ў":
            if prev.lower() in VOWELS and prev.lower() != "ў":
                lat, is_w = "w", True
            else:
                lat = UZ["ў"]
        if low == "е" and (not _letter(prev) or (prev.lower() in VOWELS and not prev_w) or prev.lower() in "ъь"):
            lat = "ye"
        if ch.isupper() and lat:
            if len(lat.replace(OKINA, "").replace(TUTUQ, "")) == 1:
                lat = lat[0].upper() + lat[1:]
            elif (_letter(prev) and prev.isupper()) or (_letter(nxt) and nxt.isupper()):
                lat = lat.upper()
            else:
                lat = lat[0].upper() + lat[1:]
            if karakalpak and low == "и":
                lat = "İ" if _word_has_kk_letters(text, i) else "I"
        out.append(lat)
        prev_w = is_w
    return "".join(out)
