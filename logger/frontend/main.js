const container = document.getElementById("log-container");

document.addEventListener("DOMContentLoaded", () => {
  const logViewer = () => {
    const wrapper = document.createElement("div");
    wrapper.style.fontFamily = "monospace";
    wrapper.style.color = "#eee";

    // Loading animation element
    const loading = document.createElement("div");
    loading.textContent = "⏳ Connection au serveur";
    loading.style.fontSize = "18px";
    loading.style.marginBottom = "10px";
    wrapper.appendChild(loading);

    // Animate the dots
    let dots = 0;
    const loadingInterval = setInterval(() => {
      dots = (dots + 1) % 4;
      loading.textContent = "⏳ Connection au serveur" + ".".repeat(dots);
    }, 500);

    // Log display element
    const pre = document.createElement("pre");
    pre.style.whiteSpace = "pre-wrap";
    wrapper.appendChild(pre);

    let ws;
    try {
      ws = new WebSocket("ws://localhost:8080");
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      loading.textContent = "❌ ConnectionError: Impossible de se connecter au serveur WebSocket.";
      clearInterval(loadingInterval);
      return wrapper;
    }

    let connectionTimeout = setTimeout(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        console.error("❌ ConnectionError: No response from WebSocket server.");
        loading.textContent = "❌ ConnectionError: Aucun serveur WebSocket n'a répondu.";
        clearInterval(loadingInterval);
        ws.close();
      }
    }, 3000);

    ws.onopen = () => {
      console.log("✅ WebSocket connection established");
      clearTimeout(connectionTimeout);

      // Ping every 5s
      setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("get_logs");
          console.log("Sent message, awaiting response...");
        }
      }, 1000);
    };

    ws.onmessage = (event) => {
      if (event.data === "NO_CONTENT") return;
      console.log("Received : ", event.data);

      // On retire le loader à la première réponse utile
      if (loading) {
        clearInterval(loadingInterval);
        loading.remove();
      }
      // Si le texte affiché est trop long, on supprime la première ligne
      if (pre.textContent.split('\n').length > 20) {
        console.log("Suppression de la premiere ligne");
        var lines = pre.textContent.split('\n');
        lines.splice(0, 1);
        pre.textContent = lines.join('\n');
      }

      // On ajoute la nouvelle ligne
      pre.textContent += "\n" + event.data;
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed.");
      clearInterval(loadingInterval);
    };

    ws.onerror = (err) => {
      console.error("WebSocket encountered an error:", err);
      pre.textContent += "\n❌ ConnectionError: Erreur de connexion WebSocket.";
      clearInterval(loadingInterval);
    };

    return wrapper;
  };

  container.appendChild(logViewer());
});

container.addEventListener("wheel", function (e){
  this.scroll(this.scrollX, this.scrollY + e.deltaY);
})