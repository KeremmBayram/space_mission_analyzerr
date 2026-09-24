const $ = id => document.getElementById(id);

async function getJSON(url, options={}) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function loadStats() {
  const s = await getJSON("/api/stats");
  $("total").textContent = s.total;
  $("successful").textContent = s.successful;
  $("successRate").textContent = s.success_rate + "%";
  $("totalCost").textContent = s.total_cost.toLocaleString();

  Plotly.newPlot("targetChart", [{
    x: s.by_target.map(x => x.target),
    y: s.by_target.map(x => x.success_rate),
    type: "bar",
    text: s.by_target.map(x => x.success_rate + "%"),
    textposition: "auto"
  }], {
    paper_bgcolor: "transparent", plot_bgcolor: "transparent",
    font: {color:"#dce5ff"}, yaxis:{title:"Success %", range:[0,100]}
  }, {responsive:true, displayModeBar:false});

  Plotly.newPlot("agencyChart", [{
    x: s.by_agency.map(x => x.agency),
    y: s.by_agency.map(x => x.success_rate),
    type: "bar",
    text: s.by_agency.map(x => x.success_rate + "%"),
    textposition: "auto"
  }], {
    paper_bgcolor: "transparent", plot_bgcolor: "transparent",
    font: {color:"#dce5ff"}, yaxis:{title:"Success %", range:[0,100]}
  }, {responsive:true, displayModeBar:false});
}

async function loadFilters() {
  const missions = await getJSON("/api/missions");
  const agencies = [...new Set(missions.map(m=>m.agency))].sort();
  const targets = [...new Set(missions.map(m=>m.target))].sort();
  agencies.forEach(a => $("agency").insertAdjacentHTML("beforeend", `<option>${a}</option>`));
  targets.forEach(t => $("target").insertAdjacentHTML("beforeend", `<option>${t}</option>`));
}

async function loadMissions() {
  const params = new URLSearchParams({
    search: $("search").value,
    agency: $("agency").value,
    target: $("target").value,
    status: $("status").value
  });
  const missions = await getJSON("/api/missions?" + params);
  $("missionTable").innerHTML = missions.map(m => `
    <tr>
      <td><b>${m.name}</b><br><small>${m.country}</small></td>
      <td>${m.agency}</td><td>${m.mission_type}</td><td>${m.target}</td>
      <td>${m.launch_date}</td>
      <td class="${m.status.toLowerCase()}">${m.status}</td>
      <td>${Number(m.cost_million).toLocaleString()}</td>
    </tr>`).join("");
}

async function predict() {
  const body = {
    agency:$("pAgency").value, country:$("pCountry").value,
    mission_type:$("pType").value, cost_million:$("pCost").value,
    duration_days:$("pDuration").value, crew:$("pCrew").value,
    target:$("pTarget").value
  };
  const p = await getJSON("/api/predict", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const box = $("prediction");
  box.classList.remove("hidden");
  box.innerHTML = `<b>${p.prediction}</b><br>Estimated success probability: <strong>${p.success_probability}%</strong>`;
}

async function apod() {
  try {
    const d = await getJSON("/api/nasa/apod");
    $("apodPanel").classList.remove("hidden");
    $("apodTitle").textContent = d.title || "NASA Astronomy Picture of the Day";
    $("apodText").textContent = d.explanation || "";
    if (d.media_type === "image") {
      $("apodImage").src = d.url;
      $("apodImage").style.display = "block";
    } else {
      $("apodImage").style.display = "none";
    }
    $("apodPanel").scrollIntoView({behavior:"smooth"});
  } catch(e) { alert("NASA API error: " + e.message); }
}

let timer;
$("search").addEventListener("input", () => {
  clearTimeout(timer); timer = setTimeout(loadMissions, 250);
});
["agency","target","status"].forEach(id => $(id).addEventListener("change", loadMissions));
$("resetBtn").addEventListener("click", () => {
  $("search").value = ""; $("agency").value = ""; $("target").value = ""; $("status").value = "";
  loadMissions();
});
$("predictBtn").addEventListener("click", predict);
$("apodBtn").addEventListener("click", apod);

(async function init(){
  await loadFilters();
  await loadStats();
  await loadMissions();
})();
