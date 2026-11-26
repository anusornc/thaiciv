// The Almanac: what every number means, caution & limitations of use, and exact primary sources with checksums.
import { resolveTables } from "../terrain.js";
import { esc } from "../format.js";
import { parseHex, luminance } from "../color.js";
import { icon, glyph } from "./icon.js";
import { t, isTh } from "../i18n.js";

const COVER_ICON = { forest_deciduous: "l-forest", forest_evergreen: "l-forest", forest_mixed: "l-forest", cropland: "l-farmland", pasture: "l-farmland", urban: "l-developed" };
const inkOn = (hex) => {
  try { return /^#[0-9a-f]{6}$/i.test(hex || "") && luminance(parseHex(hex)) > 0.4 ? "#1c1710" : "#f8f0d8"; } catch { return "#f8f0d8"; }
};
const CATEGORY = { energy: "Energy", mineral: "Minerals", agri: "Agriculture" };

export function initPedia(data) {
  const modal = document.getElementById("pedia");
  const card = modal.querySelector(".modal-card");
  const nav = document.getElementById("pedia-nav");
  const body = document.getElementById("pedia-body");
  const srcName = (id) => data.sources?.find((s) => s.id === id)?.title || id || "";
  let restoreFocus = null;
  let currentPage = "About this map";

  const h2 = (ic, fb, text) => `<h2>${icon(ic, fb, { size: 24 })}<span>${esc(text)}</span></h2>`;

  const PAGE_LABELS = {
    "About this map": () => t("About this map", "เกี่ยวกับแผนที่นี้"),
    "Caution & Validation": () => t("Caution & Validation", "ข้อควรระวังและการตรวจสอบ"),
    Yields: () => t("Yields", "ผลผลิตเศรษฐกิจ"),
    Provinces: () => t("Provinces", "77 จังหวัด"),
    Terrain: () => t("Terrain", "ภูมิประเทศ"),
    Lenses: () => t("Lenses", "เลนส์ข้อมูล"),
    Resources: () => t("Resources", "ทรัพยากรและโรงไฟฟ้า"),
    Sources: () => t("Sources", "แหล่งข้อมูลและอ้างอิง"),
  };

  const pages = {
    "About this map": () => `
      ${h2("pedia", "📖", t("About this map", "เกี่ยวกับแผนที่นี้"))}
      <p>${t(
        "This is real <b>Thailand (ประเทศไทย)</b>, drawn like a 4X strategy game. Nothing is invented: every tile, province, city and number comes from official Thai and global public datasets, listed under <i>Sources</i>.",
        "แผนที่นี้แสดงข้อมูลจริงของ <b>ประเทศไทย (Thailand)</b> ในรูปแบบเกมวางแผน 4X ไม่มีตัวเลขที่แต่งขึ้นเอง ทุกช่องพื้นที่ จังหวัด เมือง และสถิติ มาจากชุดข้อมูลเปิดสาธารณะทางการของไทยและสากล ซึ่งตรวจสอบได้ในหน้า <i>แหล่งข้อมูลและอ้างอิง</i>"
      )}</p>
      <div class="pedia-caution">
        <b>⚠ ${t("Caution to Use", "ข้อควรระวังในการใช้งาน")}:</b>
        ${t(
          "This project is an independent educational &amp; exploratory visualization — <b>not</b> an official government bulletin, real-time drinking-water safety advisory, emergency alert, or policy/investment advice. Always verify critical figures directly with the primary agencies listed in",
          "โปรเจกต์นี้จัดทำขึ้นเพื่อการเรียนรู้และสำรวจข้อมูลเชิงภาพเท่านั้น <b>ไม่ใช่</b>ประกาศทางการของหน่วยงานรัฐ ไม่ใช่คำแนะนำความปลอดภัยน้ำดื่มแบบเรียลไทม์ และไม่ใช่คำแนะนำด้านการแพทย์หรือการลงทุน โปรดตรวจสอบตัวเลขสำคัญจากหน่วยงานต้นทางโดยตรงในหน้า"
        )}
        <a href="#" data-jump="Caution & Validation">${t("Caution & Validation", "ข้อควรระวังและการตรวจสอบ")}</a> &amp;
        <a href="#" data-jump="Sources">${t("Sources", "แหล่งข้อมูลและอ้างอิง")}</a>.
      </div>
      <h4>${t("How it's built", "โครงสร้างแผนที่")}</h4>
      <p>${t(
        `All 77 provinces of Thailand are projected (Albers equal-area conic centred on 101°E, 13°N) and cut into ${data.world.grid.cols}×${data.world.grid.rows} hexes, each ${data.world.grid.radius * 2} km corner to corner (~166 km² per hex). Each hex belongs to the province (จังหวัด) and district (อำเภอ / เขต) under its centre. Elevation comes from NOAA ETOPO1 and satellite land cover from ESA WorldCover 10m (2021).`,
        `แผนที่ประเทศไทยทั้ง 77 จังหวัดถูกฉายด้วยระบบพิกัด Albers Equal-Area (ศูนย์กลาง 101°E, 13°N) และแบ่งเป็นตารางหกเหลี่ยม ${data.world.grid.cols}×${data.world.grid.rows} ช่อง ขนาดเส้นผ่านศูนย์กลาง ${data.world.grid.radius * 2} กม. (~166 ตร.กม./ช่อง) ข้อมูลระดับความสูงมาจาก NOAA ETOPO1 และข้อมูลสิ่งปกคลุมดินมาจากดาวเทียม ESA WorldCover 10m (2021)`
      )}</p>
      <p>${t(
        "<b>Cities</b> represent Thailand's 77 provincial hubs (with <b>★ Bangkok</b> as national capital), populated with official NESDC 2024p Gross Provincial Product (19 sectors), DOPA civil registration (2020–2025), and NSO Socio-Economic and Labor Force Surveys.",
        "<b>เมืองหลัก</b> แทนศูนย์กลางทั้ง 77 จังหวัด (โดยมี <b>★ กรุงเทพมหานคร</b> เป็นเมืองหลวง) ประกอบข้อมูลผลิตภัณฑ์จังหวัด NESDC GPP 2567p (19 สาขา), ทะเบียนราษฎรกรมการปกครอง (2563–2568), และผลสำรวจภาวะเศรษฐกิจสังคมและแรงงานของสำนักงานสถิติแห่งชาติ (NSO)"
      )}</p>
      <h4>${t("Controls", "การควบคุม")}</h4>
      <p>${t(
        "Drag or arrow keys / WASD to pan · scroll, +/– or double-click to zoom · click a city or province to open it · / or ⌘K to search (English or ไทย) · L to cycle lenses · R to show or hide resources · ? for shortcuts · Esc to close.",
        "ลากเมาส์หรือลูกศร/WASD เพื่อเลื่อนแผนที่ · เลื่อนลูกกลิ้งหรือ +/– เพื่อซูม · คลิกเมืองหรือจังหวัดเพื่อเปิดดูรายละเอียด · กด / หรือ ⌘K เพื่อค้นหา (ไทย/EN) · กด L เพื่อสลับเลนส์ · กด R เพื่อเปิด/ปิดทรัพยากร · กด ? ดูวิธีใช้ · กด Esc เพื่อปิดหน้าต่าง"
      )}</p>
      <p class="muted">${t("Built on the MIT-licensed usaciv visualization engine by Andrej Karpathy.", "พัฒนาต่อยอดจากเอนจินแสดงผล usaciv (MIT License) โดย Andrej Karpathy")}</p>`,

    "Caution & Validation": () => `
      ${h2("l-disasters", "⚠️", t("Caution to Use & Independent Validation", "ข้อควรระวังในการใช้งานและการตรวจสอบข้อมูล"))}
      <div class="pedia-caution">
        <b>⚠ ${t("Important Disclaimer", "คำเตือนสำคัญก่อนนำข้อมูลไปใช้งาน")}</b>
        <ul>
          <li><b>${t("Informational & educational only", "เพื่อการเรียนรู้และสำรวจข้อมูลเท่านั้น")}:</b> ${t(
            "thaiciv is an independent open-source visualization. It is NOT an official publication of the Royal Thai Government, Pollution Control Department (PCD), Ministry of Public Health (MOPH), NESDC, DOPA, or NSO.",
            "thaiciv เป็นเครื่องมือแสดงผลข้อมูลสาธารณะแบบ Open Source อิสระ ไม่ใช่ระบบแจ้งเตือนหรือประกาศทางการของกรมควบคุมมลพิษ (คพ.) กระทรวงสาธารณสุข สภาพัฒน์ กรมการปกครอง หรือสำนักงานสถิติแห่งชาติ"
          )}</li>
          <li><b>${t("Arsenic & water-safety caution", "ข้อควรระวังเรื่องข้อมูลสารหนูและความปลอดภัยของน้ำ")}:</b> ${t(
            "Surface-water Arsenic (As) values reflect a point-in-time snapshot of 23 official Chiang Rai / PCD stations (8 monitoring rounds) and the 2017–2025 KK01 baseline. Do NOT use this map to decide whether tap, well, or river water is safe to drink, cook, or irrigate. Unmonitored provinces/hexes are marked <b>no data</b> — which does <b>not</b> mean safe or uncontaminated. Always check live official advisories from PCD, Provincial Waterworks Authority (PWA), and Chiang Rai Provincial Public Health Office.",
            "ค่าสารหนู (As) ในน้ำผิวดินเป็นภาพรวมจากชุดไฟล์ CSV ทางการ 23 สถานี จ.เชียงราย (8 รอบตรวจวัด) และฐานปี 2560–2568 ของสถานี KK01 <b>ห้ามใช้แผนที่นี้ตัดสินใจว่าน้ำประปา น้ำบ่อ หรือน้ำในแม่น้ำปลอดภัยต่อการดื่ม ใช้ หรือการเกษตร</b> พื้นที่ที่ขึ้นว่า <b>ไม่มีข้อมูล (no data)</b> ไม่ได้หมายความว่าปลอดภัย โปรดติดตามประกาศสถานการณ์ล่าสุดจากกรมควบคุมมลพิษ (คพ.) การประปาส่วนภูมิภาค (กปภ.) และ สสจ.เชียงราย โดยตรง"
          )}</li>
          <li><b>${t("Spatial resolution & hex aggregation", "ข้อจำกัดด้านความละเอียดเชิงพื้นที่ (Hex 8 กม.)")}:</b> ${t(
            "Each hex spans ~8 km (~166 km²). Provincial statistics (GPP, income, debt, unemployment) apply province-wide and do not reflect street- or village-level variation. District boundaries and station markers are snapped to the hex coordinate frame for visualization.",
            "แต่ละช่อง Hex ครอบคลุมพื้นที่ ~166 ตร.กม. ตัวเลขระดับจังหวัด (เช่น GPP รายได้ หนี้สิน การว่างงาน) เป็นค่าเฉลี่ยทั้งจังหวัด ไม่สะท้อนความแตกต่างระดับตำบลหรือหมู่บ้าน และตำแหน่งสถานีถูกแสดงบนระบบพิกัดเพื่อการมองเห็นภาพรวม"
          )}</li>
          <li><b>${t("Data vintages & provisional estimates", "รอบปีข้อมูลและตัวเลขเบื้องต้น")}:</b> ${t(
            "Datasets span different official release years: NESDC GPP 2024p (preliminary), DOPA civil registration (2020–2025; counts registered residents, not unregistered migrants/tourists), NSO SES & Labor Force (2023–2024), ESA WorldCover satellite imagery (2021), and Chiang Rai / PCD Arsenic CSVs (2017–2026).",
            "ข้อมูลแต่ละชุดมีปีอ้างอิงต่างกัน ได้แก่ สภาพัฒน์ GPP 2567p (ตัวเลขเบื้องต้น), ทะเบียนราษฎรกรมการปกครอง (2563–2568 นับเฉพาะผู้มีชื่อในทะเบียนราษฎร ไม่รวมประชากรแฝง/นักท่องเที่ยว), ผลสำรวจ NSO (2566–2567), ดาวเทียม ESA WorldCover (2021) และชุดตรวจวัดสารหนูเชียงราย/คพ. (2560–2569)"
          )}</li>
          <li><b>${t("Analytical conventions", "ข้อกำหนดการประมวลผลข้อมูล")}:</b> ${t(
            "In the Arsenic CSV, raw '0' entries represent unsampled rounds (excluded from averages, never treated as 0.000 mg/L), while '<0.010' below-detection values are counted as compliant and plotted at half detection limit (0.005 mg/L) in trend charts. The 5 purple national watchpoints represent documented contextual hotspots without a unified open-data CSV.",
            "ในไฟล์ CSV สารหนู ค่า '0' หมายถึงรอบที่ไม่ได้เก็บตัวอย่าง (ไม่ถูกนำมาคิดเป็นค่าศูนย์จริง) ส่วนค่า '<0.010' นับว่าผ่านเกณฑ์และพล็อตที่ครึ่งหนึ่งของขีดจำกัด (0.005 มก./ล.) บนกราฟแนวโน้ม ขณะที่จุดสีม่วง 5 แห่งเป็นจุดเฝ้าระวังเชิงบริบทระดับประเทศที่ยังไม่มี CSV เปิดรวมชุดเดียว"
          )}</li>
        </ul>
      </div>

      <h4>${t("How to Validate Every Number Yourself", "วิธีตรวจสอบความถูกต้องของข้อมูลด้วยตนเอง")}</h4>
      <ol>
        <li><b>${t("Inspect primary official agencies & direct download URLs", "ตรวจสอบจากเว็บไซต์และไฟล์ต้นฉบับของหน่วยงานรัฐ")}:</b>
          ${t(
            "Open the Sources tab to click straight through to all 13 publishers (NESDC, DOPA, NSO, Chiang Rai Open Data / PCD, ESA, NOAA, WRI, Natural Earth, OurAirports, Wikidata) and download the exact raw files.",
            "เปิดแท็บ แหล่งข้อมูลและอ้างอิง เพื่อคลิกลิงก์ตรงไปยังทั้ง 13 หน่วยงานต้นทางและดาวน์โหลดไฟล์ต้นฉบับที่ระบบใช้จริง"
          )}
          <a href="#" data-jump="Sources">${t("Open Sources & Checksums ›", "เปิดหน้าแหล่งข้อมูลและ Checksum ›")}</a>
        </li>
        <li><b>${t("Verify SHA-256 checksums", "ตรวจเทียบค่า SHA-256 Checksum")}:</b>
          ${t(
            "Every downloaded file's exact URL, retrieval timestamp, byte size, and SHA-256 hash are recorded in",
            "ไฟล์ที่ดาวน์โหลดทุกไฟล์มีการบันทึก URL จริง วันเวลาที่ดึงข้อมูล ขนาดไฟล์ และรหัสแฮช SHA-256 ไว้ครบใน"
          )}
          <a href="data/sources.json" target="_blank" rel="noopener noreferrer"><code>data/sources.json</code></a>.
        </li>
        <li><b>${t("Reproduce the full open-source pipeline", "รันซ้ำกระบวนการสร้างข้อมูลจากโค้ดเปิด (Open Source)")}:</b>
          ${t(
            "Clone the repository on GitHub and run",
            "โคลนโค้ดจาก GitHub แล้วสั่งรันคำสั่งด้านล่างเพื่อดึงข้อมูลใหม่และรันตัวตรวจสอบอัตโนมัติ:"
          )}
          <code>uv run python -m pipeline all</code> &amp; <code>uv run python -m unittest</code> —
          <a href="https://github.com/anusornc/thaiciv" target="_blank" rel="noopener noreferrer">github.com/anusornc/thaiciv</a>.
        </li>
      </ol>

      <h4>${t("Official Reference Agencies for Live Advisories", "หน่วยงานทางการสำหรับตรวจสอบประกาศล่าสุด")}</h4>
      <ul>
        <li><b>${t("Pollution Control Department (PCD)", "กรมควบคุมมลพิษ (คพ.)")}:</b> <a href="https://www.pcd.go.th/" target="_blank" rel="noopener noreferrer">https://www.pcd.go.th/</a></li>
        <li><b>${t("Chiang Rai Open Data Portal (Arsenic CSVs)", "บัญชีข้อมูลเปิดจังหวัดเชียงราย (CSV สารหนู)")}:</b> <a href="https://chiangrai.gdcatalog.go.th/dataset/e1fc8a4f-1d5c-4571-aff2-89a35e554a08" target="_blank" rel="noopener noreferrer">chiangrai.gdcatalog.go.th</a></li>
        <li><b>${t("NESDC (Gross Provincial Product)", "สภาพัฒน์ (GPP / GDP)")}:</b> <a href="https://www.nesdc.go.th/" target="_blank" rel="noopener noreferrer">https://www.nesdc.go.th/</a></li>
        <li><b>${t("DOPA Official Statistics (Population &amp; Disasters)", "กรมการปกครอง (ทะเบียนราษฎรและภัยพิบัติ)")}:</b> <a href="https://stat.bora.dopa.go.th/" target="_blank" rel="noopener noreferrer">https://stat.bora.dopa.go.th/</a> · <a href="https://catalog.dopa.go.th/" target="_blank" rel="noopener noreferrer">catalog.dopa.go.th</a></li>
        <li><b>${t("National Statistical Office (NSO)", "สำนักงานสถิติแห่งชาติ (NSO)")}:</b> <a href="https://www.nso.go.th/" target="_blank" rel="noopener noreferrer">https://www.nso.go.th/</a></li>
      </ul>`,

    Yields: () => `
      ${h2("y-production", "⚙️", t("Yields", "ผลผลิตเศรษฐกิจ (Yields)"))}
      <p>${t(
        "Civilization's yields mapped directly onto Thailand's official NESDC 2024p Gross Provincial Product (GPP) in Thai Baht (฿). <b>Gold is total GPP</b>; Food, Production, Science and Culture represent real economic value added in their respective sectors.",
        "ค่าผลผลิตสไตล์ Civilization แปลงตรงมาจากผลิตภัณฑ์มวลรวมจังหวัด (NESDC GPP 2567p) หน่วยเงินบาท (฿) โดย <b>ทอง (Gold) คือ GPP รวม</b> ส่วนอาหาร การผลิต วิทยาศาสตร์ และวัฒนธรรม แทนมูลค่าเพิ่มทางเศรษฐกิจจริงในแต่ละกลุ่มสาขา"
      )}</p>
      <table>${data.nation.yields.map((y) => `<tr><td class="ic" style="color:${esc(y.color)}">${glyph(y, 26)}</td><td><b style="color:${esc(y.color)}">${esc(y.label)}${y.key === "gold" ? " (GPP)" : ""}</b><br>${esc(y.description)}</td></tr>`).join("")}</table>
      <h4>${t("Living & Economy", "ความเป็นอยู่และเศรษฐกิจ")}</h4>
      <p>${t(
        "Unemployment comes from the NSO Labor Force Survey. Household income, monthly spending, household debt and spending-to-income ratios come from the NSO Socio-Economic Survey (SES).",
        "อัตราการว่างงานมาจากสำรวจภาวะการทำงานของประชากร (NSO) ส่วนรายได้ รายจ่าย หนี้สินครัวเรือน และสัดส่วนรายจ่ายต่อรายได้ มาจากการสำรวจภาวะเศรษฐกิจและสังคมของครัวเรือน (NSO SES)"
      )}</p>`,

    Provinces: () => `
      ${h2("terrain", "🗺️", t("Provinces (จังหวัด)", "77 จังหวัด และ 928 อำเภอ"))}
      <p>${t(
        "Click any land hex without a city banner to open its province. All <b>77 provinces</b> (76 changwat + Bangkok Metropolis) and <b>928 districts (amphoe &amp; Bangkok khet)</b> are mapped from official geoBoundaries / Royal Thai Survey Department outlines.",
        "คลิกที่ช่องพื้นที่ใดก็ได้เพื่อเปิดข้อมูลจังหวัด ครอบคลุมทั้ง <b>77 จังหวัด</b> (76 จังหวัด + กรุงเทพมหานคร) และ <b>928 อำเภอ/เขต</b> จากแนวเขตทางการของ geoBoundaries / กรมแผนที่ทหาร"
      )}</p>
      <p>${t('<b>Ranks</b> ("#1 of 77") compare all 77 provinces of Thailand (1 = largest).', '<b>อันดับ</b> ("#1 / 77") เปรียบเทียบครบทั้ง 77 จังหวัดของประเทศไทย (อันดับ 1 = สูงสุด)')}</p>`,

    Terrain: () => {
      const tb = data.w?.tables || resolveTables(data.world.tables);
      const hasCover = Array.isArray(data.world.cover);
      const row = (x) => `<tr><td class="nm">${x.color ? `<span class="swatch" style="background:${esc(x.color)}"></span>` : ""}${
        COVER_ICON[x.key] ? icon(COVER_ICON[x.key], "", { size: 15 }) + " " : ""}<b>${esc(x.name)}</b></td><td>${esc(x.rule || "")}</td></tr>`;
      return `
      ${h2("terrain", "🗺️", t("Terrain", "ภูมิประเทศ"))}
      <p>${t(
        "Each 8 km hex averages ETOPO1 elevation samples inside it (from the shallow Gulf of Thailand and Chao Phraya delta to Doi Inthanon at 2,565 m). Shading comes from elevation differences with neighbouring hexes, lit from the north-west.",
        "แต่ละช่อง Hex 8 กม. เฉลี่ยค่าระดับความสูงจากแบบจำลอง NOAA ETOPO1 ตั้งแต่อ่าวไทยและที่ราบลุ่มเจ้าพระยาไปจนถึงดอยอินทนนท์ (2,565 ม.)"
      )}</p>
      <h4>${icon("l-forest", "🌲", { size: 16 })} ${t("Satellite land cover (ESA WorldCover 2021)", "สิ่งปกคลุมดินจากดาวเทียม (ESA WorldCover 2021)")}</h4>
      ${hasCover
        ? `<p>${t(
            "The base colour of each hex is its dominant satellite land-cover class (tropical rainforest, monsoon deciduous forest, rice & cropland, mangroves/wetland, scrub, grassland or built-up urban). Symbols scale with the real pixel mixture inside each hex.",
            "สีพื้นของแต่ละ Hex แสดงประเภทสิ่งปกคลุมดินหลักจากภาพถ่ายดาวเทียมความละเอียด 10 ม. และสัดส่วนต้นไม้/นาข้าว/เมืองบนช่องนั้นคำนวณจากสัดส่วนพิกเซลจริง"
          )}</p>
           <table>${tb.cover.filter((x) => x.id > 0).map(row).join("")}</table>`
        : `<p class="muted">No land-cover layer loaded.</p>`}
      <h4>${t("Relief", "ลักษณะภูมิประเทศ")}</h4>
      <table>${tb.relief.map(row).join("")}</table>
      <h4>${icon("r-hydro", "💧", { size: 16 })} ${t("Water", "แหล่งน้ำ")}</h4>
      <table>${tb.water.filter((x) => x.id > 0).map(row).join("")}</table>
      <h4>${t("Beyond the borders", "ประเทศเพื่อนบ้าน")}</h4>
      <p class="muted">${t("Neighbouring countries (Myanmar, Laos, Cambodia, Malaysia and Vietnam) are drawn under a light fog of war for geographic context.", "ประเทศเพื่อนบ้าน (เมียนมา ลาว กัมพูชา มาเลเซีย และเวียดนาม) แสดงภายใต้หมอกแผนที่เพื่อบริบททางภูมิศาสตร์")}</p>`;
    },

    Lenses: () => `
      ${h2("layers", "▤", t("Lenses", "เลนส์ข้อมูล (21 เลนส์)"))}
      <p>${t(
        `Lenses recolour Thailand's 3,200+ hexes by a single real measure (${esc(data.lenses.vintage)}). Land lenses show true 8 km hex satellite fractions from ESA WorldCover; demographic, economic and hazard lenses show official provincial, district, or station statistics.`,
        `เลนส์ระบายสีช่อง Hex กว่า 3,200 ช่องของไทยตามตัวชี้วัดจริง (${esc(data.lenses.vintage)}) โดยเลนส์ที่ดินมาจากภาพถ่ายดาวเทียมระดับ 8 กม. ส่วนเลนส์เศรษฐกิจ ประชากร และมลพิษมาจากสถิติทางการ`
      )}</p>
      <p>${t("The legend shows the distribution of hexes. Hover or drag across it to highlight only that range on the map.", "แถบสีด้านล่างแสดงการกระจายตัวของข้อมูล สามารถชี้หรือลากเพื่อกรองดูเฉพาะช่วงค่าบนแผนที่ได้")}</p>
      ${(data.lenses.groups || [{ id: null, name: "" }]).map((g) => {
        const ls = data.lenses.lenses.filter((l) => !g.id || l.group === g.id);
        if (!ls.length) return "";
        return `${g.name ? `<h3 class="grp">${icon(`g-${g.id}`, "", { size: 16 })} ${esc(g.name)}</h3>` : ""}${ls.map((l) => `
          <div class="lens-entry"><div class="le-ic">${glyph(l, 26)}</div><div>
          <h4>${esc(l.name)}</h4><p>${esc(l.description)}<br>
          <i class="le-ramp" style="background:linear-gradient(90deg, ${(l.ramp || []).map(esc).join(",")})"></i>
          <span class="muted">Scale: ${esc(l.scale)}, ${l.domain[0].toLocaleString()}–${l.domain[1].toLocaleString()} ${esc(l.unit)}${
            l.higher_is === "good" ? " · higher is better" : l.higher_is === "bad" ? " · higher is worse" : ""}${l.source ? " · " + esc(srcName(l.source)) : ""}</span></p></div></div>`).join("")}`;
      }).join("")}`,

    Resources: () => {
      const r = data.resources;
      if (!r?.types?.length) return `${h2("resources", "⛏️", "Resources")}<p class="muted">No resources layer.</p>`;
      const count = new Map();
      for (const it of r.items || []) count.set(it.type, (count.get(it.type) || 0) + 1);
      const cats = [...new Set(r.types.map((tp) => tp.category || "other"))];
      return `
      ${h2("resources", "⛏️", t("Resources", "ทรัพยากรและโรงไฟฟ้า"))}
      <p>${t(
        "Resources mark Thailand's major power plants (natural gas stations, Mae Moh & industrial coal plants, EGAT hydroelectric dams, solar farms, Khorat Plateau wind farms and biomass facilities) from the WRI Global Power Plant Database. Press <b>R</b> to toggle.",
        "แสดงตำแหน่งโรงไฟฟ้าหลักของไทย (ก๊าซธรรมชาติ ถ่านหินแม่เมาะ เขื่อนพลังน้ำ กฟผ. โซลาร์ฟาร์ม กังหันลม และชีวมวล) จากฐานข้อมูล WRI Global Power Plant Database กด <b>R</b> เพื่อเปิดหรือปิด"
      )}</p>
      ${cats.map((c) => `<h4>${esc(CATEGORY[c] || c)}</h4><table class="res-table">
        <tr><th></th><th>${t("Type", "ประเภท")}</th><th>${t("What counts", "รายละเอียด")}</th><th>${t("Sites", "จำนวนแห่ง")}</th></tr>
        ${r.types.filter((tp) => (tp.category || "other") === c).map((tp) => `<tr>
          <td class="ic"><span class="res-ic" style="background:${esc(tp.color || "#24384f")};color:${inkOn(tp.color)}">${glyph(tp, 20)}</span></td>
          <td class="nm"><b>${esc(tp.name)}</b>${tp.unit ? `<br><span class="muted">${esc(tp.unit)}</span>` : ""}</td>
          <td>${esc(tp.description || "")}<br><span class="muted">${t("Source", "แหล่งข้อมูล")}: ${esc(srcName(tp.source))}</span></td>
          <td class="num">${count.get(tp.id) || 0}</td></tr>`).join("")}</table>`).join("")}`;
    },

    Sources: () => `
      ${h2("pedia", "📖", t("Sources & Validation References", "แหล่งข้อมูลและลิงก์ตรวจสอบอ้างอิง"))}
      <p>${t(
        `Every figure in thaiciv traces to these <b>${data.sources.length} official public sources</b>. Click any publisher homepage or direct file URL below to verify the raw data against its recorded SHA-256 checksum, or inspect the full manifest in <a href="data/sources.json" target="_blank" rel="noopener noreferrer"><code>data/sources.json</code></a>.`,
        `ตัวเลขทุกตัวใน thaiciv ตรวจสอบย้อนกลับได้จาก <b>${data.sources.length} แหล่งข้อมูลสาธารณะทางการ</b> ด้านล่าง สามารถคลิกลิงก์หน้าหลักหรือ URL ไฟล์ต้นฉบับเพื่อตรวจสอบเทียบกับรหัส SHA-256 หรือเปิดดูรายการเต็มใน <a href="data/sources.json" target="_blank" rel="noopener noreferrer"><code>data/sources.json</code></a>`
      )}</p>
      ${data.sources.map((s) => `
        <h4>${esc(s.title)}</h4>
        <p>${esc(s.description)}<br>
        <span class="muted">${esc(s.publisher)} · ${esc(s.license)}${s.vintage ? " · " + esc(s.vintage) : ""}${
          s.homepage ? ` · <a href="${esc(s.homepage)}" target="_blank" rel="noopener noreferrer">${t("Official homepage ↗", "เว็บไซต์ต้นทาง ↗")}</a>` : ""
        }</span></p>
        <table>${(s.files || []).map((f) => `<tr>
          <td>
            <a class="src-url" href="${esc(f.url)}" target="_blank" rel="noopener noreferrer">${esc(f.url)}</a>
            ${f.sha256 ? `<br><span class="src-hash" title="Full SHA-256: ${esc(f.sha256)}">sha256: ${esc(f.sha256.slice(0, 16))}…</span>` : ""}
          </td>
          <td class="muted" style="white-space:nowrap">${esc((f.retrieved || "").slice(0, 10))}<br>${((f.bytes || 0) / 1e6).toFixed(2)} MB</td>
        </tr>`).join("")}</table>`).join("")}`,
  };

  function renderNav() {
    nav.innerHTML = `<div class="hd">${t("Almanac", "สารานุกรม")}</div>` +
      Object.keys(pages).map((p) => `<button data-page="${esc(p)}">${esc(PAGE_LABELS[p] ? PAGE_LABELS[p]() : p)}</button>`).join("");
  }

  const show = (name) => {
    if (!pages[name]) name = "About this map";
    currentPage = name;
    renderNav();
    body.innerHTML = pages[name]();
    body.scrollTop = 0;
    nav.querySelectorAll("button").forEach((b) => {
      const on = b.dataset.page === name;
      b.classList.toggle("active", on);
      b.setAttribute("aria-current", on ? "page" : "false");
    });
  };
  renderNav();
  nav.onclick = (e) => {
    const b = e.target.closest("button[data-page]");
    if (b) show(b.dataset.page);
  };
  body.addEventListener("click", (e) => {
    const j = e.target.closest("a[data-jump]");
    if (!j) return;
    e.preventDefault();
    show(j.dataset.jump);
  });
  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    if (restoreFocus && document.contains(restoreFocus)) restoreFocus.focus();
    restoreFocus = null;
  };
  modal.onclick = (e) => {
    if (e.target === modal || e.target.closest("[data-close]")) close();
  };
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...card.querySelectorAll("button, a[href], [tabindex]:not([tabindex='-1'])")].filter((x) => x.offsetParent);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  return {
    open(page = "About this map") {
      if (modal.hidden) restoreFocus = document.activeElement;
      show(page);
      modal.hidden = false;
      (nav.querySelector("button.active") || card.querySelector("[data-close]"))?.focus();
    },
    close,
    refresh() {
      if (!modal.hidden) show(currentPage);
      else renderNav();
    },
    get isOpen() {
      return !modal.hidden;
    },
  };
}
