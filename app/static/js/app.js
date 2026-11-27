// Adds a .selected class to whichever pill's radio is checked, so the
// forest-green highlight works even in browsers without :has() support.
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".pill input[type=radio]").forEach((input) => {
    const sync = () => {
      const name = input.name;
      document.querySelectorAll(`.pill input[name="${name}"]`).forEach((i) => {
        i.closest(".pill").classList.toggle("selected", i.checked);
      });
    };
    input.addEventListener("change", sync);
    sync();
  });
});
