import re
from typing import Callable, Tuple

# ----------------------------
# Core lexicon (Tunisian Arabic)
# ----------------------------

_AR_DIGITS = {
    0: "صفر", 1: "واحد", 2: "اثنين", 3: "ثلاثة", 4: "أربعة", 5: "خمسة",
    6: "ستة", 7: "سبعة", 8: "ثمانية", 9: "تسعة", 10: "عشرة",
    11: "حداش", 12: "اثناش", 13: "ثلاثاش", 14: "أربعتاش", 15: "خمستاش",
    16: "ستاش", 17: "سبعتاش", 18: "ثمانتاش", 19: "تسعتاش"
}

_AR_TENS = {
    20: "عشرين", 30: "ثلاثين", 40: "أربعين", 50: "خمسين",
    60: "ستين", 70: "سبعين", 80: "ثمانين", 90: "تسعين"
}

_AR_HUNDREDS = {
    100: "مية", 200: "ميتين", 300: "ثلاثمية", 400: "أربعمية",
    500: "خمسمية", 600: "ستمية", 700: "سبعمية",
    800: "ثمانمية", 900: "تسعمية"
}

_SCALES = [
    (1_000_000_000, "مليار", "مليارين", "ملايير"),
    (1_000_000, "مليون", "مليونين", "ملايين"),
    (1_000, "ألف", "ألفين", "آلاف"),
]

# Arabic digit mappings
_ARABIC_TO_WESTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

DECIMAL_WORD = "فاصل" 
PERCENT_WORD = "في المية"

# Currency words: Tunisian Dinar (TND) and Millimes
CURRENCY = {
    "TND": ("دينار", "دينارين", "دينارات", "مليم", "مليمين", "مليمات"),
    "د.ت": ("دينار", "دينارين", "دينارات", "مليم", "مليمين", "مليمات"),
    "دينار": ("دينار", "دينارين", "دينارات", "مليم", "مليمين", "مليمات"),
    "$": ("دولار", "دولارين", "دولارات", "سنت", "سنتين", "سنتات"),
    "USD": ("دولار", "دولارين", "دولارات", "سنت", "سنتين", "سنتات"),
    "€": ("يورو", "يوروهين", "يوروهات", "سنت", "سنتين", "سنتات"),
    "EUR": ("يورو", "يوروهين", "يوروهات", "سنت", "سنتين", "سنتات"),
}

_AR_ORDINALS = {
    1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع", 5: "الخامس",
    6: "السادس", 7: "السابع", 8: "الثامن", 9: "التاسع", 10: "العاشر",
    11: "الحداش", 12: "الاثناش"
}

_AR_MONTHS = {
    1: "جانفي", 2: "فيفري", 3: "مارس", 4: "أفريل", 5: "ماي", 6: "جوان",
    7: "جويلية", 8: "أوت", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
}

TAG_PATTERN = re.compile(r'\[(pause|laugh|cry|weep|sob|scream|shout|whisper|sigh|gasp|groan|moan|hes|stutter|breath|sniff|cough|throat_clear)\]')

def clean_tags(text):
    if not text:
        return text
    return TAG_PATTERN.sub(r'<\1>', text)

# ----------------------------
# Helper functions
# ----------------------------

def normalize_arabic_digits(text: str) -> str:
    return text.translate(_ARABIC_TO_WESTERN)

def get_plural_form(n: int, singular: str, dual: str, plural: str) -> str:
    if n == 1:
        return singular
    elif n == 2:
        return dual
    else:
        return plural

# ----------------------------
# Number to Tunisian Arabic
# ----------------------------

def int_to_tunisian_words(n: int) -> str:
    if n < 0:
        return "إلا " + int_to_tunisian_words(-n) # "Ella" is common for minus in Tunisia
    if n < 20:
        return _AR_DIGITS[n]
    if n < 100:
        tens = (n // 10) * 10
        ones = n % 10
        if ones == 0:
            return _AR_TENS[tens]
        return f"{_AR_DIGITS[ones]} و{_AR_TENS[tens]}"
    if n < 1000:
        hundreds = (n // 100) * 100
        rest = n % 100
        if rest == 0:
            return _AR_HUNDREDS[hundreds]
        return f"{_AR_HUNDREDS[hundreds]} و{int_to_tunisian_words(rest)}"

    for scale_value, scale_singular, scale_dual, scale_plural in _SCALES:
        if n >= scale_value:
            major = n // scale_value
            rest = n % scale_value
            
            if major == 1:
                major_words = scale_singular
            elif major == 2:
                major_words = scale_dual
            elif 3 <= major <= 10:
                major_words = f"{int_to_tunisian_words(major)} {scale_plural}"
            else:
                major_words = f"{int_to_tunisian_words(major)} {scale_singular}"
            
            if rest:
                major_words += f" و{int_to_tunisian_words(rest)}"
            return major_words

    return str(n)

def num_token_to_words(token: str) -> str:
    t = normalize_arabic_digits(token)
    t = t.replace("٬", "").replace(",", ".")
    
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return token

    neg = t.startswith("-")
    if neg:
        t = t[1:]

    if "." in t:
        a, b = t.split(".", 1)
        a_words = int_to_tunisian_words(int(a)) if a else "صفر"
        b_words = " ".join(_AR_DIGITS[int(ch)] for ch in b if ch.isdigit())
        out = f"{a_words} {DECIMAL_WORD} {b_words}".strip()
    else:
        out = int_to_tunisian_words(int(t))

    return ("إلا " + out) if neg else out

# ----------------------------
# Specific pattern normalizers
# ----------------------------

def normalize_percent(text: str) -> str:
    def repl(m):
        num = m.group("num")
        return f"{num_token_to_words(num)} {PERCENT_WORD}"
    return re.sub(r"(?P<num>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)\s*[%٪]+", repl, text)

def normalize_currency(text: str) -> str:
    def sym_first(m):
        sym = m.group("sym")
        num = m.group("num")
        if sym not in CURRENCY: return m.group(0)
        
        major_sg, major_du, major_pl, minor_sg, minor_du, minor_pl = CURRENCY[sym]
        t = normalize_arabic_digits(num).replace(",", ".")
        
        if "." in t:
            a, b = t.split(".", 1)
            a_i = int(a) if a else 0
            # Tunisia uses 1000 millimes per dinar
            b_i = int((b + "000")[:3])
            
            major_word = get_plural_form(a_i, major_sg, major_du, major_pl)
            if b_i == 0:
                return f"{int_to_tunisian_words(a_i)} {major_word}"
            
            minor_word = get_plural_form(b_i, minor_sg, minor_du, minor_pl)
            return f"{int_to_tunisian_words(a_i)} {major_word} و{int_to_tunisian_words(b_i)} {minor_word}"
        
        a_i = int(t)
        major_word = get_plural_form(a_i, major_sg, major_du, major_pl)
        return f"{num_token_to_words(num)} {major_word}"

    text = re.sub(r"(?P<sym>[$€£])\s*(?P<num>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)", sym_first, text)

    def num_first(m):
        num = m.group("num")
        cur = m.group("cur").strip()
        if cur not in CURRENCY: return m.group(0)
        
        major_sg, major_du, major_pl = CURRENCY[cur][:3]
        num_normalized = normalize_arabic_digits(num).replace(",", ".")
        
        if "." not in num_normalized:
            n = int(num_normalized)
            major_word = get_plural_form(n, major_sg, major_du, major_pl)
        else:
            major_word = major_sg
        return f"{num_token_to_words(num)} {major_word}"

    return re.sub(r"(?P<num>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)\s*(?P<cur>TND|USD|EUR|د\.ت|دينار)", num_first, text)

def normalize_dates(text: str) -> str:
    def repl_slash(m):
        day = int(normalize_arabic_digits(m.group("day")))
        month = int(normalize_arabic_digits(m.group("month")))
        year = int(normalize_arabic_digits(m.group("year"))) if m.group("year") else None
        
        day_word = _AR_ORDINALS.get(day, int_to_tunisian_words(day))
        month_word = _AR_MONTHS.get(month, int_to_tunisian_words(month))
        
        if year:
            year_word = int_to_tunisian_words(year)
            return f"{day_word} {month_word} {year_word}"
        return f"{day_word} {month_word}"
    
    return re.sub(r"\b(?P<day>[\d٠-٩]{1,2})[/\-](?P<month>[\d٠-٩]{1,2})(?:[/\-](?P<year>[\d٠-٩]{2,4}))?\b", repl_slash, text)

def normalize_time(text: str) -> str:
    def repl(m):
        hh = int(normalize_arabic_digits(m.group("hh")))
        mm = int(normalize_arabic_digits(m.group("mm")))
        h_words = int_to_tunisian_words(hh)
        
        if mm == 0: return f"ماضي {h_words}" # Tunisian style: "Madhi..."
        if mm == 15: return f"{h_words} وربع"
        if mm == 30: return f"{h_words} ونص"
        if mm == 45:
            next_h = (hh + 1) % 24
            return f"{int_to_tunisian_words(next_h)} غير ربع" # "Ghir" for "minus/except"
        
        m_words = int_to_tunisian_words(mm)
        if mm == 1: return f"{h_words} ودقيقة"
        elif mm == 2: return f"{h_words} ودقيقتين"
        else: return f"{h_words} و{m_words} دقيقة"
    
    return re.sub(r"\b(?P<hh>[0-2]?[\d٠-٩]):(?P<mm>[0-5][\d٠-٩])\b", repl, text)

def normalize_ranges(text: str) -> str:
    def repl(m):
        a, b = m.group("a"), m.group("b")
        return f"من {num_token_to_words(a)} حتى لـ {num_token_to_words(b)}"
    return re.sub(r"\b(?P<a>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)\s*[-–—]\s*(?P<b>-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)\b", repl, text)

def normalize_phone_like(text: str) -> str:
    def repl(m):
        s = normalize_arabic_digits(m.group(0))
        s = re.sub(r"\D", "", s)
        if len(s) < 7: return m.group(0)
        return " ".join(_AR_DIGITS[int(ch)] for ch in s)
    return re.sub(r"(\+?[\d٠-٩][\d٠-٩\s().\-]{6,}[\d٠-٩])", repl, text)

def normalize_plain_numbers(text: str) -> str:
    def repl(m):
        return num_token_to_words(m.group(0))
    return re.sub(r"(?<![A-Za-zا-ي])(-?[\d٠-٩]+(?:[.,٫][\d٠-٩]+)?)(?![A-Za-zا-ي])", repl, text)

def normalize_abbreviations(text: str) -> str:
    abbrev_map = {
        r"\bم\.": "ميترو",
        r"\bكم\.": "كيلوميتر",
        r"\bد\.": "دكتور",
        r"\bأ\.": "أستاذ",
        r"\bص\.ب\.": "بوات بوستال", # Local term
    }
    for pattern, replacement in abbrev_map.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def normalize_text_for_tts_tunisian(text: str) -> str:
    if not text or not text.strip():
        return ""
    text = text.strip()
    text = normalize_arabic_digits(text)
    text = normalize_dates(text)
    text = normalize_time(text)
    text = normalize_percent(text)
    text = normalize_currency(text)
    text = normalize_ranges(text)
    text = normalize_phone_like(text)
    text = normalize_abbreviations(text)
    text = normalize_plain_numbers(text)
    text = re.sub(r"\s+", " ", text).strip()
    return clean_tags(text)