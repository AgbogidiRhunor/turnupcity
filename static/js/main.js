/* ============================================================
   TURNUPCITY — MAIN JS
   ============================================================ */

(function() {
  'use strict';

  // ============================================================
  // USER MENU DROPDOWN
  // ============================================================
  const userMenu = document.querySelector('.user-menu');
  if (userMenu) {
    const btn = userMenu.querySelector('.user-avatar-btn');
    btn && btn.addEventListener('click', function(e) {
      e.stopPropagation();
      userMenu.classList.toggle('open');
    });
    document.addEventListener('click', function(e) {
      if (!userMenu.contains(e.target)) {
        userMenu.classList.remove('open');
      }
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') userMenu.classList.remove('open');
    });
  }

  // ============================================================
  // MOBILE HAMBURGER MENU
  // ============================================================
  const hamburger = document.querySelector('.hamburger');
  const mobileNav = document.querySelector('.mobile-nav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', function() {
      hamburger.classList.toggle('active');
      mobileNav.classList.toggle('open');
      document.body.style.overflow = mobileNav.classList.contains('open') ? 'hidden' : '';
    });
  }

  // ============================================================
  // FLASH MESSAGE AUTO-DISMISS
  // ============================================================
  document.querySelectorAll('.alert').forEach(function(alert) {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        alert.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(function() { alert.remove(); }, 300);
      });
    }
    // Auto-dismiss after 5s
    setTimeout(function() {
      if (alert.parentNode) {
        alert.style.animation = 'fadeOut 0.4s ease forwards';
        setTimeout(function() { if (alert.parentNode) alert.remove(); }, 400);
      }
    }, 5000);
  });

  // ============================================================
  // SIDEBAR TOGGLE (dashboard)
  // ============================================================
  const sidebarToggle = document.querySelector('.sidebar-toggle-btn');
  const sidebar = document.querySelector('.dashboard-sidebar');
  const sidebarOverlay = document.querySelector('.sidebar-overlay');

  function openSidebar() {
    sidebar && sidebar.classList.add('open');
    sidebarOverlay && sidebarOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    sidebarOverlay && sidebarOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
    });
  }
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // ============================================================
  // MODAL HELPERS
  // ============================================================
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      modal.addEventListener('click', function(e) {
        if (e.target === modal) window.closeModal(modalId);
      });
    }
  };
  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('hidden');
      document.body.style.overflow = '';
    }
  };
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(function(m) {
        m.classList.add('hidden');
        document.body.style.overflow = '';
      });
    }
  });

  // ============================================================
  // COUNTDOWN TIMER
  // ============================================================
  const countdowns = document.querySelectorAll('[data-countdown]');
  countdowns.forEach(function(el) {
    const target = new Date(el.dataset.countdown);
    function update() {
      const now = new Date();
      const diff = target - now;
      if (diff <= 0) {
        el.innerHTML = '<span class="text-muted">Event has started</span>';
        return;
      }
      const days  = Math.floor(diff / (1000*60*60*24));
      const hours = Math.floor((diff % (1000*60*60*24)) / (1000*60*60));
      const mins  = Math.floor((diff % (1000*60*60)) / (1000*60));
      const secs  = Math.floor((diff % (1000*60)) / 1000);
      const dEl = el.querySelector('.cd-days');
      const hEl = el.querySelector('.cd-hours');
      const mEl = el.querySelector('.cd-mins');
      const sEl = el.querySelector('.cd-secs');
      if (dEl) dEl.textContent = String(days).padStart(2,'0');
      if (hEl) hEl.textContent = String(hours).padStart(2,'0');
      if (mEl) mEl.textContent = String(mins).padStart(2,'0');
      if (sEl) sEl.textContent = String(secs).padStart(2,'0');
    }
    update();
    setInterval(update, 1000);
  });

  // ============================================================
  // QUANTITY SELECTORS
  // ============================================================
  document.querySelectorAll('.qty-selector').forEach(function(sel) {
    const input = sel.querySelector('.qty-input');
    const minusBtn = sel.querySelector('[data-qty="minus"]');
    const plusBtn  = sel.querySelector('[data-qty="plus"]');
    if (!input || !minusBtn || !plusBtn) return;
    const min = parseInt(input.min || 0);
    const max = parseInt(input.max || 99);

    minusBtn.addEventListener('click', function() {
      const val = parseInt(input.value) || 0;
      if (val > min) {
        input.value = val - 1;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    plusBtn.addEventListener('click', function() {
      const val = parseInt(input.value) || 0;
      if (val < max) {
        input.value = val + 1;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    input.addEventListener('input', function() {
      let val = parseInt(this.value) || 0;
      if (val < min) val = min;
      if (val > max) val = max;
      this.value = val;
      this.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });

  // ============================================================
  // CONFIRMATION DIALOGS
  // ============================================================
  document.querySelectorAll('[data-confirm]').forEach(function(el) {
    el.addEventListener('click', function(e) {
      const msg = el.dataset.confirm || 'Are you sure?';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // ============================================================
  // IMAGE PREVIEW ON UPLOAD
  // ============================================================
  document.querySelectorAll('input[type="file"][data-preview]').forEach(function(input) {
    const previewId = input.dataset.preview;
    const preview = document.getElementById(previewId);
    if (!preview) return;
    input.addEventListener('change', function() {
      const file = this.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          preview.src = e.target.result;
          preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  });

  // ============================================================
  // ACTIVE NAV LINK
  // ============================================================
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link, .sidebar-link').forEach(function(link) {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    }
  });

})();

// Fade out keyframe
const styleEl = document.createElement('style');
styleEl.textContent = `
  @keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to   { opacity: 0; transform: translateY(-8px); }
  }
`;
document.head.appendChild(styleEl);
