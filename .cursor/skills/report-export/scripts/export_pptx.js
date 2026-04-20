const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

function usage() {
  console.error('Usage: node export_pptx.js <slide_plan_json_path> <output_pptx_path>');
  process.exit(2);
}

if (process.argv.length !== 4) usage();

const slidePlanPath = path.resolve(process.argv[2]);
const outputPath = path.resolve(process.argv[3]);
if (!fs.existsSync(slidePlanPath)) {
  console.error(`Slide plan not found: ${slidePlanPath}`);
  process.exit(1);
}

function themePalette(name) {
  const palettes = {
    blue:   { accent: '2563EB', soft: 'EFF6FF', border: 'BFDBFE', dark: '1D4ED8', text: '0F172A' },
    teal:   { accent: '0F766E', soft: 'F0FDFA', border: '99F6E4', dark: '115E59', text: '0F172A' },
    indigo: { accent: '4F46E5', soft: 'EEF2FF', border: 'C7D2FE', dark: '3730A3', text: '111827' },
    purple: { accent: '7C3AED', soft: 'F5F3FF', border: 'DDD6FE', dark: '6D28D9', text: '111827' },
    green:  { accent: '15803D', soft: 'F0FDF4', border: 'BBF7D0', dark: '166534', text: '111827' },
    red:    { accent: 'DC2626', soft: 'FEF2F2', border: 'FECACA', dark: '991B1B', text: '111827' },
    amber:  { accent: 'D97706', soft: 'FFFBEB', border: 'FDE68A', dark: '92400E', text: '111827' },
    slate:  { accent: '475569', soft: 'F8FAFC', border: 'CBD5E1', dark: '334155', text: '111827' },
  };
  return palettes[name] || palettes.slate;
}

function safeOuterShadow(color = '000000', opacity = 0.08, angle = 45, blur = 1.5, distance = 0.35) {
  return { type: 'outer', color, opacity, angle, blur, distance };
}

function calcTextBoxHeight(fontSizePt, lineCount, lineSpacing = 1.18, padInches = 0.04) {
  return (fontSizePt / 72) * lineCount * lineSpacing + padInches * 2;
}

function approxLines(text, charsPerLine) {
  return Math.max(1, Math.ceil(String(text || '').length / charsPerLine));
}

function addFooter(slide, reportTitle, slideNumber, totalSlides, palette) {
  slide.addShape('line', {
    x: 0.7, y: 6.67, w: 11.9, h: 0,
    line: { color: 'E5E7EB', pt: 1 }
  });
  slide.addText(reportTitle, {
    x: 0.82, y: 6.78, w: 8.8, h: 0.16,
    fontFace: 'Aptos', fontSize: 8.5, color: '94A3B8'
  });
  slide.addText(`${slideNumber} / ${totalSlides}`, {
    x: 11.08, y: 6.76, w: 1.02, h: 0.16,
    fontFace: 'Aptos', fontSize: 9, color: '64748B', bold: true, align: 'right', margin: 0.01
  });
}

function addSectionChip(slide, spec, palette, opts = {}) {
  return;
}

function addTitle(slide, title) {
  slide.addText(title, {
    x: 0.82, y: 0.76, w: 10.8, h: 0.48,
    fontFace: 'Aptos Display', fontSize: 22, bold: true, color: '111827'
  });
}

function addLeadCallout(slide, lead, palette, opts = {}) {
  if (!lead) return 0;
  const x = opts.x || 0.82;
  const y = opts.y || 1.3;
  const w = opts.w || 11.0;
  const lines = approxLines(lead, 88);
  const h = Math.min(0.96, Math.max(0.46, calcTextBoxHeight(12, lines, 1.15, 0.05)));
  slide.addShape('roundRect', {
    x, y, w, h,
    rectRadius: 0.06,
    line: { color: palette.border, pt: 0.8 },
    fill: { color: palette.soft },
  });
  slide.addText(lead, {
    x: x + 0.16, y: y + 0.11, w: w - 0.32, h: h - 0.16,
    fontFace: 'Aptos', fontSize: 12, color: '334155', margin: 0.01, valign: 'mid'
  });
  return h + 0.14;
}

function addBulletCard(slide, text, palette, opts = {}) {
  const x = opts.x || 0;
  const y = opts.y || 0;
  const w = opts.w || 0;
  const indexLabel = opts.indexLabel || null;
  const compact = Boolean(opts.compact);
  const charsPerLine = Math.max(compact ? 24 : 28, Math.floor(w * (compact ? 12.5 : 11)));
  const lines = approxLines(text, charsPerLine);
  const fontSize = compact ? 12.5 : 14;
  const minH = compact ? 0.88 : 0.78;
  const maxH = compact ? 1.12 : 1.35;
  const h = Math.max(minH, Math.min(maxH, calcTextBoxHeight(fontSize, lines, compact ? 1.08 : 1.14, 0.05)));
  slide.addShape('roundRect', {
    x, y, w, h,
    rectRadius: 0.05,
    line: { color: 'E5E7EB', pt: 0.8 },
    fill: { color: 'FFFFFF' },
    shadow: safeOuterShadow('000000', 0.05, 45, 1.2, 0.25),
  });
  if (indexLabel) {
    slide.addShape('roundRect', {
      x: x + 0.12, y: y + 0.12, w: 0.34, h: 0.22,
      rectRadius: 0.03,
      line: { color: palette.accent, pt: 0 },
      fill: { color: palette.accent },
    });
    slide.addText(indexLabel, {
      x: x + 0.18, y: y + 0.18, w: 0.12, h: 0.08,
      fontFace: 'Aptos', fontSize: 9, bold: true, color: 'FFFFFF', align: 'center'
    });
  }
  slide.addText(text, {
    x: x + (indexLabel ? 0.58 : 0.16), y: y + 0.12, w: w - (indexLabel ? 0.72 : 0.3), h: h - 0.18,
    fontFace: 'Aptos', fontSize: fontSize, color: '1F2937', margin: 0.01, valign: 'mid'
  });
  return h;
}

function renderTitleSlide(slide, spec, meta, slideNumber, totalSlides) {
  const palette = themePalette('indigo');
  slide.background = { color: 'F8FAFC' };
  slide.addShape('rect', { x: 0, y: 0, w: 13.333, h: 7.5, line: { color: 'F8FAFC', pt: 0 }, fill: { color: 'F8FAFC' } });
  slide.addShape('rect', { x: 9.6, y: 0, w: 3.733, h: 7.5, line: { color: palette.soft, pt: 0 }, fill: { color: 'EEF2FF' } });
  slide.addShape('roundRect', {
    x: 0.78, y: 0.95, w: 10.35, h: 4.95,
    rectRadius: 0.08,
    line: { color: 'E5E7EB', pt: 0.8 },
    fill: { color: 'FFFFFF' },
    shadow: safeOuterShadow('000000', 0.07, 45, 1.8, 0.35),
  });
  slide.addShape('roundRect', {
    x: 1.04, y: 1.22, w: 1.5, h: 0.32,
    rectRadius: 0.03,
    line: { color: palette.border, pt: 0.5 },
    fill: { color: palette.soft },
  });
  slide.addText('Research report', {
    x: 1.18, y: 1.3, w: 1.1, h: 0.1,
    fontFace: 'Aptos', fontSize: 10, bold: true, color: palette.dark
  });
  slide.addText(spec.title || meta.report_title || 'Research Report', {
    x: 1.03, y: 1.78, w: 8.7, h: 0.95,
    fontFace: 'Aptos Display', fontSize: 28, bold: true, color: '111827'
  });
  slide.addText(spec.subtitle || `Grounded item: ${meta.ground_id || 'report'}`, {
    x: 1.08, y: 2.92, w: 7.2, h: 0.28,
    fontFace: 'Aptos', fontSize: 12, color: '64748B'
  });
  slide.addShape('line', { x: 1.05, y: 3.35, w: 8.95, h: 0, line: { color: 'E2E8F0', pt: 1 } });
  slide.addText('Presentation export generated from the reviewed final report. The layout is optimized for slide readability while preserving the original research content.', {
    x: 1.06, y: 3.62, w: 8.65, h: 0.8,
    fontFace: 'Aptos', fontSize: 14, color: '334155', margin: 0.01
  });
  let y = 4.65;
  const infoItems = spec.info || meta.info || [];
  infoItems.forEach(([label, value]) => {
    slide.addShape('roundRect', {
      x: 1.06, y, w: 1.75, h: 0.52,
      rectRadius: 0.04,
      line: { color: 'E2E8F0', pt: 0.8 },
      fill: { color: 'F8FAFC' },
    });
    slide.addText(label, {
      x: 1.2, y: y + 0.11, w: 0.7, h: 0.1,
      fontFace: 'Aptos', fontSize: 9.5, color: '64748B', bold: true
    });
    slide.addText(value, {
      x: 1.2, y: y + 0.24, w: 0.9, h: 0.12,
      fontFace: 'Aptos Display', fontSize: 14, color: '0F172A', bold: true
    });
    y += 0.64;
  });
  slide.addShape('roundRect', {
    x: 10.02, y: 1.08, w: 2.28, h: 1.55,
    rectRadius: 0.08,
    line: { color: palette.border, pt: 0.7 },
    fill: { color: 'FFFFFF' },
  });
  slide.addText('Grounded item', {
    x: 10.24, y: 1.34, w: 1.5, h: 0.1,
    fontFace: 'Aptos', fontSize: 9.5, color: '64748B', bold: true
  });
  slide.addText(meta.ground_id || 'report', {
    x: 10.24, y: 1.58, w: 1.75, h: 0.46,
    fontFace: 'Aptos Display', fontSize: 14, color: '111827', bold: true
  });
  slide.addShape('roundRect', {
    x: 10.02, y: 2.9, w: 2.28, h: 1.2,
    rectRadius: 0.08,
    line: { color: palette.border, pt: 0.7 },
    fill: { color: palette.soft },
  });
  slide.addText('Design note', {
    x: 10.24, y: 3.12, w: 1.4, h: 0.1,
    fontFace: 'Aptos', fontSize: 9.5, color: palette.dark, bold: true
  });
  slide.addText('Condensed section planning with denser continuation pages.', {
    x: 10.24, y: 3.35, w: 1.72, h: 0.44,
    fontFace: 'Aptos', fontSize: 10.5, color: '334155', margin: 0.01
  });
  addFooter(slide, meta.report_title || spec.title || 'Research Report', slideNumber, totalSlides, palette);
}

function renderSummaryGridSlide(slide, spec, meta, slideNumber, totalSlides, isClosing = false) {
  const palette = themePalette(spec.theme || (isClosing ? 'purple' : 'blue'));
  slide.background = { color: 'FFFFFF' };
  addSectionChip(slide, spec, palette);
  addTitle(slide, spec.title || (isClosing ? 'Conclusion' : 'Summary'));
  const leadOffset = addLeadCallout(slide, spec.lead || null, palette, { x: 0.82, y: 1.3, w: 11.2 });

  const bullets = Array.isArray(spec.bullets) ? spec.bullets : [];
  const positions = [
    { x: 0.92, y: 1.48 + leadOffset, w: 5.4 },
    { x: 6.48, y: 1.48 + leadOffset, w: 5.4 },
    { x: 0.92, y: 3.56 + leadOffset, w: 5.4 },
    { x: 6.48, y: 3.56 + leadOffset, w: 5.4 },
  ];
  bullets.slice(0, 4).forEach((bullet, idx) => {
    const pos = positions[idx];
    slide.addShape('roundRect', {
      x: pos.x, y: pos.y, w: pos.w, h: 1.65,
      rectRadius: 0.06,
      line: { color: idx === 0 ? palette.border : 'E5E7EB', pt: 0.8 },
      fill: { color: idx === 0 ? palette.soft : 'FFFFFF' },
      shadow: safeOuterShadow('000000', 0.04, 45, 1, 0.2),
    });
    slide.addShape('roundRect', {
      x: pos.x + 0.18, y: pos.y + 0.18, w: 0.34, h: 0.22,
      rectRadius: 0.03,
      line: { color: palette.accent, pt: 0 },
      fill: { color: palette.accent },
    });
    slide.addText(String(idx + 1), {
      x: pos.x + 0.25, y: pos.y + 0.24, w: 0.1, h: 0.08,
      fontFace: 'Aptos', fontSize: 9, bold: true, color: 'FFFFFF', align: 'center'
    });
    slide.addText(bullet, {
      x: pos.x + 0.65, y: pos.y + 0.18, w: pos.w - 0.85, h: 1.18,
      fontFace: 'Aptos', fontSize: 16, color: '1F2937', margin: 0.01, valign: 'mid'
    });
  });
  addFooter(slide, meta.report_title || spec.title || 'Research Report', slideNumber, totalSlides, palette);
}

function renderInsightSlide(slide, spec, meta, slideNumber, totalSlides) {
  const palette = themePalette(spec.theme || 'slate');
  slide.background = { color: 'FFFFFF' };
  slide.addShape('roundRect', {
    x: 0.78, y: 0.78, w: 3.18, h: 5.65,
    rectRadius: 0.08,
    line: { color: palette.border, pt: 0.8 },
    fill: { color: palette.soft },
  });
  slide.addShape('rect', {
    x: 0.78, y: 0.78, w: 0.12, h: 5.65,
    line: { color: palette.accent, pt: 0 },
    fill: { color: palette.accent },
  });
  slide.addShape('roundRect', {
    x: 1.12, y: 1.08, w: 0.6, h: 0.36,
    rectRadius: 0.03,
    line: { color: palette.accent, pt: 0 },
    fill: { color: palette.accent },
  });
  slide.addText(String(spec.section_number || ''), {
    x: 1.28, y: 1.18, w: 0.18, h: 0.09,
    fontFace: 'Aptos', fontSize: 11, bold: true, color: 'FFFFFF', align: 'center'
  });

  const sidebarTitle = spec.section_plain_title || spec.source_section || 'Section';
  const titleLines = approxLines(sidebarTitle, 11);
  const titleFont = titleLines >= 4 ? 16 : titleLines === 3 ? 18 : 20;
  const titleHeight = Math.max(0.55, Math.min(1.18, calcTextBoxHeight(titleFont, titleLines, 1.05, 0.02)));
  const titleY = 1.66;
  slide.addText(sidebarTitle, {
    x: 1.04, y: titleY, w: 2.34, h: titleHeight,
    fontFace: 'Aptos Display', fontSize: titleFont, bold: true, color: '111827', margin: 0.01
  });

  const takeawayLabelY = titleY + titleHeight + 0.16;
  slide.addText('Key takeaway', {
    x: 1.04, y: takeawayLabelY, w: 1.3, h: 0.1,
    fontFace: 'Aptos', fontSize: 10, color: palette.dark, bold: true
  });
  const takeawayBoxY = takeawayLabelY + 0.26;
  const takeawayBoxH = Math.max(1.8, 4.95 - (takeawayBoxY - 1.08));
  slide.addShape('roundRect', {
    x: 1.02, y: takeawayBoxY, w: 2.56, h: takeawayBoxH,
    rectRadius: 0.06,
    line: { color: 'FFFFFF', pt: 0 },
    fill: { color: 'FFFFFF' },
    shadow: safeOuterShadow('000000', 0.04, 45, 1, 0.2),
  });
  const takeaway = spec.takeaway || spec.lead || '';
  const takeawayLines = approxLines(takeaway, 16);
  const takeawayFont = takeawayLines >= 9 ? 12.5 : takeawayLines >= 7 ? 13.5 : 15;
  slide.addText(takeaway, {
    x: 1.18, y: takeawayBoxY + 0.16, w: 2.18, h: takeawayBoxH - 0.22,
    fontFace: 'Aptos', fontSize: takeawayFont, bold: true, color: '1F2937', margin: 0.01, valign: 'mid'
  });

  addSectionChip(slide, spec, palette, { x: 4.32, y: 0.45, w: 3.4 });
  slide.addText(spec.title || spec.source_section || 'Section', {
    x: 4.32, y: 0.88, w: 7.7, h: 0.46,
    fontFace: 'Aptos Display', fontSize: 22, bold: true, color: '111827'
  });
  const insightBullets = (spec.bullets || []).slice(0, 4);
  if (insightBullets.length >= 4) {
    const positions = [
      { x: 4.34, y: 1.52, w: 3.62 },
      { x: 8.16, y: 1.52, w: 3.62 },
      { x: 4.34, y: 3.08, w: 3.62 },
      { x: 8.16, y: 3.08, w: 3.62 },
    ];
    insightBullets.forEach((bullet, idx) => {
      addBulletCard(slide, bullet, palette, { ...positions[idx], indexLabel: String(idx + 1), compact: true });
    });
  } else {
    let y = 1.52;
    insightBullets.forEach((bullet, idx) => {
      const h = addBulletCard(slide, bullet, palette, { x: 4.34, y, w: 7.56, indexLabel: String(idx + 1) });
      y += h + 0.18;
    });
  }
  addFooter(slide, meta.report_title || spec.title || 'Research Report', slideNumber, totalSlides, palette);
}

function renderBulletsSlide(slide, spec, meta, slideNumber, totalSlides) {
  const palette = themePalette(spec.theme || 'slate');
  slide.background = { color: 'FFFFFF' };
  addSectionChip(slide, spec, palette);
  addTitle(slide, spec.title || 'Section');
  const leadOffset = addLeadCallout(slide, spec.lead || null, palette, { x: 0.82, y: 1.3, w: 11.2 });

  const bullets = Array.isArray(spec.bullets) ? spec.bullets : [];
  const topY = 1.46 + leadOffset;
  const denseLayout = Boolean(spec.dense_layout) || bullets.length >= 5;
  const twoCol = !denseLayout && bullets.length >= 4 && bullets.every((b) => String(b).length <= 170);

  if (denseLayout) {
    const positions = [
      { x: 0.92, y: topY, w: 5.32 },
      { x: 6.42, y: topY, w: 5.32 },
      { x: 0.92, y: topY + 1.28, w: 5.32 },
      { x: 6.42, y: topY + 1.28, w: 5.32 },
      { x: 0.92, y: topY + 2.56, w: 5.32 },
      { x: 6.42, y: topY + 2.56, w: 5.32 },
    ];
    bullets.slice(0, 6).forEach((bullet, idx) => {
      addBulletCard(slide, bullet, palette, { ...positions[idx], indexLabel: String(idx + 1), compact: true });
    });
  } else if (twoCol) {
    const positions = [
      { x: 0.92, y: topY, w: 5.32 },
      { x: 6.42, y: topY, w: 5.32 },
      { x: 0.92, y: topY + 1.7, w: 5.32 },
      { x: 6.42, y: topY + 1.7, w: 5.32 },
    ];
    bullets.slice(0, 4).forEach((bullet, idx) => {
      addBulletCard(slide, bullet, palette, { ...positions[idx], indexLabel: String(idx + 1) });
    });
  } else {
    let y = topY;
    bullets.slice(0, 4).forEach((bullet, idx) => {
      const h = addBulletCard(slide, bullet, palette, { x: 0.92, y, w: 10.96, indexLabel: String(idx + 1) });
      y += h + 0.16;
    });
  }
  addFooter(slide, meta.report_title || spec.title || 'Research Report', slideNumber, totalSlides, palette);
}

function renderTableSlide(slide, spec, meta, slideNumber, totalSlides) {
  const palette = themePalette(spec.theme || 'slate');
  slide.background = { color: 'FFFFFF' };
  addSectionChip(slide, spec, palette);
  addTitle(slide, spec.title || 'Table');

  slide.addShape('roundRect', {
    x: 0.88, y: 1.42, w: 11.05, h: 4.95,
    rectRadius: 0.06,
    line: { color: 'E5E7EB', pt: 0.8 },
    fill: { color: 'FFFFFF' },
    shadow: safeOuterShadow('000000', 0.04, 45, 1, 0.2),
  });

  const headers = (spec.headers || []).map((x) => String(x || ''));
  const rows = (spec.rows || []).map((row) => (row || []).map((x) => String(x || '')));
  const tableRows = [headers, ...rows];
  const nCols = Math.max(1, headers.length || (rows[0] || []).length || 1);
  const colW = Math.min(3.2, 10.2 / nCols);
  const colWidths = Array.from({ length: nCols }, () => colW);
  const maxRows = headers.length ? 9 : 10;
  const clippedRows = tableRows.slice(0, maxRows);
  if (tableRows.length > maxRows) {
    const filler = Array.from({ length: nCols }, (_, idx) => (idx === 0 ? '…' : ''));
    clippedRows[clippedRows.length - 1] = filler;
  }

  slide.addTable(clippedRows, {
    x: 1.16, y: 1.78, w: 10.5, h: 4.15,
    colW: colWidths,
    border: { type: 'solid', color: 'D1D5DB', pt: 1 },
    fill: 'FFFFFF',
    color: '1F2937',
    fontFace: 'Aptos',
    fontSize: 11,
    margin: 0.04,
    valign: 'mid',
    bold: false,
    autoFit: true,
    rowH: 0.42,
    bandRow: true,
    fillHeader: palette.soft,
    colorHeader: '111827',
    boldHeader: true,
  });
  addFooter(slide, meta.report_title || spec.title || 'Research Report', slideNumber, totalSlides, palette);
}

function renderFigureSlide(slide, spec, meta, slideNumber, totalSlides) {
  const palette = themePalette(spec.theme || 'slate');
  slide.background = { color: 'FFFFFF' };
  addSectionChip(slide, spec, palette);
  addTitle(slide, spec.title || 'Figure');

  const imgPath = spec.image_path ? path.resolve(spec.image_path) : null;
  const boxX = 0.96;
  const boxY = 1.46;
  const boxW = 11.0;
  const boxH = 4.8;

  slide.addShape('roundRect', {
    x: boxX, y: boxY, w: boxW, h: boxH,
    rectRadius: 0.06,
    line: { color: 'E5E7EB', pt: 0.8 },
    fill: { color: 'FFFFFF' },
  });
  if (imgPath && fs.existsSync(imgPath)) {
    slide.addImage({ path: imgPath, x: boxX + 0.18, y: boxY + 0.18, w: boxW - 0.36, h: boxH - 0.36, contain: true });
  } else {
    slide.addText('Figure placeholder', {
      x: boxX + 0.2, y: boxY + 1.78, w: boxW - 0.4, h: 0.35,
      fontFace: 'Aptos Display', fontSize: 20, bold: true, color: '94A3B8', align: 'center'
    });
    slide.addText(imgPath ? `Image file not found: ${imgPath}` : 'No image path available in slide plan.', {
      x: boxX + 0.3, y: boxY + 2.26, w: boxW - 0.6, h: 0.4,
      fontFace: 'Aptos', fontSize: 11, color: '64748B', align: 'center'
    });
  }
  if (spec.caption) {
    slide.addText(spec.caption, {
      x: 1.02, y: 6.1, w: 10.86, h: 0.18,
      fontFace: 'Aptos', fontSize: 10.5, color: '475569', align: 'center'
    });
  }
  addFooter(slide, meta.report_title || spec.title || 'Research Report', slideNumber, totalSlides, palette);
}

async function main() {
  const plan = JSON.parse(fs.readFileSync(slidePlanPath, 'utf8'));
  const slides = Array.isArray(plan.slides) ? plan.slides : [];
  const meta = plan.meta || {};

  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';
  pptx.author = 'OpenAI';
  pptx.company = 'OpenAI';
  pptx.subject = 'Exported research report';
  pptx.title = meta.report_title || 'Research Report';
  pptx.lang = 'en-US';
  pptx.theme = { headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'en-US' };

  slides.forEach((spec, idx) => {
    const slide = pptx.addSlide();
    const type = spec.type || 'bullets';
    const slideNumber = idx + 1;
    const totalSlides = slides.length;

    if (type === 'title') {
      renderTitleSlide(slide, spec, meta, slideNumber, totalSlides);
    } else if (type === 'summary') {
      renderSummaryGridSlide(slide, spec, meta, slideNumber, totalSlides, false);
    } else if (type === 'closing') {
      renderSummaryGridSlide(slide, spec, meta, slideNumber, totalSlides, true);
    } else if (type === 'insight') {
      renderInsightSlide(slide, spec, meta, slideNumber, totalSlides);
    } else if (type === 'table') {
      renderTableSlide(slide, spec, meta, slideNumber, totalSlides);
    } else if (type === 'figure') {
      renderFigureSlide(slide, spec, meta, slideNumber, totalSlides);
    } else {
      renderBulletsSlide(slide, spec, meta, slideNumber, totalSlides);
    }
  });

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  await pptx.writeFile({ fileName: outputPath });
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
