let selectedIndex = -1;
let currentPlayerChannel = null;

function api() { return window.pywebview.api; }

function fmtRemaining(seconds) {
  if (seconds === null || seconds === undefined) return "— remaining";
  const m = Math.floor(seconds / 60), s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")} remaining`;
}

function renderQueue(items, activeIndex) {
  const list = document.getElementById("queue-list");
  list.innerHTML = "";
  items.forEach((item, i) => {
    const li = document.createElement("li");
    if (i === selectedIndex) li.classList.add("selected");
    const marker = document.createElement("span");
    marker.className = "marker";
    marker.textContent = i === activeIndex ? "●" : "○";
    const name = document.createElement("span");
    name.textContent = item.login;
    name.style.flex = "1";
    const mins = document.createElement("span");
    mins.className = "mins";
    mins.textContent = item.minutes > 0 ? `${item.minutes} min` : "until drops earned";
    li.append(marker, name, mins);
    li.addEventListener("click", () => { selectedIndex = i; refresh(); });
    li.addEventListener("dblclick", () => { api().play_stream(i); });
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

  renderQueue(status.items, status.active_index);

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
  setInterval(refresh, 1000);
  setInterval(refreshDrops, 15000);
  refresh();
  refreshDrops();
}

window.addEventListener("pywebviewready", wire);
