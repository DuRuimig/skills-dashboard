const state = {
  items: [],
  categoryColors: {},
  settings: null,
  selectedId: null,
  filter: "all",
  category: "全部",
  query: "",
  view: localStorage.getItem("skills-dashboard-view") || "grid",
  navCollapsed: localStorage.getItem("skills-dashboard-nav-collapsed") === "true",
  detailCollapsed: localStorage.getItem("skills-dashboard-detail-collapsed") === "true",
  settingsOpen: false,
  mobileNavOpen: false,
  aiBusy: false,
  preferences: {
    autoCollapseDetailOnCategory: getStoredBoolean("skills-dashboard-auto-collapse-detail-on-category", true),
    focusDetailOnSkillSelect: getStoredBoolean("skills-dashboard-focus-detail-on-skill-select", true),
  },
};

const els = {
  appShell: document.querySelector(".app-shell"),
  summary: document.querySelector("#summary"),
  viewLabel: document.querySelector("#viewLabel"),
  search: document.querySelector("#search"),
  categories: document.querySelector("#categories"),
  items: document.querySelector("#items"),
  listPanel: document.querySelector(".list-panel"),
  detailPanel: document.querySelector("#detailPanel"),
  detail: document.querySelector("#detail"),
  catalogPath: document.querySelector("#catalogPath"),
  refresh: document.querySelector("#refresh"),
  aiEnrich: document.querySelector("#aiEnrich"),
  mobileMenu: document.querySelector("#mobileMenu"),
  mobileNavBackdrop: document.querySelector("#mobileNavBackdrop"),
  openSettings: document.querySelector("#openSettings"),
  closeSettings: document.querySelector("#closeSettings"),
  settingsBackdrop: document.querySelector("#settingsBackdrop"),
  settingsPanel: document.querySelector("#settingsPanel"),
  settingCards: document.querySelectorAll(".setting-card"),
  toggleNav: document.querySelector("#toggleNav"),
  toggleDetail: document.querySelector("#toggleDetail"),
  tabs: document.querySelectorAll(".segment"),
  viewButtons: document.querySelectorAll(".view-button"),
  aiEnabled: document.querySelector("#aiEnabled"),
  aiBaseUrl: document.querySelector("#aiBaseUrl"),
  aiApiKey: document.querySelector("#aiApiKey"),
  aiKeyHint: document.querySelector("#aiKeyHint"),
  aiModel: document.querySelector("#aiModel"),
  saveAiSettings: document.querySelector("#saveAiSettings"),
  testAiSettings: document.querySelector("#testAiSettings"),
  aiSettingsStatus: document.querySelector("#aiSettingsStatus"),
};

const preferenceStorageKeys = {
  autoCollapseDetailOnCategory: "skills-dashboard-auto-collapse-detail-on-category",
  focusDetailOnSkillSelect: "skills-dashboard-focus-detail-on-skill-select",
};

const mobileLayoutQuery = window.matchMedia("(max-width: 760px)");

const filterLabels = {
  all: "全部 Skills",
  favorite: "常用 Skills",
  skill: "Skills",
  cli: "命令行工具",
  hidden: "已隐藏",
};

const kindLabels = {
  skill: "Skill",
  cli: "命令",
};

const aiStatusLabels = {
  pending: "待整理",
  ready: "AI 已整理",
  failed: "整理失败",
  "built-in": "内置整理",
  unsupported: "不支持",
};

async function fetchItems() {
  const res = await fetch("/api/items");
  const data = await res.json();
  state.items = data.items;
  state.categoryColors = data.categoryColors || {};
  els.catalogPath.textContent = data.catalogPath;
  render();
}

async function fetchSettings() {
  const res = await fetch("/api/settings");
  state.settings = await res.json();
  renderSettings();
}

function visibleItems() {
  const query = state.query.trim().toLowerCase();
  return state.items.filter((item) => {
    if (state.filter === "favorite" && !item.favorite) return false;
    if (state.filter === "skill" && item.kind !== "skill") return false;
    if (state.filter === "cli" && item.kind !== "cli") return false;
    if (state.filter === "hidden" && !item.hidden) return false;
    if (state.filter !== "hidden" && item.hidden) return false;
    if (state.category !== "全部" && item.category !== state.category) return false;
    if (!query) return true;
    const haystack = [
      item.name,
      item.summary,
      item.description,
      item.whenToUse,
      item.requirements,
      item.category,
      item.path,
      item.notes,
      item.callHint,
      item.customCallHint,
      ...(item.examples || []),
      ...(item.tags || []),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function categoryCounts() {
  const counts = new Map([["全部", 0]]);
  for (const item of state.items) {
    if (state.filter !== "hidden" && item.hidden) continue;
    if (state.filter === "favorite" && !item.favorite) continue;
    if (state.filter === "skill" && item.kind !== "skill") continue;
    if (state.filter === "cli" && item.kind !== "cli") continue;
    counts.set("全部", counts.get("全部") + 1);
    counts.set(item.category, (counts.get(item.category) || 0) + 1);
  }
  const order = ["全部", "代码开发", "知识搜索", "文档媒体", "产品研发", "个人知识库", "其他工具"];
  return [...counts.entries()].sort((a, b) => {
    const ai = order.indexOf(a[0]);
    const bi = order.indexOf(b[0]);
    if (ai !== -1 || bi !== -1) return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    return a[0].localeCompare(b[0], "zh-CN");
  });
}

function renderCategories() {
  els.categories.innerHTML = "";
  for (const [name, count] of categoryCounts()) {
    const row = document.createElement("div");
    row.className = "category-item";
    const color = categoryColor(name);

    if (name === "全部") {
      const dot = document.createElement("span");
      dot.className = "category-dot";
      dot.setAttribute("aria-hidden", "true");
      dot.setAttribute("style", categoryDotStyle(color));
      row.append(dot);
    } else {
      const input = document.createElement("input");
      input.className = "category-color-input";
      input.type = "color";
      input.value = normalizeColor(color);
      input.title = `更改${name}颜色`;
      input.setAttribute("aria-label", `更改${name}颜色`);
      input.setAttribute("style", categoryDotStyle(color));
      input.addEventListener("click", (event) => event.stopPropagation());
      input.addEventListener("change", async (event) => {
        event.stopPropagation();
        await saveCategoryColor(name, event.target.value);
      });
      row.append(input);
    }

    const button = document.createElement("button");
    button.className = `category-button ${state.category === name ? "active" : ""}`;
    button.innerHTML = `
      <span>${escapeHtml(name)}</span>
      <span class="count">${count}</span>
    `;
    button.addEventListener("click", () => {
      state.category = name;
      if (state.preferences.autoCollapseDetailOnCategory) {
        setDetailCollapsed(true);
      }
      if (isMobileLayout()) {
        setMobileNavOpen(false);
      }
      render();
    });
    row.append(button);
    els.categories.append(row);
  }
}

function renderItems() {
  const items = visibleItems();
  const totalSkills = state.items.filter((item) => item.kind === "skill").length;
  const totalTools = state.items.filter((item) => item.kind === "cli").length;
  const visibleSkills = items.filter((item) => item.kind === "skill").length;
  const visibleTools = items.filter((item) => item.kind === "cli").length;
  const totalParts = [`${totalSkills} 个 Skills`];
  if (totalTools) totalParts.push(`${totalTools} 个工具`);
  const visibleParts = [`${visibleSkills} 个 Skills`];
  if (visibleTools) visibleParts.push(`${visibleTools} 个工具`);
  els.summary.textContent = `${totalParts.join("，")}，当前 ${visibleParts.join("，")}`;
  const pendingAi = state.items.filter((item) => item.kind === "skill" && ["pending", "failed"].includes(item.aiStatus)).length;
  els.aiEnrich.textContent = state.aiBusy ? "整理中..." : pendingAi ? `AI 整理 ${pendingAi}` : "AI 整理";
  els.aiEnrich.disabled = state.aiBusy || !pendingAi;
  els.viewLabel.textContent = `${filterLabels[state.filter]} · ${state.category}`;
  els.items.className = `item-list ${state.view === "grid" ? "grid-mode" : "list-mode"}`;
  els.listPanel.classList.toggle("is-grid", state.view === "grid");
  els.listPanel.classList.toggle("is-list", state.view === "list");
  els.items.innerHTML = "";
  if (!items.some((item) => item.id === state.selectedId)) {
    state.selectedId = null;
  }
  if (!items.length) {
    els.items.innerHTML = `<div class="empty-state"><h2>没有匹配结果</h2><p>换一个关键词，或切回“全部”。</p></div>`;
    return;
  }
  for (const item of items) {
    const row = document.createElement("button");
    row.className = `item-row ${state.view === "grid" ? "item-card" : ""} ${item.id === state.selectedId ? "active" : ""}`;
    const color = item.categoryColor || categoryColor(item.category);
    row.style.setProperty("--item-bg", hexToRgba(color, 0.06));
    row.style.setProperty("--item-border", hexToRgba(color, 0.42));
    row.style.setProperty("--item-outline", hexToRgba(color, 0.2));
    row.innerHTML = `
      <span class="row-main">
        <span class="row-title">
          <span class="favorite-dot ${item.favorite ? "active" : ""}" aria-hidden="true"></span>
          <span class="name">${escapeHtml(item.name)}</span>
        </span>
        <span class="row-summary">${escapeHtml(item.summary || item.description || "")}</span>
      </span>
      <span class="row-meta">
        <span class="pill category-pill" style="${categoryPillStyle(color)}">${escapeHtml(item.category)}</span>
        ${item.aiStatus && item.aiStatus !== "unsupported" ? `<span class="pill ai-pill ${escapeAttr(item.aiStatus)}">${escapeHtml(aiStatusLabels[item.aiStatus] || item.aiStatus)}</span>` : ""}
      </span>
    `;
    row.addEventListener("click", () => {
      state.selectedId = item.id;
      setDetailCollapsed(false);
      if (state.preferences.focusDetailOnSkillSelect) {
        setNavCollapsed(true);
      }
      render();
    });
    els.items.append(row);
  }
}

function renderDetail() {
  const item = state.items.find((entry) => entry.id === state.selectedId);
  if (!item) {
    els.detail.innerHTML = `<div class="empty-state"><h2>选择一个 Skill</h2><p>右侧会显示用途、适用场景、依赖条件和调用方式。</p></div>`;
    return;
  }
  const hint = item.customCallHint || item.callHint || "";
  const examples = (item.examples || []).filter(Boolean);
  const color = item.categoryColor || categoryColor(item.category);
  els.detail.innerHTML = `
    <div class="detail">
      <div class="detail-heading">
        <div class="title-line">
          <div class="title-copy">
            <h2>${escapeHtml(item.name)}</h2>
            <p class="meta">${escapeHtml(kindLabels[item.kind] || item.kind)}${item.version ? " · " + escapeHtml(item.version) : ""}</p>
          </div>
          <button class="favorite-button ${item.favorite ? "active" : ""}">${item.favorite ? "已常用" : "设常用"}</button>
        </div>
        <div class="status-line">
          <span class="status-chip category-chip" style="${categoryPillStyle(color)}">${escapeHtml(item.category)}</span>
          <span class="status-chip">${item.hidden ? "已隐藏" : "使用中"}</span>
          ${item.aiStatus && item.aiStatus !== "unsupported" ? `<span class="status-chip">${escapeHtml(aiStatusLabels[item.aiStatus] || item.aiStatus)}</span>` : ""}
        </div>
      </div>

      <section class="section">
        <h3>功能介绍</h3>
        <p class="detail-text">${escapeHtml(item.summary || item.description || "暂无说明。")}</p>
      </section>

      <section class="section">
        <h3>适用场景</h3>
        <p class="detail-text">${escapeHtml(item.whenToUse || "当你的任务和它的名称、说明匹配时使用。")}</p>
      </section>

      <section class="section">
        <h3>使用限制</h3>
        <p class="detail-text">${escapeHtml(item.requirements || "无额外记录。")}</p>
      </section>

      <section class="section">
        <h3>如何调用</h3>
        <ul class="example-list">
          ${examples.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("") || `<li>${escapeHtml(hint || "直接描述你的需求即可。")}</li>`}
        </ul>
      </section>

      <section class="section">
        <h3>命令或提示</h3>
        <div class="command-box">
          <code>${escapeHtml(hint)}</code>
          <button class="plain-button" data-copy="${escapeAttr(hint)}">复制</button>
        </div>
      </section>

      <section class="section">
        <h3>我的标注</h3>
        <div class="form-grid">
          <div class="field">
            <label>分类</label>
            <input id="detailCategory" value="${escapeAttr(item.category)}" />
          </div>
          <div class="field">
            <label>标签，逗号分隔</label>
            <input id="detailTags" value="${escapeAttr((item.tags || []).join(", "))}" />
          </div>
          <div class="field">
            <label>自定义调用提示</label>
            <input id="detailHint" value="${escapeAttr(item.customCallHint || "")}" placeholder="${escapeAttr(item.callHint || "")}" />
          </div>
          <div class="field">
            <label>备注</label>
            <textarea id="detailNotes">${escapeHtml(item.notes || "")}</textarea>
          </div>
        </div>
      </section>

      ${
        item.kind === "skill"
          ? `<section class="section">
              <h3>AI 整理</h3>
              <p class="detail-text">${escapeHtml(aiStatusText(item))}</p>
              <button class="plain-button" id="enrichCurrentSkill">${state.aiBusy ? "整理中..." : "重新整理这个 Skill"}</button>
            </section>`
          : ""
      }

      <section class="section">
        <h3>本地位置</h3>
        <code>${escapeHtml(item.path)}</code>
      </section>

      <div class="detail-actions">
        <button class="plain-button" id="saveMeta">保存标注</button>
        <button class="plain-button" id="toggleHidden">${item.hidden ? "取消隐藏" : "隐藏"}</button>
        <button class="plain-button" id="revealPath">在 Finder 显示</button>
      </div>
    </div>
  `;

  els.detail.querySelector(".favorite-button").addEventListener("click", () => updateMeta(item.id, { favorite: !item.favorite }));
  els.detail.querySelector("#toggleHidden").addEventListener("click", () => updateMeta(item.id, { hidden: !item.hidden }));
  const enrichCurrent = els.detail.querySelector("#enrichCurrentSkill");
  if (enrichCurrent) {
    enrichCurrent.addEventListener("click", () => enrichSkills({ id: item.id, force: true }));
  }
  els.detail.querySelector("#saveMeta").addEventListener("click", async () => {
    await updateMeta(item.id, {
      category: document.querySelector("#detailCategory").value.trim() || item.autoCategory,
      tags: document
        .querySelector("#detailTags")
        .value.split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      notes: document.querySelector("#detailNotes").value,
      customCallHint: document.querySelector("#detailHint").value.trim(),
    });
  });
  els.detail.querySelector("#revealPath").addEventListener("click", () => {
    fetch(`/api/open?path=${encodeURIComponent(item.path)}`);
  });
  for (const button of els.detail.querySelectorAll("[data-copy]")) {
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(button.dataset.copy || "");
      button.textContent = "已复制";
      setTimeout(() => (button.textContent = "复制"), 1100);
    });
  }
}

async function updateMeta(id, patch) {
  await fetch("/api/meta", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, ...patch }),
  });
  await fetchItems();
}

async function updateCategoryColor(category, color) {
  await fetch("/api/category-color", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category, color }),
  });
}

async function saveCategoryColor(category, color) {
  await updateCategoryColor(category, color);
  await fetchItems();
}

async function saveAiSettings() {
  setAiStatus("正在保存...");
  const payload = {
    ai: {
      enabled: els.aiEnabled.checked,
      baseUrl: els.aiBaseUrl.value.trim(),
      model: els.aiModel.value.trim(),
    },
  };
  const apiKey = els.aiApiKey.value.trim();
  if (apiKey) payload.ai.apiKey = apiKey;
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    setAiStatus(data.error || "保存失败");
    return false;
  }
  state.settings = data;
  els.aiApiKey.value = "";
  renderSettings();
  setAiStatus("设置已保存。");
  return true;
}

async function testAiSettings() {
  const saved = await saveAiSettings();
  if (!saved) return;
  setAiStatus("正在测试配置...");
  const res = await fetch("/api/ai/test", { method: "POST" });
  const data = await res.json();
  setAiStatus(data.ok ? "配置可用。" : data.error || "测试失败");
}

async function enrichSkills(options = {}) {
  const saved = await saveAiSettings();
  if (!saved) return;
  state.aiBusy = true;
  render();
  setAiStatus(options.id ? "正在整理当前 Skill..." : "正在整理待整理 Skill...");
  try {
    const res = await fetch("/api/ai/enrich", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit: 12, ...options }),
    });
    const data = await res.json();
    if (!res.ok) {
      setAiStatus(data.error || "AI 整理失败");
      return;
    }
    const failed = (data.results || []).filter((entry) => !entry.ok).length;
    setAiStatus(`已处理 ${data.processed || 0} 个 Skill${failed ? `，${failed} 个失败` : ""}。`);
    await fetchItems();
  } finally {
    state.aiBusy = false;
    render();
  }
}

function setAiStatus(message) {
  if (els.aiSettingsStatus) {
    els.aiSettingsStatus.textContent = message || "";
  }
}

function categoryColor(category) {
  if (category === "全部") return "#334155";
  return state.categoryColors[category] || "#64748b";
}

function categoryDotStyle(color) {
  const safeColor = normalizeColor(color);
  return `--category-color: ${safeColor}`;
}

function categoryPillStyle(color) {
  const safeColor = normalizeColor(color);
  return `--category-color: ${safeColor}; --category-bg: ${hexToRgba(safeColor, 0.12)}; --category-border: ${hexToRgba(safeColor, 0.28)}; --category-text: ${darkenHex(safeColor, 0.72)}`;
}

function normalizeColor(color) {
  return /^#[0-9a-fA-F]{6}$/.test(color || "") ? color : "#64748b";
}

function hexToRgba(hex, alpha) {
  const value = normalizeColor(hex).slice(1);
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function darkenHex(hex, factor) {
  const value = normalizeColor(hex).slice(1);
  const r = Math.max(0, Math.round(parseInt(value.slice(0, 2), 16) * factor));
  const g = Math.max(0, Math.round(parseInt(value.slice(2, 4), 16) * factor));
  const b = Math.max(0, Math.round(parseInt(value.slice(4, 6), 16) * factor));
  return `#${[r, g, b].map((part) => part.toString(16).padStart(2, "0")).join("")}`;
}

function render() {
  renderShellState();
  renderSettings();
  els.viewButtons.forEach((button) => button.classList.toggle("active", button.dataset.view === state.view));
  renderCategories();
  renderItems();
  renderDetail();
}

function renderShellState() {
  els.appShell.classList.toggle("nav-collapsed", state.navCollapsed);
  els.appShell.classList.toggle("detail-collapsed", state.detailCollapsed);
  els.appShell.classList.toggle("mobile-nav-open", state.mobileNavOpen);
  els.appShell.classList.toggle("has-selection", Boolean(state.selectedId));
  els.toggleNav.setAttribute("aria-expanded", String(!state.navCollapsed));
  els.toggleNav.setAttribute("aria-label", isMobileLayout() ? "关闭分类菜单" : state.navCollapsed ? "展开左侧栏" : "收起左侧栏");
  els.toggleNav.title = isMobileLayout() ? "关闭分类菜单" : state.navCollapsed ? "展开左侧栏" : "收起左侧栏";
  els.toggleDetail.setAttribute("aria-expanded", String(!state.detailCollapsed));
  els.toggleDetail.setAttribute("aria-label", state.detailCollapsed ? "展开详情栏" : "收起详情栏");
  els.toggleDetail.title = state.detailCollapsed ? "展开详情栏" : "收起详情栏";
  els.mobileMenu.setAttribute("aria-expanded", String(state.mobileNavOpen));
  els.mobileMenu.setAttribute("aria-label", state.mobileNavOpen ? "关闭分类菜单" : "打开分类菜单");
  els.mobileMenu.title = state.mobileNavOpen ? "关闭分类菜单" : "打开分类菜单";
  els.mobileNavBackdrop.hidden = !state.mobileNavOpen;
}

function renderSettings() {
  document.body.classList.toggle("settings-open", state.settingsOpen);
  els.settingsBackdrop.hidden = !state.settingsOpen;
  els.settingsPanel.setAttribute("aria-hidden", String(!state.settingsOpen));
  for (const card of els.settingCards) {
    const setting = card.dataset.setting;
    const value = card.dataset.value === "true";
    const selected = state.preferences[setting] === value;
    card.classList.toggle("selected", selected);
    card.setAttribute("aria-pressed", String(selected));
  }
  renderAiSettings();
}

function renderAiSettings() {
  const ai = state.settings?.ai || {};
  if (!els.aiEnabled) return;
  els.aiEnabled.checked = Boolean(ai.enabled);
  if (document.activeElement !== els.aiBaseUrl) els.aiBaseUrl.value = ai.baseUrl || "";
  if (document.activeElement !== els.aiModel) els.aiModel.value = ai.model || "";
  els.aiKeyHint.textContent = ai.apiKeyConfigured ? `已配置密钥：${ai.apiKeyPreview || "已配置"}` : "尚未配置密钥。";
}

function aiStatusText(item) {
  if (item.aiStatus === "ready") return `已使用 AI 整理。${item.aiUpdatedAt ? "更新时间：" + item.aiUpdatedAt : ""}`;
  if (item.aiStatus === "failed") return `上次整理失败：${item.aiError || "未知错误"}`;
  if (item.aiStatus === "built-in") return "当前使用内置整理画像。你也可以用自己的接口重新整理。";
  if (item.aiStatus === "pending") return "这个 Skill 还没有 AI 整理缓存，可以点击按钮生成统一中文说明。";
  return "当前条目不支持 AI 整理。";
}

function setNavCollapsed(collapsed) {
  state.navCollapsed = collapsed;
  localStorage.setItem("skills-dashboard-nav-collapsed", String(collapsed));
}

function setMobileNavOpen(open) {
  state.mobileNavOpen = open;
  renderShellState();
}

function setDetailCollapsed(collapsed) {
  state.detailCollapsed = collapsed;
  localStorage.setItem("skills-dashboard-detail-collapsed", String(collapsed));
}

function setPreference(setting, value) {
  if (!(setting in preferenceStorageKeys)) return;
  state.preferences[setting] = value;
  localStorage.setItem(preferenceStorageKeys[setting], String(value));
  renderSettings();
}

function getStoredBoolean(key, fallback) {
  const value = localStorage.getItem(key);
  if (value === null) return fallback;
  return value === "true";
}

function isMobileLayout() {
  return mobileLayoutQuery.matches;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

els.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

els.refresh.addEventListener("click", fetchItems);

els.aiEnrich.addEventListener("click", () => enrichSkills());

els.toggleNav.addEventListener("click", () => {
  if (isMobileLayout()) {
    setMobileNavOpen(false);
    return;
  }
  setNavCollapsed(!state.navCollapsed);
  renderShellState();
});

els.toggleDetail.addEventListener("click", () => {
  setDetailCollapsed(!state.detailCollapsed);
  renderShellState();
});

els.mobileMenu.addEventListener("click", () => {
  setMobileNavOpen(!state.mobileNavOpen);
});

els.mobileNavBackdrop.addEventListener("click", () => {
  setMobileNavOpen(false);
});

els.openSettings.addEventListener("click", () => {
  state.settingsOpen = true;
  renderSettings();
});

els.closeSettings.addEventListener("click", () => {
  state.settingsOpen = false;
  renderSettings();
});

els.settingsBackdrop.addEventListener("click", () => {
  state.settingsOpen = false;
  renderSettings();
});

for (const card of els.settingCards) {
  card.addEventListener("click", () => {
    setPreference(card.dataset.setting, card.dataset.value === "true");
  });
}

els.saveAiSettings.addEventListener("click", saveAiSettings);
els.testAiSettings.addEventListener("click", testAiSettings);

window.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (state.settingsOpen) {
    state.settingsOpen = false;
    renderSettings();
  }
  if (state.mobileNavOpen) {
    setMobileNavOpen(false);
  }
});

mobileLayoutQuery.addEventListener("change", () => {
  if (!isMobileLayout()) {
    state.mobileNavOpen = false;
  }
  renderShellState();
});

for (const tab of els.tabs) {
  tab.addEventListener("click", () => {
    els.tabs.forEach((entry) => entry.classList.remove("active"));
    tab.classList.add("active");
    state.filter = tab.dataset.filter;
    state.category = "全部";
    if (state.preferences.autoCollapseDetailOnCategory) {
      setDetailCollapsed(true);
    }
    render();
  });
}

for (const button of els.viewButtons) {
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    localStorage.setItem("skills-dashboard-view", state.view);
    render();
  });
}

Promise.all([fetchSettings(), fetchItems()]);
