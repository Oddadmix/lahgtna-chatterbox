import re
from typing import Callable, Tuple

# ----------------------------
# Core lexicon (Saudi/Gulf Arabic)
# ----------------------------

_AR_DIGITS = {
    0: "صفر", 1: "واحد", 2: "اثنين", 3: "ثلاثة", 4: "أربعة", 5: "خمسة",
    6: "ستة", 7: "سبعة", 8: "ثمانية", 9: "تسعة", 10: "عشرة",
    11: "أحد عشر", 12: "اثنا عشر", 13: "ثلاثة عشر", 14: "أربعة عشر",
    15: "خمسة عشر", 16: "ستة عشر", 17: "سبعة عشر", 18: "ثمانية عشر",
    19: "تسعة عشر"
}

_AR_TENS = {
    20: "عشرون", 30: "ثلاثون", 40: "أربعون", 50: "خمسون",
    60: "ستون", 70: "سبعون", 80: "ثمانون", 90: "تسعون"
}

# Accusative/genitive form of tens (used after "و")
_AR_TENS_ACC = {
    20: "عشرين", 30: "ثلاثين", 40: "أربعين", 50: "خمسين",
    60: "ستين", 70: "سبعين", 80: "ثمانين", 90: "تسعين"
}

_AR_HUNDREDS = {
    100: "مئة", 200: "مئتان", 300: "ثلاثمئة", 400: "أربعمئة",
    500: "خمسمئة", 600: "ستمئة", 700: "سبعمئة",
    800: "ثمانمئة", 900: "تسعمئة"
}

_SCALES = [
    (1_000_000_000, "مليار", "ملياران", "مليارات"),
    (1_000_000,     "مليون", "مليونان", "ملايين"),
    (1_000,         "ألف",   "ألفان",   "آلاف"),
]

# Arabic-Indic digit mapping
_ARABIC_TO_WESTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

DECIMAL_WORD  = "فاصلة"
PERCENT_WORD  = "بالمئة"

# Currency: (singular, dual, plural, minor_sg, minor_du, minor_pl)
CURRENCY = {
    "SAR": ("ريال", "ريالان", "ريالات", "هللة", "هللتان", "هللات"),
    "ر.س": ("ريال", "ريالان", "ريالات", "هللة", "هللتان", "هللات"),
    "ريال": ("ريال", "ريالان", "ريالات", "هللة", "هللتان", "هللات"),
    "$":   ("دولار", "دولاران", "دولارات", "سنت", "سنتان", "سنتات"),
    "USD": ("دولار", "دولاران", "دولارات", "سنت", "سنتان", "سنتات"),
    "€":   ("يورو", "يوروان", "يوروات", "سنت", "سنتان", "سنتات"),
    "EUR": ("يورو", "يوروان", "يوروات", "سنت", "سنتان", "سنتات"),
    "£":   ("جنيه", "جنيهان", "جنيهات", "بنس", "بنسان", "بنسات"),
    "GBP": ("جنيه", "جنيهان", "جنيهات", "بنس", "بنسان", "بنسات"),
    "AED": ("درهم", "درهمان", "دراهم",  "فلس", "فلسان",  "فلوس"),
    "KWD": ("دينار", "ديناران", "دنانير", "فلس", "فلسان",  "فلوس"),
}

# Ordinal numbers
_AR_ORDINALS = {
    1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع", 5: "الخامس",
    6: "السادس", 7: "السابع", 8: "الثامن", 9: "التاسع", 10: "العاشر",
    11: "الحادي عشر", 12: "الثاني عشر", 13: "الثالث عشر",
    14: "الرابع عشر", 15: "الخامس عشر",
}

# Hijri month names (primary for Saudi context)
_HIJRI_MONTHS = {
    1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الثاني",
    5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
    9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
}

# Gregorian month names
_GREGORIAN_MONTHS = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
    7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
}

# Supported emotive tags
TAG_PATTERN = re.compile(
    r'\[(pause|laugh|cry|weep|sob|scream|shout|whisper|sigh|gasp|groan|moan|hes|stutter|breath|sniff|cough|throat_clear)\]'
)


# ----------------------------
# Helper utilities
# ----------------------------

def clean_tags(text: str) -> str:
    """Convert [tag] → <tag> for supported emotive tokens."""
    if not text:
        return text
    return TAG_PATTERN.sub(r'<\1>', text)


def normalize_arabic_digits(text: str) -> str:
    """Convert Arabic-Indic digits (٠-٩) to Western digits (0-9)."""
    return text.translate(_ARABIC_TO_WESTERN)


def get_plural_form(n: int, singular: str, dual: str, plural: str) -> str:
    """Return the appropriate Arabic plural form based on the number."""
    if n == 1:
        return singular
    elif n == 2:
        return dual
    else:
        return plural


# ----------------------------
# Number → Saudi Arabic words
# ----------------------------

def int_to_saudi_words(n: int) -> str:
    """
    Convert a non-negative integer to Saudi/MSA Arabic words.
    Uses accusative case for natural TTS flow.
    """
    if n < 0:
        return "سالب " + int_to_saudi_words(-n)
    if n in _AR_DIGITS:
        return _AR_DIGITS[n]
    if n < 100:
        tens = (n // 10) * 10
        ones = n % 10
        if ones == 0:
            return _AR_TENS_ACC[tens]
        # e.g. "خمسة وعشرين"
        return f"{_AR_DIGITS[ones]} و{_AR_TENS_ACC[tens]}"
    if n < 1000:
        hundreds = (n // 100) * 100
        rest = n % 100
        base = _AR_HUNDREDS[hundreds]
        if rest == 0:
            return base
        return f"{base} و{int_to_saudi_words(rest)}"

    for scale_value, scale_sg, scale_du, scale_pl in _SCALES:
        if n >= scale_value:
            major = n // scale_value
            rest  = n % scale_value

            if major == 1:
                major_words = scale_sg          # "ألف"
            elif major == 2:
                major_words = scale_du          # "ألفان"
            elif 3 <= major <= 10:
                major_words = f"{int_to_saudi_words(major)} {scale_pl}"   # "ثلاثة آلاف"
            else:
                major_words = f"{int_to_saudi_words(major)} {scale_sg}"   # "أحد عشر ألف"

            if rest:
                major_words += f" و{int_to_saudi_words(rest)}"
            return major_words

    return str(n)


def num_token_to_words(token: str) -> str:
    """
    Convert a numeric token to Saudi Arabic words.
    Handles integers and decimals (dot or comma separator).
    """
    t = normalize_arabic_digits(token)
    t = t.replace("٬", "").replace(",", ".")

    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return token

    neg = t.startswith("-")
    if neg:
        t = t[1:]

    if "." in t:
        a, b = t.split(".", 1)
        a_words = int_to_saudi_words(int(a)) if a else "صفر"
        b_words = " ".join(_AR_DIGITS[int(ch)] for ch in b if ch.isdigit())
        out = f"{a_words} {DECIMAL_WORD} {b_words}".strip()
    else:
        out = int_to_saudi_words(int(t))

    return ("سالب " + out) if neg else out


# ----------------------------
# Specific pattern normalizers
# ----------------------------

def normalize_percent(text: str) -> str:
    """Convert percentage expressions: '25%' → 'خمسة وعشرون بالمئة'."""
    def repl(m):
        num = m.group("num")
        return f"{num_token_to_words(num)} {PERCENT_WORD}"

    return re.sub(
        r"(?P<num>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)\s*[%٪]+",
        repl,
        text
    )


def normalize_currency(text: str) -> str:
    """
    Convert currency expressions with proper pluralization.
    Handles: '100 SAR', '100 ر.س', '$12.50', '€30'
    """
    def sym_first(m):
        sym = m.group("sym")
        num = m.group("num")
        if sym not in CURRENCY:
            return m.group(0)

        major_sg, major_du, major_pl, minor_sg, minor_du, minor_pl = CURRENCY[sym]
        t = normalize_arabic_digits(num).replace(",", ".")

        if "." in t:
            a, b = t.split(".", 1)
            a_i = int(a) if a else 0
            b2  = (b + "00")[:2]
            b_i = int(b2)
            major_word = get_plural_form(a_i, major_sg, major_du, major_pl)
            if b_i == 0:
                return f"{int_to_saudi_words(a_i)} {major_word}"
            minor_word = get_plural_form(b_i, minor_sg, minor_du, minor_pl)
            return f"{int_to_saudi_words(a_i)} {major_word} و{int_to_saudi_words(b_i)} {minor_word}"

        a_i = int(t)
        major_word = get_plural_form(a_i, major_sg, major_du, major_pl)
        return f"{num_token_to_words(num)} {major_word}"

    # Symbol-first: $100, €30
    text = re.sub(
        r"(?P<sym>[$€£])\s*(?P<num>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)",
        sym_first,
        text
    )

    def num_first(m):
        num = m.group("num")
        cur = m.group("cur").strip()
        if cur not in CURRENCY:
            return m.group(0)

        major_sg, major_du, major_pl, minor_sg, minor_du, minor_pl = CURRENCY[cur]
        t = normalize_arabic_digits(num).replace(",", ".")

        if "." in t:
            a, b = t.split(".", 1)
            a_i = int(a) if a else 0
            b2  = (b + "00")[:2]
            b_i = int(b2)
            major_word = get_plural_form(a_i, major_sg, major_du, major_pl)
            if b_i == 0:
                return f"{int_to_saudi_words(a_i)} {major_word}"
            minor_word = get_plural_form(b_i, minor_sg, minor_du, minor_pl)
            return f"{int_to_saudi_words(a_i)} {major_word} و{int_to_saudi_words(b_i)} {minor_word}"

        n = int(t)
        major_word = get_plural_form(n, major_sg, major_du, major_pl)
        return f"{num_token_to_words(num)} {major_word}"

    # Num-first: 100 SAR, 50 ريال, 3.75 ر.س
    text = re.sub(
        r"(?P<num>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)\s*(?P<cur>SAR|AED|KWD|USD|EUR|GBP|ر\.س|ريال)",
        num_first,
        text
    )

    return text


def normalize_dates(text: str) -> str:
    """
    Convert date patterns to words.
    DD/MM/YYYY or DD/MM or YYYY-MM-DD.
    Uses Gregorian month names (Saudi context; swap for Hijri if needed).
    """
    def repl_dmy(m):
        day   = int(normalize_arabic_digits(m.group("day")))
        month = int(normalize_arabic_digits(m.group("month")))
        year  = m.group("year")

        day_word   = _AR_ORDINALS.get(day, int_to_saudi_words(day))
        month_word = _GREGORIAN_MONTHS.get(month, int_to_saudi_words(month))

        if year:
            year_word = int_to_saudi_words(int(normalize_arabic_digits(year)))
            return f"{day_word} {month_word} {year_word}"
        return f"{day_word} {month_word}"

    def repl_ymd(m):
        year  = int(normalize_arabic_digits(m.group("year")))
        month = int(normalize_arabic_digits(m.group("month")))
        day   = int(normalize_arabic_digits(m.group("day")))

        day_word   = _AR_ORDINALS.get(day, int_to_saudi_words(day))
        month_word = _GREGORIAN_MONTHS.get(month, int_to_saudi_words(month))
        year_word  = int_to_saudi_words(year)
        return f"{day_word} {month_word} {year_word}"

    # YYYY-MM-DD (ISO) — must be run before DD/MM to avoid partial matches
    text = re.sub(
        r"\b(?P<year>[\d٠-٩]{4})-(?P<month>0?[1-9]|1[0-2])-(?P<day>0?[1-9]|[12][0-9]|3[01])\b",
        repl_ymd,
        text
    )

    # DD/MM/YYYY or DD/MM (slash separator only, to avoid eating ranges with dashes)
    text = re.sub(
        r"\b(?P<day>0?[1-9]|[12][0-9]|3[01])/(?P<month>0?[1-9]|1[0-2])(?:/(?P<year>[\d٠-٩]{2,4}))?\b",
        repl_dmy,
        text
    )

    return text


def normalize_time(text: str) -> str:
    """
    Convert time expressions to natural Saudi Arabic.
    e.g. '3:00' → 'الساعة الثالثة تماماً'
         '3:15' → 'الساعة الثالثة وربع'
         '3:30' → 'الساعة الثالثة ونصف'
         '3:45' → 'الساعة الرابعة إلا ربع'
    """
    _HOUR_ORDINALS = {
        1: "الأولى", 2: "الثانية", 3: "الثالثة", 4: "الرابعة",
        5: "الخامسة", 6: "السادسة", 7: "السابعة", 8: "الثامنة",
        9: "التاسعة", 10: "العاشرة", 11: "الحادية عشرة", 12: "الثانية عشرة",
    }

    def repl(m):
        hh = int(normalize_arabic_digits(m.group("hh"))) % 12 or 12
        mm = int(normalize_arabic_digits(m.group("mm")))

        h_word = _HOUR_ORDINALS.get(hh, int_to_saudi_words(hh))

        if mm == 0:
            return f"الساعة {h_word} تماماً"
        if mm == 15:
            return f"الساعة {h_word} وربع"
        if mm == 30:
            return f"الساعة {h_word} ونصف"
        if mm == 45:
            next_h = (hh % 12) + 1
            next_word = _HOUR_ORDINALS.get(next_h, int_to_saudi_words(next_h))
            return f"الساعة {next_word} إلا ربع"
        if mm == 1:
            return f"الساعة {h_word} ودقيقة"
        if mm == 2:
            return f"الساعة {h_word} ودقيقتان"
        return f"الساعة {h_word} و{int_to_saudi_words(mm)} دقيقة"

    return re.sub(r"(?<![٠-٩\d])(?P<hh>[0-2]?[0-9]):(?P<mm>[0-5][0-9])(?!\d)", repl, text)


def normalize_ranges(text: str) -> str:
    """
    Convert numeric ranges.
    e.g. '10-20' → 'من عشرة إلى عشرين'
    """
    def repl(m):
        a, b = m.group("a"), m.group("b")
        return f"من {num_token_to_words(a)} إلى {num_token_to_words(b)}"

    return re.sub(
        r"(?<!\d)(?P<a>\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<b>\d+(?:[.,]\d+)?)(?!\d)",
        repl,
        text
    )


def normalize_phone_like(text: str) -> str:
    """
    Spell out phone numbers digit by digit.
    Recognizes Saudi mobile patterns (05X XXX XXXX) and general long sequences.
    Short digit sequences (< 7 digits) are left for plain-number handling.
    """
    def repl(m):
        s = normalize_arabic_digits(m.group(0))
        s = re.sub(r"\D", "", s)
        if len(s) < 7:
            return m.group(0)
        return " ".join(_AR_DIGITS[int(ch)] for ch in s)

    return re.sub(r"(\+?[\d٠-٩][\d٠-٩\s().\-]{6,}[\d٠-٩])", repl, text)


def normalize_abbreviations(text: str) -> str:
    """Expand common Saudi/Arabic abbreviations."""
    abbrev_map = {
        r"\bم\.":      "متر",
        r"\bكم\.":     "كيلومتر",
        r"\bكجم\.":    "كيلوجرام",
        r"\bد\.":      "دكتور",
        r"\bأ\.د\.":   "أستاذ دكتور",
        r"\bش\.":      "شارع",
        r"\bص\.ب\.":   "صندوق بريد",
        r"\bهـ\.":     "هجري",
        r"\bم\.م\.":   "المملكة العربية السعودية",
        r"\bرح\.":     "رحمه الله",
    }
    for pattern, replacement in abbrev_map.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def normalize_plain_numbers(text: str) -> str:
    """Convert remaining standalone numbers to words (last step)."""
    def repl(m):
        return num_token_to_words(m.group(0))

    return re.sub(
        r"(?<![A-Za-zا-ي])(-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)(?![A-Za-zا-ي])",
        repl,
        text
    )


# ----------------------------
# Main pipeline
# ----------------------------

def normalize_text_for_tts_saudi(text: str) -> str:
    """
    Full normalization pipeline for Saudi Arabic TTS.
    Order matters — most-specific patterns run before general ones.

    Steps:
      1. Strip & normalize Arabic-Indic digits
      2. Dates           (before ranges/plain numbers)
      3. Times
      4. Percentages
      5. Currency
      6. Ranges          (before plain numbers)
      7. Phone numbers   (before plain numbers)
      8. Abbreviations
      9. Plain numbers   (catch-all)
     10. Tag conversion  ([pause] → <pause>)
     11. Whitespace cleanup
    """
    if not text or not text.strip():
        return ""

    text = text.strip()
    text = normalize_arabic_digits(text)

    text = normalize_dates(text)
    text = normalize_time(text)
    text = normalize_percent(text)
    text = normalize_ranges(text)      # Before currency (ranges contain hyphens that confuse currency)
    text = normalize_currency(text)
    text = normalize_phone_like(text)
    text = normalize_abbreviations(text)
    text = normalize_plain_numbers(text)

    text = re.sub(r"\s+", " ", text).strip()
    return clean_tags(text)


# ----------------------------
# Quick smoke tests
# ----------------------------

if __name__ == "__main__":
    tests = [
        ("سعر الدولار اليوم 3.75 ر.س",        "currency with SAR"),
        ("الخصم 20% على جميع المنتجات",         "percent"),
        ("موعد الاجتماع 15/3/2024",             "date DD/MM/YYYY"),
        ("ISO date: 2024-03-15",                "date ISO"),
        ("الرحلة تغادر الساعة 9:00",            "time on hour"),
        ("يصل بين 3:15 و3:45",                  "time quarter/three-quarter"),
        ("السعر من 100-500 ريال",               "range"),
        ("اتصل على 0501234567",                 "Saudi mobile"),
        ("د. أحمد في ش. الملك فهد",             "abbreviations"),
        ("اشتريت 3 كتب بـ $45.99",              "USD symbol-first"),
        ("رصيدك 1500 SAR",                      "SAR num-first"),
        ("درجة الحرارة -3 درجات",               "negative number"),
        ("[pause] هل أنت جاهز؟",               "emotive tag"),
        ("٣ كيلو بـ ٢٥ ريال",                   "Arabic-Indic digits"),
        ("الفصل الثالث يبدأ من صفحة 120",       "plain number"),
    ]

    print("=" * 60)
    print("Saudi Arabic TTS Normalizer — Smoke Tests")
    print("=" * 60)
    for src, label in tests:
        result = normalize_text_for_tts_saudi(src)
        print(f"\n[{label}]")
        print(f"  IN : {src}")
        print(f"  OUT: {result}")