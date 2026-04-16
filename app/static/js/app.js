const state = {
  token: localStorage.getItem("messenger_token"),
  ws: null,
  currentUser: null,
  adminUsers: [],
};

const t = {
  unknownUser: "Неизвестный пользователь",
  searchStart: "Начните поиск, чтобы выбрать пользователя.",
  messageHint: "Сообщения появятся здесь после выбора чата.",
  wallHint: "Откройте стену пользователя, чтобы увидеть посты.",
};

function showStatus(message, level = "info") {
  const alert = document.getElementById("statusAlert");
  alert.className = `alert alert-${level}`;
  alert.textContent = formatApiError(message);
  alert.classList.remove("d-none");
}

function clearStatus() {
  document.getElementById("statusAlert").classList.add("d-none");
}

function setToken(token) {
  state.token = token;
  if (token) {
    localStorage.setItem("messenger_token", token);
  } else {
    localStorage.removeItem("messenger_token");
  }
}

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatApiError(payload) {
  if (payload instanceof Error) {
    return payload.message || "Произошла ошибка.";
  }
  if (typeof payload === "string") {
    return payload;
  }
  if (Array.isArray(payload)) {
    return payload.map((item) => formatApiError(item)).filter(Boolean).join("; ");
  }
  if (payload?.detail) {
    return formatApiError(payload.detail);
  }
  if (payload?.msg) {
    const location = Array.isArray(payload.loc) ? payload.loc.join(" -> ") : "";
    return location ? `${location}: ${payload.msg}` : payload.msg;
  }
  if (payload && typeof payload === "object") {
    return JSON.stringify(payload, null, 2);
  }
  return "Произошла неизвестная ошибка.";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    throw new Error(formatApiError(payload));
  }
  return payload;
}

function userLabel(user, fallbackId = null) {
  if (!user) {
    return fallbackId ? `Пользователь #${fallbackId}` : t.unknownUser;
  }
  return user.email ? `${user.username} (${user.email})` : user.username;
}

function senderLabelForMessage(message) {
  if (state.currentUser && message.sender_id === state.currentUser.id) {
    return "Вы";
  }
  return (
    message.sender?.username ||
    message.sender_username ||
    `Пользователь #${message.sender_id}`
  );
}

function statusLabel(status) {
  return (
    {
      sent: "Отправлено",
      delivered: "Доставлено",
      read: "Прочитано",
    }[status] || status
  );
}

function updateAuthUi() {
  const badge = document.getElementById("sessionBadge");
  const info = document.getElementById("currentUserInfo");
  const logoutBtn = document.getElementById("logoutBtn");
  const profileSubtitle = document.getElementById("profileSubtitle");
  const profileBadge = document.getElementById("profileBadge");
  const profileUsername = document.getElementById("profileUsernameInput");
  const profileEmail = document.getElementById("profileEmailInput");
  const profileCreatedAt = document.getElementById("profileCreatedAt");
  const openMyWallBtn = document.getElementById("openMyWallBtn");
  const saveProfileBtn = document.getElementById("saveProfileBtn");
  const adminPanel = document.getElementById("adminPanel");

  if (state.currentUser && state.token) {
    badge.className = "badge text-bg-success";
    badge.textContent = "Авторизован";
    info.textContent = `Вы вошли как ${state.currentUser.username} (${state.currentUser.email}).`;
    logoutBtn.disabled = false;
    profileSubtitle.textContent = "Ваш профиль и быстрые действия.";
    profileBadge.className = "badge text-bg-success";
    profileBadge.textContent = "Онлайн";
    profileUsername.value = state.currentUser.username;
    profileEmail.value = state.currentUser.email;
    profileCreatedAt.textContent = state.currentUser.created_at
      ? new Date(state.currentUser.created_at).toLocaleString("ru-RU")
      : "-";
    openMyWallBtn.disabled = false;
    saveProfileBtn.disabled = false;
    adminPanel.classList.toggle("d-none", !state.currentUser.is_admin);
    return;
  }

  badge.className = "badge text-bg-secondary";
  badge.textContent = "Не авторизован";
  info.textContent = "Войдите, чтобы искать людей, открывать стены и переписываться.";
  logoutBtn.disabled = true;
  profileSubtitle.textContent = "Войдите, чтобы увидеть свой профиль.";
  profileBadge.className = "badge text-bg-light";
  profileBadge.textContent = "Гость";
  profileUsername.value = "";
  profileEmail.value = "";
  profileCreatedAt.textContent = "-";
  openMyWallBtn.disabled = true;
  saveProfileBtn.disabled = true;
  adminPanel.classList.add("d-none");
}

function resetMessagesPlaceholder(text) {
  document.getElementById("messages").innerHTML = `<div class="text-muted">${text}</div>`;
}

function resetUserSearchResults(text = t.searchStart) {
  document.getElementById("userSearchResults").innerHTML = `<li class="list-group-item text-muted">${text}</li>`;
}

function renderAttachments(attachments = []) {
  if (!attachments.length) {
    return "";
  }
  return `
    <div class="message-attachments d-flex flex-column gap-1 mt-1">
      ${attachments
        .map(
          (attachment) => `
            <button
              type="button"
              class="btn btn-link p-0 d-inline-flex align-items-center gap-2 text-decoration-none attachment-link"
              data-file-id="${attachment.id}"
              data-file-name="${escapeHtml(attachment.original_name)}"
            >
              <span>[файл]</span>
              <span>${escapeHtml(attachment.original_name)}</span>
            </button>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderMessageBody(message) {
  if (!message.text && !message.attachments?.length) {
    return '<div class="text-muted"><i>Пустое сообщение</i></div>';
  }
  return `${message.text ? `<div>${escapeHtml(message.text)}</div>` : ""}${renderAttachments(message.attachments)}`;
}

async function downloadAttachment(fileId, fileName) {
  try {
    clearStatus();
    const response = await fetch(`/api/v1/files/${fileId}/download`, {
      headers: authHeaders(),
    });
    if (!response.ok) {
      const contentType = response.headers.get("content-type") ?? "";
      const payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();
      throw new Error(formatApiError(payload));
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = fileName || "attachment";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
  } catch (error) {
    showStatus(error, "danger");
  }
}

function bindAttachmentDownloads(root) {
  root.querySelectorAll(".attachment-link").forEach((button) => {
    button.onclick = () =>
      downloadAttachment(button.dataset.fileId, button.dataset.fileName);
  });
}
function renderMessage(message) {
  const box = document.getElementById("messages");
  const item = document.createElement("div");
  const createdAt = message.created_at
    ? new Date(message.created_at).toLocaleString("ru-RU")
    : "только что";
  const canEdit =
    Boolean(state.currentUser) &&
    (state.currentUser.is_admin || message.sender_id === state.currentUser.id);
  const canDelete = canEdit;

  item.className = "message-item py-2";
  item.innerHTML = `
    <div class="message-meta">${senderLabelForMessage(message)} • ${createdAt} • ${statusLabel(message.status)}</div>
    <div>${renderMessageBody(message)}</div>
    ${
      canEdit || canDelete
        ? `<div class="mt-2">
             ${canEdit ? '<button type="button" class="btn btn-sm btn-outline-secondary" data-action="edit-message">Изменить</button>' : ""}
             ${canDelete ? '<button type="button" class="btn btn-sm btn-outline-danger ms-2" data-action="delete-message">Удалить</button>' : ""}
           </div>`
        : ""
    }
  `;

  bindAttachmentDownloads(item);

  const editBtn = item.querySelector('[data-action="edit-message"]');
  if (editBtn) {
    editBtn.onclick = async () => {
      const nextText = window.prompt("Новый текст сообщения", message.text || "");
      if (nextText === null) {
        return;
      }
      await editMessage(message.id, nextText);
    };
  }

  const deleteBtn = item.querySelector('[data-action="delete-message"]');
  if (deleteBtn) {
    deleteBtn.onclick = async () => {
      if (!window.confirm("Удалить сообщение?")) {
        return;
      }
      await deleteMessage(message.id);
    };
  }

  box.appendChild(item);
}

function setWallContext(user = null) {
  const input = document.getElementById("wallUserId");
  const title = document.getElementById("postsTitle");
  if (user) {
    input.value = user.id;
    title.textContent = `Стена ${userLabel(user)}`;
    return;
  }
  input.value = "";
  title.textContent = t.wallHint;
}

async function loadCurrentUser() {
  if (!state.token) {
    state.currentUser = null;
    updateAuthUi();
    return;
  }
  try {
    state.currentUser = await requestJson("/api/v1/auth/me", {
      headers: authHeaders(),
    });
    updateAuthUi();
  } catch (_) {
    logout(false);
  }
}

async function restoreSession() {
  if (!state.token) {
    updateAuthUi();
    return;
  }
  await loadCurrentUser();
  if (state.token) {
    await Promise.all([loadChats(), loadAdminUsersIfNeeded()]);
    connectWebSocket();
  }
}

function selectUser(user) {
  document.getElementById("otherUserId").value = user.id;
  setWallContext(user);
  showStatus(
    `Выбран пользователь ${user.username}. Можно создать чат или сразу открыть его стену.`,
    "info",
  );
}

async function openUserWall(user) {
  setWallContext(user);
  if (state.currentUser?.is_admin) {
    await loadAdminUserChats(user);
  }
  await loadUserWall(user.id);
}

async function openMyWall() {
  if (!state.currentUser) {
    showStatus("Сначала войдите в аккаунт.", "warning");
    return;
  }
  await openUserWall(state.currentUser);
}

async function saveProfile() {
  if (!state.currentUser) {
    showStatus("Сначала войдите в аккаунт.", "warning");
    return;
  }
  try {
    clearStatus();
    const payload = {
      username: document.getElementById("profileUsernameInput").value.trim(),
      email: document.getElementById("profileEmailInput").value.trim(),
    };
    state.currentUser = await requestJson("/api/v1/users/me", {
      method: "PATCH",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    updateAuthUi();
    await Promise.all([loadChats(), reloadPostsView()]);
    showStatus("Профиль обновлен.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

function logout(showMessage = true) {
  if (state.ws) {
    state.ws.close();
    state.ws = null;
  }
  setToken(null);
  state.currentUser = null;
  state.adminUsers = [];
  updateAuthUi();
  document.getElementById("chatList").innerHTML = "";
  document.getElementById("posts").innerHTML = "";
  document.getElementById("activeChatId").value = "";
  document.getElementById("otherUserId").value = "";
  document.getElementById("adminUsersList").innerHTML =
    '<div class="list-group-item text-muted">Войдите как администратор, чтобы управлять пользователями.</div>';
  setWallContext(null);
  resetUserSearchResults();
  resetMessagesPlaceholder(t.messageHint);
  if (showMessage) {
    showStatus("Вы вышли из системы.", "secondary");
  }
}

async function register() {
  try {
    clearStatus();
    const payload = {
      username: document.getElementById("username").value.trim(),
      email: document.getElementById("email").value.trim(),
      password: document.getElementById("password").value,
    };
    await requestJson("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await requestJson("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: payload.email, password: payload.password }),
    });
    setToken(data.access_token);
    await loadCurrentUser();
    await Promise.all([loadChats(), loadAdminUsersIfNeeded()]);
    connectWebSocket();
    showStatus("Регистрация завершена, вы автоматически вошли в систему.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function login() {
  try {
    clearStatus();
    const payload = {
      email: document.getElementById("email").value.trim(),
      password: document.getElementById("password").value,
    };
    const data = await requestJson("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setToken(data.access_token);
    await loadCurrentUser();
    await Promise.all([loadChats(), loadAdminUsersIfNeeded()]);
    connectWebSocket();
    showStatus("Вход выполнен успешно.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

function connectWebSocket() {
  if (!state.token) {
    return;
  }
  if (state.ws) {
    state.ws.close();
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  state.ws = new WebSocket(
    `${protocol}://${window.location.host}/api/v1/ws?token=${state.token}`,
  );
  state.ws.onopen = () => showStatus("Сессия активна, realtime подключен.", "success");
  state.ws.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (
      (
        payload.type === "message:new" ||
        payload.type === "message:read" ||
        payload.type === "message:updated" ||
        payload.type === "message:deleted"
      ) &&
      payload.data.chat_id === Number(document.getElementById("activeChatId").value)
    ) {
      loadMessages();
    }
  };
  state.ws.onerror = () => showStatus("Не удалось подключить realtime-канал.", "danger");
  state.ws.onclose = () => {
    state.ws = null;
  };
}
async function searchUsers() {
  try {
    clearStatus();
    const query = document.getElementById("userSearchInput").value.trim();
    if (!query) {
      resetUserSearchResults("Введите имя пользователя или email для поиска.");
      return;
    }
    const users = await requestJson(`/api/v1/users?q=${encodeURIComponent(query)}`, {
      headers: authHeaders(),
    });
    const box = document.getElementById("userSearchResults");
    box.innerHTML = "";
    if (!users.length) {
      resetUserSearchResults("Ничего не найдено.");
      return;
    }
    users.forEach((user) => {
      const item = document.createElement("li");
      item.className = "list-group-item";
      item.innerHTML = `
        <div class="d-flex justify-content-between align-items-center gap-3">
          <div>
            <div class="fw-semibold">${escapeHtml(user.username)}</div>
            <div class="small text-muted">${escapeHtml(user.email)}</div>
          </div>
          <div class="d-flex gap-2 flex-wrap">
            <button class="btn btn-sm btn-outline-primary" data-action="chat">Чат</button>
            <button class="btn btn-sm btn-outline-secondary" data-action="wall">Стена</button>
          </div>
        </div>
      `;
      item.querySelector('[data-action="chat"]').onclick = () => selectUser(user);
      item.querySelector('[data-action="wall"]').onclick = () => openUserWall(user);
      box.appendChild(item);
    });
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function createChat() {
  try {
    clearStatus();
    const otherUserId = Number(document.getElementById("otherUserId").value);
    const data = await requestJson("/api/v1/chats/private", {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ other_user_id: otherUserId }),
    });
    document.getElementById("activeChatId").value = data.id;
    await loadChats();
    await loadMessages();
    showStatus(`Чат #${data.id} готов к работе.`, "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function loadChats() {
  try {
    const chats = await requestJson("/api/v1/chats", { headers: authHeaders() });
    const list = document.getElementById("chatList");
    list.innerHTML = "";
    if (!chats.length) {
      list.innerHTML = '<li class="list-group-item text-muted">Пока нет ни одного чата.</li>';
      return;
    }
    chats.forEach((chat) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      const title = chat.other_user
        ? `${chat.other_user.username} (${chat.other_user.email})`
        : `Чат #${chat.id}`;
      li.innerHTML = `<span>${escapeHtml(title)}</span><button class="btn btn-sm btn-outline-primary">Открыть</button>`;
      li.querySelector("button").onclick = () => {
        document.getElementById("activeChatId").value = chat.id;
        loadMessages();
      };
      list.appendChild(li);
    });
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function maybeUploadFile() {
  const input = document.getElementById("messageFile");
  if (!input.files.length) {
    return [];
  }
  const form = new FormData();
  form.append("upload", input.files[0]);
  const file = await requestJson("/api/v1/files/upload", {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  return [file.id];
}

async function markVisibleMessagesAsRead(messages) {
  if (!state.currentUser) {
    return;
  }
  const unreadIncoming = messages.filter(
    (message) => message.sender_id !== state.currentUser.id && message.status !== "read",
  );
  await Promise.all(
    unreadIncoming.map((message) =>
      requestJson(`/api/v1/messages/${message.id}/read`, {
        method: "POST",
        headers: authHeaders(),
      }).catch(() => null),
    ),
  );
}

async function sendMessage() {
  try {
    clearStatus();
    const chatId = Number(document.getElementById("activeChatId").value);
    const text = document.getElementById("messageText").value;
    const fileIds = await maybeUploadFile();
    await requestJson(`/api/v1/chats/${chatId}/messages`, {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, file_ids: fileIds }),
    });
    document.getElementById("messageText").value = "";
    document.getElementById("messageFile").value = "";
    await loadMessages();
    showStatus("Сообщение отправлено.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function editMessage(messageId, text) {
  try {
    clearStatus();
    await requestJson(`/api/v1/messages/${messageId}`, {
      method: "PATCH",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });
    await loadMessages();
    showStatus("Сообщение изменено.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function deleteMessage(messageId) {
  try {
    clearStatus();
    await requestJson(`/api/v1/messages/${messageId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    await loadMessages();
    showStatus("Сообщение удалено.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function loadMessages() {
  try {
    const chatId = Number(document.getElementById("activeChatId").value);
    if (!chatId) {
      resetMessagesPlaceholder("Выберите чат, чтобы увидеть сообщения.");
      return;
    }
    const messages = await requestJson(`/api/v1/chats/${chatId}/messages`, {
      headers: authHeaders(),
    });
    if (!messages.length) {
      resetMessagesPlaceholder("В этом чате пока нет сообщений.");
      return;
    }
    await markVisibleMessagesAsRead(messages);
    const refreshedMessages = await requestJson(`/api/v1/chats/${chatId}/messages`, {
      headers: authHeaders(),
    });
    const box = document.getElementById("messages");
    box.innerHTML = "";
    refreshedMessages.forEach((message) => renderMessage(message));
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function createPost() {
  try {
    clearStatus();
    const text = document.getElementById("postText").value.trim();
    await requestJson("/api/v1/posts", {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });
    document.getElementById("postText").value = "";
    await reloadPostsView();
    showStatus("Пост опубликован.", "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}
function renderAdminUsers(users) {
  const list = document.getElementById("adminUsersList");
  list.innerHTML = "";
  if (!users.length) {
    list.innerHTML = '<div class="list-group-item text-muted">Пользователи не найдены.</div>';
    return;
  }
  users.forEach((user) => {
    const item = document.createElement("div");
    item.className = "list-group-item admin-user-row";
    const statusLabelText = user.is_active ? "Активен" : "Заблокирован";
    const statusClass = user.is_active ? "text-bg-success" : "text-bg-secondary";
    const adminBadge = user.is_admin ? '<span class="badge text-bg-danger">admin</span>' : "";
    const isCurrentUser = state.currentUser && user.id === state.currentUser.id;
    item.innerHTML = `
      <div class="d-flex justify-content-between align-items-start gap-3">
        <div>
          <div class="fw-semibold d-flex align-items-center gap-2 flex-wrap">
            <span>${escapeHtml(user.username)}</span>
            ${adminBadge}
            <span class="badge ${statusClass}">${statusLabelText}</span>
          </div>
          <div class="admin-user-meta">${escapeHtml(user.email)}</div>
        </div>
        <div class="admin-user-actions">
          <button class="btn btn-sm btn-outline-secondary" data-action="wall">Стена</button>
          <button class="btn btn-sm btn-outline-primary" data-action="user-chats">Чаты</button>
          <button
            class="btn btn-sm btn-outline-${user.is_active ? "warning" : "success"}"
            data-action="${user.is_active ? "ban" : "unban"}"
            ${isCurrentUser ? "disabled" : ""}
          >
            ${user.is_active ? "Забанить" : "Разбанить"}
          </button>
        </div>
      </div>
    `;
    item.querySelector('[data-action="wall"]').onclick = () => openUserWall(user);
    item.querySelector('[data-action="user-chats"]').onclick = () => loadAdminUserChats(user);
    const actionBtn = item.querySelector(
      `[data-action="${user.is_active ? "ban" : "unban"}"]`,
    );
    actionBtn.onclick = () => (user.is_active ? banUser(user.id) : unbanUser(user.id));
    list.appendChild(item);
  });
}

function filterAdminData() {
  const query = document.getElementById("adminSearchInput").value.trim().toLowerCase();
  const filteredUsers = !query
    ? state.adminUsers
    : state.adminUsers.filter((user) =>
        `${user.username} ${user.email}`.toLowerCase().includes(query),
      );
  renderAdminUsers(filteredUsers);
}

async function loadAdminUsersIfNeeded() {
  if (!state.currentUser?.is_admin) {
    return;
  }
  await loadAdminUsers();
}

async function loadAdminUsers() {
  try {
    clearStatus();
    state.adminUsers = await requestJson("/api/v1/admin/users", {
      headers: authHeaders(),
    });
    filterAdminData();
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function banUser(userId) {
  try {
    clearStatus();
    await requestJson(`/api/v1/admin/users/${userId}/ban`, {
      method: "POST",
      headers: authHeaders(),
    });
    await Promise.all([loadAdminUsers(), loadChats(), reloadPostsView()]);
    showStatus(`Пользователь #${userId} заблокирован.`, "warning");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function unbanUser(userId) {
  try {
    clearStatus();
    await requestJson(`/api/v1/admin/users/${userId}/unban`, {
      method: "POST",
      headers: authHeaders(),
    });
    await Promise.all([loadAdminUsers(), loadChats(), reloadPostsView()]);
    showStatus(`Пользователь #${userId} разблокирован.`, "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function loadAdminUserChats(user) {
  try {
    clearStatus();
    const chats = await requestJson(`/api/v1/admin/users/${user.id}/chats`, {
      headers: authHeaders(),
    });
    const list = document.getElementById("chatList");
    list.innerHTML = "";
    if (!chats.length) {
      list.innerHTML = `<li class="list-group-item text-muted">У ${escapeHtml(user.username)} пока нет чатов.</li>`;
      showStatus(`У пользователя ${user.username} пока нет чатов.`, "info");
      return;
    }
    chats.forEach((chat) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      const participants = chat.participants.length
        ? chat.participants
            .map((participant) => escapeHtml(userLabel(participant, participant.id)))
            .join(", ")
        : `Чат #${chat.id}`;
      li.innerHTML = `<span>${participants}</span><button class="btn btn-sm btn-outline-primary">Открыть</button>`;
      li.querySelector("button").onclick = async () => {
        document.getElementById("activeChatId").value = chat.id;
        await loadMessages();
      };
      list.appendChild(li);
    });
    showStatus(`Показаны чаты пользователя ${user.username}.`, "info");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function deletePost(postId) {
  try {
    clearStatus();
    await requestJson(`/api/v1/posts/${postId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    await reloadPostsView();
    showStatus(`Пост #${postId} удален.`, "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function editPost(postId, currentText) {
  try {
    clearStatus();
    const nextText = window.prompt("Новый текст поста", currentText || "");
    if (nextText === null) {
      return;
    }
    await requestJson(`/api/v1/posts/${postId}`, {
      method: "PATCH",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: nextText }),
    });
    await reloadPostsView();
    showStatus(`Пост #${postId} изменен.`, "success");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function submitComment(postId) {
  try {
    clearStatus();
    const input = document.getElementById(`comment-input-${postId}`);
    const text = input.value.trim();
    if (!text) {
      showStatus("Введите текст комментария.", "warning");
      return;
    }
    await requestJson(`/api/v1/posts/${postId}/comments`, {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });
    input.value = "";
    await reloadPostsView();
  } catch (error) {
    showStatus(error, "danger");
  }
}
function renderComments(post) {
  if (!post.comments?.length) {
    return '<div class="small text-muted">Комментариев пока нет.</div>';
  }
  return `
    <div class="comment-list d-grid gap-2">
      ${post.comments
        .map(
          (comment) => `
            <div class="comment-item">
              <div class="comment-meta">${escapeHtml(userLabel(comment.author, comment.author_id))} • ${new Date(comment.created_at).toLocaleString("ru-RU")}</div>
              <div>${escapeHtml(comment.text)}</div>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPosts(posts, emptyText) {
  const box = document.getElementById("posts");
  box.innerHTML = "";
  if (!posts.length) {
    box.innerHTML = `<div class="text-muted">${emptyText}</div>`;
    return;
  }

  posts.forEach((post) => {
    const createdAt = new Date(post.created_at).toLocaleString("ru-RU");
    const canEdit =
      Boolean(state.currentUser) &&
      (state.currentUser.is_admin || post.author_id === state.currentUser.id);
    const canDelete = canEdit;

    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start gap-3">
          <div>
            <h5 class="card-title mb-1">${escapeHtml(userLabel(post.author, post.author_id))}</h5>
            <div class="small text-muted">${createdAt}</div>
          </div>
          <button class="btn btn-sm btn-outline-secondary" data-action="open-author-wall">Стена автора</button>
        </div>

        <p class="card-text mt-3">${escapeHtml(post.text)}</p>
        <p class="text-muted small mb-3">Лайки: ${post.likes_count} • Комментарии: ${post.comments_count}</p>

        <div class="d-flex gap-2 mb-3">
          <button class="btn btn-sm ${post.liked_by_me ? "btn-secondary" : "btn-primary"}" data-action="like">
            ${post.liked_by_me ? "Лайк поставлен" : "Лайк"}
          </button>
          <button class="btn btn-sm btn-outline-secondary" data-action="unlike">Убрать лайк</button>
        </div>

        <div class="post-comments mb-3">${renderComments(post)}</div>

        <div class="input-group">
          <input class="form-control" id="comment-input-${post.id}" placeholder="Написать комментарий">
          <button class="btn btn-outline-primary" data-action="comment">Комментировать</button>
        </div>

        ${
          canEdit || canDelete
            ? `<div class="post-admin-actions mt-3">
                 ${canEdit ? '<button class="btn btn-sm btn-outline-secondary" data-action="edit-post">Изменить пост</button>' : ""}
                 ${canDelete ? '<button class="btn btn-sm btn-outline-danger" data-action="delete-post">Удалить пост</button>' : ""}
               </div>`
            : ""
        }
      </div>
    `;

    div.querySelector('[data-action="like"]').onclick = () => likePost(post.id);
    div.querySelector('[data-action="unlike"]').onclick = () => unlikePost(post.id);
    div.querySelector('[data-action="comment"]').onclick = () => submitComment(post.id);
    div.querySelector('[data-action="open-author-wall"]').onclick = () =>
      openUserWall(
        post.author ?? {
          id: post.author_id,
          username: `Пользователь #${post.author_id}`,
          email: "",
        },
      );

    const editBtn = div.querySelector('[data-action="edit-post"]');
    if (editBtn) {
      editBtn.onclick = () => editPost(post.id, post.text);
    }

    const deleteBtn = div.querySelector('[data-action="delete-post"]');
    if (deleteBtn) {
      deleteBtn.onclick = async () => {
        if (!window.confirm("Удалить пост?")) {
          return;
        }
        await deletePost(post.id);
      };
    }

    box.appendChild(div);
  });
}

async function likePost(postId) {
  try {
    await requestJson(`/api/v1/posts/${postId}/like`, {
      method: "POST",
      headers: authHeaders(),
    });
    await reloadPostsView();
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function unlikePost(postId) {
  try {
    await requestJson(`/api/v1/posts/${postId}/like`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    await reloadPostsView();
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function loadUserWall(userId = null) {
  try {
    clearStatus();
    const resolvedUserId = userId ?? Number(document.getElementById("wallUserId").value);
    if (!resolvedUserId) {
      showStatus("Укажите пользователя для просмотра стены.", "warning");
      return;
    }
    const posts = await requestJson(`/api/v1/posts/user/${resolvedUserId}`, {
      headers: authHeaders(),
    });
    if (!userId) {
      document.getElementById("postsTitle").textContent = `Стена пользователя #${resolvedUserId}`;
    }
    renderPosts(posts, "У этого пользователя пока нет постов.");
  } catch (error) {
    showStatus(error, "danger");
  }
}

async function reloadPostsView() {
  const wallUserId = Number(document.getElementById("wallUserId").value);
  if (wallUserId) {
    await loadUserWall(wallUserId);
    return;
  }
  if (state.currentUser) {
    await openMyWall();
    return;
  }
  setWallContext(null);
  renderPosts([], t.wallHint);
}

document.getElementById("registerBtn").onclick = register;
document.getElementById("loginBtn").onclick = login;
document.getElementById("logoutBtn").onclick = () => logout(true);
document.getElementById("searchUsersBtn").onclick = searchUsers;
document.getElementById("createChatBtn").onclick = createChat;
document.getElementById("loadWallBtn").onclick = () => loadUserWall();
document.getElementById("openMyWallBtn").onclick = openMyWall;
document.getElementById("saveProfileBtn").onclick = saveProfile;
document.getElementById("loadAdminUsersBtn").onclick = () => loadAdminUsers();
document.getElementById("adminSearchInput").oninput = filterAdminData;
document.getElementById("sendMessageBtn").onclick = sendMessage;
document.getElementById("createPostBtn").onclick = createPost;

updateAuthUi();
resetUserSearchResults();
resetMessagesPlaceholder(t.messageHint);
restoreSession();
