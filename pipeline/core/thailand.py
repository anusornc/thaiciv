"""Canonical reference table for all 77 provinces of Thailand (DOPA / ISO 3166-2 / NESDC).

Used by every source and builder so Thai names, English spelling variants,
NESDC codes, ISO codes (TH-10..TH-96) and DOPA 2-digit codes (10..96) always
join cleanly to the exact same 77 provinces.
"""

from __future__ import annotations

import re

# (dopa_code, abbr, en_name, th_name, region, cap_lon, cap_lat)
PROVINCES: list[tuple[str, str, str, str, str, float, float]] = [
    # Bangkok & Vicinities (6)
    ("10", "BKK", "Bangkok", "กรุงเทพมหานคร", "Bangkok & Vicinities", 100.5018, 13.7563),
    ("11", "SPK", "Samut Prakan", "สมุทรปราการ", "Bangkok & Vicinities", 100.5998, 13.5991),
    ("12", "NBI", "Nonthaburi", "นนทบุรี", "Bangkok & Vicinities", 100.5147, 13.8621),
    ("13", "PTE", "Pathum Thani", "ปทุมธานี", "Bangkok & Vicinities", 100.5250, 14.0208),
    ("73", "NPT", "Nakhon Pathom", "นครปฐม", "Bangkok & Vicinities", 100.0622, 13.8196),
    ("74", "SKN", "Samut Sakhon", "สมุทรสาคร", "Bangkok & Vicinities", 100.2736, 13.5475),
    # Central (6)
    ("14", "AYA", "Phra Nakhon Si Ayutthaya", "พระนครศรีอยุธยา", "Central", 100.5693, 14.3532),
    ("15", "ATG", "Ang Thong", "อ่างทอง", "Central", 100.4550, 14.5896),
    ("16", "LRI", "Lop Buri", "ลพบุรี", "Central", 100.6534, 14.7995),
    ("17", "SBR", "Sing Buri", "สิงห์บุรี", "Central", 100.4046, 14.8936),
    ("18", "CNT", "Chai Nat", "ชัยนาท", "Central", 100.1251, 15.1852),
    ("19", "SRI", "Saraburi", "สระบุรี", "Central", 100.9101, 14.5289),
    # Eastern (8)
    ("20", "CBI", "Chon Buri", "ชลบุรี", "Eastern", 100.9847, 13.3611),
    ("21", "RYG", "Rayong", "ระยอง", "Eastern", 101.2816, 12.6814),
    ("22", "CTI", "Chanthaburi", "จันทบุรี", "Eastern", 102.1045, 12.6113),
    ("23", "TRT", "Trat", "ตราด", "Eastern", 102.5175, 12.2428),
    ("24", "CCO", "Chachoengsao", "ฉะเชิงเทรา", "Eastern", 101.0779, 13.6904),
    ("25", "PRI", "Prachin Buri", "ปราจีนบุรี", "Eastern", 101.3686, 14.0509),
    ("26", "NYK", "Nakhon Nayok", "นครนายก", "Eastern", 101.2131, 14.2069),
    ("27", "SKW", "Sa Kaeo", "สระแก้ว", "Eastern", 102.0722, 13.8240),
    # Northeastern / Isan (20)
    ("30", "NMA", "Nakhon Ratchasima", "นครราชสีมา", "Northeastern", 102.0978, 14.9799),
    ("31", "BRM", "Buri Ram", "บุรีรัมย์", "Northeastern", 103.1029, 14.9930),
    ("32", "SRN", "Surin", "สุรินทร์", "Northeastern", 103.4937, 14.8829),
    ("33", "SSK", "Si Sa Ket", "ศรีสะเกษ", "Northeastern", 104.3220, 15.1186),
    ("34", "UBN", "Ubon Ratchathani", "อุบลราชธานี", "Northeastern", 104.8473, 15.2287),
    ("35", "YST", "Yasothon", "ยโสธร", "Northeastern", 104.1453, 15.7926),
    ("36", "CPM", "Chaiyaphum", "ชัยภูมิ", "Northeastern", 102.0315, 15.8068),
    ("37", "ACR", "Amnat Charoen", "อำนาจเจริญ", "Northeastern", 104.6258, 15.8657),
    ("38", "BKN", "Bueng Kan", "บึงกาฬ", "Northeastern", 103.6464, 18.3609),
    ("39", "NBP", "Nong Bua Lam Phu", "หนองบัวลำภู", "Northeastern", 102.4260, 17.2218),
    ("40", "KKN", "Khon Kaen", "ขอนแก่น", "Northeastern", 102.8236, 16.4322),
    ("41", "UDN", "Udon Thani", "อุดรธานี", "Northeastern", 102.7872, 17.4138),
    ("42", "LEI", "Loei", "เลย", "Northeastern", 101.7223, 17.4860),
    ("43", "NKI", "Nong Khai", "หนองคาย", "Northeastern", 102.7413, 17.8783),
    ("44", "MKM", "Maha Sarakham", "มหาสารคาม", "Northeastern", 103.3007, 16.1851),
    ("45", "RET", "Roi Et", "ร้อยเอ็ด", "Northeastern", 103.6520, 16.0538),
    ("46", "KSN", "Kalasin", "กาฬสินธุ์", "Northeastern", 103.5059, 16.4314),
    ("47", "SNK", "Sakon Nakhon", "สกลนคร", "Northeastern", 104.1486, 17.1546),
    ("48", "NPM", "Nakhon Phanom", "นครพนม", "Northeastern", 104.7786, 17.4108),
    ("49", "MDH", "Mukdahan", "มุกดาหาร", "Northeastern", 104.7235, 16.5453),
    # Northern (17)
    ("50", "CMI", "Chiang Mai", "เชียงใหม่", "Northern", 98.9853, 18.7883),
    ("51", "LPN", "Lamphun", "ลำพูน", "Northern", 99.0087, 18.5745),
    ("52", "LPG", "Lampang", "ลำปาง", "Northern", 99.4909, 18.2888),
    ("53", "UTT", "Uttaradit", "อุตรดิตถ์", "Northern", 100.0993, 17.6201),
    ("54", "PRE", "Phrae", "แพร่", "Northern", 100.1403, 18.1446),
    ("55", "NAN", "Nan", "น่าน", "Northern", 100.7790, 18.7756),
    ("56", "PYO", "Phayao", "พะเยา", "Northern", 99.8788, 19.1665),
    ("57", "CRI", "Chiang Rai", "เชียงราย", "Northern", 99.8325, 19.9105),
    ("58", "MSN", "Mae Hong Son", "แม่ฮ่องสอน", "Northern", 97.9654, 19.3020),
    ("60", "NSN", "Nakhon Sawan", "นครสวรรค์", "Northern", 100.1372, 15.7047),
    ("61", "UTI", "Uthai Thani", "อุทัยธานี", "Northern", 100.0246, 15.3835),
    ("62", "KPT", "Kamphaeng Phet", "กำแพงเพชร", "Northern", 99.5227, 16.4828),
    ("63", "TAK", "Tak", "ตาก", "Northern", 99.1259, 16.8840),
    ("64", "STI", "Sukhothai", "สุโขทัย", "Northern", 99.8265, 17.0056),
    ("65", "PLK", "Phitsanulok", "พิษณุโลก", "Northern", 100.2659, 16.8211),
    ("66", "PCT", "Phichit", "พิจิตร", "Northern", 100.3488, 16.4429),
    ("67", "PNB", "Phetchabun", "เพชรบูรณ์", "Northern", 101.1591, 16.4190),
    # Western (6)
    ("70", "RBR", "Ratchaburi", "ราชบุรี", "Western", 99.8134, 13.5283),
    ("71", "KRI", "Kanchanaburi", "กาญจนบุรี", "Western", 99.5328, 14.0228),
    ("72", "SPB", "Suphan Buri", "สุพรรณบุรี", "Western", 100.1177, 14.4745),
    ("75", "SKM", "Samut Songkhram", "สมุทรสงคราม", "Western", 100.0023, 13.4098),
    ("76", "PBI", "Phetchaburi", "เพชรบุรี", "Western", 99.9577, 13.1119),
    ("77", "PKN", "Prachuap Khiri Khan", "ประจวบคีรีขันธ์", "Western", 99.7958, 11.8124),
    # Southern (14)
    ("80", "NRT", "Nakhon Si Thammarat", "นครศรีธรรมราช", "Southern", 99.9631, 8.4304),
    ("81", "KBI", "Krabi", "กระบี่", "Southern", 98.9063, 8.0863),
    ("82", "PNA", "Phang Nga", "พังงา", "Southern", 98.5255, 8.4501),
    ("83", "PKT", "Phuket", "ภูเก็ต", "Southern", 98.3923, 7.8804),
    ("84", "SNI", "Surat Thani", "สุราษฎร์ธานี", "Southern", 99.3295, 9.1382),
    ("85", "RNG", "Ranong", "ระนอง", "Southern", 98.6348, 9.9658),
    ("86", "CPN", "Chumphon", "ชุมพร", "Southern", 99.1800, 10.4930),
    ("90", "SKA", "Songkhla", "สงขลา", "Southern", 100.5951, 7.1898),
    ("91", "STN", "Satun", "สตูล", "Southern", 100.0674, 6.6238),
    ("92", "TRG", "Trang", "ตรัง", "Southern", 99.6114, 7.5563),
    ("93", "PLG", "Phatthalung", "พัทลุง", "Southern", 100.0740, 7.6167),
    ("94", "PTN", "Pattani", "ปัตตานี", "Southern", 101.2501, 6.8695),
    ("95", "YLA", "Yala", "ยะลา", "Southern", 101.2804, 6.5411),
    ("96", "NWT", "Narathiwat", "นราธิวาส", "Southern", 101.8253, 6.4255),
]

BY_CODE = {p[0]: p for p in PROVINCES}
BY_ABBR = {p[1]: p for p in PROVINCES}

_EXTRA_ALIASES = {
    "krungthepmahanakhon": "10",
    "bangkokmetropolis": "10",
    "ayutthaya": "14",
    "phranakhonsiayutthaya": "14",
    "phranakhonsiayuthaya": "14",
    "phranakhonsriayuthaya": "14",
    "phranakhonsriayutthaya": "14",
    "chonburi": "20",
    "prachinburi": "25",
    "lopburi": "16",
    "singburi": "17",
    "suphanburi": "72",
    "buriram": "31",
    "sisaket": "33",
    "si-saket": "33",
    "srisaket": "33",
    "nongbualamphu": "39",
    "nongbualumphu": "39",
    "bungkan": "38",
    "buengkan": "38",
    "phangnga": "82",
    "phang-nga": "82",
    "phetchaburi": "76",
    "phetburi": "76",
    "prachuapkhirikhan": "77",
    "prachuabkhirikhan": "77",
    "phachuapkhirikhan": "77",
    "nakhonsithammarat": "80",
    "mahasarakham": "44",
    "sakonnakhon": "47",
    "nakhonphanom": "48",
    "nakhonratchasima": "30",
    "korat": "30",
    "ubonratchathani": "34",
    "amnatcharoen": "37",
    "amnatchareon": "37",
    "sakaew": "27",
    "kamphaengphet": "62",
    "maehongson": "58",
    "samutprakan": "11",
    "samutsakhon": "74",
    "samutsongkhram": "75",
    "patumthani": "13",
    "pathumthani": "13",
    "nakhonpathom": "73",
    "nakhonnayok": "26",
    "nakhonsawan": "60",
    "uthaithani": "61",
    "suratthani": "84",
    "udonthani": "41",
    "khonkaen": "40",
    "nongkhai": "43",
    "roiet": "45",
    "sakaeo": "27",
    "angthong": "15",
    "chainat": "18",
    "chiangmai": "50",
    "chiangrai": "57",
    "phatthalung": "93",
    "patthalung": "93",
    "songkla": "90",
    "กรุงเทพ": "10",
    "กทม": "10",
    "อยุธยา": "14",
    "ศรีสะเกศ": "33",
}


def _norm(s: str) -> str:
    s = str(s).strip()
    # Strip leading NESDC 4-digit codes like "0101 KHON KAEN" or "0401 - CHON BURI"
    s = re.sub(r"^\d{4}\s*[-–]?\s*", "", s)
    # Strip Thai province prefix
    s = re.sub(r"^(จังหวัด|จ\.)\s*", "", s)
    # Strip English suffix
    s = re.sub(r"\s+province$", "", s, flags=re.I)
    s = re.sub(r"[\s\-_.'()]+", "", s).lower()
    return s


_LOOKUP: dict[str, str] = {}
for _code, _abbr, _en, _th, _reg, _lon, _lat in PROVINCES:
    _LOOKUP[_code] = _code
    _LOOKUP[f"th-{_code}"] = _code
    _LOOKUP[f"th{_code}"] = _code
    _LOOKUP[_abbr.lower()] = _code
    _LOOKUP[_norm(_en)] = _code
    _LOOKUP[_norm(_th)] = _code
_LOOKUP.update(_EXTRA_ALIASES)


def resolve_province(raw: str | int | None) -> str | None:
    """Resolve any Thai/English name, ISO code, or DOPA 2-digit code → DOPA 2-digit string ('10'..'96')."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s.isdigit() and len(s) in (1, 2):
        c = s.zfill(2)
        if c in BY_CODE:
            return c
    k = _norm(s)
    if k in _LOOKUP:
        return _LOOKUP[k]
    return None


def short_city_name(code: str) -> str:
    """Concise display name for city banners (keeps Phra Nakhon Si Ayutthaya readable as Ayutthaya)."""
    en = BY_CODE[code][2]
    if en == "Phra Nakhon Si Ayutthaya":
        return "Ayutthaya"
    return en
