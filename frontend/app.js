const state = {
  world: "",
  plot: "",
  novel: "",
  cover: "",
  directions: [],
  publicLibraries: {},
};

const $ = (selector) => document.querySelector(selector);

const els = {
  cacheState: $("#cacheState"),
  referenceFile: $("#referenceFile"),
  referenceText: $("#referenceText"),
  uploadBtn: $("#uploadBtn"),
  analyzeBtn: $("#analyzeBtn"),
  generateAllBtn: $("#generateAllBtn"),
  checkinBtn: $("#checkinBtn"),
  worldBtn: $("#worldBtn"),
  plotBtn: $("#plotBtn"),
  coverBtn: $("#coverBtn"),
  directionsBtn: $("#directionsBtn"),
  novelBtn: $("#novelBtn"),
  uploadStatus: $("#uploadStatus"),
  styleOutput: $("#styleOutput"),
  worldOutput: $("#worldOutput"),
  plotOutput: $("#plotOutput"),
  coverOutput: $("#coverOutput"),
  directionsOutput: $("#directionsOutput"),
  novelOutput: $("#novelOutput"),
  analysisMeta: $("#analysisMeta"),
  worldMeta: $("#worldMeta"),
  plotMeta: $("#plotMeta"),
  coverMeta: $("#coverMeta"),
  directionsMeta: $("#directionsMeta"),
  novelMeta: $("#novelMeta"),
  publicLibrary: $("#publicLibrary"),
  networkCanvas: $("#networkCanvas"),
  chapterText: $("#chapterText"),
  chapterIntelBtn: $("#chapterIntelBtn"),
  chapterIntelOutput: $("#chapterIntelOutput"),
  deconstructText: $("#deconstructText"),
  deconstructBtn: $("#deconstructBtn"),
  deconstructOutput: $("#deconstructOutput"),
  reviewText: $("#reviewText"),
  reviewBtn: $("#reviewBtn"),
  reviewOutput: $("#reviewOutput"),
  infoQuery: $("#infoQuery"),
  infoPlatform: $("#infoPlatform"),
  infoBtn: $("#infoBtn"),
  infoOutput: $("#infoOutput"),
  historyBtn: $("#historyBtn"),
  historyOutput: $("#historyOutput"),
  toast: $("#toast"),
};

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadPublicLibraries();
  refreshCacheState();
  refreshHistory();
  renderNetwork();
});

function bindEvents() {
  els.uploadBtn.addEventListener("click", uploadReference);
  els.analyzeBtn.addEventListener("click", analyzeReference);
  els.generateAllBtn.addEventListener("click", generateAll);
  els.checkinBtn.addEventListener("click", dailyCheckin);
  els.worldBtn.addEventListener("click", generateWorld);
  els.plotBtn.addEventListener("click", generatePlot);
  els.coverBtn.addEventListener("click", generateCover);
  els.directionsBtn.addEventListener("click", generateDirections);
  els.novelBtn.addEventListener("click", generateNovel);
  els.referenceFile.addEventListener("change", showSelectedFile);
  $("#characters").addEventListener("input", renderNetwork);
  els.chapterIntelBtn.addEventListener("click", summarizeChapter);
  els.deconstructBtn.addEventListener("click", deconstructBook);
  els.reviewBtn.addEventListener("click", reviewText);
  els.infoBtn.addEventListener("click", queryInfo);
  els.historyBtn.addEventListener("click", refreshHistory);
}

async function loadPublicLibraries() {
  const response = await fetch("/public_libraries");
  state.publicLibraries = await response.json();
  els.publicLibrary.innerHTML = Object.entries(state.publicLibraries)
    .map(([name, item]) => `<option value="${escapeAttr(item.logic + " " + item.style)}">${name}</option>`)
    .join("");
}

function showSelectedFile() {
  const file = els.referenceFile.files[0];
  els.uploadStatus.textContent = file ? file.name : "私有库未载入";
}

async function uploadReference() {
  await withBusy(els.uploadBtn, "保存中", async () => {
    const formData = new FormData();
    const file = els.referenceFile.files[0];
    if (file) {
      formData.append("file", file);
    } else {
      formData.append("text", els.referenceText.value.trim());
    }

    const response = await fetch("/upload_reference", { method: "POST", body: formData });
    const data = await readResponse(response);
    els.uploadStatus.textContent = `${data.length} 字`;
    els.analysisMeta.textContent = "待分析";
    els.styleOutput.textContent = "私有库已保存，请进行文风分析";
    toast("私有库已保存");
    await refreshCacheState();
  });
}

async function analyzeReference() {
  await withBusy(els.analyzeBtn, "分析中", async () => {
    const response = await fetch("/analyze_reference", { method: "POST" });
    const data = await readResponse(response);
    els.styleOutput.textContent = JSON.stringify(data, null, 2);
    els.analysisMeta.textContent = "已完成";
    toast("文风分析完成");
    await refreshCacheState();
  });
}

async function generateAll() {
  await withBusy(els.generateAllBtn, "生成中", async () => {
    const response = await postJson("/generate_all", getSetting());
    const data = await readResponse(response);
    state.plot = data.outline;
    state.cover = data.cover.svg;
    state.novel = data.novel;
    state.directions = data.directions;
    renderText(els.plotOutput, data.outline);
    renderCover(data.cover.svg);
    renderText(els.novelOutput, data.novel);
    renderDirections(data.directions);
    els.plotMeta.textContent = "已生成";
    els.coverMeta.textContent = data.cover.title;
    els.novelMeta.textContent = "已生成";
    els.directionsMeta.textContent = "已生成";
    await refreshHistory();
    toast("大纲、封面、正文和走向已生成");
  });
}

async function generateWorld() {
  await withBusy(els.worldBtn, "生成中", async () => {
    const response = await postJson("/generate_world", getSetting());
    const data = await readResponse(response);
    state.world = data.content;
    renderText(els.worldOutput, data.content);
    els.worldMeta.textContent = "已生成";
    await refreshHistory();
    toast("世界观已生成");
  });
}

async function generatePlot() {
  await withBusy(els.plotBtn, "生成中", async () => {
    const payload = { ...getSetting(), world: state.world || els.worldOutput.textContent };
    const response = await postJson("/generate_outline", payload);
    const data = await readResponse(response);
    state.plot = data.content;
    renderText(els.plotOutput, data.content);
    els.plotMeta.textContent = "已生成";
    await refreshHistory();
    toast("完整大纲已生成");
  });
}

async function generateCover() {
  await withBusy(els.coverBtn, "生成中", async () => {
    const response = await postJson("/generate_cover", getSetting());
    const data = await readResponse(response);
    state.cover = data.svg;
    renderCover(data.svg);
    els.coverMeta.textContent = data.title;
    await refreshHistory();
    toast("封面已生成");
  });
}

async function generateDirections() {
  await withBusy(els.directionsBtn, "生成中", async () => {
    const payload = { ...getSetting(), world: state.world, plot: state.plot };
    const response = await postJson("/generate_directions", payload);
    const data = await readResponse(response);
    state.directions = data.directions;
    renderDirections(data.directions);
    els.directionsMeta.textContent = "已生成";
    await refreshHistory();
    toast("剧情走向已生成");
  });
}

async function generateNovel() {
  await withBusy(els.novelBtn, "生成中", async () => {
    const payload = {
      ...getSetting(),
      world: state.world || els.worldOutput.textContent.trim(),
      plot: state.plot || els.plotOutput.textContent.trim(),
    };
    const response = await postJson("/generate_novel", payload);
    const data = await readResponse(response);
    state.novel = data.content;
    renderText(els.novelOutput, data.content);
    els.novelMeta.textContent = "已生成";
    await refreshHistory();
    toast("正文内容已生成");
  });
}

async function summarizeChapter() {
  await withBusy(els.chapterIntelBtn, "汇总中", async () => {
    const response = await postJson("/summarize_chapter", { text: els.chapterText.value, title: "章节情报" });
    const data = await readResponse(response);
    els.chapterIntelOutput.innerHTML = renderIntel(data);
    await refreshHistory();
    toast("章节情报已汇总");
  });
}

async function deconstructBook() {
  await withBusy(els.deconstructBtn, "拆解中", async () => {
    const response = await postJson("/deconstruct_book", { text: els.deconstructText.value, title: "拆书报告" });
    const data = await readResponse(response);
    els.deconstructOutput.textContent = JSON.stringify(data, null, 2);
    await refreshHistory();
    toast("拆书报告已生成");
  });
}

async function reviewText() {
  await withBusy(els.reviewBtn, "审稿中", async () => {
    const response = await postJson("/review_text", { text: els.reviewText.value, title: "审稿报告" });
    const data = await readResponse(response);
    els.reviewOutput.textContent = JSON.stringify(data, null, 2);
    await refreshHistory();
    toast("审稿完成");
  });
}

async function queryInfo() {
  await withBusy(els.infoBtn, "查询中", async () => {
    const response = await postJson("/query_info", {
      query: els.infoQuery.value,
      platform: els.infoPlatform.value,
    });
    const data = await readResponse(response);
    els.infoOutput.textContent = JSON.stringify(data, null, 2);
    await refreshHistory();
    toast("资讯查询完成");
  });
}

async function dailyCheckin() {
  await withBusy(els.checkinBtn, "领取中", async () => {
    const response = await fetch("/daily_checkin", { method: "POST" });
    const data = await readResponse(response);
    toast(data.message);
  });
}

async function refreshHistory() {
  try {
    const response = await fetch("/history");
    const records = await response.json();
    if (!records.length) {
      els.historyOutput.textContent = "暂无记录";
      return;
    }
    els.historyOutput.innerHTML = records
      .slice(0, 12)
      .map(
        (record) => `
          <button class="history-item" type="button" data-content="${escapeAttr(record.content)}">
            <strong>${escapeHtml(record.title)}</strong>
            <span>${escapeHtml(record.kind)} · ${escapeHtml(record.created_at)}</span>
          </button>
        `,
      )
      .join("");
    els.historyOutput.querySelectorAll(".history-item").forEach((item) => {
      item.addEventListener("click", () => {
        renderText(els.novelOutput, item.dataset.content);
        els.novelMeta.textContent = "历史记录";
      });
    });
  } catch {
    els.historyOutput.textContent = "历史记录读取失败";
  }
}

async function refreshCacheState() {
  try {
    const response = await fetch("/cache_state");
    const data = await response.json();
    if (data.has_reference) {
      els.cacheState.textContent = `私有库 ${data.reference_length} 字${data.has_style ? "，文风已分析" : ""}`;
      els.uploadStatus.textContent = `${data.reference_length} 字`;
      if (data.style) {
        els.styleOutput.textContent = JSON.stringify(data.style, null, 2);
        els.analysisMeta.textContent = "已完成";
      }
    } else {
      els.cacheState.textContent = "等待私有库样章";
    }
  } catch {
    els.cacheState.textContent = "服务未连接";
  }
}

function getSetting() {
  return {
    inspiration: $("#inspiration").value.trim(),
    genre: $("#genre").value.trim(),
    location: $("#location").value.trim(),
    background: $("#background").value.trim(),
    characters: $("#characters").value.trim(),
    writing_style: $("#writingStyle").value,
    template: $("#template").value,
    public_library: $("#publicLibrary").value,
  };
}

function renderCover(svg) {
  els.coverOutput.innerHTML = svg;
}

function renderDirections(directions) {
  els.directionsOutput.innerHTML = directions
    .map((item, index) => `<button type="button" class="direction-card">${index + 1}. ${escapeHtml(item)}</button>`)
    .join("");
}

function renderIntel(data) {
  const labels = {
    main_line: "主线",
    side_line: "支线",
    romance_line: "感情线",
    faction_line: "势力线",
    risks: "风险",
  };
  return Object.entries(labels)
    .map(([key, label]) => `<h3>${label}</h3><ul>${data[key].map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`)
    .join("");
}

function renderNetwork() {
  const raw = $("#characters").value.trim();
  const names = raw
    ? raw.split(/[\n，,、。；; ]+/).filter(Boolean).slice(0, 8)
    : ["主角", "搭档", "对手", "导师"];
  els.networkCanvas.innerHTML = names
    .map((name, index) => {
      const x = 18 + ((index * 31) % 68);
      const y = 18 + ((index * 23) % 58);
      return `<button class="network-node" style="left:${x}%;top:${y}%;" type="button">${escapeHtml(name.slice(0, 8))}</button>`;
    })
    .join("");
  els.networkCanvas.querySelectorAll(".network-node").forEach(makeDraggable);
}

function makeDraggable(node) {
  let offsetX = 0;
  let offsetY = 0;
  node.addEventListener("pointerdown", (event) => {
    node.setPointerCapture(event.pointerId);
    const rect = node.getBoundingClientRect();
    offsetX = event.clientX - rect.left;
    offsetY = event.clientY - rect.top;
  });
  node.addEventListener("pointermove", (event) => {
    if (!node.hasPointerCapture(event.pointerId)) return;
    const canvas = els.networkCanvas.getBoundingClientRect();
    const x = Math.max(0, Math.min(canvas.width - node.offsetWidth, event.clientX - canvas.left - offsetX));
    const y = Math.max(0, Math.min(canvas.height - node.offsetHeight, event.clientY - canvas.top - offsetY));
    node.style.left = `${x}px`;
    node.style.top = `${y}px`;
  });
}

async function postJson(url, payload) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function withBusy(button, label, task) {
  const previous = button.textContent;
  setButtonsDisabled(true);
  button.textContent = label;
  try {
    await task();
  } catch (error) {
    toast(error.message || "操作失败", true);
  } finally {
    button.textContent = previous;
    setButtonsDisabled(false);
  }
}

function setButtonsDisabled(disabled) {
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = disabled;
  });
}

async function readResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

function renderText(container, text) {
  container.textContent = text || "暂无内容";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("\n", " ");
}

let toastTimer;
function toast(message, isError = false) {
  clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.classList.toggle("is-error", isError);
  els.toast.classList.add("is-visible");
  toastTimer = setTimeout(() => {
    els.toast.classList.remove("is-visible");
  }, 2600);
}
