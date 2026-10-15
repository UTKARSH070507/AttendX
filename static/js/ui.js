/**
 * AttendX - UI Controller & Utilities
 * Tab navigation, Modals, Toasts, and DOM Helpers
 */

const UI = (() => {
  // Safe string escaper for XSS prevention (CodeRabbit compliance)
  function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  // Toast notification system
  function showToast(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div style="flex: 1;">${escapeHTML(message)}</div>
      <button style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:16px;" aria-label="Close">&times;</button>
    `;

    const closeBtn = toast.querySelector('button');
    closeBtn.onclick = () => {
      toast.remove();
    };

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.transition = 'opacity 200ms ease, transform 200ms ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 250);
      }
    }, duration);
  }

  // Accessible Modal Controller
  let activeModal = null;

  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('active');
    activeModal = modal;
    
    // Focus first input if available
    const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea, button.btn-primary');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 50);
    }
  }

  function closeModal(modalId) {
    const modal = modalId ? document.getElementById(modalId) : activeModal;
    if (!modal) return;
    modal.classList.remove('active');
    activeModal = null;
  }

  // Initialize Global Modal and Keyboard Listeners
  function initModals() {
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          closeModal(overlay.id);
        }
      });
    });

    document.querySelectorAll('[data-close-modal]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-overlay');
        if (modal) closeModal(modal.id);
      });
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && activeModal) {
        closeModal(activeModal.id);
      }
    });
  }

  // Navigation & Tab Switching
  function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.tab-section');
    const pageTitle = document.getElementById('current-page-title');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    const toggleBtn = document.getElementById('menu-toggle-btn');

    function switchTab(tabId) {
      // Update link active states
      navLinks.forEach(link => {
        const target = link.getAttribute('data-tab');
        if (target === tabId) {
          link.classList.add('active');
          const title = link.getAttribute('data-title') || 'Dashboard';
          if (pageTitle) pageTitle.textContent = title;
        } else {
          link.classList.remove('active');
        }
      });

      // Update section visibility
      sections.forEach(sec => {
        if (sec.id === `section-${tabId}`) {
          sec.classList.add('active');
        } else {
          sec.classList.remove('active');
        }
      });

      // Close mobile drawer if open
      if (sidebar && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
      }

      window.location.hash = tabId;
      window.scrollTo({ top: 0, behavior: 'smooth' });

      // Automatically refresh statistical calculations when navigating to analysis tab
      if (tabId === 'analysis' && window.App && typeof window.App.loadStatisticalAnalysis === 'function') {
        window.App.loadStatisticalAnalysis();
      }
    }

    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = link.getAttribute('data-tab');
        if (tab) switchTab(tab);
      });
    });

    // Mobile menu toggle
    if (toggleBtn && sidebar && backdrop) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        backdrop.classList.toggle('active');
      });

      backdrop.addEventListener('click', () => {
        sidebar.classList.remove('open');
        backdrop.classList.remove('active');
      });
    }

    // Hash change routing
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      switchTab(hash);
    });

    // Initial load tab
    const initialTab = window.location.hash.replace('#', '') || 'dashboard';
    switchTab(initialTab);
  }

  return {
    escapeHTML,
    showToast,
    openModal,
    closeModal,
    initModals,
    initNavigation
  };
})();

