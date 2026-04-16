const state = {
  token: null,
  ws: null,
  uploadedFileId: null,
};

function showStatus(message, level = "info") {
  const alert = document.getElementById("statusAlert");
  alert.className = `alert alert-${level}`;
  alert.textContent = message;
  alert.classList.remove("d-none");
}

function clearStatus() {
  document.getElementById("statusAlert").classList.add("d-none");
}

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "string" ? payload : payload.detail ?? JSON.stringify(payload);
    throw new Error(detail);
  }

  return payload;
}

function appendMessage(text) {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "border-bottom py-2";
  div.textContent = text;
  box.appendChild(div);
}

async function register() {
  try {
    clearStatus();
    const payload = {
      username: document.getElementById("username").value.trim(),
      email: document.getElementById("email").value.trim(),
      password: document.getElementById("password").value,
    };
    const user = await requestJson("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showStatus(`User #${user.id} registered successfully.`, "success");
  } catch (error) {
    showStatus(error.message, "danger");
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
    state.token = data.access_token;
    document.getElementById("token").value = state.token;
    showStatus("Authentication succeeded. Token stored in the page state.", "success");
    await Promise.all([loadChats(), loadFeed()]);
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

function connectWebSocket() {
  const token = document.getElementById("token").value;
  if (!token) {
    showStatus("Log in before connecting the WebSocket.", "warning");
    return;
  }
  clearStatus();
  if (state.ws) {
    state.ws.close();
  }
  state.token = token;
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  state.ws = new WebSocket(`${protocol}://${window.location.host}/api/v1/ws?token=${token}`);
  state.ws.onopen = () => showStatus("WebSocket connected.", "success");
  state.ws.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    appendMessage(`WS: ${JSON.stringify(payload)}`);
  };
  state.ws.onerror = () => showStatus("WebSocket connection failed.", "danger");
  state.ws.onclose = () => showStatus("WebSocket disconnected.", "secondary");
}

async function createChat() {
  try {
    clearStatus();
    const payload = { other_user_id: Number(document.getElementById("otherUserId").value) };
    const data = await requestJson("/api/v1/chats/private", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    document.getElementById("activeChatId").value = data.id;
    await loadChats();
    showStatus(`Chat #${data.id} is ready.`, "success");
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function loadChats() {
  try {
    const chats = await requestJson("/api/v1/chats", { headers: authHeaders() });
    const list = document.getElementById("chatList");
    list.innerHTML = "";
    chats.forEach((chat) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      li.innerHTML = `<span>Chat #${chat.id}</span><button class="btn btn-sm btn-outline-primary">Open</button>`;
      li.querySelector("button").onclick = () => {
        document.getElementById("activeChatId").value = chat.id;
        loadMessages();
      };
      list.appendChild(li);
    });
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function maybeUploadFile() {
  const input = document.getElementById("messageFile");
  if (!input.files.length) return [];
  const form = new FormData();
  form.append("upload", input.files[0]);
  const res = await fetch("/api/v1/files/upload", { method: "POST", headers: authHeaders(), body: form });
  const file = await res.json();
  return [file.id];
}

async function sendMessage() {
  try {
    clearStatus();
    const chatId = Number(document.getElementById("activeChatId").value);
    const text = document.getElementById("messageText").value;
    const fileIds = await maybeUploadFile();
    const payload = { text, file_ids: fileIds };
    const data = await requestJson(`/api/v1/chats/${chatId}/messages`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    appendMessage(`HTTP: ${JSON.stringify(data)}`);
    document.getElementById("messageText").value = "";
    document.getElementById("messageFile").value = "";
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function loadMessages() {
  try {
    const chatId = Number(document.getElementById("activeChatId").value);
    const messages = await requestJson(`/api/v1/chats/${chatId}/messages`, { headers: authHeaders() });
    const box = document.getElementById("messages");
    box.innerHTML = "";
    messages.forEach((message) => appendMessage(`#${message.id} ${message.text} [${message.status}]`));
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function createPost() {
  try {
    clearStatus();
    const payload = { text: document.getElementById("postText").value.trim() };
    await requestJson("/api/v1/posts", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    document.getElementById("postText").value = "";
    await loadFeed();
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function likePost(postId) {
  try {
    await requestJson(`/api/v1/posts/${postId}/like`, { method: "POST", headers: authHeaders() });
    await loadFeed();
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function unlikePost(postId) {
  try {
    await requestJson(`/api/v1/posts/${postId}/like`, { method: "DELETE", headers: authHeaders() });
    await loadFeed();
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

async function loadFeed() {
  try {
    const posts = await requestJson("/api/v1/posts/feed", { headers: authHeaders() });
    const box = document.getElementById("posts");
    box.innerHTML = "";
    posts.forEach((post) => {
      const div = document.createElement("div");
      div.className = "card";
      div.innerHTML = `
        <div class="card-body">
          <h5 class="card-title">Post #${post.id}</h5>
          <p class="card-text">${post.text}</p>
          <p class="text-muted small">Likes: ${post.likes_count}</p>
          <div class="d-flex gap-2">
            <button class="btn btn-sm ${post.liked_by_me ? "btn-secondary" : "btn-primary"}">
              ${post.liked_by_me ? "Liked" : "Like"}
            </button>
            <button class="btn btn-sm btn-outline-secondary">Unlike</button>
          </div>
        </div>
      `;
      const [likeBtn, unlikeBtn] = div.querySelectorAll("button");
      likeBtn.onclick = () => likePost(post.id);
      unlikeBtn.onclick = () => unlikePost(post.id);
      box.appendChild(div);
    });
  } catch (error) {
    showStatus(error.message, "danger");
  }
}

document.getElementById("registerBtn").onclick = register;
document.getElementById("loginBtn").onclick = login;
document.getElementById("connectBtn").onclick = connectWebSocket;
document.getElementById("createChatBtn").onclick = createChat;
document.getElementById("sendMessageBtn").onclick = sendMessage;
document.getElementById("loadMessagesBtn").onclick = loadMessages;
document.getElementById("createPostBtn").onclick = createPost;
