let selectedIndex = -1;
let currentPlayerChannel = null;
let lastDropsChannel = null;

function api() { return window.pywebview.api; }

function showDropsLoading() {
  const container = document.getElementById("drops-list");
  container.innerHTML = `<div class="drops-loading"><span class="spinner"></span> Loading drop info…</div>`;
}

function fmtRemaining(seconds) {
  if (seconds === null || seconds === undefined) return "— remaining";
  const m = Math.floor(seconds / 60), s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")} remaining`;
}

let editingIndex = -1;

function renderQueue(items, activeIndex, running) {
  const list = document.getElementById("queue-list");
  list.innerHTML = "";
  items.forEach((item, i) => {
    const li = document.createElement("li");
    li.draggable = !running;
    if (i === selectedIndex) li.classList.add("selected");

    if (i === editingIndex) {
      const editRow = document.createElement("div");
      editRow.className = "queue-item-edit";
      const modeSel = document.createElement("select");
      modeSel.innerHTML = `<option value="fixed">Fixed time</option><option value="until-earned">Until drops earned</option>`;
      modeSel.value = item.minutes > 0 ? "fixed" : "until-earned";
      const minInput = document.createElement("input");
      minInput.type = "number"; minInput.min = "1"; minInput.max = "1440";
      minInput.value = item.minutes > 0 ? item.minutes : 60;
      minInput.style.display = modeSel.value === "until-earned" ? "none" : "inline-block";
      modeSel.addEventListener("change", () => {
        minInput.style.display = modeSel.value === "until-earned" ? "none" : "inline-block";
      });
      const saveBtn = document.createElement("button");
      saveBtn.textContent = "Save"; saveBtn.className = "primary";
      saveBtn.addEventListener("click", async () => {
        const minutes = modeSel.value === "until-earned" ? 0 : (parseInt(minInput.value, 10) || 60);
        await api().edit_stream(i, minutes);
        editingIndex = -1; refresh();
      });
      const cancelBtn = document.createElement("button");
      cancelBtn.textContent = "Cancel";
      cancelBtn.addEventListener("click", () => { editingIndex = -1; refresh(); });
      editRow.append(modeSel, minInput, saveBtn, cancelBtn);
      li.appendChild(editRow);
      list.appendChild(li);
      return;
    }

    const marker = document.createElement("span");
    marker.className = "marker";
    marker.textContent = i === activeIndex ? "●" : "○";
    const name = document.createElement("span");
    name.textContent = item.login;
    name.style.flex = "1";
    const mins = document.createElement("span");
    mins.className = "mins";
    mins.textContent = item.minutes > 0 ? `${item.minutes} min` : "until drops earned";
    const editBtn = document.createElement("button");
    editBtn.className = "edit-btn"; editBtn.textContent = "✎"; editBtn.title = "Edit";
    editBtn.addEventListener("click", (e) => { e.stopPropagation(); editingIndex = i; refresh(); });
    li.append(marker, name, mins, editBtn);
    li.addEventListener("click", () => { selectedIndex = i; refresh(); });
    li.addEventListener("dblclick", () => { api().play_stream(i); });

    li.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(i));
      li.classList.add("dragging");
    });
    li.addEventListener("dragend", () => li.classList.remove("dragging"));
    li.addEventListener("dragover", (e) => { if (!running) e.preventDefault(); });
    li.addEventListener("drop", async (e) => {
      e.preventDefault();
      const from = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (!Number.isNaN(from) && from !== i) {
        await api().reorder_stream(from, i);
        refresh();
      }
    });

    list.appendChild(li);
  });
}

function updatePlayer(channel) {
  if (channel === currentPlayerChannel) return;
  currentPlayerChannel = channel;
  const frame = document.getElementById("player-frame");
  const placeholder = document.getElementById("player-placeholder");
  if (!channel) {
    frame.style.display = "none";
    placeholder.style.display = "flex";
    placeholder.textContent = "Start the queue to load a stream here.";
    frame.src = "";
    return;
  }
  placeholder.style.display = "none";
  frame.style.display = "block";
  frame.src = `https://player.twitch.tv/?channel=${encodeURIComponent(channel)}&parent=localhost&autoplay=true`;
}

async function refresh() {
  const status = await api().get_status();
  const accountEl = document.getElementById("account-status");
  accountEl.textContent = status.linked ? "Twitch linked" : "Not linked";
  accountEl.classList.toggle("linked", status.linked);
  document.getElementById("link-btn").style.display = status.linked ? "none" : "inline-block";
  document.getElementById("unlink-btn").style.display = status.linked ? "inline-block" : "none";

  const playerLoginBtn = document.getElementById("player-login-btn");
  if (status.player_signed_in) {
    playerLoginBtn.textContent = "Player signed in ✓";
    playerLoginBtn.disabled = true;
  } else {
    playerLoginBtn.textContent = "Sign in to Twitch player";
    playerLoginBtn.disabled = false;
  }

  renderQueue(status.items, status.active_index, status.running);

  document.getElementById("now-watching").textContent =
    status.running && status.now_channel ? status.now_channel : "Queue paused";
  document.getElementById("remaining").textContent = status.running
    ? (status.no_timer ? "Watching until drops earned" : fmtRemaining(status.remaining))
    : "— remaining";
  const startBtn = document.getElementById("start-btn");
  startBtn.textContent = status.running ? "Stop queue" : "Start queue";
  const canStart = status.running || status.player_signed_in;
  startBtn.disabled = !canStart;
  startBtn.title = canStart ? "" : "Sign in to Twitch player first";

  const hint = document.getElementById("player-signin-hint");
  hint.style.display = status.player_signed_in ? "none" : "block";

  updatePlayer(status.player_channel);

  if (status.player_channel !== lastDropsChannel) {
    lastDropsChannel = status.player_channel;
    if (status.player_channel) {
      showDropsLoading();
      refreshDrops();
    }
  }
}

function renderDrops(campaigns) {
  const container = document.getElementById("drops-list");
  container.innerHTML = "";
  if (!campaigns || campaigns.length === 0) {
    const empty = document.createElement("div");
    empty.className = "drops-empty";
    empty.textContent = "No drop campaigns for the current stream's game right now.";
    container.appendChild(empty);
    return;
  }
  campaigns.forEach((campaign) => {
    const heading = document.createElement("div");
    heading.className = "drop-campaign";
    heading.textContent = `${campaign.name} — ${campaign.game}`;
    container.appendChild(heading);
    campaign.drops.forEach((drop) => {
      const pct = drop.required_minutes > 0
        ? Math.min(100, Math.round((drop.current_minutes / drop.required_minutes) * 100))
        : 0;
      const wrap = document.createElement("div");
      wrap.className = "drop-item";
      const nameRow = document.createElement("div");
      nameRow.className = "drop-name" + (drop.earned ? " claimed" : "");
      const label = document.createElement("span");
      label.textContent = drop.earned ? `✓ ${drop.name}` : drop.name;
      const pctEl = document.createElement("span");
      pctEl.className = "pct";
      if (drop.earned) {
        const when = drop.earned_at
          ? new Date(drop.earned_at * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          : null;
        const claimNote = drop.claimed ? "" : " · claim on Twitch";
        pctEl.textContent = (when ? `Earned at ${when}` : "Earned") + claimNote;
      } else {
        pctEl.textContent = `${drop.current_minutes}/${drop.required_minutes} min`;
      }
      nameRow.append(label, pctEl);
      const track = document.createElement("div");
      track.className = "bar-track";
      const fill = document.createElement("div");
      fill.className = "bar-fill" + (drop.earned ? " claimed" : "");
      fill.style.width = `${pct}%`;
      track.appendChild(fill);
      wrap.append(nameRow, track);
      container.appendChild(wrap);
    });
  });
}

async function refreshDrops() {
  try {
    const campaigns = await api().get_drops_progress();
    const error = await api().get_drops_error();
    if (error) {
      const container = document.getElementById("drops-list");
      container.innerHTML = "";
      const errEl = document.createElement("div");
      errEl.className = "drops-empty";
      errEl.style.color = "#e07a7a";
      errEl.textContent = `Drops check failed: ${error}`;
      container.appendChild(errEl);
      return;
    }
    renderDrops(campaigns);
  } catch (e) { /* ignore transient failures */ }
}

function renderHistory(entries) {
  const container = document.getElementById("drops-history-list");
  container.innerHTML = "";
  if (!entries || entries.length === 0) {
    const empty = document.createElement("div");
    empty.className = "drops-empty";
    empty.textContent = "No drops earned yet.";
    container.appendChild(empty);
    return;
  }
  entries.slice(0, 50).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "history-item";
    const label = document.createElement("span");
    label.textContent = `${entry.drop_name} — ${entry.game}`;
    const when = document.createElement("span");
    when.className = "when";
    when.textContent = new Date(entry.earned_at * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    row.append(label, when);
    container.appendChild(row);
  });
}

async function refreshHistory() {
  try {
    const entries = await api().get_drops_history();
    renderHistory(entries);
  } catch (e) { /* ignore */ }
}

async function searchDropStreams() {
  const gameName = document.getElementById("game-search-input").value.trim();
  const resultsEl = document.getElementById("game-search-results");
  if (!gameName) return;
  resultsEl.innerHTML = "<div class=\"drops-empty\">Searching…</div>";
  const result = await api().find_drop_streams(gameName);
  resultsEl.innerHTML = "";
  if (result.error) {
    const err = document.createElement("div");
    err.className = "drops-empty"; err.style.color = "#e07a7a";
    err.textContent = result.error;
    resultsEl.appendChild(err);
    return;
  }
  if (!result.streams || result.streams.length === 0) {
    const empty = document.createElement("div");
    empty.className = "drops-empty";
    empty.textContent = `No live streams with drops enabled found for ${result.game}.`;
    resultsEl.appendChild(empty);
    return;
  }
  result.streams.forEach((stream) => {
    const row = document.createElement("div");
    row.className = "found-item";
    const info = document.createElement("span");
    info.className = "title";
    info.textContent = `${stream.display_name} · ${stream.viewer_count} viewers`;
    const addBtn = document.createElement("button");
    addBtn.textContent = "+ Add";
    addBtn.addEventListener("click", async () => {
      await api().add_found_stream(stream.login, 0);
      refresh();
    });
    row.append(info, addBtn);
    resultsEl.appendChild(row);
  });
}

function wire() {
  document.getElementById("link-btn").addEventListener("click", async (e) => {
    e.target.disabled = true; e.target.textContent = "Waiting for Twitch…";
    await api().link_twitch();
    setTimeout(() => { e.target.disabled = false; e.target.textContent = "Link Twitch"; }, 1500);
  });
  document.getElementById("unlink-btn").addEventListener("click", async () => {
    await api().unlink_twitch(); refresh();
  });
  document.getElementById("player-login-btn").addEventListener("click", async () => {
    await api().open_player_login();
  });
  document.getElementById("mode-select").addEventListener("change", (e) => {
    document.getElementById("minutes-input").style.display = e.target.value === "until-earned" ? "none" : "block";
  });
  document.getElementById("add-btn").addEventListener("click", async () => {
    const url = document.getElementById("url-input").value.trim();
    const mode = document.getElementById("mode-select").value;
    const minutes = mode === "until-earned" ? 0 : (parseInt(document.getElementById("minutes-input").value, 10) || 60);
    if (!url.includes("twitch.tv/")) { alert("Enter a full Twitch channel URL."); return; }
    await api().add_stream(url, minutes);
    document.getElementById("url-input").value = "";
    refresh();
  });
  document.getElementById("remove-btn").addEventListener("click", async () => {
    if (selectedIndex < 0) return;
    await api().remove_stream(selectedIndex);
    selectedIndex = -1; refresh();
  });
  document.getElementById("play-btn").addEventListener("click", async () => {
    if (selectedIndex < 0) return;
    await api().play_stream(selectedIndex);
  });
  document.getElementById("stop-stream-btn").addEventListener("click", async () => {
    await api().stop_stream(); refresh();
  });
  document.getElementById("start-btn").addEventListener("click", async () => {
    await api().toggle_queue(); refresh();
  });
  document.getElementById("confirm-btn").addEventListener("click", async () => {
    await api().confirm_drops();
  });
  document.getElementById("inventory-btn").addEventListener("click", async () => {
    await api().open_inventory();
  });
  document.getElementById("settings-btn").addEventListener("click", async (e) => {
    e.stopPropagation();
    const panel = document.getElementById("settings-panel");
    const opening = panel.classList.contains("hidden");
    panel.classList.toggle("hidden");
    if (opening) {
      const current = await api().get_settings();
      document.getElementById("minimize-tray-setting").checked = !!current.minimize_to_tray;
    }
  });
  document.addEventListener("click", (e) => {
    const panel = document.getElementById("settings-panel");
    if (!panel.contains(e.target) && e.target.id !== "settings-btn") panel.classList.add("hidden");
  });
  document.getElementById("minimize-tray-setting").addEventListener("change", async (e) => {
    await api().set_setting("minimize_to_tray", e.target.checked);
  });
  document.getElementById("minimize-tray-btn").addEventListener("click", async () => {
    await api().minimize_to_tray();
  });
  document.getElementById("game-search-btn").addEventListener("click", searchDropStreams);
  document.getElementById("game-search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") searchDropStreams();
  });
  setInterval(refresh, 1000);
  setInterval(refreshDrops, 15000);
  setInterval(refreshHistory, 20000);
  refresh();
  refreshDrops();
  refreshHistory();
}

window.addEventListener("pywebviewready", wire);
