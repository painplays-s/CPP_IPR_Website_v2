/* ==========================
   NAV TRANSLATION FUNCTION
   Uses navTranslations from header.html
   ========================== */
function applyNavTranslations(lang) {
  if (!window.navTranslations) return;

  const dict = window.navTranslations[lang] || {};
  document.querySelectorAll('[data-i18n-nav]').forEach(el => {
    const key = el.getAttribute('data-i18n-nav');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });
}


/* ==========================
   CLASS-BASED UI BILINGUAL
   (Title / Subtitle handled in UI)
   Supports HTML content (sup, sub, strong, em, etc.)
   ========================== */
function applyClassBasedBilingual(lang) {
  document
    .querySelectorAll('.bilingual-title, .bilingual-subtitle, .bilingual-text')
    .forEach(el => {
      const html =
        lang === 'hi'
          ? el.getAttribute('data-hi')
          : el.getAttribute('data-en');

      if (html) {
        // Using innerHTML instead of textContent to preserve HTML tags
        // This allows <sup>, <sub>, <strong>, <em>, etc. to render properly
        el.innerHTML = html;
      }
    });
}


/* ==========================
   LANGUAGE TOGGLE LOGIC
   ========================== */
(function initBilingualNav() {
  const langOptions = document.querySelectorAll('.lang-option');
  if (!langOptions || !langOptions.length) return;

  // Load saved language or default to EN
  const savedLang = localStorage.getItem('preferred-language') || 'en';

  // Set button visual state
  langOptions.forEach(opt => {
    const lang = opt.getAttribute('data-lang');
    if (lang === savedLang) {
      opt.classList.add('active');
      opt.classList.remove('inactive');
    } else {
      opt.classList.remove('active');
      opt.classList.add('inactive');
    }
  });

  // Initial translation application
  applyNavTranslations(savedLang);
  applyClassBasedBilingual(savedLang);

  // Page-specific translation hooks (SAFE)
  if (typeof window.applyTranslations === 'function') {
    window.applyTranslations(savedLang);
  }
  if (typeof window.applyHomeCarouselLang === 'function') {
    window.applyHomeCarouselLang(savedLang);
  }
  if (typeof window.applyCurrentNoticeLang === 'function') {
    window.applyCurrentNoticeLang(savedLang);
  }
  if (typeof window.applyresearchHighlightLang === 'function') {
    window.applyresearchHighlightLang(savedLang);
  }
  if (typeof window.applyRecentPublicationLang === 'function') {
    window.applyRecentPublicationLang(savedLang);
  }

  // Click handlers
  langOptions.forEach(option => {
    option.addEventListener('click', () => {
      const lang = option.getAttribute('data-lang');
      if (!lang) return;

      // Update visual state
      langOptions.forEach(opt => {
        opt.classList.remove('active');
        opt.classList.add('inactive');
      });
      option.classList.add('active');
      option.classList.remove('inactive');

      // Persist language
      localStorage.setItem('preferred-language', lang);

      // Apply translations
      applyNavTranslations(lang);
      applyClassBasedBilingual(lang);

      // Page-specific hooks
      if (typeof window.applyTranslations === 'function') {
        window.applyTranslations(lang);
      }
      if (typeof window.applyHomeCarouselLang === 'function') {
        window.applyHomeCarouselLang(lang);
      }
      if (typeof window.applyCurrentNoticeLang === 'function') {
        window.applyCurrentNoticeLang(lang);
      }
      if (typeof window.applyresearchHighlightLang === 'function') {
        window.applyresearchHighlightLang(lang);
      }
      if (typeof window.applyRecentPublicationLang === 'function') {
        window.applyRecentPublicationLang(lang);
      }
    });
  });
})();