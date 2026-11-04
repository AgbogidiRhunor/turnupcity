/* ============================================================
   TURNUPCITY — CHECKOUT JS
   ============================================================ */

(function() {
  'use strict';

  const eventId = document.getElementById('event-id') && document.getElementById('event-id').value;
  const summaryContainer = document.getElementById('order-summary-lines');
  const subtotalEl = document.getElementById('order-subtotal');
  const discountRow = document.getElementById('discount-row');
  const discountEl = document.getElementById('order-discount');
  const totalEl = document.getElementById('order-total');
  const submitBtn = document.getElementById('checkout-submit-btn');
  const couponInput = document.getElementById('coupon-input');
  const couponBtn = document.getElementById('coupon-apply-btn');
  const couponMsg = document.getElementById('coupon-message');

  let appliedCoupon = null;
  let ticketSelections = {};

  // ============================================================
  // PRICE CALCULATION
  // ============================================================
  function getTicketRows() {
    return document.querySelectorAll('.ticket-type-row');
  }

  function updateSummary() {
    let subtotal = 0;
    const lines = [];

    getTicketRows().forEach(function(row) {
      const input = row.querySelector('.qty-input');
      const qty = parseInt(input && input.value) || 0;
      const price = parseFloat(row.dataset.price) || 0;
      const name = row.dataset.name || 'Ticket';

      if (qty > 0) {
        const lineTotal = qty * price;
        subtotal += lineTotal;
        lines.push({ name, qty, price, lineTotal });
      }
    });

    // Render lines
    if (summaryContainer) {
      summaryContainer.innerHTML = '';
      if (lines.length === 0) {
        summaryContainer.innerHTML = '<div class="order-line text-muted"><span>No tickets selected</span></div>';
      } else {
        lines.forEach(function(l) {
          const div = document.createElement('div');
          div.className = 'order-line';
          div.innerHTML = `
            <span>${escapeHtml(l.name)} × ${l.qty}</span>
            <span>$${l.lineTotal.toFixed(2)}</span>
          `;
          summaryContainer.appendChild(div);
        });
      }
    }

    // Calculate discount
    let discountAmount = 0;
    if (appliedCoupon) {
      if (appliedCoupon.discount_type === 'percent') {
        discountAmount = subtotal * (parseFloat(appliedCoupon.discount_value) / 100);
      } else {
        discountAmount = Math.min(parseFloat(appliedCoupon.discount_value), subtotal);
      }
    }

    const total = Math.max(0, subtotal - discountAmount);

    if (subtotalEl) subtotalEl.textContent = '$' + subtotal.toFixed(2);
    if (discountRow) discountRow.style.display = discountAmount > 0 ? '' : 'none';
    if (discountEl) discountEl.textContent = '-$' + discountAmount.toFixed(2);
    if (totalEl) totalEl.textContent = '$' + total.toFixed(2);

    // Enable/disable submit
    if (submitBtn) {
      submitBtn.disabled = lines.length === 0;
    }
  }

  // ============================================================
  // LISTEN FOR QTY CHANGES
  // ============================================================
  document.querySelectorAll('.qty-input').forEach(function(input) {
    input.addEventListener('change', updateSummary);
  });

  // ============================================================
  // COUPON VALIDATION
  // ============================================================
  if (couponBtn) {
    couponBtn.addEventListener('click', function() {
      const code = couponInput && couponInput.value.trim();
      if (!code) return;
      couponBtn.disabled = true;
      couponBtn.textContent = 'Checking...';
      couponMsg.textContent = '';
      couponMsg.className = 'form-hint';

      fetch('/orders/validate-coupon/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ code, event_id: eventId }),
      })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.valid) {
          appliedCoupon = data;
          couponMsg.textContent = '✓ Coupon applied!';
          couponMsg.className = 'form-hint text-success';
          couponInput.disabled = true;
          couponBtn.textContent = 'Applied';
          couponBtn.classList.add('btn-success');
          couponBtn.classList.remove('btn-secondary');
        } else {
          appliedCoupon = null;
          couponMsg.textContent = data.message || 'Invalid coupon.';
          couponMsg.className = 'form-hint text-danger';
          couponBtn.disabled = false;
          couponBtn.textContent = 'Apply';
        }
        updateSummary();
      })
      .catch(function() {
        couponMsg.textContent = 'Error validating coupon. Try again.';
        couponMsg.className = 'form-hint text-danger';
        couponBtn.disabled = false;
        couponBtn.textContent = 'Apply';
      });
    });

    if (couponInput) {
      couponInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); couponBtn.click(); }
      });
    }
  }

  // ============================================================
  // INIT
  // ============================================================
  updateSummary();

  // ============================================================
  // UTILS
  // ============================================================
  function getCsrfToken() {
    const meta = document.querySelector('[name=csrfmiddlewaretoken]');
    return meta ? meta.value : '';
  }

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
  }

})();
