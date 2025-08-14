// Config
const WHATSAPP_NUMBER = '15551640765';

// Rotating examples
const examples = [
  "Hi Aremu, I'd like jobs for Software Developers (Remote)",
  "Hi Aremu, show Product Manager roles in Lagos (Hybrid)",
  "Hi Aremu, data analyst internships in Abuja",
  "Hi Aremu, senior backend engineer roles paying $100k+",
  "Hi Aremu, junior frontend jobs (React) — remote"
];

function buildWhatsAppLink(number, text) {
  const encoded = encodeURIComponent(text);
  return `https://wa.me/${number}?text=${encoded}`;
}

function initHeader() {
  const header = document.querySelector('.header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });
}

function initRotatingPlaceholder() {
  const input = document.getElementById('job-input');
  if (!input) return;

  let index = 0;

  function updatePlaceholder() {
    input.placeholder = examples[index];
    index = (index + 1) % examples.length;
  }

  updatePlaceholder();
  setInterval(updatePlaceholder, 3000);
}

function initCTAs() {
  const input = document.getElementById('job-input');
  const sendBtn = document.getElementById('send-btn');

  function getCurrentText() {
    return input?.value.trim() || input?.placeholder || examples[0];
  }

  function openWhatsApp() {
    const text = getCurrentText();
    const link = buildWhatsAppLink(WHATSAPP_NUMBER, text);
    window.open(link, '_blank', 'noopener,noreferrer');
  }

  // Wire up send button
  if (sendBtn) {
    sendBtn.addEventListener('click', openWhatsApp);
  }

  // Enter key support
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        openWhatsApp();
      }
    });
  }

  // Wire up all CTA buttons
  const ctaButtons = document.querySelectorAll('.nav-cta, .pricing-btn');
  ctaButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (btn.textContent.includes('Get Started') || btn.textContent.includes('Start Free Trial')) {
        e.preventDefault();
        openWhatsApp();
      }
    });
  });

  // Wire up Message Aremu link
  const messageAremuLink = document.getElementById('message-aremu');
  if (messageAremuLink) {
    messageAremuLink.addEventListener('click', (e) => {
      e.preventDefault();
      openWhatsApp();
    });
  }
}

function initMobileMenu() {
  const toggle = document.querySelector('.mobile-menu-toggle');
  const nav = document.querySelector('.nav');

  if (!toggle || !nav) return;

  toggle.addEventListener('click', () => {
    toggle.classList.toggle('active');
    nav.classList.toggle('mobile-open');
  });

  // Close menu when clicking nav links
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      toggle.classList.remove('active');
      nav.classList.remove('mobile-open');
    });
  });
}

function initSmoothScrolling() {
  const links = document.querySelectorAll('a[href^="#"]');

  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();

      const targetId = link.getAttribute('href');
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        const headerHeight = document.querySelector('.header').offsetHeight;
        const targetPosition = targetElement.offsetTop - headerHeight - 20;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initRotatingPlaceholder();
  initCTAs();
  initMobileMenu();
  initSmoothScrolling();
});
