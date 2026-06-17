(async () => {
  // Analytics
  if (!window.location.pathname.includes('/analytics') && !window.location.pathname.includes('/api/')) {
    const payload = {
      url: window.location.href,
      ref: document.referrer || '',
      w: window.innerWidth,
      h: window.innerHeight,
      lang: navigator.language || '',
    };
    if (navigator.sendBeacon) {
      navigator.sendBeacon('api/analytics', JSON.stringify(payload));
    } else {
      fetch('api/analytics', { method: 'POST', body: JSON.stringify(payload), keepalive: true });
    }
  }

  const ICONS = {
    strategy: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/><line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/><line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/></svg>',
    code: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    shield: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  };

  try {
    const res = await fetch('web_conf.json');
    const config = await res.json();

    document.title = config.company_name;
    document.getElementById('logo').textContent = config.company_name;
    document.getElementById('hero-title').textContent = config.company_name;
    document.getElementById('hero-tagline').textContent = config.tagline;

    if (config.hero_image) {
      const img = new Image();
      img.onload = () => {
        document.getElementById('hero-bg').style.backgroundImage = `url(${config.hero_image})`;
      };
      img.src = config.hero_image;
    }

    const aboutDesc = document.getElementById('about-description');
    aboutDesc.innerHTML = config.description;

    if (config.about_image) {
      document.getElementById('about-image').style.backgroundImage = `url(${config.about_image})`;
    }

    const servicesGrid = document.getElementById('services-grid');
    config.services.forEach(svc => {
      const card = document.createElement('div');
      card.className = 'service-card';
      const iconSvg = ICONS[svc.icon] || '';
      card.innerHTML = `
        <div class="service-icon">${iconSvg}</div>
        <h3>${svc.title}</h3>
        <p>${svc.desc}</p>
      `;
      servicesGrid.appendChild(card);
    });

    const contactEl = document.getElementById('contact-details');
    contactEl.innerHTML = `
      <p><strong>Email:</strong> <a href="mailto:${config.contact.email}">${config.contact.email}</a></p>
      <p><strong>Phone:</strong> ${config.contact.phone}</p>
    `;

    const year = new Date().getFullYear();
    document.getElementById('footer-text').textContent = `\u00A9 ${year} ${config.company_name}. All rights reserved.`;

    const socialLinks = document.getElementById('social-links');
    Object.entries(config.social_links).forEach(([platform, url]) => {
      const a = document.createElement('a');
      a.href = url;
      a.textContent = platform.charAt(0).toUpperCase() + platform.slice(1);
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      socialLinks.appendChild(a);
    });
  } catch (err) {
    console.error('Failed to load configuration:', err);
    document.body.innerHTML = '<p style="text-align:center;padding:2rem;color:red;">Failed to load site configuration.</p>';
  }

  const toggle = document.getElementById('theme-toggle');
  const html = document.documentElement;

  const saved = localStorage.getItem('theme');
  if (saved) {
    html.setAttribute('data-theme', saved);
  }

  toggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
})();
