const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = function(event) {
    const messages = JSON.parse(event.data);
    const messagesList = document.getElementById("messages");
    messagesList.innerHTML = "";
    messages.forEach(msg => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${msg.username}:</strong> ${msg.message ? msg.message : ''} ${msg.file ? `<a href="/download/${msg.file}">Download ${msg.file}</a>` : ''}`;
        messagesList.appendChild(li);
    });
};