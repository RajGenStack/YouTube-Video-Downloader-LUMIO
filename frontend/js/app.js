// Client-side app entrypoint. Move the script logic from public/index.html into this file for production.

const downloadApiEndpoint = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;
let mode = 'mp3', fmt = '320k';
let fetchedVideoId = null;
let fetchedUrl = '';
let fetchedTitle = '';
let theme = 'light';

// ─── TOAST
function toast(msg, dur = 3200) {
  const t = document.getElementById('toast');
  if (!t) return; // page may not include toast element in minimal previews
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), dur);
}

function toggleTheme() {
  theme = theme === 'light' ? 'dark' : 'light';
  document.body.classList.toggle('dark', theme === 'dark');
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = theme === 'dark' ? 'Light' : 'Dark';
  localStorage.setItem('lumioTheme', theme);
}

function initTheme() {
  const saved = localStorage.getItem('lumioTheme');
  theme = saved === 'dark' ? 'dark' : 'light';
  document.body.classList.toggle('dark', theme === 'dark');
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = theme === 'dark' ? 'Light' : 'Dark';
}

// ─── MODE SWITCH
function setMode(m) {
  mode = m;
  const mp3T = document.getElementById('mp3Tog');
  const mp4T = document.getElementById('mp4Tog');
  if (mp3T) mp3T.classList.toggle('active', m === 'mp3');
  if (mp4T) mp4T.classList.toggle('active', m === 'mp4');
  const p3 = document.getElementById('panelMp3');
  const p4 = document.getElementById('panelMp4');
  if (p3) p3.style.display = m === 'mp3' ? '' : 'none';
  if (p4) p4.style.display = m === 'mp4' ? '' : 'none';
  if (m === 'mp3') { fmt = '320k'; highlightChip('panelMp3', '320k'); }
  else { fmt = '720p'; highlightChip('panelMp4', '720p'); }
}

function highlightChip(panelId, val) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  panel.querySelectorAll('.chip').forEach(c => {
    c.classList.toggle('sel', c.getAttribute('onclick')?.includes("'" + val + "'") );
  });
}

function getChipQuality(c) {
  const attr = c.getAttribute('onclick') || '';
  const match = attr.match(/'([^']+)'/);
  return match ? match[1] : '';
}

// ─── CHIP SELECT
function pick(el, f) {
  if (!el) return;
  // ignore clicks on disabled chips
  if (el.classList.contains('disabled')) return;
  const panel = el.closest('#panelMp3,#panelMp4');
  if (panel) panel.querySelectorAll('.chip').forEach(c => c.classList.remove('sel'));
  el.classList.add('sel');
  fmt = f;
}

// ─── EXTRACT VIDEO ID
function getVid(url) {
  const m = url.match(/(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{11})/);
  return m ? m[1] : null;
}

// ─── FETCH INFO
function doFetch() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { toast('⚠️ Paste a YouTube URL first'); return; }
  if (!url.includes('youtube.com') && !url.includes('youtu.be')) { toast('⚠️ Enter a valid YouTube URL'); return; }

  const ctrl = document.getElementById('downloadControls');
  if (ctrl) ctrl.style.display = 'none';

  const btn = document.getElementById('fetchBtn');
  const lbl = document.getElementById('fetchLabel');
  const sp = document.getElementById('fetchSpin');
  if (btn) btn.disabled = true; if (lbl) lbl.style.display = 'none'; if (sp) sp.classList.add('show');

  const complete = () => { if (btn) btn.disabled = false; if (lbl) lbl.style.display = ''; if (sp) sp.classList.remove('show'); };
  const id = getVid(url);
  const prev = document.getElementById('vPreview');

  if (!id) {
    setTimeout(() => {
      complete();
      if (prev) prev.classList.remove('show');
      toast('⚠️ Could not parse video ID. Check the URL.');
    }, 900);
    return;
  }

  fetchedVideoId = id;
  fetchedTitle = 'YouTube Video · ID: ' + id;

  if (downloadApiEndpoint.trim()) {
    const api = downloadApiEndpoint.replace(/\/$/, '');
    fetch(`${api}/api/fetch-info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
      .then(async response => {
        if (!response.ok) {
          const err = await response.json().catch(() => null);
          throw new Error(err?.detail || 'Failed to fetch video info');
        }
        return response.json();
      })
      .then(data => {
        // backend returns structured VideoInfoResponse
        fetchedVideoId = id;
        fetchedUrl = url;
        fetchedTitle = data.title || fetchedTitle;
        const thumb = document.getElementById('vThumb');
        if (thumb) thumb.src = data.thumbnail || `https://img.youtube.com/vi/${fetchedVideoId}/mqdefault.jpg`;
        const titleEl = document.getElementById('vTitle'); if (titleEl) titleEl.textContent = fetchedTitle;
        const dur = document.getElementById('vDur'); if (dur) dur.textContent = data.duration_str || 'Fetched ✓';

        // Dynamically show/hide MP4 resolution chips based on available_formats
        const avail = Array.isArray(data.available_formats) ? data.available_formats : [];
        let highestAvailableChip = null;
        let selectedIsAvailable = false;

        document.querySelectorAll('#panelMp4 .chip').forEach(c => {
          const q = getChipQuality(c);
          const isAvailable = avail.includes(q) || avail.includes(q.toLowerCase());
          
          c.classList.toggle('disabled', !isAvailable);
          
          if (isAvailable) {
            c.style.display = '';
            highestAvailableChip = c;
            if (c.classList.contains('sel')) {
              selectedIsAvailable = true;
            }
          } else {
            c.style.display = 'none';
          }
        });

        // If currently selected resolution is hidden/unavailable, select the highest available one
        if (!selectedIsAvailable && highestAvailableChip) {
          const q = getChipQuality(highestAvailableChip);
          document.querySelectorAll('#panelMp4 .chip').forEach(c => c.classList.remove('sel'));
          highestAvailableChip.classList.add('sel');
          fmt = q;
        }

        if (prev) prev.classList.add('show');
        const ctrl = document.getElementById('downloadControls');
        if (ctrl) ctrl.style.display = '';
        complete();
        toast('✓ Video info loaded — choose format and download');
      })
      .catch(error => {
        complete();
        toast('⚠️ ' + error.message);
      });
  } else {
    const thumb = document.getElementById('vThumb'); if (thumb) thumb.src = `https://img.youtube.com/vi/${id}/mqdefault.jpg`;
    const titleEl = document.getElementById('vTitle'); if (titleEl) titleEl.textContent = fetchedTitle;
    const dur = document.getElementById('vDur'); if (dur) dur.textContent = 'Fetched ✓';
    if (prev) prev.classList.add('show');
    fetchedUrl = url;
    setTimeout(() => { complete(); toast('✓ Video detected — choose format and download'); }, 900);
  }
}

// ─── RESET
function doReset() {
  const urlIn = document.getElementById('urlInput'); if (urlIn) urlIn.value = '';
  fetchedUrl = '';
  const prev = document.getElementById('vPreview'); if (prev) prev.classList.remove('show');
  const pw = document.getElementById('progWrap'); if (pw) pw.classList.remove('show');
  const pb = document.getElementById('progBar'); if (pb) pb.style.width = '0%';
  setMode('mp3');
  // Restore all video quality chips
  document.querySelectorAll('#panelMp4 .chip').forEach(c => {
    c.style.display = '';
    c.classList.remove('disabled');
  });
  const ctrl = document.getElementById('downloadControls');
  if (ctrl) ctrl.style.display = 'none';
  toast('Reset complete');
}

// ─── DOWNLOAD helpers
function getFileNameFromResponse(response) {
  const cd = response.headers.get('content-disposition') || '';
  const match = cd.match(/filename\*=UTF-8''([^;\n]+)/i) || cd.match(/filename="?([^";\n]+)"?/i);
  return match ? decodeURIComponent(match[1]) : null;
}

function sanitizeFileName(name) {
  return name.replace(/[^a-zA-Z0-9-_\.]/g, '_').replace(/_+/g, '_').substring(0, 120);
}

// ─── DOWNLOAD
function doDownload() {
  if (!fetchedUrl) { toast('⚠️ Paste and fetch a URL first'); return; }
  if (!fetchedVideoId) { toast('⚠️ Paste and fetch a valid YouTube URL first'); return; }
  if (!downloadApiEndpoint.trim()) { toast('⚠️ No backend configured. Set downloadApiEndpoint in the script.'); return; }

  const btn = document.getElementById('dlBtn'); const lbl = document.getElementById('dlLabel');
  const pw = document.getElementById('progWrap'); const pb = document.getElementById('progBar'); const pl = document.getElementById('progLabel');

  if (btn) btn.disabled = true; if (lbl) lbl.textContent = 'Preparing download…'; if (pw) pw.classList.add('show'); if (pb) pb.style.width = '5%'; if (pl) pl.textContent = 'Preparing request…';

  const api = downloadApiEndpoint.replace(/\/$/, '');
  const endpoint = `${api}/api/download`;

  const progressStages = [
    'Connecting to download service…',
    mode === 'mp3' ? 'Extracting audio stream…' : 'Extracting video stream…',
    'Processing file…',
    `Encoding ${fmt}…`,
    'Finalizing download…'
  ];

  let stage = 0;
  const interval = setInterval(() => {
    const current = Math.min(progressStages.length - 1, stage);
    if (pb) pb.style.width = `${5 + current * 18}%`;
    if (pl) pl.textContent = progressStages[current];
    if (stage < progressStages.length - 1) stage += 1;
  }, 700);

  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: fetchedUrl, mode, quality: fmt }),
  })
    .then(async response => {
      clearInterval(interval);
      if (!response.ok) {
        const err = await response.json().catch(() => null);
        throw new Error(err?.detail || 'Download request failed.');
      }
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const payload = await response.json();
        if (payload.url) { window.open(payload.url, '_blank'); if (pl) pl.textContent = 'Redirecting to download…'; if (pb) pb.style.width = '100%'; return; }
        if (payload.error) throw new Error(payload.error);
      }
      const blob = await response.blob();
      const fileName = getFileNameFromResponse(response) || sanitizeFileName(`${fetchedTitle || fetchedVideoId}_${fmt}.${mode === 'mp3' ? 'mp3' : 'mp4'}`);
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = objectUrl; a.download = fileName; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(objectUrl);
      if (pl) pl.textContent = `✓ Download ready: ${fileName}`; if (pb) pb.style.width = '100%';
    })
    .catch(error => {
      clearInterval(interval);
      if (pb) pb.style.width = '0%'; if (pl) pl.textContent = 'Download failed.'; toast('⚠️ ' + error.message);
    })
    .finally(() => {
      if (btn) btn.disabled = false; if (lbl) lbl.textContent = 'Download YouTube Video'; setTimeout(() => { if (pw) pw.classList.remove('show'); if (pb) pb.style.width = '0%'; }, 3000);
    });
}

// ─── FAQ ACCORDION
function toggleFaq(id) {
  const item = document.getElementById(id); if (!item) return;
  const body = item.querySelector('.faq-a'); const isOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(fi => { fi.classList.remove('open'); fi.querySelector('.faq-a').style.maxHeight = '0'; });
  if (!isOpen) { item.classList.add('open'); body.style.maxHeight = body.scrollHeight + 'px'; }
}

(() => {
  const f = document.getElementById('f1'); if (!f) return; const b = f.querySelector('.faq-a'); if (b) b.style.maxHeight = b.scrollHeight + 'px';
})();

// ─── ISSUE ACCORDION
function toggleIssue(id) {
  const item = document.getElementById(id); if (!item) return; const body = item.querySelector('.issue-body'); const isOpen = item.classList.contains('open');
  document.querySelectorAll('.issue-item').forEach(ii => { ii.classList.remove('open'); ii.querySelector('.issue-body').style.maxHeight = '0'; });
  if (!isOpen) { item.classList.add('open'); body.style.maxHeight = body.scrollHeight + 'px'; }
}

(() => {
  const i = document.getElementById('iss1'); if (!i) return; const b = i.querySelector('.issue-body'); i.classList.add('open'); if (b) b.style.maxHeight = b.scrollHeight + 'px';
})();

// ─── FORMATS TAB
function switchTab(t) {
  const tabMp4 = document.getElementById('tabMp4'); const tabMp3 = document.getElementById('tabMp3'); if (tabMp4) tabMp4.style.display = t === 'mp4' ? '' : 'none'; if (tabMp3) tabMp3.style.display = t === 'mp3' ? '' : 'none';
  document.querySelectorAll('.tab-btn').forEach((b, i) => { b.classList.toggle('active', (i === 0 && t === 'mp4') || (i === 1 && t === 'mp3')); });
}

initTheme();

document.getElementById('urlInput')?.addEventListener('paste', e => {
  setTimeout(() => {
    const v = document.getElementById('urlInput').value;
    if (v.includes('youtube.com') || v.includes('youtu.be')) doFetch();
  }, 60);
});
