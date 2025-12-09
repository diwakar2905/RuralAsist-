
function escapeHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

const API_BASE_URL = window.AppConfig?.API_BASE_URL;

const chatBox = document.getElementById("chat-box");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

if (chatInput) {
  chatInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}
if (sendBtn) {
  sendBtn.addEventListener("click", sendMessage);
}

function addMessage(text, sender) {
  if (!chatBox) return;
  const msg = document.createElement("div");
  msg.className = sender === "user" ? "msg user-msg" : "msg bot-msg";
  if (sender === "user") {
    msg.innerHTML = escapeHTML(text).replace(/\n/g, "<br>");
  } else {
    const safeBotMessage = escapeHTML(text).replace(/&lt;br&gt;/g, "<br>");
    msg.innerHTML = safeBotMessage;
  }
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  if (!chatInput) return;
  const text = chatInput.value.trim();
  if (text.length === 0) return;

  addMessage(text, "user");
  chatInput.value = "";

  // Typing bubble
  const typing = document.createElement("div");
  typing.className = "msg bot-msg typing";
  typing.innerHTML = "Typing...";
  if (chatBox) {
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/chatbot/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text })
    });

    const data = await res.json();

    typing.remove();
    addMessage(data.reply, "bot");

  } catch (err) {
    typing.remove();
    addMessage("❌ Error connecting to chatbot.", "bot");
    console.error(err);
  }
}