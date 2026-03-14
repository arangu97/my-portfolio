const roles = ["Product Engineer", "Tech Lead", "Problem Solver"];
const STORAGE_KEY = "theme-preference";

const themeToggle = document.getElementById("theme-toggle");
const savedTheme = window.localStorage.getItem(STORAGE_KEY);

if (savedTheme === "light") {
  document.body.classList.add("light-theme");
}

function updateThemeButton() {
  if (!themeToggle) return;
  const isLight = document.body.classList.contains("light-theme");
  themeToggle.setAttribute(
    "aria-label",
    isLight ? "Activar modo oscuro" : "Activar modo claro"
  );
  themeToggle.title = isLight ? "Modo oscuro" : "Modo claro";
  themeToggle.setAttribute("aria-pressed", String(isLight));
}

updateThemeButton();

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("light-theme");
    const isLight = document.body.classList.contains("light-theme");
    window.localStorage.setItem(STORAGE_KEY, isLight ? "light" : "dark");
    updateThemeButton();
  });
}

const roleElement = document.getElementById("role-rotator");
if (roleElement) {
  let currentRoleIndex = 0;
  window.setInterval(() => {
    roleElement.style.opacity = "0";
    window.setTimeout(() => {
      currentRoleIndex = (currentRoleIndex + 1) % roles.length;
      roleElement.textContent = roles[currentRoleIndex];
      roleElement.style.opacity = "1";
    }, 200);
  }, 2200);
}

const yearElement = document.getElementById("current-year");
if (yearElement) {
  yearElement.textContent = new Date().getFullYear();
}
