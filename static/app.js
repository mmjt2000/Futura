/* ============================================================
   FUTURA — utilitaires partagés par toutes les pages.
   Aucune dépendance externe : le site doit fonctionner hors-ligne
   après le premier chargement (service worker).
   ============================================================ */
const Futura = (() => {
  const API = ""; // même origine : fonctionne en local comme sur Render

  async function api(path, options = {}) {
    const response = await fetch(API + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`${response.status} ${detail}`.trim());
    }
    return response.status === 204 ? null : response.json();
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  /* ---------- thème ---------- */
  function initTheme() {
    const saved = localStorage.getItem("futura_theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
    updateThemeMeta(saved);
    const knob = document.getElementById("themeKnob");
    if (knob) knob.textContent = saved === "dark" ? "🌙" : "☀️";
  }

  function toggleTheme() {
    const html = document.documentElement;
    const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    localStorage.setItem("futura_theme", next);
    updateThemeMeta(next);
    const knob = document.getElementById("themeKnob");
    if (knob) knob.textContent = next === "dark" ? "🌙" : "☀️";
  }

  function updateThemeMeta(theme) {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "dark" ? "#0a0e27" : "#f8fafc");
  }

  function mountThemeSwitch() {
    const el = document.getElementById("themeSwitch");
    if (el) el.addEventListener("click", toggleTheme);
  }

  /* ---------- profil ---------- */
  function storedName() {
    return localStorage.getItem("futura_user") || "Maryse";
  }

  async function allUsers() {
    return api("/api/users/");
  }

  async function currentUser() {
    const users = await allUsers();
    return users.find((u) => u.name === storedName()) || users[0];
  }

  async function switchUser() {
    const users = await allUsers();
    if (users.length < 2) return users[0];
    const index = users.findIndex((u) => u.name === storedName());
    const next = users[(index + 1) % users.length];
    localStorage.setItem("futura_user", next.name);
    return next;
  }

  /* ---------- navigation ---------- */
  const TABS = [
    { id: "inicio", icon: "🏠", label: "Inicio", href: "/" },
    { id: "progreso", icon: "📊", label: "Progreso", href: "/static/progreso.html" },
    { id: "hermanas", icon: "👭", label: "Hermanas", href: "/static/hermanas.html" },
    { id: "laboratorio", icon: "🎓", label: "Laboratorio", href: "/static/laboratorio.html" },
  ];

  function mountNav(active) {
    const target = document.getElementById("nav");
    if (!target) return;
    target.className = "bottom-nav";
    target.innerHTML = TABS.map((tab) => `
      <a class="nav-item ${tab.id === active ? "active" : ""}" href="${tab.href}">
        <span class="icon">${tab.icon}</span>${tab.label}
      </a>
    `).join("");
  }

  /* ---------- divers ---------- */
  function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString("es", { day: "numeric", month: "short" });
  }

  function xpLabel(xp) {
    return `${xp} XP`;
  }

  return {
    api, escapeHtml, initTheme, toggleTheme, mountThemeSwitch,
    storedName, allUsers, currentUser, switchUser,
    mountNav, formatDate, xpLabel,
  };
})();
