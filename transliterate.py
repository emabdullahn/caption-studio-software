"""Automatic Urdu -> Roman transliteration for Caption Studio.

A dictionary covers common poetry/function words exactly; anything else
falls back to a character-based mapping (Urdu script drops short vowels,
so fallback spellings are approximate). Every word can be corrected by
editing the generated plan.json and re-rendering.
"""

DICT = {
 'ہے': 'HAI', 'ہیں': 'HAIN', 'نہیں': 'NAHIN', 'کوئی': 'KOI', 'کچھ': 'KUCH',
 'میں': 'MEIN', 'نے': 'NE', 'کو': 'KO', 'کا': 'KA', 'کی': 'KI', 'کے': 'KE',
 'سے': 'SE', 'تو': 'TO', 'تم': 'TUM', 'وہ': 'WOH', 'یہ': 'YEH', 'بھی': 'BHI',
 'اور': 'AUR', 'کیا': 'KYA', 'کیوں': 'KYUN', 'کہ': 'KE', 'ایک': 'AIK',
 'میرے': 'MERE', 'تیرے': 'TERE', 'مجھے': 'MUJHE', 'تجھے': 'TUJHE',
 'ہوں': 'HOON', 'ہو': 'HO', 'تھا': 'THA', 'تھی': 'THI', 'دل': 'DIL',
 'عشق': 'ISHQ', 'دنیا': 'DUNIYA', 'دیکھا': 'DEKHA', 'کبھی': 'KABHI',
 'شام': 'SHAAM', 'بعد': 'BAAD', 'رات': 'RAAT', 'دکھ': 'DUKH',
 'معلوم': 'MALOOM', 'کہاں': 'KAHAAN', 'سورج': 'SOORAJ', 'اچھا': 'ACHHA',
 'برا': 'BURA', 'جانا': 'JANA', 'مانو': 'MANO', 'میری': 'MERI',
 'دور': 'DOOR', 'رہو': 'RAHO', 'درد': 'DARD', 'ملا': 'MILA',
 'پاگل': 'PAGAL', 'حقیقت': 'HAQEEQAT', 'فلم': 'FILM', 'غزل': 'GHAZAL',
 'آواز': 'AAWAZ', 'آتا': 'AATA', 'مناتا': 'MANAATA', 'خفا': 'KHAFA',
 'الگ': 'ALAG', 'بھاتا': 'BHAATA', 'آیا': 'AAYA', 'پاس': 'PAAS',
 'وجہ': 'WAJAH', 'ورنہ': 'WARNA', 'انا': 'ANA', 'بت': 'BUT',
 'گراتا': 'GIRAATA', 'چہرے': 'CHEHRE', 'دیکھ': 'DEKH', 'آنکھوں': 'AANKHON',
 'سمت': 'SIMT', 'اندر': 'ANDAR', 'بے': 'BE', 'بسی': 'BASI',
 'بتاتا': 'BATAATA', 'بتانا': 'BATANA', 'پڑے': 'PADE', 'گا': 'GA',
 'تجھ': 'TUJH', 'لیلہ': 'LAILA', 'لیلا': 'LAILA', 'لیلیٰ': 'LAILA', 'ہیر': 'HEER',
 'ناداں': 'NADAAN', 'علم': 'ILM', 'تمہیں': 'TUMHEIN', 'نظر': 'NAZAR',
 'شجر': 'SHAJAR', 'چپ': 'CHUP', 'چاپ': 'CHAAP', 'لگتے': 'LAGTE',
 'کتنے': 'KITNE', 'ابھی': 'ABHI', 'گھر': 'GHAR', 'روز': 'ROZ',
 'کسی': 'KISI', 'اتر': 'UTAR', 'نشیں': 'NASHEEN', 'ہم': 'HUM',
 'سر': 'SAR', 'پھروں': 'PHIRON', 'یوں': 'YUN', 'ہی': 'HI', 'رہا': 'RAHA',
 'دے': 'DE', 'طرف': 'TARAF', 'سارے': 'SAARE', 'توجہ': 'TAWAJJO',
 'کریں': 'KAREIN', 'کر': 'KAR', 'رہوں': 'RAHOON', 'آپ': 'AAP',
 'اے': 'AE', 'جھانک': 'JHAANK', 'اب': 'AB', 'تک': 'TAK', 'اگر': 'AGAR',
 'مگر': 'MAGAR', 'جب': 'JAB', 'تب': 'TAB', 'پھر': 'PHIR', 'جو': 'JO',
 'وہی': 'WOHI', 'یہی': 'YEHI', ' زندگی': 'ZINDAGI', 'زندگی': 'ZINDAGI',
 'محبت': 'MOHABBAT', 'دلبر': 'DILBAR', 'جان': 'JAAN', 'خدا': 'KHUDA',
 'اللہ': 'ALLAH', 'وقت': 'WAQT', 'لمحہ': 'LAMHA', 'خواب': 'KHWAAB',
 'آنکھ': 'AANKH', 'آنکھیں': 'AANKHEIN', 'زلف': 'ZULF', 'چاند': 'CHAAND',
 'ستارے': 'SITAARE', 'ہوا': 'HAWA', 'موسم': 'MAUSAM', 'بہار': 'BAHAAR',
 'خزاں': 'KHIZAAN', 'گل': 'GUL', 'پھول': 'PHOOL', 'یار': 'YAAR',
 'دوست': 'DOST', 'رقیب': 'RAQEEB', 'ستم': 'SITAM', 'ظلم': 'ZULM',
 'وفا': 'WAFA', 'جفا': 'JAFA', 'قسم': 'QASAM', 'وعدہ': 'WAADA',
 'انتظار': 'INTEZAAR', 'ملاقات': 'MULAQAAT', 'جدائی': 'JUDAAI',
 'تنہائی': 'TANHAAI', 'خاموشی': 'KHAAMOSHI', 'آنسو': 'AANSOO',
 'مسکراہٹ': 'MUSKURAAHAT', 'چہرہ': 'CHEHRA', 'لب': 'LAB', 'رخ': 'RUKH',
}

CHARS = {
 'ا': 'a', 'آ': 'aa', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ٹ': 't', 'ث': 's',
 'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd', 'ڈ': 'd', 'ذ': 'z',
 'ر': 'r', 'ڑ': 'r', 'ز': 'z', 'ژ': 'zh', 'س': 's', 'ش': 'sh', 'ص': 's',
 'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
 'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ں': 'n', 'ہ': 'h',
 'ۃ': 't', 'ى': 'a', 'ء': '', 'ـ': '',
}
DIACRITICS = set('ًٌٍَُِّْٰٓٔ')


def _fallback(word):
    out = []
    chars = list(word)
    for i, c in enumerate(chars):
        if c in DIACRITICS:
            continue
        if c == 'ھ':                      # aspiration marker: کھ -> kh
            out.append('h')
        elif c == 'و':
            out.append('w' if i == 0 else 'o')
        elif c == 'ی':
            out.append('y' if i == 0 else 'i')
        elif c == 'ے':
            out.append('e')
        elif c == 'ئ':
            out.append('i')
        elif c == 'ؤ':
            out.append('o')
        elif c in CHARS:
            out.append(CHARS[c])
        elif c.isalpha():
            out.append(c)
    s = ''.join(out)
    return s.upper() if s else word.upper()


def transliterate(word):
    w = word.strip().strip('،۔!؟;:"()')
    if not w:
        return ''
    if w in DICT:
        return DICT[w]
    return _fallback(w)
