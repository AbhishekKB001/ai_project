// NexusNotice AI - Frontend Core Application Logic
const API_BASE = "";

const state = {
  activeTab: "recommendations",
  currentUser: null,
  availablePersonas: [],
  systemStatus: null,
  feed: null,
  notices: [],
  selectedCategory: "All",
  selectedDept: "All Departments",
  selectedPriority: "All",
  searchQuery: "",
  useSemanticSearch: true,
  activeNotice: null,
  chatModel: "gemini",
  chatHistory: [],
  analyticsData: null,
  vectorChart: null,
  categoryChart: null
};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initApp();
  setupEventListeners();
});

async function initApp() {
  showLoading(true);
  try {
    await Promise.all([
      fetchSystemStatus(),
      fetchUserProfile(),
      fetchFeed()
    ]);
    renderHeaderPills();
    renderFeed();
  } catch (err) {
    console.error("Initialization error:", err);
  } finally {
    showLoading(false);
  }
}

// ----------------- API Calls ----------------- //

async function fetchSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    state.systemStatus = await res.json();
    renderStatusPills();
  } catch (e) {
    console.error("Failed to fetch system status:", e);
  }
}

async function fetchUserProfile() {
  try {
    const res = await fetch(`${API_BASE}/api/user/profile`);
    const data = await res.json();
    state.currentUser = data.current_user;
    state.availablePersonas = data.available_personas;
    renderUserPersonaUI();
  } catch (e) {
    console.error("Failed to fetch user profile:", e);
  }
}

async function fetchFeed() {
  try {
    const res = await fetch(`${API_BASE}/api/feed`);
    const data = await res.json();
    state.feed = data.feed;
  } catch (e) {
    console.error("Failed to fetch feed:", e);
  }
}

async function fetchAllNotices() {
  try {
    let url = `${API_BASE}/api/notices?category=${encodeURIComponent(state.selectedCategory)}&department=${encodeURIComponent(state.selectedDept)}&priority=${encodeURIComponent(state.selectedPriority)}`;
    if (state.searchQuery) {
      url += `&search=${encodeURIComponent(state.searchQuery)}`;
    }
    const res = await fetch(url);
    const data = await res.json();
    state.notices = data.notices;
    renderNoticesGrid(state.notices, "allNoticesContainer");
  } catch (e) {
    console.error("Failed to fetch notices:", e);
  }
}

async function searchNotices(explicitQuery = null) {
  const searchInput = document.getElementById("mainSearchInput");
  if (explicitQuery !== null && explicitQuery !== undefined) {
    state.searchQuery = explicitQuery.trim();
    if (searchInput) searchInput.value = explicitQuery;
  } else if (searchInput) {
    state.searchQuery = searchInput.value.trim();
  }

  if (!state.searchQuery || !state.searchQuery.trim()) {
    clearSearch();
    return;
  }

  const clearBtn = document.getElementById("clearSearchBtn");
  if (clearBtn) clearBtn.classList.remove("hidden");

  showLoading(true);
  try {
    const res = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: state.searchQuery,
        use_semantic: state.useSemanticSearch,
        category: null,
        department: null,
        priority: null,
        limit: 12
      })
    });
    const data = await res.json();
    renderSearchResults(data);
  } catch (e) {
    console.error("Search error:", e);
  } finally {
    showLoading(false);
  }
}

function clearSearch() {
  state.searchQuery = "";
  const input = document.getElementById("mainSearchInput");
  if (input) input.value = "";
  
  const clearBtn = document.getElementById("clearSearchBtn");
  if (clearBtn) clearBtn.classList.add("hidden");

  const searchTabBtn = document.getElementById("tab-btn-search");
  if (searchTabBtn) searchTabBtn.classList.add("hidden");

  switchTab("recommendations");
}

// ----------------- Rendering Functions ----------------- //

function renderStatusPills() {
  const container = document.getElementById("aiStatusPills");
  if (container) {
    container.innerHTML = "";
  }
}

function renderHeaderPills() {
  renderStatusPills();
}

function renderUserPersonaUI() {
  const select = document.getElementById("personaSwitcher");
  const userBadge = document.getElementById("currentUserBadge");
  const actionContainer = document.getElementById("publishNoticeActionContainer");

  if (!state.currentUser) return;

  const isOfficial = state.currentUser.role === "official" || state.currentUser.role === "faculty" || state.currentUser.role === "admin";

  if (userBadge) {
    userBadge.innerHTML = `
      <div class="text-right hidden sm:block">
        <div class="text-sm font-semibold text-slate-200 flex items-center justify-end gap-1.5">
          ${isOfficial ? '<span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold uppercase tracking-wider">Official</span>' : '<span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 font-bold uppercase tracking-wider">Student</span>'}
          <span>${state.currentUser.name}</span>
        </div>
        <div class="text-xs text-slate-400">${state.currentUser.department} • ${state.currentUser.year}</div>
      </div>
    `;
  }

  // Update Top Bar Action Button based on Role
  if (actionContainer) {
    if (!isOfficial) {
      actionContainer.innerHTML = `
        <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/70 text-slate-400 text-xs cursor-default" title="Student mode: Notice publishing is restricted to verified College Authorities and Faculty.">
          <i data-lucide="shield" class="w-3.5 h-3.5 text-indigo-400"></i>
          <span class="hidden sm:inline">Student View</span>
        </div>
      `;
    } else {
      actionContainer.innerHTML = `
        <button onclick="openAdminStudioModal()" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-md shadow-emerald-600/20">
          <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
          <span class="hidden sm:inline">Publish Notice</span>
        </button>
      `;
    }
  }

  if (select && state.availablePersonas) {
    select.innerHTML = state.availablePersonas.map(p => `
      <option value="${p.user_id}" ${p.user_id === state.currentUser.user_id ? 'selected' : ''}>
        ${p.name} [${p.year}]
      </option>
    `).join("");
  }

  lucide.createIcons();
}

function renderFeed() {
  if (!state.feed) return;

  // 1. Personalized Recommendations
  const recContainer = document.getElementById("recommendationsContainer");
  if (recContainer) {
    const recs = state.feed.personalized || [];
    if (recs.length === 0) {
      recContainer.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400">No notices matched your profile yet. Try tweaking interests or explore All Notices!</div>`;
    } else {
      recContainer.innerHTML = recs.map(item => createNoticeCardHTML(item.notice, item.score, item.match_reason)).join("");
    }
  }

  // 2. Critical Deadlines
  const deadlineContainer = document.getElementById("criticalDeadlinesContainer");
  if (deadlineContainer) {
    const deadlines = state.feed.critical_deadlines || [];
    deadlineContainer.innerHTML = deadlines.map(n => createNoticeCardHTML(n, null, null, true)).join("");
  }

  // 3. Trending Notices
  const trendingContainer = document.getElementById("trendingContainer");
  if (trendingContainer) {
    const trending = state.feed.trending || [];
    trendingContainer.innerHTML = trending.map(n => createNoticeCardHTML(n)).join("");
  }
}

function renderNoticesGrid(notices, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!notices || notices.length === 0) {
    container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400">No notices found matching the filters.</div>`;
    return;
  }
  container.innerHTML = notices.map(n => createNoticeCardHTML(n)).join("");
}

function renderSearchResults(data) {
  const container = document.getElementById("searchResultsContainer");
  const countSpan = document.getElementById("searchResultCount");
  const engineSpan = document.getElementById("searchEngineBadge");
  const queryDisplay = document.getElementById("searchQueryDisplay");
  const searchTabBtn = document.getElementById("tab-btn-search");
  const clearBtn = document.getElementById("clearSearchBtn");

  if (clearBtn) clearBtn.classList.remove("hidden");
  if (searchTabBtn) searchTabBtn.classList.remove("hidden");

  if (countSpan) countSpan.textContent = `${data.count} notice(s) found`;
  if (engineSpan) engineSpan.textContent = "";
  if (queryDisplay) queryDisplay.textContent = `"${data.query}"`;

  if (!container) return;
  if (!data.results || data.results.length === 0) {
    container.innerHTML = `
      <div class="col-span-3 text-center py-12 text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800 p-6">
        <i data-lucide="search-x" class="w-10 h-10 mx-auto text-slate-500 mb-2"></i>
        <p class="font-semibold text-slate-300">No notices found for "${data.query}"</p>
        <p class="text-xs text-slate-500 mt-1">Try searching with different keywords or browse categories.</p>
        <button onclick="clearSearch()" class="mt-4 px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700">
          Clear Search & Return to Feed
        </button>
      </div>
    `;
    switchTab("search");
    lucide.createIcons();
    return;
  }

  container.innerHTML = data.results.map(item => {
    const notice = item.notice;
    const sim = item.similarity_score;
    const matchReason = sim ? `Match: ${Math.round(sim * 100)}%` : null;
    return createNoticeCardHTML(notice, sim, matchReason);
  }).join("");

  switchTab("search");
  lucide.createIcons();
}

function getCategoryBadgeClass(category) {
  const map = {
    "Examinations": "badge-exam",
    "Placements": "badge-placement",
    "Events": "badge-event",
    "Scholarships": "badge-scholarship",
    "Fees & Finance": "badge-fees",
    "Campus & Hostel": "badge-hostel",
    "Sports": "badge-sports",
    "Academics": "badge-general"
  };
  return map[category] || "badge-general";
}

function getPriorityBadgeClass(priority) {
  if (priority === "Critical") return "bg-red-500/20 text-red-400 border border-red-500/40 pulse-critical";
  if (priority === "High") return "bg-amber-500/20 text-amber-400 border border-amber-500/40";
  if (priority === "Medium") return "bg-blue-500/20 text-blue-400 border border-blue-500/40";
  return "bg-slate-700/50 text-slate-300 border border-slate-600";
}

function formatDeadlineCountdown(deadlineStr) {
  if (!deadlineStr) return null;
  try {
    const d = new Date(deadlineStr);
    const now = new Date();
    const diffDays = Math.ceil((d - now) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { text: "Expired", class: "text-slate-500 bg-slate-800/80" };
    if (diffDays === 0) return { text: "Due Today!", class: "text-red-400 bg-red-950/80 font-bold animate-pulse" };
    if (diffDays <= 3) return { text: `${diffDays} days left`, class: "text-amber-400 bg-amber-950/80 font-semibold" };
    return { text: `Due in ${diffDays} days`, class: "text-emerald-400 bg-emerald-950/80" };
  } catch (e) {
    return { text: deadlineStr, class: "text-slate-400 bg-slate-800" };
  }
}

function createNoticeCardHTML(notice, score = null, matchReason = null, highlightDeadline = false) {
  const categoryClass = getCategoryBadgeClass(notice.category);
  const priorityClass = getPriorityBadgeClass(notice.priority);
  const deadlineInfo = formatDeadlineCountdown(notice.deadline);
  const isBookmarked = state.currentUser?.bookmarked_notice_ids?.includes(notice.id);

  return `
    <div class="glass-panel glass-panel-hover rounded-2xl p-5 flex flex-col justify-between relative group border transition duration-200">
      <div>
        <!-- Top meta row -->
        <div class="flex items-center justify-between gap-2 mb-3">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-xs px-2.5 py-0.8 rounded-full font-medium ${categoryClass}">
              ${notice.category}
            </span>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium ${priorityClass}">
              ${notice.priority}
            </span>
            ${notice.extracted_from_ocr ? `
              <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/40 flex items-center gap-1" title="Official Scanned Document">
                <i data-lucide="file-text" class="w-3 h-3"></i> Scanned
              </span>
            ` : ''}
          </div>
          <button onclick="toggleBookmark('${notice.id}', event)" class="p-1.5 rounded-full hover:bg-slate-700/60 transition text-slate-400 hover:text-amber-400">
            <i data-lucide="bookmark" class="w-4 h-4 ${isBookmarked ? 'fill-amber-400 text-amber-400' : ''}"></i>
          </button>
        </div>

        <!-- Title -->
        <h3 class="text-base font-semibold text-slate-100 group-hover:text-indigo-300 transition line-clamp-2 mb-2">
          ${notice.title}
        </h3>

        <!-- Gist / Summary snippet -->
        <p class="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">
          ${notice.summary || notice.content}
        </p>

        <!-- Reason / Score Pill if recommendation -->
        ${matchReason ? `
          <div class="mb-3 px-2.5 py-1.5 rounded-lg bg-indigo-950/60 border border-indigo-800/50 text-[11px] text-indigo-300 flex items-center gap-1.5">
            <i data-lucide="sparkles" class="w-3.5 h-3.5 text-indigo-400 shrink-0"></i>
            <span class="truncate">${matchReason}</span>
          </div>
        ` : ''}

        <!-- Department & Audience -->
        <div class="flex items-center gap-2 text-[11px] text-slate-400 mb-3 flex-wrap">
          <span class="flex items-center gap-1">
            <i data-lucide="building-2" class="w-3 h-3 text-slate-500"></i> ${notice.department}
          </span>
          <span>•</span>
          <span class="flex items-center gap-1">
            <i data-lucide="users" class="w-3 h-3 text-slate-500"></i> ${(notice.target_audience || []).slice(0, 2).join(", ")}
          </span>
        </div>
      </div>

      <!-- Bottom Action Row -->
      <div class="pt-3 border-t border-slate-700/50 flex items-center justify-between gap-2 mt-2">
        <div>
          ${deadlineInfo ? `
            <span class="text-[11px] px-2.5 py-1 rounded-full font-medium ${deadlineInfo.class}">
              ${deadlineInfo.text}
            </span>
          ` : `
            <span class="text-[11px] text-slate-500">${notice.published_date.split(" ")[0]}</span>
          `}
        </div>

        <div class="flex items-center gap-1">
          <button onclick="speakNotice('${notice.id}', event)" class="p-2 rounded-xl hover:bg-slate-700/60 text-slate-400 hover:text-indigo-400 transition" title="Read Aloud">
            <i data-lucide="volume-2" class="w-4 h-4"></i>
          </button>
          <button onclick="openNoticeModal('${notice.id}')" class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center gap-1 shadow-lg shadow-indigo-600/20">
            <span>Read & Chat</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    </div>
  `;
}

// ----------------- Interactive Notice Modal & NoticeBot ----------------- //

async function openNoticeModal(noticeId) {
  showLoading(true);
  try {
    const res = await fetch(`${API_BASE}/api/notices/${noticeId}`);
    const data = await res.json();
    state.activeNotice = data.notice;
    state.chatHistory = [];

    const modal = document.getElementById("noticeDetailModal");
    const titleEl = document.getElementById("modalNoticeTitle");
    const deptEl = document.getElementById("modalNoticeDept");
    const catEl = document.getElementById("modalNoticeCategory");
    const priorityEl = document.getElementById("modalNoticePriority");
    const dateEl = document.getElementById("modalNoticeDate");
    const deadlineEl = document.getElementById("modalNoticeDeadline");
    const contentEl = document.getElementById("modalNoticeContent");
    const summaryEl = document.getElementById("modalNoticeSummary");
    const tagsContainer = document.getElementById("modalNoticeTags");
    const imgContainer = document.getElementById("modalNoticeImageContainer");

    if (titleEl) titleEl.textContent = state.activeNotice.title;
    if (deptEl) deptEl.textContent = state.activeNotice.department;
    if (catEl) {
      catEl.textContent = state.activeNotice.category;
      catEl.className = `text-xs px-2.5 py-1 rounded-full font-medium ${getCategoryBadgeClass(state.activeNotice.category)}`;
    }
    if (priorityEl) {
      priorityEl.textContent = state.activeNotice.priority;
      priorityEl.className = `text-xs px-2.5 py-1 rounded-full font-medium ${getPriorityBadgeClass(state.activeNotice.priority)}`;
    }
    if (dateEl) dateEl.textContent = state.activeNotice.published_date;
    if (deadlineEl) {
      deadlineEl.textContent = state.activeNotice.deadline || "None specified";
    }
    if (contentEl) contentEl.textContent = state.activeNotice.content;
    if (summaryEl) {
      summaryEl.innerHTML = (state.activeNotice.summary || "Generating AI summary...")
        .split("\n")
        .map(line => `<p class="mb-1">${line}</p>`)
        .join("");
    }
    if (tagsContainer) {
      tagsContainer.innerHTML = (state.activeNotice.tags || []).map(t => `
        <span class="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">#${t}</span>
      `).join("");
    }
    if (imgContainer) {
      if (state.activeNotice.image_path) {
        imgContainer.innerHTML = `
          <div class="mb-4 rounded-xl overflow-hidden border border-slate-700 bg-slate-900">
            <div class="px-3 py-1.5 bg-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
              <span>Original Scanned Circular</span>
              <span class="text-emerald-400 flex items-center gap-1"><i data-lucide="check" class="w-3 h-3"></i> Verified Circular</span>
            </div>
            <img src="${state.activeNotice.image_path}" class="max-h-64 w-full object-contain p-2" alt="Notice Attachment" />
          </div>
        `;
      } else {
        imgContainer.innerHTML = "";
      }
    }

    // Reset Chatbot Messages
    renderChatMessages();

    // Show modal
    if (modal) modal.classList.remove("hidden");
    lucide.createIcons();
  } catch (e) {
    console.error("Error opening notice modal:", e);
  } finally {
    showLoading(false);
  }
}

function closeNoticeModal() {
  const modal = document.getElementById("noticeDetailModal");
  if (modal) modal.classList.add("hidden");
  state.activeNotice = null;
}

// ----------------- Chatbot Logic ----------------- //

function renderChatMessages() {
  const container = document.getElementById("chatMessagesContainer");
  if (!container) return;

  if (state.chatHistory.length === 0) {
    container.innerHTML = `
      <div class="text-center py-6 text-slate-400 text-xs">
        <i data-lucide="bot" class="w-8 h-8 mx-auto text-indigo-400 mb-2"></i>
        <p class="font-medium text-slate-200">Hi! I'm NoticeBot.</p>
        <p class="text-slate-400 mt-1">Ask me anything about this circular—deadlines, eligibility, penalties, or rules!</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = state.chatHistory.map(m => `
    <div class="flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} mb-3">
      <div class="max-w-[85%] px-4 py-2.5 text-xs leading-relaxed ${m.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}">
        ${m.role === 'assistant' ? `<div class="text-[10px] text-indigo-400 font-semibold mb-1 flex items-center gap-1"><i data-lucide="bot" class="w-3 h-3"></i> NoticeBot</div>` : ''}
        <div>${m.content}</div>
      </div>
    </div>
  `).join("");

  container.scrollTop = container.scrollHeight;
  lucide.createIcons();
}

async function sendChatMessage(promptText = null) {
  const input = document.getElementById("chatInput");
  const msg = promptText || (input ? input.value.trim() : "");
  if (!msg) return;

  if (input) input.value = "";

  // Append user message
  state.chatHistory.push({ role: "user", content: msg });
  renderChatMessages();

  // Add temporary thinking indicator
  const container = document.getElementById("chatMessagesContainer");
  const thinkingId = `thinking-${Date.now()}`;
  if (container) {
    container.innerHTML += `
      <div id="${thinkingId}" class="flex justify-start mb-3">
        <div class="chat-bubble-ai px-4 py-2.5 text-xs text-indigo-300 flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style="animation-delay: 0.15s"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style="animation-delay: 0.3s"></span>
          <span class="ml-1 text-[11px] text-slate-400">NoticeBot is analyzing this circular...</span>
        </div>
      </div>
    `;
    container.scrollTop = container.scrollHeight;
  }

  try {
    const res = await fetch(`${API_BASE}/api/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        notice_id: state.activeNotice ? state.activeNotice.id : null,
        message: msg,
        model: state.chatModel,
        history: state.chatHistory.slice(-4)
      })
    });
    const data = await res.json();

    // Remove thinking
    const thinkingEl = document.getElementById(thinkingId);
    if (thinkingEl) thinkingEl.remove();

    state.chatHistory.push({
      role: "assistant",
      content: data.reply,
      engine: data.engine
    });
    renderChatMessages();
  } catch (e) {
    console.error("Chat error:", e);
    const thinkingEl = document.getElementById(thinkingId);
    if (thinkingEl) thinkingEl.remove();
    state.chatHistory.push({
      role: "assistant",
      content: "Error communicating with AI service. Please check network or try again.",
      engine: "error"
    });
    renderChatMessages();
  }
}

// ----------------- OCR Upload & AI Draft Studio ----------------- //

function openAdminStudioModal() {
  if (state.currentUser?.role === "student") {
    alert("Notice Publishing Restricted:\n\nIn accordance with university protocol, students cannot publish circulars. Only verified College Authorities (Dean, Examination Controller, HODs, and Faculty) hold publishing privileges.\n\nPlease switch to a College Official or Faculty persona using the Role menu in the top bar.");
    return;
  }
  const modal = document.getElementById("adminStudioModal");
  if (modal) modal.classList.remove("hidden");

  const authLabel = document.getElementById("officialPublisherLabel");
  if (authLabel && state.currentUser) {
    authLabel.textContent = `Authorized Publisher: ${state.currentUser.name} (${state.currentUser.department})`;
  }

  // Pre-select department if faculty/official belongs to one
  const deptSelect = document.getElementById("newNoticeDept");
  if (deptSelect && state.currentUser && state.currentUser.department !== "Administration" && state.currentUser.department !== "Examination Cell") {
    deptSelect.value = state.currentUser.department;
  }

  lucide.createIcons();
}

function closeAdminStudioModal() {
  const modal = document.getElementById("adminStudioModal");
  if (modal) modal.classList.add("hidden");
}

async function handleOCRFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  await processOCRUpload(file);
}

async function testSampleNotice(sampleFilename) {
  showLoading(true);
  try {
    // Fetch the sample image from uploads
    const res = await fetch(`/uploads/${sampleFilename}`);
    const blob = await res.blob();
    const file = new File([blob], sampleFilename, { type: "image/png" });
    await processOCRUpload(file);
  } catch (e) {
    console.error("Sample OCR error:", e);
  } finally {
    showLoading(false);
  }
}

async function processOCRUpload(file) {
  const statusEl = document.getElementById("ocrExtractionStatus");
  if (statusEl) {
    statusEl.innerHTML = `
      <div class="p-4 rounded-xl bg-indigo-950/70 border border-indigo-700/60 text-xs text-indigo-200 flex items-center gap-3">
        <span class="w-3 h-3 rounded-full bg-indigo-400 animate-ping"></span>
        <span>Scanning circular and reading details from <b>${file.name}</b>...</span>
      </div>
    `;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/api/ocr/upload`, {
      method: "POST",
      body: formData
    });
    const result = await res.json();

    if (statusEl) {
      statusEl.innerHTML = `
        <div class="p-4 rounded-xl bg-emerald-950/70 border border-emerald-700/60 text-xs text-emerald-200 space-y-2">
          <div class="flex items-center justify-between">
            <span class="font-semibold flex items-center gap-1.5 text-emerald-300">
              <i data-lucide="check-circle" class="w-4 h-4"></i> Notice Scanned Successfully
            </span>
            <span class="px-2 py-0.5 rounded bg-emerald-800 text-emerald-200 text-[10px]">Form Auto-filled</span>
          </div>
          <div class="text-[11px] text-slate-300">Detected: <b>${result.detected_category}</b> | Deadline: <b>${result.detected_deadline || 'Not specified'}</b> | Dept: <b>${result.detected_department}</b></div>
        </div>
      `;
    }

    // Auto-populate form fields
    const titleInput = document.getElementById("newNoticeTitle");
    const categorySelect = document.getElementById("newNoticeCategory");
    const deptSelect = document.getElementById("newNoticeDept");
    const prioritySelect = document.getElementById("newNoticePriority");
    const deadlineInput = document.getElementById("newNoticeDeadline");
    const contentTextarea = document.getElementById("newNoticeContent");
    const tagsInput = document.getElementById("newNoticeTags");
    const imgPathInput = document.getElementById("newNoticeImagePath");

    if (titleInput && result.detected_title) titleInput.value = result.detected_title;
    if (categorySelect && result.detected_category) categorySelect.value = result.detected_category;
    if (deptSelect && result.detected_department) deptSelect.value = result.detected_department;
    if (prioritySelect && result.detected_urgency) prioritySelect.value = result.detected_urgency;
    if (deadlineInput && result.detected_deadline) deadlineInput.value = result.detected_deadline;
    if (contentTextarea && result.raw_text) contentTextarea.value = result.raw_text;
    if (tagsInput && result.suggested_tags) tagsInput.value = result.suggested_tags.join(", ");
    if (imgPathInput && result.file_url) imgPathInput.value = result.file_url;

    lucide.createIcons();
  } catch (e) {
    console.error("OCR Upload error:", e);
    if (statusEl) {
      statusEl.innerHTML = `
        <div class="p-3 rounded-xl bg-red-950/70 border border-red-700 text-xs text-red-300">
          Failed to process OCR: ${e.message}
        </div>
      `;
    }
  }
}

async function generateAIDraft() {
  const promptInput = document.getElementById("aiDraftPrompt");
  const modelSelect = document.getElementById("aiDraftModel");
  const prompt = promptInput ? promptInput.value.trim() : "";
  if (!prompt) {
    alert("Please write a topic or notes for the AI draft assistant!");
    return;
  }

  const model = modelSelect ? modelSelect.value : "gemini";
  const btn = document.getElementById("generateDraftBtn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin mr-1">⏳</span> Drafting notice...`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/ai/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt,
        category: document.getElementById("newNoticeCategory")?.value || "General",
        department: document.getElementById("newNoticeDept")?.value || "All Departments",
        urgency: document.getElementById("newNoticePriority")?.value || "Medium",
        model: model
      })
    });
    const data = await res.json();
    const contentEl = document.getElementById("newNoticeContent");
    if (contentEl) {
      contentEl.value = data.draft;
    }
    const titleEl = document.getElementById("newNoticeTitle");
    if (titleEl && !titleEl.value) {
      titleEl.value = prompt.length > 60 ? prompt.substring(0, 60) + "..." : prompt;
    }
  } catch (e) {
    console.error("AI Draft error:", e);
    alert("Draft generation error. Please try again.");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Generate Draft</span>`;
    }
  }
}

async function publishNotice() {
  const title = document.getElementById("newNoticeTitle")?.value.trim();
  const content = document.getElementById("newNoticeContent")?.value.trim();
  const category = document.getElementById("newNoticeCategory")?.value || "General";
  const department = document.getElementById("newNoticeDept")?.value || "All Departments";
  const priority = document.getElementById("newNoticePriority")?.value || "Medium";
  const deadline = document.getElementById("newNoticeDeadline")?.value || null;
  const tagsStr = document.getElementById("newNoticeTags")?.value || "";
  const imgPath = document.getElementById("newNoticeImagePath")?.value || null;

  if (!title || !content) {
    alert("Notice title and content are required!");
    return;
  }

  const tags = tagsStr.split(",").map(t => t.trim()).filter(Boolean);

  showLoading(true);
  try {
    const res = await fetch(`${API_BASE}/api/notices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        category,
        department,
        priority,
        content,
        deadline,
        tags,
        image_path: imgPath,
        extracted_from_ocr: Boolean(imgPath)
      })
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(err.detail || "Failed to publish notice: Unauthorized action.");
      return;
    }

    const data = await res.json();
    alert("Official notice published and broadcasted successfully!");
    closeAdminStudioModal();
    // Refresh feed and system status
    await Promise.all([fetchFeed(), fetchSystemStatus()]);
    renderFeed();
  } catch (e) {
    console.error("Error creating notice:", e);
    alert("Failed to publish notice.");
  } finally {
    showLoading(false);
  }
}

// ----------------- Persona & Bookmarks ----------------- //

async function switchPersona(userId) {
  showLoading(true);
  try {
    const formData = new FormData();
    formData.append("user_id", userId);
    const res = await fetch(`${API_BASE}/api/user/switch`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    state.currentUser = data.current_user;
    renderUserPersonaUI();
    // Reload feed tailored to new persona
    await fetchFeed();
    renderFeed();
  } catch (e) {
    console.error("Error switching persona:", e);
  } finally {
    showLoading(false);
  }
}

async function toggleBookmark(noticeId, event) {
  if (event) event.stopPropagation();
  try {
    const res = await fetch(`${API_BASE}/api/notices/${noticeId}/bookmark`, { method: "POST" });
    const data = await res.json();

    if (state.currentUser) {
      if (data.is_bookmarked) {
        if (!state.currentUser.bookmarked_notice_ids.includes(noticeId)) {
          state.currentUser.bookmarked_notice_ids.push(noticeId);
        }
      } else {
        state.currentUser.bookmarked_notice_ids = state.currentUser.bookmarked_notice_ids.filter(id => id !== noticeId);
      }
    }

    // Refresh active tab rendering
    if (state.activeTab === "all") fetchAllNotices();
    else if (state.activeTab === "recommendations") renderFeed();
    else if (state.activeTab === "search") searchNotices();

    lucide.createIcons();
  } catch (e) {
    console.error("Bookmark toggle error:", e);
  }
}

// ----------------- Accessibility & Calendar Export ----------------- //

function speakNotice(noticeId, event) {
  if (event) event.stopPropagation();
  const notice = state.feed?.personalized?.find(p => p.notice.id === noticeId)?.notice ||
                 state.notices.find(n => n.id === noticeId) ||
                 state.activeNotice;

  if (!notice) return;

  if (!('speechSynthesis' in window)) {
    alert("Text to speech is not supported in this browser.");
    return;
  }

  window.speechSynthesis.cancel();
  const speechText = `Notice from ${notice.department}. Title: ${notice.title}. Summary: ${notice.summary || notice.content}. Deadline: ${notice.deadline || 'No fixed deadline'}.`;
  const utterance = new SpeechSynthesisUtterance(speechText);
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}

function exportCalendarEvent() {
  if (!state.activeNotice || !state.activeNotice.deadline) {
    alert("This notice doesn't have a specific deadline date.");
    return;
  }

  const notice = state.activeNotice;
  const dStr = notice.deadline.replace(/-/g, "");
  const icsData = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//NexusNotice AI//Smart Campus//EN",
    "BEGIN:VEVENT",
    `SUMMARY:${notice.title.replace(/,/g, "\\,")}`,
    `DESCRIPTION:${(notice.summary || notice.content).substring(0, 150).replace(/\n/g, " ")}`,
    `DTSTART;VALUE=DATE:${dStr.substring(0, 8)}`,
    `DTEND;VALUE=DATE:${dStr.substring(0, 8)}`,
    "STATUS:CONFIRMED",
    "END:VEVENT",
    "END:VCALENDAR"
  ].join("\r\n");

  const blob = new Blob([icsData], { type: "text/calendar;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${notice.id}-deadline.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ----------------- Analytics & FAISS 2D Vector Space ----------------- //

async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/api/analytics`);
    state.analyticsData = await res.json();
    renderAnalyticsCharts();
  } catch (e) {
    console.error("Analytics fetch error:", e);
  }
}

function renderAnalyticsCharts() {
  if (!state.analyticsData) return;
  const data = state.analyticsData;

  // Stats Counters
  document.getElementById("statTotalNotices").textContent = data.total_notices;
  document.getElementById("statTotalViews").textContent = data.total_views;
  document.getElementById("statTotalBookmarks").textContent = data.total_bookmarks;
  document.getElementById("statTotalVectors").textContent = Object.keys(data.categories || {}).length || 8;

  // Category Chart
  const catCanvas = document.getElementById("categoryChartCanvas");
  if (catCanvas && window.Chart) {
    if (state.categoryChart) state.categoryChart.destroy();
    const labels = Object.keys(data.categories);
    const values = Object.values(data.categories);
    state.categoryChart = new Chart(catCanvas, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ["#ef4444", "#3b82f6", "#a855f7", "#10b981", "#f59e0b", "#ec4899", "#14b8a6", "#64748b"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: "#94a3b8", font: { size: 11 } } }
        }
      }
    });
  }

  // 2D FAISS Vector Space PCA Scatter Plot
  const vectorCanvas = document.getElementById("vectorSpaceCanvas");
  if (vectorCanvas && window.Chart && data.vector_space_2d) {
    if (state.vectorChart) state.vectorChart.destroy();
    const points = data.vector_space_2d.map(pt => ({
      x: pt.x,
      y: pt.y,
      title: pt.title,
      category: pt.category,
      department: pt.department
    }));

    state.vectorChart = new Chart(vectorCanvas, {
      type: "scatter",
      data: {
        datasets: [{
          label: "Notice Distribution by Topic",
          data: points,
          backgroundColor: points.map(p => {
            if (p.category === "Examinations") return "#ef4444";
            if (p.category === "Placements") return "#3b82f6";
            if (p.category === "Events") return "#a855f7";
            if (p.category === "Scholarships") return "#10b981";
            if (p.category === "Fees & Finance") return "#f59e0b";
            return "#6366f1";
          }),
          pointRadius: 6,
          pointHoverRadius: 9
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const p = ctx.raw;
                return `${p.category}: ${p.title} (${p.department})`;
              }
            }
          },
          legend: { labels: { color: "#94a3b8" } }
        },
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#64748b" } },
          y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#64748b" } }
        }
      }
    });
  }
}

// ----------------- Settings Modal ----------------- //

async function openSettingsModal() {
  const modal = document.getElementById("settingsModal");
  if (!modal) return;
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    const cfg = await res.json();
    const gInput = document.getElementById("settingsGeminiKey");
    const cInput = document.getElementById("settingsClaudeKey");
    const mSelect = document.getElementById("settingsPreferredLlm");

    if (gInput && cfg.gemini_api_key) gInput.placeholder = `Configured: ${cfg.gemini_api_key}`;
    if (cInput && cfg.anthropic_api_key) cInput.placeholder = `Configured: ${cfg.anthropic_api_key}`;
    if (mSelect && cfg.preferred_llm) mSelect.value = cfg.preferred_llm;

    modal.classList.remove("hidden");
  } catch (e) {
    console.error("Settings load error:", e);
  }
}

function closeSettingsModal() {
  const modal = document.getElementById("settingsModal");
  if (modal) modal.classList.add("hidden");
}

async function saveSettingsFromUI() {
  const geminiKey = document.getElementById("settingsGeminiKey")?.value.trim();
  const claudeKey = document.getElementById("settingsClaudeKey")?.value.trim();
  const preferredLlm = document.getElementById("settingsPreferredLlm")?.value;

  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gemini_api_key: geminiKey || "",
        anthropic_api_key: claudeKey || "",
        preferred_llm: preferredLlm
      })
    });
    const data = await res.json();
    alert("API Keys and LLM preferences updated successfully!");
    closeSettingsModal();
    await fetchSystemStatus();
  } catch (e) {
    console.error("Save settings error:", e);
    alert("Failed to save settings.");
  }
}

// ----------------- Tabs & Event Listeners ----------------- //

function switchTab(tabName) {
  state.activeTab = tabName;
  const tabs = ["recommendations", "all", "deadlines", "trending", "analytics", "search"];

  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (view) {
      if (t === tabName) view.classList.remove("hidden");
      else view.classList.add("hidden");
    }
    if (btn) {
      if (t === tabName) {
        btn.classList.add("bg-indigo-600", "text-white");
        btn.classList.remove("text-slate-400", "hover:bg-slate-800");
      } else {
        btn.classList.remove("bg-indigo-600", "text-white");
        btn.classList.add("text-slate-400", "hover:bg-slate-800");
      }
    }
  });

  if (tabName === "all") fetchAllNotices();
  if (tabName === "analytics") loadAnalytics();
  lucide.createIcons();
}

function setupEventListeners() {
  // Search bar input & enter key
  const searchInput = document.getElementById("mainSearchInput");
  const clearBtn = document.getElementById("clearSearchBtn");

  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        searchNotices();
      }
    });

    searchInput.addEventListener("input", (e) => {
      state.searchQuery = e.target.value.trim();
      if (clearBtn) {
        if (state.searchQuery.length > 0) {
          clearBtn.classList.remove("hidden");
        } else {
          clearBtn.classList.add("hidden");
        }
      }
    });
  }

  // Semantic toggle switch
  const semanticToggle = document.getElementById("semanticSearchToggle");
  if (semanticToggle) {
    semanticToggle.addEventListener("change", (e) => {
      state.useSemanticSearch = e.target.checked;
      if (state.searchQuery && state.searchQuery.trim().length > 0) {
        searchNotices();
      }
    });
  }

  // Chat model toggle
  const chatModelSelect = document.getElementById("chatModelSelect");
  if (chatModelSelect) {
    chatModelSelect.addEventListener("change", (e) => {
      state.chatModel = e.target.value;
    });
  }
}

function showLoading(isLoading) {
  const loader = document.getElementById("globalLoader");
  if (loader) {
    if (isLoading) loader.classList.remove("hidden");
    else loader.classList.add("hidden");
  }
}
