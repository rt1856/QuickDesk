document.getElementById("ticketForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = {
    subject: document.getElementById("subject").value,
    description: document.getElementById("description").value,
    created_by: parseInt(document.getElementById("created_by").value),
  };

  const res = await fetch("http://localhost:5000/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  const result = await res.json();
  alert(result.message);
  loadTickets();
});

async function loadTickets() {
  const res = await fetch("http://localhost:5000/tickets");
  const tickets = await res.json();
  const list = document.getElementById("ticketList");
  list.innerHTML = "";
  tickets.forEach(t => {
    const li = document.createElement("li");
    li.className = "list-group-item";
    li.textContent = `#${t.id} - ${t.subject} [${t.status}]`;
    list.appendChild(li);
  });
}

loadTickets();
