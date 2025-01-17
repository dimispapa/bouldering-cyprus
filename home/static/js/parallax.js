document.addEventListener('DOMContentLoaded', () => {
    const textBoxes = document.querySelectorAll('.text-box');
  
    // Create an IntersectionObserver
    const observer = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible'); // Add 'visible' class to trigger animation
          observer.unobserve(entry.target); // Stop observing once it's visible
        }
      });
    }, {
      threshold: 0.5 // Trigger when 50% of the element is visible
    });
  
    // Observe each text box
    textBoxes.forEach(box => observer.observe(box));
  });
  