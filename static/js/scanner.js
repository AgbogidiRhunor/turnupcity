/* ============================================================
   TURNUPCITY — QR SCANNER
   Uses jsQR (loaded via CDN in template)
   ============================================================ */

(function() {
  'use strict';

  const video = document.getElementById('scanner-video');
  const canvas = document.getElementById('scanner-canvas');
  const resultContainer = document.getElementById('scan-result');
  const scanHistoryList = document.getElementById('scan-history-list');
  const startBtn = document.getElementById('start-scanner-btn');
  const stopBtn = document.getElementById('stop-scanner-btn');
  const manualForm = document.getElementById('manual-scan-form');
  const manualInput = document.getElementById('manual-ticket-input');
  const eventSlug = document.getElementById('event-slug') && document.getElementById('event-slug').value;

  let scanning = false;
  let stream = null;
  let animationId = null;
  let lastScan = '';
  let scanCooldown = false;
  const COOLDOWN_MS = 3000;

  // ============================================================
  // CAMERA START / STOP
  // ============================================================
  if (startBtn) {
    startBtn.addEventListener('click', startCamera);
  }
  if (stopBtn) {
    stopBtn.addEventListener('click', stopCamera);
  }

  function startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showResult('error', '📷', 'Camera Not Supported', 'Your browser does not support camera access. Use manual lookup below.');
      return;
    }

    navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment',
        width: { ideal: 1280 },
        height: { ideal: 720 },
      }
    }).then(function(s) {
      stream = s;
      video.srcObject = stream;
      video.setAttribute('playsinline', true);
      video.play();
      scanning = true;
      if (startBtn) startBtn.style.display = 'none';
      if (stopBtn) stopBtn.style.display = '';
      clearResult();
      requestAnimationFrame(scanFrame);
    }).catch(function(err) {
      showResult('error', '🚫', 'Camera Access Denied',
        'Please allow camera access in your browser settings, then try again.');
      console.error('Camera error:', err);
    });
  }

  function stopCamera() {
    scanning = false;
    if (animationId) cancelAnimationFrame(animationId);
    if (stream) {
      stream.getTracks().forEach(function(t) { t.stop(); });
      stream = null;
    }
    video.srcObject = null;
    if (startBtn) startBtn.style.display = '';
    if (stopBtn) stopBtn.style.display = 'none';
  }

  // ============================================================
  // SCAN LOOP
  // ============================================================
  function scanFrame() {
    if (!scanning) return;
    animationId = requestAnimationFrame(scanFrame);

    if (video.readyState !== video.HAVE_ENOUGH_DATA) return;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.height = video.videoHeight;
    canvas.width  = video.videoWidth;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    if (typeof jsQR === 'undefined') return;

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert',
    });

    if (code && code.data && code.data !== lastScan && !scanCooldown) {
      lastScan = code.data;
      scanCooldown = true;
      processQRCode(code.data);
      setTimeout(function() {
        scanCooldown = false;
        lastScan = '';
      }, COOLDOWN_MS);
    }
  }

  // ============================================================
  // PROCESS QR CODE
  // ============================================================
  function processQRCode(data) {
    showResult('loading', '⌛', 'Validating...', 'Checking ticket, please wait.');
    submitScan(data);
  }

  function submitScan(qrData) {
    const gateInput = document.getElementById('gate-input');
    const gate = gateInput ? gateInput.value : '';

    fetch('/checkin/scan/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({
        qr_data: qrData,
        event_slug: eventSlug || '',
        gate: gate,
      }),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.success) {
        showResult('success', '✅', 'Check-In Successful!',
          '<strong>' + escapeHtml(data.attendee_name) + '</strong><br>' +
          escapeHtml(data.ticket_type)
        );
        addToScanHistory({
          status: 'success',
          name: data.attendee_name,
          type: data.ticket_type,
          time: new Date().toLocaleTimeString(),
        });
        vibrate([100, 50, 100]);
      } else if (data.already_used) {
        showResult('warning', '⚠️', 'Already Checked In',
          '<strong>' + escapeHtml(data.attendee_name || 'Unknown') + '</strong><br>' +
          escapeHtml(data.message)
        );
        addToScanHistory({
          status: 'warning',
          name: data.attendee_name || 'Unknown',
          type: data.ticket_type || '',
          time: new Date().toLocaleTimeString(),
        });
        vibrate([200, 100, 200, 100, 200]);
      } else {
        showResult('error', '❌', 'Invalid Ticket', escapeHtml(data.message || 'Ticket not valid.'));
        addToScanHistory({
          status: 'error',
          name: 'Invalid',
          type: data.message || 'Not valid',
          time: new Date().toLocaleTimeString(),
        });
        vibrate([500]);
      }
    })
    .catch(function(err) {
      showResult('error', '🔌', 'Connection Error', 'Could not connect to server. Check your internet connection.');
      console.error('Scan error:', err);
    });
  }

  // ============================================================
  // MANUAL SCAN FORM
  // ============================================================
  if (manualForm) {
    manualForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const val = manualInput && manualInput.value.trim();
      if (!val) return;
      const qrData = val.startsWith('TURNUPCITY:') ? val : 'TURNUPCITY:' + val;
      submitScan(qrData);
      if (manualInput) manualInput.value = '';
    });
  }

  // ============================================================
  // UI HELPERS
  // ============================================================
  function showResult(type, icon, title, body) {
    if (!resultContainer) return;
    const typeMap = {
      success: 'success',
      error: 'error',
      warning: 'warning',
      loading: '',
    };
    resultContainer.className = 'scan-result ' + (typeMap[type] || '');
    resultContainer.innerHTML = `
      <div class="scan-icon">${icon}</div>
      <h3>${title}</h3>
      <p>${body}</p>
    `;
    resultContainer.style.display = 'flex';
  }

  function clearResult() {
    if (resultContainer) {
      resultContainer.style.display = 'none';
      resultContainer.innerHTML = '';
    }
  }

  function addToScanHistory(entry) {
    if (!scanHistoryList) return;
    const emptyMsg = scanHistoryList.querySelector('.scan-history-empty');
    if (emptyMsg) emptyMsg.remove();

    const div = document.createElement('div');
    div.className = 'scan-entry';
    div.innerHTML = `
      <div class="scan-status-dot ${entry.status}"></div>
      <div class="scan-entry-attendee">${escapeHtml(entry.name)}</div>
      <div class="scan-entry-ticket-type text-muted" style="font-size:var(--text-xs);flex:1;">${escapeHtml(entry.type)}</div>
      <div class="scan-entry-time">${entry.time}</div>
    `;
    scanHistoryList.insertBefore(div, scanHistoryList.firstChild);

    // Keep max 20 items
    const items = scanHistoryList.querySelectorAll('.scan-entry');
    if (items.length > 20) items[items.length - 1].remove();
  }

  function vibrate(pattern) {
    if (navigator.vibrate) {
      try { navigator.vibrate(pattern); } catch(e) {}
    }
  }

  function getCsrfToken() {
    const meta = document.querySelector('[name=csrfmiddlewaretoken]');
    return meta ? meta.value : '';
  }

  function escapeHtml(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
  }

})();
