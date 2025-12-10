// Scroll Reveal Animation
document.addEventListener('DOMContentLoaded', () => {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if(entry.isIntersecting){
        entry.target.classList.add('show');
      }
    });
  }, {threshold: 0.2});

  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
});
