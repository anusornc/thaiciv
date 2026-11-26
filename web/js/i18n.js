// Bilingual Thai / English (ไทย / EN) localization for thaiciv.
// Persists in localStorage ("thaiciv.lang") and syncs with URL hash (#lang=th).

const STORAGE_KEY = "thaiciv.lang";
const listeners = new Set();

function detectInitialLang() {
  try {
    const hash = new URLSearchParams(String(location.hash || "").replace(/^#/, "")).get("lang");
    if (hash === "th" || hash === "en") return hash;
    const qs = new URLSearchParams(location.search || "").get("lang");
    if (qs === "th" || qs === "en") return qs;
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "th" || saved === "en") return saved;
  } catch { /* ignore */ }
  return "en";
}

let lang = detectInitialLang();
if (typeof document !== "undefined") document.documentElement.lang = lang;

export const getLang = () => lang;
export const isTh = () => lang === "th";
export const t = (en, th) => (lang === "th" ? th : en);

export function setLang(next, { silent = false } = {}) {
  const v = next === "th" ? "th" : "en";
  if (v === lang) return false;
  lang = v;
  try { localStorage.setItem(STORAGE_KEY, lang); } catch { /* ignore */ }
  if (typeof document !== "undefined") document.documentElement.lang = lang;
  if (!silent) {
    for (const fn of [...listeners]) {
      try { fn(lang); } catch (err) { console.error("i18n listener failed", err); }
    }
  }
  return true;
}

export function toggleLang() {
  setLang(lang === "th" ? "en" : "th");
  return lang;
}

export function onLangChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// --- Place & region names --------------------------------------------------------------------------------------

export function placeName(obj) {
  if (!obj) return "";
  return lang === "th" ? (obj.th_name || obj.name || "") : (obj.name || obj.th_name || "");
}

const REGIONS_TH = {
  "Bangkok & Vicinities": "กรุงเทพฯ และปริมณฑล",
  "Northern": "ภาคเหนือ",
  "Northeastern": "ภาคตะวันออกเฉียงเหนือ",
  "Central": "ภาคกลาง",
  "Eastern": "ภาคตะวันออก",
  "Western": "ภาคตะวันตก",
  "Southern": "ภาคใต้",
};

export function regionName(r) {
  if (!r) return "";
  return lang === "th" ? (REGIONS_TH[r] || r) : r;
}

// --- Terrain & water tables ------------------------------------------------------------------------------------

const TERRAIN_TH = {
  "Land": "แผ่นดิน",
  "Ocean": "ทะเล/มหาสมุทร",
  "Coast": "ชายฝั่ง",
  "Lake": "ทะเลสาบ",
  "Flat": "ที่ราบ",
  "Hills": "เนินเขา",
  "Mountains": "ภูเขา",
  "Peaks": "ยอดเขาสูง",
  "None": "ไม่มี",
  "Monsoon & deciduous forest": "ป่าผลัดใบ / ป่ามรสุม",
  "Tropical rainforest": "ป่าดิบชื้น",
  "Mixed tropical forest": "ป่าผสมเขตร้อน",
  "Shrubland": "ไม้พุ่ม",
  "Grassland & savanna": "ทุ่งหญ้า / สะวันนา",
  "Orchards & rubber mosaic": "สวนผลไม้และสวนยาง",
  "Rice & cropland": "นาข้าวและพื้นที่เกษตร",
  "Mangroves & wetland": "ป่าชายเลนและพื้นที่ชุ่มน้ำ",
  "Built-up urban": "เขตเมืองและสิ่งปลูกสร้าง",
  "Bare ground": "พื้นดินโล่ง",
  "Snow & ice": "หิมะและน้ำแข็ง",
};

export function terrainName(name) {
  if (!name) return "";
  return lang === "th" ? (TERRAIN_TH[name] || name) : name;
}

// --- National yields & 19 NESDC industries ---------------------------------------------------------------------

const YIELDS_TH = {
  population: { label: "ประชากร", name: "ประชากร", desc: "จำนวนประชากรตามทะเบียนราษฎร 77 จังหวัด (กรมการปกครอง DOPA)" },
  food: { label: "อาหาร", name: "อาหาร (เกษตรกรรม)", desc: "มูลค่าผลิตภัณฑ์จังหวัด (GPP) สาขาเกษตรกรรม ป่าไม้ และการประมง (สภาพัฒน์)" },
  production: { label: "การผลิต", name: "การผลิตและอุตสาหกรรม", desc: "มูลค่า GPP สาขาอุตสาหกรรม เหมืองแร่ พลังงาน และการก่อสร้าง (สภาพัฒน์)" },
  gold: { label: "เศรษฐกิจ (GPP)", name: "เศรษฐกิจ (GPP / GDP)", desc: "ผลิตภัณฑ์มวลรวมจังหวัด/ประเทศ ณ ราคาประจำปี สกุลเงินบาท (สภาพัฒน์)" },
  science: { label: "วิทย์-เทคโนโลยี", name: "วิทย์ เทคโนโลยี และการศึกษา", desc: "มูลค่า GPP สาขาเทคโนโลยีสารสนเทศ วิชาชีพวิทยาศาสตร์ และการศึกษา (สภาพัฒน์)" },
  culture: { label: "วัฒนธรรม-ท่องเที่ยว", name: "วัฒนธรรมและการท่องเที่ยว", desc: "มูลค่า GPP สาขาโรงแรม ภัตตาคาร การท่องเที่ยว ศิลปะ และนันทนาการ (สภาพัฒน์)" },
  unemployment: { label: "ว่างงาน", name: "อัตราการว่างงาน", desc: "สัดส่วนผู้ว่างงานต่อกำลังแรงงานรวม (สำนักงานสถิติแห่งชาติ NSO)" },
};

export function yieldLabel(key, fallback = "") {
  return lang === "th" ? (YIELDS_TH[key]?.label || fallback) : fallback;
}
export function yieldName(key, fallback = "") {
  return lang === "th" ? (YIELDS_TH[key]?.name || fallback) : fallback;
}
export function yieldDesc(key, fallback = "") {
  return lang === "th" ? (YIELDS_TH[key]?.desc || fallback) : fallback;
}

const INDUSTRIES_TH = {
  agriculture: "เกษตรกรรม ป่าไม้ และการประมง",
  mining: "การทำเหมืองแร่และเหมืองหิน",
  manufacturing: "อุตสาหกรรมการผลิต",
  utilities: "ไฟฟ้า ก๊าซ และไอน้ำ",
  water_waste: "การจัดหาน้ำและจัดการของเสีย",
  construction: "การก่อสร้าง",
  trade: "การขายส่งและการขายปลีก",
  transportation: "การขนส่งและสถานที่เก็บสินค้า",
  accommodation: "ที่พักแรม อาหาร และการท่องเที่ยว",
  information: "ข้อมูลข่าวสารและการสื่อสาร",
  finance: "กิจกรรมทางการเงินและการประกันภัย",
  real_estate: "กิจกรรมอสังหาริมทรัพย์",
  professional: "กิจกรรมวิชาชีพ วิทยาศาสตร์ และเทคนิค",
  admin: "กิจกรรมการบริหารและบริการสนับสนุน",
  public_admin: "การบริหารราชการและการป้องกันประเทศ",
  education: "การศึกษา",
  health: "กิจกรรมด้านสุขภาพและงานสังคมสงเคราะห์",
  arts: "ศิลปะ ความบันเทิง และนันทนาการ",
  other: "กิจกรรมบริการอื่นๆ",
  government: "ภาครัฐและการบริหารราชการ",
};

export function industryName(key, fallback = "") {
  return lang === "th" ? (INDUSTRIES_TH[key] || fallback || key) : (fallback || key);
}

// --- Map Lenses & Groups ---------------------------------------------------------------------------------------

const LENS_GROUPS_TH = {
  base: "แผนที่ฐาน",
  people: "ประชากร",
  prosperity: "รายได้และความมั่งคั่ง",
  economy: "เศรษฐกิจและอุตสาหกรรม",
  life: "คุณภาพชีวิต",
  faith: "ศาสนาและวัฒนธรรม",
  hazards: "ภัยพิบัติและมลพิษ",
  land: "การใช้ที่ดินและดาวเทียม",
  __other: "อื่นๆ",
};

const LENSES_TH = {
  density: {
    name: "ความหนาแน่นประชากร",
    desc: "จำนวนประชากรต่อตารางกิโลเมตรในแต่ละอำเภอ (ทะเบียนราษฎร กรมการปกครอง)",
    unit: "คน / ตร.กม.",
  },
  growth: {
    name: "การเติบโตประชากร",
    desc: "อัตราการเปลี่ยนแปลงประชากรตามทะเบียนราษฎร พ.ศ. 2564–2568 (กรมการปกครอง)",
    unit: "% (2564–2568)",
  },
  foreign_born: {
    name: "ประชากรสัญชาติอื่น",
    desc: "สัดส่วนผู้ไม่มีสัญชาติไทยในทะเบียนราษฎรรายจังหวัด (กรมการปกครอง)",
    unit: "% ของประชากร",
  },
  migration: {
    name: "ผู้ย้ายถิ่นข้ามจังหวัด",
    desc: "สัดส่วนประชากรที่ย้ายถิ่นฐานจากต่างจังหวัด (สำนักงานสถิติแห่งชาติ)",
    unit: "% ของประชากร",
  },
  income: {
    name: "รายได้ครัวเรือน",
    desc: "รายได้เฉลี่ยต่อเดือนของครัวเรือนรายจังหวัด (สำนักงานสถิติแห่งชาติ SES)",
    unit: "บาท / เดือน",
  },
  gpp_pc: {
    name: "GPP ต่อหัว",
    desc: "ผลิตภัณฑ์จังหวัดต่อประชากร 1 คน (สภาพัฒน์ NESDC 2567p)",
    unit: "บาท / คน / ปี",
  },
  home: {
    name: "หนี้สินครัวเรือน",
    desc: "หนี้สินเฉลี่ยต่อครัวเรือนรายจังหวัด (สำนักงานสถิติแห่งชาติ SES)",
    unit: "บาท / ครัวเรือน",
  },
  poverty: {
    name: "สัดส่วนรายจ่ายต่อรายได้",
    desc: "อัตราส่วนค่าใช้จ่ายครัวเรือนเทียบกับรายได้รายเดือน (NSO SES)",
    unit: "% ของรายได้",
  },
  mfg_share: {
    name: "สัดส่วนอุตสาหกรรมผลิต",
    desc: "สัดส่วน GPP จากภาคอุตสาหกรรมการผลิตต่อ GPP รวมของจังหวัด (สภาพัฒน์)",
    unit: "% ของ GPP",
  },
  tour_share: {
    name: "การท่องเที่ยวและบริการ",
    desc: "สัดส่วน GPP จากโรงแรม อาหาร และนันทนาการต่อ GPP จังหวัด (สภาพัฒน์)",
    unit: "% ของ GPP",
  },
  agri_share: {
    name: "สัดส่วนเกษตรกรรม",
    desc: "สัดส่วน GPP จากภาคเกษตรกรรม ป่าไม้ และประมงต่อ GPP จังหวัด (สภาพัฒน์)",
    unit: "% ของ GPP",
  },
  sci_share: {
    name: "เทคโนโลยี วิทย์ และการศึกษา",
    desc: "สัดส่วน GPP จากไอที วิชาชีพวิทยาศาสตร์ และการศึกษา (สภาพัฒน์)",
    unit: "% ของ GPP",
  },
  homeownership: {
    name: "การเป็นเจ้าของบ้าน",
    desc: "สัดส่วนครัวเรือนที่เป็นเจ้าของที่อยู่อาศัย (สำนักงานสถิติแห่งชาติ)",
    unit: "% ของครัวเรือน",
  },
  unemployment: {
    name: "อัตราการว่างงาน",
    desc: "สัดส่วนผู้ว่างงานต่อกำลังแรงงานรวมรายจังหวัด (NSO)",
    unit: "% ของกำลังแรงงาน",
  },
  broadband: {
    name: "ความหนาแน่นสถานประกอบการ",
    desc: "จำนวนสถานประกอบการธุรกิจต่อประชากร 1,000 คน (สำมะโนธุรกิจ NSO)",
    unit: "แห่ง / พันคน",
  },
  disasters: {
    name: "รายงานความเสี่ยงภัยพิบัติ",
    desc: "รายงานความเสี่ยงอุทกภัย ภัยแล้ง วาตภัย และดินถล่มระดับหมู่บ้าน (กรมการปกครอง)",
    unit: "รายงาน / จังหวัด",
  },
  arsenic: {
    name: "สารหนูในลำน้ำ (As)",
    desc: "ค่าสารหนู (As) สูงสุดที่ตรวจวัดได้ในน้ำผิวดินจาก 23 สถานีทางการ จ.เชียงราย / คพ. (มาตรฐานไทย ≤ 0.010 มก./ล.)",
    note: "แสดงสีเฉพาะพื้นที่ Hex ที่มีข้อมูล CSV ตรวจวัดทางการ (แม่น้ำกก สาย รวก โขง และลำน้ำควบคุม) จังหวัดที่ไม่มีข้อมูลตรวจวัดจะแสดงเป็น \"ไม่มีข้อมูล\"",
    unit: "มก./ล. (ค่าสูงสุด As)",
  },
  forest: {
    name: "พื้นที่ป่าไม้ (ดาวเทียม)",
    desc: "สัดส่วนพื้นที่ป่าไม้ต่อ Hex ขนาด 8 กม. จากภาพถ่ายดาวเทียม ESA WorldCover 2021",
    unit: "% พื้นที่ป่า",
  },
  farmland: {
    name: "นาข้าวและเกษตรกรรม",
    desc: "สัดส่วนพื้นที่เพาะปลูกต่อ Hex ขนาด 8 กม. จากภาพถ่ายดาวเทียม ESA WorldCover 2021",
    unit: "% พื้นที่เกษตร",
  },
  developed: {
    name: "พื้นที่เมืองและสิ่งปลูกสร้าง",
    desc: "สัดส่วนพื้นที่สิ่งปลูกสร้างต่อ Hex ขนาด 8 กม. จากภาพถ่ายดาวเทียม ESA WorldCover 2021",
    unit: "% เขตเมือง",
  },
  faith_tradition: {
    name: "มรดกทางศาสนา",
    desc: "สัดส่วนผู้นับถือศาสนาหลักรายจังหวัด (สำนักงานสถิติแห่งชาติ)",
    unit: "ศาสนาหลัก",
  },
};

export function lensGroupName(g) {
  if (!g) return "";
  return lang === "th" ? (LENS_GROUPS_TH[g.id] || g.name || "") : (g.name || "");
}
export function lensName(l) {
  if (!l) return "";
  if (l.id == null) return t("Terrain", "ภูมิประเทศ");
  return lang === "th" ? (LENSES_TH[l.id]?.name || l.name) : l.name;
}
export function lensDesc(l) {
  if (!l) return "";
  return lang === "th" ? (LENSES_TH[l.id]?.desc || l.description || l.unit || "") : (l.description || l.unit || "");
}
export function lensNote(l) {
  if (!l) return "";
  return lang === "th" ? (LENSES_TH[l.id]?.note || l.note || "") : (l.note || "");
}
export function lensUnit(l) {
  if (!l) return "";
  return lang === "th" ? (LENSES_TH[l.id]?.unit || l.unit || "") : (l.unit || "");
}

// --- Map Layer Toggles -----------------------------------------------------------------------------------------

const MAP_TOGGLES_TH = {
  roads: { label: "ทางหลวง", title: "มอเตอร์เวย์และทางหลวงแผ่นดินสายหลัก (Natural Earth)" },
  rail: { label: "ทางรถไฟ รฟท.", title: "เส้นทางรถไฟแห่งประเทศไทย (Natural Earth)" },
  hubs: { label: "ท่าเรือและสนามบิน", title: "ท่าเรือพาณิชย์หลักและสนามบินพาณิชย์ของไทย (OurAirports)" },
  military: { label: "ฐานทัพ", title: "ที่ตั้งกองทัพบก กองทัพเรือ และกองทัพอากาศไทย" },
  wonders: { label: "สถานที่สำคัญ", title: "อุทยานแห่งชาติ มหาวิทยาลัยวิจัยแห่งชาติ และมรดกโลกยูเนสโก" },
  trade: { label: "เส้นทางเศรษฐกิจ", title: "20 เส้นทางเศรษฐกิจหลักของไทยถ่วงน้ำหนักด้วย GPP สภาพัฒน์" },
  arsenic: { label: "สารหนู (As)", title: "สถานีตรวจวัดสารหนูในน้ำผิวดิน จ.เชียงราย / คพ. และจุดเฝ้าระวังระดับประเทศ" },
};

export function mapToggleLabel(id, fallback = "") {
  return lang === "th" ? (MAP_TOGGLES_TH[id]?.label || fallback) : fallback;
}
export function mapToggleTitle(id, fallback = "") {
  return lang === "th" ? (MAP_TOGGLES_TH[id]?.title || fallback) : fallback;
}

// --- Advisors & Council ----------------------------------------------------------------------------------------

const ADVISORS_TH = {
  energy: { name: "พลังงานและทรัพยากร", role: "เสนาบดีพลังงาน", blurb: "โรงไฟฟ้าก๊าซธรรมชาติ ถ่านหินแม่เมาะ เขื่อน กฟผ. โซลาร์ฟาร์ม และกังหันลมทั่วไทย" },
  economy: { name: "เศรษฐกิจ", role: "ขุนคลัง", blurb: "โครงสร้าง GPP 19 สาขาจากสภาพัฒน์ และจังหวัดผู้นำในแต่ละอุตสาหกรรม" },
  people: { name: "ประชากร", role: "นายทะเบียนราษฎร", blurb: "การกระจายตัวของประชากร การย้ายถิ่น และการเติบโตของจังหวัด (กรมการปกครอง)" },
  prosperity: { name: "ความเป็นอยู่", role: "ผู้ดูแลครัวเรือน", blurb: "รายได้ ค่าใช้จ่าย หนี้สินครัวเรือน และการเป็นเจ้าของบ้านทั่วไทย (NSO)" },
  knowledge: { name: "ความรู้และเทคโนโลยี", role: "ราชบัณฑิต", blurb: "ภาคเทคโนโลยี วิชาชีพวิทยาศาสตร์ การศึกษา และความหนาแน่นธุรกิจ" },
  land: { name: "ผืนดินและป่าไม้", role: "เจ้ากรมแผนที่", blurb: "ป่าไม้ นาข้าว ป่าชายเลน และพื้นที่เมืองจากดาวเทียม ESA WorldCover" },
  military: { name: "ความมั่นคง", role: "แม่ทัพ", blurb: "ฐานทัพบก ฐานทัพเรือ และกองบินกองทัพอากาศทั่วราชอาณาจักร" },
  commerce: { name: "การค้าและคมนาคม", role: "เจ้าท่าและพาณิชย์", blurb: "เส้นทางเศรษฐกิจหลัก ท่าเรือน้ำลึก และสนามบินนานาชาติของไทย" },
  culture: { name: "วัฒนธรรมและภัยพิบัติ", role: "ผู้พิทักษ์มรดก", blurb: "อุทยานแห่งชาติ มรดกโลกยูเนสโก มหาวิทยาลัย ศาสนา และความเสี่ยงภัยพิบัติ" },
  arsenic: { name: "น้ำและสารหนู", role: "ผู้พิทักษ์สายน้ำ", blurb: "วิกฤตสารหนูข้ามพรมแดน (แม่น้ำกก สาย รวก โขง) ข้อมูลฐานปี 2560–2568 และจุดเฝ้าระวังทั่วไทย" },
  explorer: { name: "สำรวจข้อมูล", role: "นักทำแผนที่", blurb: "วิเคราะห์ กรอง เรียงลำดับ และพล็อตกราฟข้อมูลทุกมิติของ 77 จังหวัด และ 928 อำเภอ" },
};

const COUNCIL_GROUPS_TH = {
  "Wealth and work": "ความมั่งคั่งและเศรษฐกิจ",
  "People, land & environment": "ประชากร ผืนดิน และสิ่งแวดล้อม",
  "Defense": "ความมั่นคง",
  "Your own questions": "วิเคราะห์ข้อมูลเอง",
};

export function advisorInfo(adv) {
  if (!adv) return adv;
  if (lang !== "th") return adv;
  const tr = ADVISORS_TH[adv.id];
  return tr ? { ...adv, ...tr } : adv;
}

export function councilGroupLabel(label) {
  return lang === "th" ? (COUNCIL_GROUPS_TH[label] || label) : label;
}

// --- Arsenic Rivers & Watchpoints ------------------------------------------------------------------------------

const RIVERS_TH = {
  sai: "แม่น้ำสาย",
  kok: "แม่น้ำกก",
  mekong: "แม่น้ำโขง",
  ruak: "แม่น้ำรวก",
  korn: "แม่กรณ์ (ควบคุม)",
  lao: "แม่ลาว (ควบคุม)",
  suai: "แม่สรวย (ควบคุม)",
};

const WATCHPOINTS_TH = {
  "wp-kk01-maeai": {
    name: "จุดน้ำกกเข้าไทย · ท่าตอน (KK01–KK03)",
    province: "เชียงใหม่",
    status: "วิกฤตข้ามพรมแดนปัจจุบัน (2568–2569)",
    summary: "จุดต้นน้ำที่แม่น้ำกกไหลจากรัฐฉาน เมียนมา เข้าสู่ไทย ตรวจพบค่าสารหนูเกิน 0.010 มก./ล. ต่อเนื่อง นำไปสู่ข้อเสนอประกาศเขตควบคุมมลพิษ ~150 กม.",
    source: "กรมควบคุมมลพิษ (คพ.) / สสจ.เชียงใหม่",
  },
  "wp-salween": {
    name: "ลุ่มน้ำสาละวิน · ชายแดนแม่ฮ่องสอน",
    province: "แม่ฮ่องสอน",
    status: "พื้นที่เฝ้าระวังข้ามพรมแดน (2568–2569)",
    summary: "ลุ่มน้ำชายแดนด้านตะวันตกที่ภาคประชาสังคมและ คพ. ร่วมเฝ้าระวังผลกระทบจากเหมืองทองคำและแร่หายากตอนบนในรัฐฉาน/กะเหรี่ยง",
    source: "กรมควบคุมมลพิษ (คพ.) / ข่าวสิ่งแวดล้อม",
  },
  "wp-ronphibun": {
    name: "อำเภอร่อนพิบูลย์ · แหล่งมรดกเหมืองดีบุก",
    province: "นครศรีธรรมราช",
    status: "พื้นที่เสี่ยงสารหนูในน้ำบาดาลเรื้อรัง",
    summary: "กรณีการปนเปื้อนสารหนูจากกากแร่อาร์เซโนไพไรต์จากการทำเหมืองดีบุกในอดีตที่รู้จักมากที่สุดของไทย มีรายงานโรคพิษสารหนูเรื้อรังตั้งแต่ปี 2530",
    source: "กระทรวงสาธารณสุข / กรมทรัพยากรธรณี",
  },
  "wp-chatree": {
    name: "รอบเหมืองทองคำชาตรี (พิจิตร–เพชรบูรณ์)",
    province: "พิจิตร",
    status: "พื้นที่เฝ้าระวังสิ่งแวดล้อมและสุขภาพ",
    summary: "พื้นที่รอบแหล่งแร่ทองคำที่มีการตรวจติดตามสารหนูและแมงกานีสในน้ำบาดาลและสิ่งแวดล้อมอย่างต่อเนื่องโดยหน่วยงานรัฐและนักวิชาการ",
    source: "กรมอุตสาหกรรมพื้นฐานและการเหมืองแร่ / คพ.",
  },
  "wp-banrai": {
    name: "อำเภอบ้านไร่ · แหล่งสารหนูตามธรณีวิทยา",
    province: "อุทัยธานี",
    status: "พื้นที่เฝ้าระวังสารหนูในน้ำบาดาลตามธรรมชาติ",
    summary: "พื้นที่ที่มีการตรวจพบสารหนูในแหล่งน้ำบาดาลจากโครงสร้างชั้นหินตามธรรมชาติ จำเป็นต้องใช้ระบบบำบัดก่อนบริโภค",
    source: "กรมทรัพยากรน้ำบาดาล / กระทรวงสาธารณสุข",
  },
};

export function arsenicRiverLabel(r) {
  if (!r) return "";
  return lang === "th" ? (RIVERS_TH[r.id] || r.short || r.name) : (r.short || r.name);
}

export function arsenicWatchpoint(wp) {
  if (!wp) return wp;
  if (lang !== "th") return wp;
  const tr = WATCHPOINTS_TH[wp.id];
  return tr ? { ...wp, ...tr } : wp;
}
