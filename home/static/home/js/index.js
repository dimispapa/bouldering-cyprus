document.addEventListener("DOMContentLoaded", () => {
  const textBoxes = document.querySelectorAll(".text-box"); // Text boxes
  const heroImages = document.querySelectorAll(".hero-image"); // Hero images
  const scrollDownArrow = document.getElementById("scroll-down-arrow"); // Down arrow
  const scrollToTopArrow = document.getElementById("scroll-to-top-arrow"); // Up arrow
  const navbar = document.querySelector(".navbar");
  const navbarHeight = (navbar ? navbar.offsetHeight : 0) + 100; // Navbar height
  const sideNavToggle = document.getElementById("side-nav-toggle"); // Side nav toggle button
  const sideNavigation = document.querySelector("#side-navigation"); // The list of navigation dots
  const sideNavItems = document.querySelectorAll("#side-navigation li"); // The navigation dots

  // Function to update hero image visibility
  const updateHeroImage = (index) => {
    heroImages.forEach((image, i) => {
      if (i === index) {
        image.classList.add("visible");
      } else {
        image.classList.remove("visible");
      }
    });
  };

  // Smooth scrolling function taking into account the navbar height
  const smoothScrollTo = (targetElement) => {
    // Calculate the target position
    const targetPosition =
      targetElement.getBoundingClientRect().top + window.scrollY - navbarHeight;

    // Scroll to the target position
    window.scrollTo({
      top: targetPosition,
      behavior: "smooth"
    });
  };

  // Scroll-down functionality to move to the next text box
  scrollDownArrow.addEventListener("click", (e) => {
    e.preventDefault();

    // get the current target
    let currentTargetId = scrollDownArrow.getAttribute("data-target");
    let currentTarget = document.getElementById(currentTargetId);
    let currentIndex = [...textBoxes].indexOf(currentTarget);

    // If there is a next text box, scroll to it
    if (currentIndex < textBoxes.length) {
      smoothScrollTo(currentTarget);
    }
  });

  // IntersectionObserver to track text boxes and update scroll arrow
  const textBoxObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        // Get the index of the text box
        const index = [...textBoxes].indexOf(entry.target);

        // If the text box is intersecting, add the visible class
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");

          // Update scroll-down arrow target to the next text box
          if (index < textBoxes.length - 1) {
            scrollDownArrow.setAttribute("data-target", textBoxes[index + 1].id);
            scrollDownArrow.classList.remove("hidden");
          } else {
            // Hide the scroll-down arrow on the last text box
            scrollDownArrow.classList.add("hidden");
          }

          // Update hero image based on text box index
          updateHeroImage(index);
        }
      });
    },
    { threshold: 0.5 } // Trigger when 50% of the text box is visible
  );

  // Observe each text box
  textBoxes.forEach((box) => textBoxObserver.observe(box));

  // Scroll-to-Top Arrow Logic
  scrollToTopArrow.addEventListener("click", (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // Attach click events to each side navigation item
  document.querySelectorAll("#side-navigation .nav-item").forEach((item) => {
    item.addEventListener("click", function () {
      // Retrieve the target element from the data-target attribute
      const targetSelector = this.getAttribute("data-target");
      const targetElement = document.querySelector(targetSelector);
      if (targetElement) {
        // Calculate the offset position so the text box appears slightly offscreen at the top
        const offset = 100; // Adjust this value as needed
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.scrollY - offset;
        window.scrollTo({
          top: offsetPosition,
          behavior: "smooth"
        });
      }
      // Close the offcanvas sidebar after clicking a navigation item
      const offcanvasEl = document.getElementById("offcanvasSidebar");
      const offcanvasInstance = bootstrap.Offcanvas.getInstance(offcanvasEl);
      if (offcanvasInstance) {
        offcanvasInstance.hide();
      }
    });
  });

  // Initialize visibility
  updateHeroImage(0); // Ensure the first hero image is visible
});
