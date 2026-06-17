(async () => {
  try {
    const res = await fetch('web_conf.json');
    const config = await res.json();

    document.title = config.company_name;
    document.getElementById('logo').textContent = config.company_name;
    document.getElementById('hero-title').textContent = config.company_name;
    document.getElementById('hero-tagline').textContent = config.tagline;
    document.getElementById('about-description').textContent = config.description;

    const servicesGrid = document.getElementById('services-grid');
    config.services.forEach(svc => {
      const card = document.createElement('div');
      card.className = 'service-card';
      card.innerHTML = `<h3>${svc.title}</h3><p>${svc.desc}</p>`;
      servicesGrid.appendChild(card);
    });

    const contactEl = document.getElementById('contact-details');
    contactEl.innerHTML = `
      <p><strong>Email:</strong> <a href="mailto:${config.contact.email}">${config.contact.email}</a></p>
      <p><strong>Phone:</strong> ${config.contact.phone}</p>
    `;

    document.getElementById('footer-text').textContent = `\u00A9 ${new Date().getFullYear()} ${config.company_name}. All rights reserved.`;

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
})();
