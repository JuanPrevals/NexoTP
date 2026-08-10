const savedTheme = localStorage.getItem("theme") || "light";
document.documentElement.dataset.theme = savedTheme;
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

document.querySelectorAll('form[method="post"], form[method="POST"]').forEach((form) => {
  if (form.querySelector('input[name="_csrf_token"]')) return;
  const input = document.createElement("input");
  input.type = "hidden";
  input.name = "_csrf_token";
  input.value = csrfToken;
  form.append(input);
});

function normalizeRut(value) {
  return String(value || "").toUpperCase().replace(/[^0-9K]/g, "");
}

function validRut(value) {
  if (!/^[0-9K.\-\s]+$/i.test(String(value || "").trim())) return false;
  const rut = normalizeRut(value);
  if (rut.length < 8 || !/^\d+[0-9K]$/.test(rut)) return false;
  let total = 0;
  let factor = 2;
  for (let index = rut.length - 2; index >= 0; index -= 1) {
    total += Number(rut[index]) * factor;
    factor = factor === 7 ? 2 : factor + 1;
  }
  const rest = 11 - (total % 11);
  const expected = rest === 11 ? "0" : rest === 10 ? "K" : String(rest);
  return rut.at(-1) === expected;
}

function formatRut(value) {
  const rut = normalizeRut(value);
  if (rut.length < 2) return rut;
  const body = Number(rut.slice(0, -1)).toLocaleString("es-CL");
  return `${body}-${rut.at(-1)}`;
}

async function lookupCompanyRut(form) {
  const rutInput = form?.querySelector("[data-company-rut]");
  const status = form?.querySelector("[data-sii-status]");
  const rut = rutInput?.value.trim() || "";
  const normalized = normalizeRut(rut);
  if (!rutInput || !status || !validRut(rut)) return;
  if (form.dataset.siiLoading === "1" || form.dataset.siiVerifiedRut === normalized) return;
  form.dataset.siiLoading = "1";
  status.textContent = "Consultando antecedentes empresariales en el SII...";
  try {
    const response = await fetch("/api/verificar-rut-empresa", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
        "X-Requested-With": "fetch",
      },
      body: JSON.stringify({ rut }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.ok) {
      form.dataset.siiVerifiedRut = "";
      status.textContent = data.message || "No fue posible verificar el RUT.";
      return;
    }
    rutInput.value = data.rut;
    form.elements.razon_social.value = data.razon_social;
    if (form.elements.nombre && !form.elements.nombre.value.trim()) {
      form.elements.nombre.value = data.razon_social;
    }
    if (form.elements.rubro && !form.elements.rubro.value.trim() && data.actividad) {
      form.elements.rubro.value = data.actividad;
    }
    form.dataset.siiVerifiedRut = normalizeRut(data.rut);
    status.textContent = data.inicio_actividades
      ? `Empresa encontrada: ${data.razon_social}. Inicio de actividades vigente.`
      : `Empresa encontrada: ${data.razon_social}. El SII no informa inicio de actividades vigente.`;
  } catch (_error) {
    form.dataset.siiVerifiedRut = "";
    status.textContent = "No se pudo conectar con el verificador. Intenta nuevamente.";
  } finally {
    form.dataset.siiLoading = "0";
  }
}

document.addEventListener("focusout", (event) => {
  const input = event.target.closest("[data-rut-input]");
  if (!input) return;
  const isValid = validRut(input.value);
  if (isValid) input.value = formatRut(input.value);
  input.setCustomValidity(isValid ? "" : "Revisa el RUT ingresado.");
  if (!input.validationMessage) lookupCompanyRut(input.closest("[data-sii-form]"));
});

document.addEventListener("input", (event) => {
  const input = event.target.closest("[data-rut-input]");
  if (!input) return;
  input.setCustomValidity("");
  const form = input.closest("[data-sii-form]");
  if (form?.dataset.siiVerifiedRut && form.dataset.siiVerifiedRut !== normalizeRut(input.value)) {
    form.dataset.siiVerifiedRut = "";
    if (form.elements.razon_social) form.elements.razon_social.value = "";
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-sii-form]");
  if (!form) return;
  const input = form.querySelector("[data-company-rut]");
  const normalized = normalizeRut(input?.value);
  if (form.dataset.siiVerifiedRut === normalized) return;
  event.preventDefault();
  if (form.dataset.siiLoading !== "1") await lookupCompanyRut(form);
  for (let attempt = 0; form.dataset.siiLoading === "1" && attempt < 100; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (form.dataset.siiVerifiedRut === normalizeRut(input?.value)) form.requestSubmit();
});

document.addEventListener("click", async (event) => {
  const themeButton = event.target.closest("[data-theme-toggle]");
  if (themeButton) {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
    return;
  }

  const applyButton = event.target.closest("[data-apply]");
  if (!applyButton) return;

  event.preventDefault();
  applyButton.disabled = true;
  applyButton.textContent = "Enviando";

  try {
    const response = await fetch(`/postular/${applyButton.dataset.apply}`, {
      method: "POST",
      headers: { "X-Requested-With": "fetch", "X-CSRF-Token": csrfToken },
    });
    const data = await response.json();
    applyButton.textContent = data.ok ? "Postulado" : data.message || "No enviado";
    if (data.ok) {
      applyButton.classList.remove("btn-primary");
      applyButton.classList.add("btn-secondary");
    } else {
      applyButton.disabled = false;
    }
  } catch (_error) {
    applyButton.disabled = false;
    applyButton.textContent = "Reintentar";
  }
});

setTimeout(() => {
  document.querySelectorAll(".flash").forEach((el) => el.remove());
}, 4200);

const onboardingCard = document.querySelector("[data-onboarding-card]");
const onboardingOverlay = document.querySelector("[data-onboarding-overlay]");
const onboardingTitle = document.querySelector("[data-onboarding-title]");
const onboardingCopy = document.querySelector("[data-onboarding-copy]");
const onboardingProgress = document.querySelector("[data-onboarding-progress]");
const onboardingPrev = document.querySelector("[data-onboarding-prev]");
const onboardingNext = document.querySelector("[data-onboarding-next]");
const onboardingLink = document.querySelector("[data-onboarding-link]");
let onboardingIndex = 0;
let highlightedTarget = null;

const onboardingSteps = [
  {
    title: "Tu punto de partida",
    copy: "Este feed muestra oportunidades ordenadas por compatibilidad. En escritorio veras filtros a la izquierda; en telefono quedan arriba para que puedas postular sin perder espacio.",
    selector: ".feed-main",
  },
  {
    title: "Filtra sin perderte",
    copy: "Usa especialidad, modalidad, comuna o busqueda para encontrar ofertas que hagan sentido con tu perfil tecnico-profesional.",
    selector: ".feed-filters",
  },
  {
    title: "Lee primero lo importante",
    copy: "Cada tarjeta separa empresa, cargo, match, modalidad y requisitos. Abre requisitos solo cuando necesites mas detalle.",
    selector: ".feed-job-card",
  },
  {
    title: "Mide tu avance",
    copy: "El dashboard resume postulaciones enviadas, respuestas, tasa de aceptacion y recomendaciones para que no tengas que adivinar como vas.",
    selector: "a[href='/dashboard']",
    href: "/dashboard",
  },
  {
    title: "Sigue tus postulaciones",
    copy: "En Postulado veras el estado de cada proceso. Si te responden, recibiras una notificacion en la campana.",
    selector: "a[href='/postulado']",
    href: "/postulado",
  },
  {
    title: "Conversa con empresas",
    copy: "Mensajes funciona como chat en tiempo real. Si una postulacion queda rechazada, la conversacion se cierra y queda solo como historial.",
    selector: "a[href='/mensajes']",
    href: "/mensajes",
  },
  {
    title: "Practicas y mentoria",
    copy: "Cuando una oferta sea de practica o incluya mentoria, tendras seguimiento de horas, sesiones, avances y evaluaciones.",
    selector: "a[href='/practicas']",
    href: "/practicas",
  },
  {
    title: "Busca cerca de tu comuna",
    copy: "El mapa te ayuda a revisar oportunidades por zona y radio de busqueda, algo clave cuando el transporte importa.",
    selector: "a[href='/mapa']",
    href: "/mapa",
  },
  {
    title: "Completa tu perfil y CV",
    copy: "Mientras mas completo este tu perfil, mejor funcionara el match. Desde Perfil puedes generar tu CV PDF y compartir tu perfil publico.",
    selector: "a[href='/perfil']",
    href: "/perfil",
  },
];

function clearOnboardingHighlight() {
  if (highlightedTarget) {
    highlightedTarget.classList.remove("onboarding-highlight");
    highlightedTarget = null;
  }
}

function renderOnboardingStep() {
  if (!onboardingCard) return;
  const step = onboardingSteps[onboardingIndex];
  clearOnboardingHighlight();
  onboardingTitle.textContent = step.title;
  onboardingCopy.textContent = step.copy;
  onboardingProgress.textContent = `${onboardingIndex + 1} de ${onboardingSteps.length}`;
  onboardingPrev.disabled = onboardingIndex === 0;
  onboardingNext.textContent = onboardingIndex === onboardingSteps.length - 1 ? "Terminar" : "Siguiente";

  if (step.href && window.location.pathname !== step.href) {
    onboardingLink.hidden = false;
    onboardingLink.href = step.href;
  } else {
    onboardingLink.hidden = true;
  }

  const target = step.selector ? document.querySelector(step.selector) : null;
  if (target) {
    highlightedTarget = target;
    highlightedTarget.classList.add("onboarding-highlight");
    target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  }
}

function closeOnboarding() {
  clearOnboardingHighlight();
  if (onboardingCard) onboardingCard.hidden = true;
  if (onboardingOverlay) onboardingOverlay.hidden = true;
}

function startOnboarding() {
  if (!onboardingCard || document.body.dataset.onboardingNewUser !== "1") return;
  onboardingCard.hidden = false;
  if (onboardingOverlay) onboardingOverlay.hidden = false;
  renderOnboardingStep();
}

document.addEventListener("click", (event) => {
  if (event.target.closest("[data-onboarding-skip]")) {
    closeOnboarding();
    return;
  }
  if (event.target.closest("[data-onboarding-prev]")) {
    onboardingIndex = Math.max(0, onboardingIndex - 1);
    renderOnboardingStep();
    return;
  }
  if (event.target.closest("[data-onboarding-next]")) {
    if (onboardingIndex >= onboardingSteps.length - 1) {
      closeOnboarding();
      return;
    }
    onboardingIndex += 1;
    renderOnboardingStep();
  }
});

const notificationBadge = document.querySelector("[data-notification-badge]");
const notificationList = document.querySelector("[data-notification-list]");
const messagesPanel = document.querySelector("[data-conversation-id]");
const messageThread = document.querySelector("[data-message-thread]");
const typingIndicator = document.querySelector("[data-typing-indicator]");
const typingText = document.querySelector("[data-typing-text]");
let lastMessageSignature = "";
let lastTypingSentAt = 0;
let realtimeConnected = false;

function escapeHTML(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function updateNotificationBadge(unread) {
  if (!notificationBadge) return;
  const total = Number(unread || 0);
  notificationBadge.textContent = total;
  notificationBadge.hidden = total === 0;
}

async function refreshNotificationsFallback() {
  if (!notificationBadge) return;
  try {
    const response = await fetch("/api/notificaciones/unread", { headers: { "X-Requested-With": "fetch" } });
    if (!response.ok) return;
    const data = await response.json();
    updateNotificationBadge(data.unread);
  } catch (_error) {
    // Best-effort fallback when EventSource is not available.
  }
}

function renderNotificationList(items) {
  if (!notificationList || !Array.isArray(items)) return;
  if (!items.length) {
    notificationList.innerHTML = `
      <div class="empty-state">
        <h2>No tienes notificaciones pendientes.</h2>
        <p class="muted">Cuando marques una notificacion como leida, desaparecera de esta lista.</p>
      </div>`;
    return;
  }
  notificationList.innerHTML = items.map((item) => `
    <article class="feed-card ${item.leida ? "" : "unread"}">
      <div class="row between">
        <div>
          <strong>${escapeHTML(item.titulo)}</strong>
          <p class="muted">${escapeHTML(item.contenido)}</p>
          <p class="muted mini">${escapeHTML(item.fecha)}</p>
        </div>
        ${item.url ? `<a class="btn btn-secondary" href="${escapeHTML(item.url)}">Abrir</a>` : ""}
      </div>
    </article>
  `).join("");
}

function renderMessages(conversation, forceStickToBottom = false) {
  if (!messageThread || !conversation || !Array.isArray(conversation.mensajes)) return;
  const signature = conversation.mensajes.map((message) => `${message.id}:${message.contenido}`).join("|");
  if (signature === lastMessageSignature) return;
  const shouldStickToBottom = forceStickToBottom || messageThread.scrollTop + messageThread.clientHeight >= messageThread.scrollHeight - 80;
  lastMessageSignature = signature;
  if (!conversation.mensajes.length) {
    messageThread.innerHTML = '<p class="muted">Esta conversacion todavia no tiene mensajes.</p>';
    return;
  }
  messageThread.innerHTML = conversation.mensajes.map((message) => `
    <div class="message-bubble ${message.own ? "own" : ""}">
      <strong>${escapeHTML(message.autor)}</strong>
      <p>${escapeHTML(message.contenido)}</p>
      <span>${escapeHTML(message.fecha)}</span>
      ${message.own ? "" : `<details class="report-box"><summary>Reportar mensaje</summary><form class="form-card flat" method="post" action="/reportar/mensaje/${Number(message.id)}"><input type="hidden" name="_csrf_token" value="${escapeHTML(csrfToken)}"><input type="hidden" name="motivo" value="Acoso"><div class="field"><label>Explica el problema</label><textarea name="detalle" minlength="20" maxlength="1000" required></textarea></div><button class="btn btn-secondary">Enviar reporte</button></form></details>`}
    </div>
  `).join("");
  if (shouldStickToBottom) {
    messageThread.scrollTop = messageThread.scrollHeight;
  }
}

async function refreshConversation(forceStickToBottom = false) {
  if (!messagesPanel?.dataset.conversationId) return;
  try {
    const response = await fetch(`/api/mensajes/${messagesPanel.dataset.conversationId}`, {
      headers: { "X-Requested-With": "fetch" },
    });
    if (!response.ok) return;
    const data = await response.json();
    if (data.ok && data.conversation) {
      renderMessages(data.conversation, forceStickToBottom);
      renderTyping(data.conversation.typing);
    }
  } catch (_error) {
    // The SSE stream remains the primary channel; this keeps the active chat fresh if it drops.
  }
}

function renderTyping(typing) {
  if (!typingIndicator || !typingText) return;
  if (!Array.isArray(typing) || !typing.length) {
    typingIndicator.hidden = true;
    typingText.textContent = "";
    return;
  }
  const names = typing.map((item) => item.nombre).filter(Boolean).join(", ");
  typingText.textContent = `${names || "La otra persona"} esta escribiendo`;
  typingIndicator.hidden = false;
}

function startRealtimeStream() {
  const shouldConnect = notificationBadge || notificationList || messagesPanel;
  if (!shouldConnect) return;
  if (!window.EventSource) {
    refreshNotificationsFallback();
    setInterval(refreshNotificationsFallback, 5000);
    return;
  }
  const params = new URLSearchParams();
  if (messagesPanel?.dataset.conversationId) {
    params.set("postulacion_id", messagesPanel.dataset.conversationId);
  }
  const source = new EventSource(`/api/realtime/stream${params.toString() ? `?${params}` : ""}`);
  source.onopen = () => {
    realtimeConnected = true;
  };
  source.onerror = () => {
    realtimeConnected = false;
  };
  source.addEventListener("realtime", (event) => {
    const data = JSON.parse(event.data);
    if (data.notifications) {
      updateNotificationBadge(data.notifications.unread);
      renderNotificationList(data.notifications.items);
    }
    if (data.conversation) {
      renderMessages(data.conversation);
      renderTyping(data.conversation.typing);
    }
  });
}

document.addEventListener("input", (event) => {
  const input = event.target.closest("[data-typing-input]");
  if (!input || !messagesPanel?.dataset.conversationId || !input.value.trim()) return;
  const now = Date.now();
  if (now - lastTypingSentAt < 900) return;
  lastTypingSentAt = now;
  fetch(`/api/typing/${messagesPanel.dataset.conversationId}`, {
    method: "POST",
    headers: { "X-Requested-With": "fetch", "X-CSRF-Token": csrfToken },
  }).catch(() => {});
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("[data-message-form]");
  if (!form) return;
  event.preventDefault();
  const button = form.querySelector("button");
  const textarea = form.querySelector("textarea[name='contenido']");
  if (!textarea || !textarea.value.trim()) return;
  if (button) button.disabled = true;
  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "fetch", "X-CSRF-Token": csrfToken },
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data.ok !== false) {
      textarea.value = "";
      textarea.focus();
      await refreshConversation(true);
    } else if (data.message) {
      textarea.setCustomValidity(data.message);
      textarea.reportValidity();
      setTimeout(() => textarea.setCustomValidity(""), 2500);
    }
  } finally {
    if (button) button.disabled = false;
  }
});

startRealtimeStream();
startOnboarding();
refreshConversation(true);
if (messagesPanel) {
  setInterval(() => {
    if (!realtimeConnected) refreshConversation(true);
  }, 5000);
}

if (window.NexoMapData && window.L) {
  const mapElement = document.getElementById("opportunity-map");
  const densityList = document.getElementById("density-list");
  if (mapElement) {
    const map = L.map(mapElement).setView(window.NexoMapData.centro, 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    L.circle(window.NexoMapData.centro, {
      radius: Number(window.NexoMapData.radio || 10) * 1000,
      color: "#0f766e",
      fillColor: "#0f766e",
      fillOpacity: 0.08,
      weight: 1,
    }).addTo(map).bindPopup("Tu comuna de referencia");

    window.NexoMapData.puntos.forEach((punto) => {
      L.marker([punto.lat, punto.lng]).addTo(map).bindPopup(
        `<strong>${punto.titulo}</strong><br>${punto.empresa}<br>${punto.comuna}<br>${punto.match}% compatible`
      );
    });

    window.NexoMapData.densidad.forEach((zona) => {
      L.circle([zona.lat, zona.lng], {
        radius: 350 + zona.total * 140,
        color: "#111827",
        fillColor: "#2563eb",
        fillOpacity: 0.16,
        weight: 1,
      }).addTo(map).bindPopup(`${zona.comuna}: ${zona.total} oportunidades`);
      if (densityList) {
        const item = document.createElement("div");
        item.className = "feed-card flat row between";
        item.innerHTML = `<strong>${zona.comuna}</strong><span class="chip">${zona.total}</span>`;
        densityList.appendChild(item);
      }
    });
  }
}
