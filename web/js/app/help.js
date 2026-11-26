// Keyboard & mouse cheat-sheet.
import { icon } from "../ui/icon.js";
import { t, isTh } from "../i18n.js";

const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "");
const MOD = isMac ? "⌘" : "Ctrl";

const rowsFor = () => isTh() ? [
  ["การเลื่อนและซูม", [
    [["ลากเมาส์", "←↑→↓", "WASD"], "เลื่อนแผนที่"],
    [["เลื่อนลูกกลิ้ง", "+", "–"], "ซูมเข้าและออก"],
    [["ดับเบิลคลิก"], "ซูมเข้าไปยังตำแหน่งนั้น"],
    [["สองนิ้ว"], "ถ่างนิ้วเพื่อซูม ลากเพื่อเลื่อน (จอสัมผัส)"],
    [["แผนที่ย่อ"], "คลิกหรือลากเพื่อกระโดดไปยังพื้นที่"],
  ]],
  ["การสำรวจข้อมูล", [
    [["คลิกเมือง"], "เปิดหน้าจอมุมมองเมือง"],
    [["คลิกพื้นที่"], "เปิดข้อมูลจังหวัดนั้น"],
    [["/", `${MOD} K`], "ค้นหาเมืองและจังหวัด (ไทย / EN)"],
    [["L", "Shift L"], "สลับเลนส์ถัดไป / ก่อนหน้า"],
    [["แถบสีเลนส์"], "ชี้หรือลากเพื่อกรองดูเฉพาะช่วงค่า"],
    [["R"], "แสดงหรือซ่อนทรัพยากรบนแผนที่"],
  ]],
  ["หน้าต่างและคำสั่ง", [
    [["?"], "เปิดหน้าต่างวิธีใช้งานนี้"],
    [["Esc"], "ปิดหน้าต่าง ค้นหา สารานุกรม หรือแผงข้อมูล"],
  ]],
] : [
  ["Move", [
    [["Drag", "←↑→↓", "WASD"], "Pan the map"],
    [["Scroll", "+", "–"], "Zoom in and out"],
    [["Double-click"], "Zoom in on a spot"],
    [["Two fingers"], "Pinch to zoom, drag to pan (touch)"],
    [["Minimap"], "Click or drag to jump"],
  ]],
  ["Explore", [
    [["Click city"], "Open the city screen"],
    [["Click land"], "Open that province"],
    [["/", `${MOD} K`], "Search cities and provinces (EN / ไทย)"],
    [["L", "Shift L"], "Next / previous lens"],
    [["Legend"], "Hover or drag the scale to show only that range"],
    [["R"], "Show or hide resources"],
  ]],
  ["Panels", [
    [["?"], "This help"],
    [["Esc"], "Close help, search, Almanac, then the panel"],
  ]],
];

export function initHelp() {
  const modal = document.getElementById("help");
  if (!modal) return { open() {}, close() {}, refresh() {}, get isOpen() { return false; } };
  const card = modal.querySelector(".help-card");
  let restore = null;
  function render() {
    card.innerHTML = `
      <button class="icon-btn help-close" data-close aria-label="${t("Close help", "ปิดหน้าต่างช่วยเหลือ")}">${icon("close", "✕", { size: 13 })}</button>
      <h2 id="help-title">${icon("help", "?", { size: 22 })}<span>${t("Controls", "วิธีใช้งานและคีย์ลัด")}</span></h2>
      <div class="help-cols">${rowsFor().map(([title, rows]) => `
        <section><h3>${title}</h3>${rows.map(([keys, what]) => `
          <div class="help-row"><span class="keys">${keys.map((k) => `<kbd>${k}</kbd>`).join("")}</span><span>${what}</span></div>`).join("")}
        </section>`).join("")}</div>
      <p class="help-foot">${t(
        'Every number traces back to public Thai &amp; global data: open the <b>Almanac</b> for sources. The link in the address bar always reopens this exact view. <b>thaiciv</b> is built on the MIT-licensed <i>usaciv</i> engine by Andrej Karpathy.',
        'ตัวเลขทั้งหมดมาจากข้อมูลสาธารณะทางการของไทยและสากล เปิดดูรายละเอียดได้ใน <b>สารานุกรม (Almanac)</b> ลิงก์บนแถบที่อยู่สามารถแชร์เพื่อเปิดมุมมองเดิมได้ทันที <b>thaiciv</b> พัฒนาต่อยอดจากเอนจิน <i>usaciv</i> (MIT) ของ Andrej Karpathy'
      )}</p>`;
  }
  render();

  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    if (restore && document.contains(restore)) restore.focus();
    restore = null;
  };
  modal.addEventListener("click", (e) => {
    if (e.target === modal || e.target.closest("[data-close]")) close();
  });
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    e.preventDefault(); // the only focusable control is the close button
    card.querySelector("[data-close]").focus();
  });

  return {
    open() {
      if (!modal.hidden) return;
      render();
      restore = document.activeElement;
      modal.hidden = false;
      card.querySelector("[data-close]").focus();
    },
    close,
    refresh() { if (!modal.hidden) render(); },
    toggle() { modal.hidden ? this.open() : close(); },
    get isOpen() { return !modal.hidden; },
  };
}
