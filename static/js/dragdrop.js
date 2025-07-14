
document.addEventListener("DOMContentLoaded", () => {
    const list = document.getElementById("playlist-sortable");
    if (!list) return;

    new Sortable(list, {
        animation: 150,
        handle: ".handle",
        onEnd: () => {
            const items = list.querySelectorAll("[data-filename]");
            const order = Array.from(items).map(el => el.dataset.filename);
            fetch("/save_playlist_order", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ order })
            }).then(response => {
                if (!response.ok) {
                    alert("Fehler beim Speichern der Reihenfolge");
                }
            });
        }
    });
});
