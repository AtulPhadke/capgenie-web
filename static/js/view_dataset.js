// Global variables
let currentOption = "percentage";
let lastParsedData = null;
let bioChart = null;
let bubbleChart = null;
let motif_list = [];

// Helper: round numbers for display
function roundStringNumber(str, method, digits) {
  const num = parseFloat(str);
  if (isNaN(num)) return "";
  if (method === "toFixed") return num.toFixed(digits);
  return num;
}

// Helper: update nav bar active state
function setActiveNav(option) {
  document.querySelectorAll('.label-with-icon').forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById(option + '_values_btn');
  if (btn) btn.classList.add('active');
}

// Helper: show/hide cards
function showCards(option) {
  ["spreadCard", "logoCard", "bubbleCard", "motifListCard", "chartCard", "overallChartCard"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });
  if (option === "motif") {
    if (document.getElementById("motifListCard")) document.getElementById("motifListCard").style.display = "block";
    if (document.getElementById("logoCard")) document.getElementById("logoCard").style.display = "block";
  } else if (option === "quality") {
    if (document.getElementById("chartCard")) document.getElementById("chartCard").style.display = "block";
    if (document.getElementById("overallChartCard")) document.getElementById("overallChartCard").style.display = "block";
  } else {
    if (document.getElementById("spreadCard")) document.getElementById("spreadCard").style.display = "block";
    if (document.getElementById("bubbleCard")) document.getElementById("bubbleCard").style.display = "block";
  }
}

// Helper: update stat cards
function updateStats(data, option) {
  const maxTitle = document.getElementById("MaxTitle");
  const maxPeptide = document.getElementById("MaxPeptide");
  if (!data || !data[option] || data[option].length < 2) return;
  let maxVal = -Infinity;
  let topPeptide = "";
  for (let i = 1; i < data[option].length; i++) {
    const val = parseFloat(data[option][i][data[option][i].length - 1]);
    if (!isNaN(val) && val > maxVal) {
      maxVal = val;
      topPeptide = data[option][i][0];
    }
  }
  document.getElementById("max").textContent = roundStringNumber(maxVal, "toFixed", 3);
  document.getElementById("top_peptide").textContent = topPeptide;
  // Update stat card titles based on tab
  if (option === "enrichment") {
    maxTitle.textContent = "Highest Enrichment";
    maxPeptide.textContent = "Most enriched peptide:";
  } else if (option === "percentage") {
    maxTitle.textContent = "Highest value";
    maxPeptide.textContent = "Most common peptide:";
  } else if (option === "quality") {
    maxTitle.textContent = "Average quality score";
    maxPeptide.textContent = "Total number of reads analyzed:";
  } else if (option === "motif") {
    maxTitle.textContent = "Most common motif:";
    maxPeptide.textContent = "Total number of motifs analyzed:";
  }
}

// Helper: render spreadsheet table
function renderTable(data, option) {
  const table = document.getElementById("data");
  const headerRow = document.getElementById("headerRow");
  const body = document.getElementById("spreadData");
  const filePicker = document.getElementById("file-picker");
  headerRow.innerHTML = "";
  body.innerHTML = "";

  // Always show file-picker, even for single-table datasets
  let subfolders = null;
  let selectedSubfolder = null;
  console.log(data);
  if (data && data.spreadsheets) {
    subfolders = Object.keys(data.spreadsheets);
    console.log('Subfolders in dataset:', subfolders);
    selectedSubfolder = filePicker.value || subfolders[0];
    filePicker.innerHTML = "";
    subfolders.forEach(sub => {
      const opt = document.createElement("option");
      opt.value = sub;
      opt.textContent = sub;
      if (sub === selectedSubfolder) opt.selected = true;
      filePicker.appendChild(opt);
    });
    filePicker.style.display = '';
    if (data.spreadsheets[selectedSubfolder] && data.spreadsheets[selectedSubfolder][option]) {
      renderTableRows(data.spreadsheets[selectedSubfolder][option]);
    }
    filePicker.onchange = () => {
      renderTable(data, option);
    };
    return;
  } else if (data && data[option]) {
    // For single-table datasets, show a single option
    filePicker.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = option;
    opt.textContent = option;
    opt.selected = true;
    filePicker.appendChild(opt);
    filePicker.style.display = '';
    renderTableRows(data[option]);
    filePicker.onchange = null;
  }

  function renderTableRows(arr) {
    for (let j = 0; j < arr.length; j++) {
      const rowArr = arr[j];
      if (j === 0) {
        for (let i = 0; i < rowArr.length; i++) {
          const th = document.createElement("th");
          th.textContent = rowArr[i];
          if (i === 0) {
            th.style.position = "sticky";
            th.style.left = "0";
            th.style.zIndex = "3";
            th.style.background = "#eaeaea";
            th.style.color = "#222";
          } else {
            th.style.background = "#eaeaea";
          }
          headerRow.appendChild(th);
        }
      } else {
        const tr = document.createElement("tr");
        for (let i = 0; i < rowArr.length; i++) {
          const td = document.createElement("td");
          td.textContent = i > 0 ? roundStringNumber(rowArr[i], "toFixed", 3) : rowArr[i];
          if (i === 0) {
            td.style.position = "sticky";
            td.style.left = "0";
            td.style.zIndex = "2";
            td.style.background = "#eaeaea";
            td.style.color = "#222";
          }
          tr.appendChild(td);
        }
        body.appendChild(tr);
      }
    }
  }
}

// Helper: render motif list
function renderMotifList(motifData) {
  const motif_list = motifData.motifs || [];
  const motifBody = document.getElementById("motifBody");
  const motifSearch = document.getElementById("motif_search");
  function renderRows(list) {
    motifBody.innerHTML = "";
    list.slice(0, 40).forEach(row => {
      const tr = document.createElement("tr");
      row.forEach(cell => {
        const td = document.createElement("td");
        td.textContent = cell;
        td.style.padding = "10px";
        td.style.textAlign = "center";
        td.style.whiteSpace = "nowrap";
        td.style.boxSizing = "border-box";
        td.style.border = "1px solid #ddd";
        tr.appendChild(td);
      });
      motifBody.appendChild(tr);
    });
  }
  renderRows(motif_list);
  motifSearch.oninput = () => {
    const term = motifSearch.value.toLowerCase();
    const filtered = motif_list.filter(row => row[0].toLowerCase().includes(term));
    renderRows(filtered);
  };
  // Motif logo
  const motifLogo = document.getElementById("motifLogo");
  if (motifLogo && motifData.img) motifLogo.src = motifData.img;
  // Make motif list horizontally scrollable if too wide
  const motifListCard = document.getElementById("motifListCard");
  if (motifListCard) motifListCard.style.overflowX = "auto";
  // Style header like spreadsheet
  const motifHeader = document.getElementById("motifHeader");
  if (motifHeader) {
    Array.from(motifHeader.children[0].children).forEach(th => {
      th.style.textAlign = "center";
      th.style.padding = "10px";
      th.style.whiteSpace = "nowrap";
      th.style.boxSizing = "border-box";
      th.style.border = "1px solid #ddd";
      th.style.background = "#f5f5f5";
      th.style.position = "sticky";
      th.style.top = "0";
      th.style.zIndex = "2";
    });
  }
}

// Helper: render main chart
function renderMainChart(data, option) {
  if (bioChart) bioChart.destroy();
  if (option === "motif" && data.motif && data.motif.motifs && data.motif.motifs.length > 0) {
    // Motif count distribution, sorted greatest to least, limit to top 100
    const sortedMotifs = [...data.motif.motifs].sort((a, b) => (parseInt(b[1]) || 0) - (parseInt(a[1]) || 0));
    const top100Motifs = sortedMotifs.slice(0, 100);
    const motifLabels = top100Motifs.map(row => row[0]);
    const motifCounts = top100Motifs.map(row => parseInt(row[1]) || 0);
    bioChart = new Chart("bio-chart", {
      type: "bar",
      data: {
        labels: motifLabels,
        datasets: [{
          label: "Motif Count",
          backgroundColor: "#4e79a7",
          borderColor: "#333",
          borderWidth: 1,
          data: motifCounts
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
          title: {
            display: false // No header for motif distribution small chart
          }
        },
        scales: {
          x: {
            title: { display: false },
            ticks: {
              display: false,
              autoSkip: true, maxRotation: 90, minRotation: 60
            }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Motif Count" }
          }
        }
      }
    });
  } else if (option === "quality" && data.quality && Array.isArray(data.quality) && data.quality.length > 0) {
    // Show average quality value per file in frequency distribution
    const qualityData = data.quality;
    const labels = [];
    const avgQualities = [];
    for (let i = 0; i < qualityData.length; i++) {
      const fileData = qualityData[i];
      const fileName = Object.keys(fileData)[0];
      const avgQuality = fileData[fileName]["avg_quality"];
      labels.push(fileName);
      avgQualities.push(avgQuality);
    }
    bioChart = new Chart("bio-chart", {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Average Quality",
          backgroundColor: "#4e79a7",
          borderColor: "#333",
          borderWidth: 1,
          data: avgQualities
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
          title: {
            display: false // No header for quality distribution small chart
          }
        },
        scales: {
          x: {
            title: { display: false },
            ticks: {
              display: false,
              autoSkip: true, maxRotation: 90, minRotation: 60
            }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Average Quality" }
          }
        }
      }
    });
  } else {
    // Default: enrichment or percentage
    const arr = data[option];
    if (!arr || arr.length < 2) return;
    const labels = arr.slice(1).map(row => row[0]);
    const values = arr.slice(1).map(row => parseFloat(row[row.length - 1]));
    let chartLabel = option === "enrichment" ? "Enrichment Value" : "% Percentage";
    let chartTitle = option === "enrichment" ? "Enrichment Distribution" : "Percentage Distribution";
    bioChart = new Chart("bio-chart", {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: chartLabel,
          backgroundColor: "#4e79a7",
          borderColor: "#333",
          borderWidth: 1,
          data: values
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
          title: {
            display: false // No header for frequency distribution small chart
          }
        },
        scales: {
          x: { title: { display: false }, ticks: { display: false } },
          y: { beginAtZero: true, title: { display: true, text: chartLabel } }
        }
      }
    });
  }
}

// Helper: render bubble chart (simple version)
function renderBubbleChart() {
  // ... (implement as needed, similar to GUI)
}

// Helper: render quality charts
function renderQualityCharts(qualityData) {
  // File-level chart
  const fileChartCanvas = document.getElementById('fileChart');
  if (!fileChartCanvas) return;
  // Make fileChart horizontally scrollable if too wide
  const chartContent = document.getElementById('chartContent');
  if (chartContent) chartContent.style.overflowX = 'auto';
  const labels = [];
  const normalReads = [];
  const lowQualityReads = [];
  const totals = [];
  const qualityScores = [];
  qualityData.forEach(file_data => {
    const dataset = Object.values(file_data)[0];
    labels.push(Object.keys(file_data)[0]);
    normalReads.push(dataset["num_reads"] - dataset["low_quality_reads"]);
    lowQualityReads.push(dataset["low_quality_reads"]);
    totals.push(dataset["num_reads"]);
    qualityScores.push(dataset["avg_quality"]);
  });
  // Set canvas width to at least 100px per column, but not less than parent width
  const minWidth = Math.max(labels.length * 100, fileChartCanvas.parentElement.offsetWidth);
  fileChartCanvas.width = minWidth;
  fileChartCanvas.height = fileChartCanvas.parentElement.offsetHeight;
  if (window.fileChartInstance) { window.fileChartInstance.destroy(); }
  window.fileChartInstance = new Chart(fileChartCanvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Normal reads',
          data: normalReads,
          backgroundColor: '#d9d9d9',
          borderColor: "#888",
          borderWidth: 2,
          barThickness: 75,
          stack: 'stack1',
        },
        {
          label: 'Low quality reads',
          data: lowQualityReads,
          backgroundColor: '#f28e8e',
          borderColor: "#888",
          borderWidth: 2,
          barThickness: 75, // thinner columns
          stack: 'stack1',
        }
      ]
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          stacked: true,
          ticks: { display: false },
          categoryPercentage: 0.6, // more space between bars
          barPercentage: 0.5 // thinner bars
        },
        y: { display: true, stacked: true, max: Math.max(...totals)}
      },
    }
  });
  // Overall chart
  const overallChartCanvas = document.getElementById('overallChart');
  if (!overallChartCanvas) return;
  overallChartCanvas.width = overallChartCanvas.parentElement.offsetWidth;
  overallChartCanvas.height = overallChartCanvas.parentElement.offsetHeight;
  if (window.overallChartInstance) { window.overallChartInstance.destroy(); }
  const sumLowQuality = lowQualityReads.reduce((acc, curr) => acc + curr, 0);
  const sumNormal = normalReads.reduce((acc, curr) => acc + curr, 0);
  const sumTotal = totals.reduce((acc, curr) => acc + curr, 0);
  window.overallChartInstance = new Chart(overallChartCanvas, {
    type: 'bar',
    data: {
      labels: ["Overall"],
      datasets: [
        {
          label: 'Normal reads',
          data: [sumNormal],
          backgroundColor: '#d9d9d9',
          borderColor: "#888",
          borderWidth: 2,
          barThickness: 60,
        },
        {
          label: 'Low quality reads',
          data: [sumLowQuality],
          backgroundColor: '#f28e8e',
          borderColor: "#888",
          borderWidth: 2,
          barThickness: 60,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }, // remove tooltips
      },
      scales: {
        x: {
          display: false, // remove x-axis
          stacked: true,
          ticks: { display: false }, // remove x-axis ticks
        },
        y: {
          display: false, // remove y-axis
          stacked: true,
          max: sumTotal,
          ticks: { display: false }, // remove y-axis ticks
        }
      },
    }
  });
  // Add left/right labels for overall chart (GUI style)
  document.getElementById('overallLeftLabel').textContent = `${sumNormal.toLocaleString()} Normal reads (${((sumNormal/sumTotal)*100).toFixed(1)}%)`;
  document.getElementById('overallRightLabel').textContent = `${sumLowQuality.toLocaleString()} Low quality reads (${((sumLowQuality/sumTotal)*100).toFixed(1)}%)`;
}

// Update all UI for current state
function updateAll(data) {
  setActiveNav(currentOption);
  showCards(currentOption);
  let selectedSubfolder = null;
  let subData = data;
  if (data.spreadsheets) {
    const filePicker = document.getElementById("file-picker");
    const subfolders = Object.keys(data.spreadsheets);
    selectedSubfolder = (filePicker && filePicker.value) || subfolders[0];
    subData = data.spreadsheets[selectedSubfolder];
  }
  renderMainChart(data, currentOption); // Always update the small chart
  if (currentOption === "quality" && data.quality && Array.isArray(data.quality) && data.quality.length > 0) {
    renderQualityCharts(data.quality);
    // Update stat cards for quality
    document.getElementById("MaxTitle").textContent = "Average quality score";
    document.getElementById("MaxPeptide").textContent = "Total number of reads analyzed:";
    // Set stat values
    const qualityScores = data.quality.map(q => Object.values(q)[0]["avg_quality"]);
    const totals = data.quality.map(q => Object.values(q)[0]["num_reads"]);
    document.getElementById("max").textContent = (qualityScores.reduce((a,b)=>a+b,0)/qualityScores.length).toFixed(3);
    document.getElementById("top_peptide").textContent = totals.reduce((a,b)=>a+b,0).toLocaleString();
  } else if (currentOption === "motif" && data.motif) {
    renderMotifList(data.motif);
    // Update stat cards for motif
    document.getElementById("MaxTitle").textContent = "Most common motif:";
    document.getElementById("MaxPeptide").textContent = "Total number of motifs analyzed:";
    // Set stat values
    const motifs = data.motif.motifs || [];
    if (motifs.length > 0) {
      let mostCommonMotif = motifs[0][0];
      let highestCount = parseInt(motifs[0][1]) || 0;
      for (let i = 1; i < motifs.length; i++) {
        const count = parseInt(motifs[i][1]) || 0;
        if (count > highestCount) {
          highestCount = count;
          mostCommonMotif = motifs[i][0];
        }
      }
      document.getElementById("max").textContent = mostCommonMotif;
      document.getElementById("top_peptide").textContent = motifs.length.toLocaleString();
    } else {
      document.getElementById("max").textContent = "No motifs found";
      document.getElementById("top_peptide").textContent = "0";
    }
  } else {
    updateStats(subData, currentOption);
    renderTable(data, currentOption);
    renderMainChart(subData, currentOption);
    if (currentOption === "motif" && data.motif) renderMotifList(data.motif);
    updateBubbleChart(subData);
  }
}

// Event listeners for nav
function setupNavEvents() {
  ["quality", "enrichment", "percentage", "motif"].forEach(option => {
    const btn = document.getElementById(option + "_values_btn");
    if (btn) {
      btn.onclick = () => {
        // Don't allow clicking on disabled/struck-through options
        if (btn.hasAttribute('disabled') || btn.classList.contains('strike')) {
          return;
        }
        currentOption = option;
        updateAll(lastParsedData);
      };
    }
  });
}

function createCharts(data) {
    console.log("createCharts called with currentOption:", currentOption);
    console.log("createCharts data:", data);
    
    if (currentOption === "motif" && data.motif && data.motif.length > 0) {
        // Motif count distribution, sorted greatest to least, limit to top 100
        const sortedMotifs = [...data.motif].sort((a, b) => (parseInt(b[1]) || 0) - (parseInt(a[1]) || 0));
        const top100Motifs = sortedMotifs.slice(0, 100); // Limit to top 100
        const motifLabels = top100Motifs.map(row => row[0]);
        const motifCounts = top100Motifs.map(row => parseInt(row[1]) || 0);

        if (bioChart) {
            bioChart.destroy(); 
        }
        
        bioChart = new Chart("bio-chart", {
            type: "bar",
            data: {
                labels: motifLabels,
                datasets: [{
                    label: "Motif Count",
                    backgroundColor: "#4e79a7",
                    borderColor: "#333",
                    borderWidth: 1,
                    data: motifCounts
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true },
                    title: {
                        display: true,
                        text: "Motif Distribution",
                        font: { size: 16, weight: 'bold' },
                        padding: { top: 10, bottom: 10 }
                    }
                },
                scales: {
                    x: {
                        title: { display: false },
                        ticks: {
                            display: false,
                            autoSkip: true, maxRotation: 90, minRotation: 60
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: "Motif Count" }
                    }
                }
            }
        });
    } else if (currentOption === "quality" && data.quality && Array.isArray(data.quality) && data.quality.length > 0) {
        // Show average quality value per file in frequency distribution
        console.log("Quality condition met - creating quality chart");
        const qualityData = data.quality;
        const labels = [];
        const avgQualities = [];
        for (let i = 0; i < qualityData.length; i++) {
            const fileData = qualityData[i];
            const fileName = Object.keys(fileData)[0];
            const avgQuality = fileData[fileName]["avg_quality"];
            labels.push(fileName);
            avgQualities.push(avgQuality);
        }
        
        console.log("Quality chart labels:", labels);
        console.log("Quality chart values:", avgQualities);
        
        // Force destroy any existing bioChart
        if (bioChart) {
            bioChart.destroy();
            bioChart = null;
        }
        
        console.log("Creating new bioChart for quality data");
        bioChart = new Chart("bio-chart", {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Average Quality",
                    backgroundColor: "#4e79a7",
                    borderColor: "#333",
                    borderWidth: 1,
                    data: avgQualities
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true },
                    title: {
                        display: true,
                        text: "Quality Distribution",
                        font: { size: 16, weight: 'bold' },
                        padding: { top: 10, bottom: 10 }
                    }
                },
                scales: {
                    x: {
                        title: { display: false },
                        ticks: {
                            display: false,
                            autoSkip: true, maxRotation: 90, minRotation: 60
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: "Average Quality" }
                    }
                }
            }
        });
    } else {
        // Show spreadsheet card and hide logo card for non-motif options
        console.log("Falling through to else condition - not quality or motif");
        console.log("Current option:", currentOption);
        console.log("Data keys:", data ? Object.keys(data) : "No data");
        document.getElementById("spreadCard").style.visibility = "visible";
        document.getElementById("logoCard").style.visibility = "hidden";
        
        var freq_data = data[currentOption];
        var values = {};
        for (var i = 0; i < freq_data.length; i++) {
            if (i > 0) {
                values[freq_data[i][0]] = freq_data[i][freq_data[i].length - 1];
            }
        }
        // Sort by value descending for frequency distribution
        const sortedEntries = Object.entries(values).sort((a, b) => b[1] - a[1]);
        const sortedLabels = sortedEntries.map(entry => entry[0]);
        const sortedValues = sortedEntries.map(entry => entry[1]);

        if (bioChart) {
            bioChart.destroy(); 
        }
        // Set chart labels based on context
        let chartLabel = "Frequency";
        let xLabel = ""; // Remove x-axis label
        let chartTitle = "Frequency Distribution";
        if (currentOption === "enrichment") {
            chartLabel = "Enrichment Value";
            chartTitle = "Enrichment Distribution";
        } else if (currentOption === "percentage") {
            chartLabel = "% Percentage";
            chartTitle = "Percentage Distribution";
        }
        // For non-motif cards, hide x-axis tick labels
        let showXLabels = currentOption === "motif";
        bioChart = new Chart("bio-chart", {
            type: "bar",
            data: {
                labels: sortedLabels,
                datasets: [{
                    label: chartLabel,
                    backgroundColor: "#4e79a7",
                    borderColor: "#333",
                    borderWidth: 1,
                    data: sortedValues
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true },
                    title: {
                        display: true,
                        text: chartTitle,
                        font: { size: 16, weight: 'bold' },
                        padding: { top: 10, bottom: 10 }
                    }
                },
                scales: {
                    x: {
                        title: { display: false, text: xLabel },
                        ticks: {
                            display: showXLabels,
                            autoSkip: true, maxRotation: 90, minRotation: 60
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: chartLabel }
                    }
                }
            }
        });
    }
}

function updateBubbleChart(data) {
    // Only run for percentage or enrichment tab
    if (!data || !data.percentage || !data.enrichment) return;
    const percentage = data.percentage;
    const enrichment = data.enrichment;

    // Build lookup for enrichment values by peptide
    const enrichmentMap = {};
    for (let i = 1; i < enrichment.length; i++) {
        const peptide = enrichment[i][0];
        const value = parseFloat(enrichment[i][enrichment[i].length - 1]);
        if (peptide && !isNaN(value)) {
            enrichmentMap[peptide] = value;
        }
    }

    // Build bubble data: X = percentage, Y = enrichment, r = percentage (scaled)
    const bubbleDataArr = [];
    for (let i = 1; i < percentage.length; i++) {
        const peptide = percentage[i][0];
        const percValue = parseFloat(percentage[i][percentage[i].length - 1]);
        const enrichValue = enrichmentMap[peptide];
        if (peptide && !isNaN(percValue) && typeof enrichValue === 'number' && !isNaN(enrichValue)) {
            bubbleDataArr.push({
                x: percValue,
                y: enrichValue,
                r: Math.max(5, percValue * 2), // scale for visibility
                peptide: peptide,
                percentage: percValue,
                enrichment: enrichValue
            });
        }
    }

    if (bubbleChart) {
        bubbleChart.destroy();
    }

    bubbleChart = new Chart("bubble-chart", {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Peptides',
                data: bubbleDataArr,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const d = context.raw;
                            return [
                                `Peptide: ${d.peptide}`,
                                `Percentage: ${d.percentage.toFixed(3)}`,
                                `Enrichment: ${d.enrichment.toFixed(3)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: { display: true, text: '% Percentage' }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Enrichment Value' }
                }
            }
        }
    });
}

function loadMaxes(data) {
    // Update statistics
    if (data.percentage && data.percentage.length > 1) {
        const values = data.percentage.slice(1).map(row => parseFloat(row[row.length - 1]) || 0);
        const maxValue = Math.max(...values);
        const maxIndex = values.indexOf(maxValue);
        const maxPeptide = data.percentage[maxIndex + 1][0];
        
        document.getElementById('max').textContent = maxValue.toFixed(2);
        document.getElementById('top_peptide').textContent = maxPeptide;
    }
}

function filterMotifs(searchTerm) {
    if (!lastParsedData || !lastParsedData.motif) return;
    
    const filteredMotifs = lastParsedData.motif.filter(motif => 
        motif[0].toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    // Update motif list display
    const motifBody = document.getElementById('motifBody');
    if (motifBody) {
        motifBody.innerHTML = '';
        filteredMotifs.slice(0, 50).forEach(motif => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${motif[0]}</td>
                <td>${motif[1]}</td>
            `;
            motifBody.appendChild(row);
        });
    }
    
    // Update frequency distribution chart
    createCharts({ ...lastParsedData, motif: filteredMotifs });
}

// Modal chart instances
let freqChartModalInstance = null;
let bubbleChartModalInstance = null;

function renderFreqModalChart(data, option) {
  const ctx = document.getElementById('freq-chart-modal');
  if (!ctx) return;
  if (freqChartModalInstance) freqChartModalInstance.destroy();
  // Motif
  if (option === "motif" && data.motif && data.motif.motifs && data.motif.motifs.length > 0) {
    const sortedMotifs = [...data.motif.motifs].sort((a, b) => (parseInt(b[1]) || 0) - (parseInt(a[1]) || 0));
    const top100Motifs = sortedMotifs.slice(0, 100);
    const motifLabels = top100Motifs.map(row => row[0]);
    const motifCounts = top100Motifs.map(row => parseInt(row[1]) || 0);
    freqChartModalInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: motifLabels,
        datasets: [{
          label: "Motif Count",
          backgroundColor: "#4e79a7",
          borderColor: "#333",
          borderWidth: 1,
          data: motifCounts
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
          title: {
            display: false // No header for motif distribution modal
          }
        },
        scales: {
          x: {
            title: { display: false },
            ticks: {
              display: false,
              autoSkip: true, maxRotation: 90, minRotation: 60
            }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Motif Count" }
          }
        }
      }
    });
    return;
  }
  // Quality
  if (option === "quality" && data.quality && Array.isArray(data.quality) && data.quality.length > 0) {
    const qualityData = data.quality;
    const labels = [];
    const avgQualities = [];
    for (let i = 0; i < qualityData.length; i++) {
      const fileData = qualityData[i];
      const fileName = Object.keys(fileData)[0];
      const avgQuality = fileData[fileName]["avg_quality"];
      labels.push(fileName);
      avgQualities.push(avgQuality);
    }
    freqChartModalInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Average Quality",
          backgroundColor: "#4e79a7",
          borderColor: "#333",
          borderWidth: 1,
          data: avgQualities
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
          title: {
            display: false // No header for quality distribution modal
          }
        },
        scales: {
          x: {
            title: { display: false },
            ticks: {
              display: false,
              autoSkip: true, maxRotation: 90, minRotation: 60
            }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: "Average Quality" }
          }
        }
      }
    });
    return;
  }
  // Enrichment/Percentage
  const arr = data[option];
  if (!arr || arr.length < 2) return;
  const labels = arr.slice(1).map(row => row[0]);
  const values = arr.slice(1).map(row => parseFloat(row[row.length - 1]));
  let chartLabel = option === "enrichment" ? "Enrichment Value" : "% Percentage";
  freqChartModalInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: chartLabel,
        backgroundColor: "#4e79a7",
        borderColor: "#333",
        borderWidth: 1,
        data: values
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true },
        title: {
          display: false // No header for frequency distribution modal
        }
      },
      scales: {
        x: { title: { display: false }, ticks: { display: false } },
        y: { beginAtZero: true, title: { display: true, text: chartLabel } }
      }
    }
  });
}

function renderBubbleModalChart(data) {
  const ctx = document.getElementById('bubble-chart-modal');
  if (!ctx) return;
  if (bubbleChartModalInstance) bubbleChartModalInstance.destroy();
  if (!data || !data.percentage || !data.enrichment) return;
  const percentage = data.percentage;
  const enrichment = data.enrichment;
  const enrichmentMap = {};
  for (let i = 1; i < enrichment.length; i++) {
    const peptide = enrichment[i][0];
    const value = parseFloat(enrichment[i][enrichment[i].length - 1]);
    if (peptide && !isNaN(value)) {
      enrichmentMap[peptide] = value;
    }
  }
  const bubbleDataArr = [];
  for (let i = 1; i < percentage.length; i++) {
    const peptide = percentage[i][0];
    const percValue = parseFloat(percentage[i][percentage[i].length - 1]);
    const enrichValue = enrichmentMap[peptide];
    if (peptide && !isNaN(percValue) && typeof enrichValue === 'number' && !isNaN(enrichValue)) {
      bubbleDataArr.push({
        x: percValue,
        y: enrichValue,
        r: Math.max(5, percValue * 2),
        peptide: peptide,
        percentage: percValue,
        enrichment: enrichValue
      });
    }
  }
  bubbleChartModalInstance = new Chart(ctx, {
    type: 'bubble',
    data: {
      datasets: [{
        label: 'Peptides',
        data: bubbleDataArr,
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const d = context.raw;
              return [
                `Peptide: ${d.peptide}`,
                `Percentage: ${d.percentage.toFixed(3)}`,
                `Enrichment: ${d.enrichment.toFixed(3)}`
              ];
            }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          title: { display: true, text: '% Percentage' }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Enrichment Value' }
        }
      }
    }
  });
}

// Modal functions
function openFreqModal() {
  const modal = document.getElementById('freqModal');
  modal.style.display = 'block';
  modal.classList.add('show');
  // Update modal header
  const modalHeader = modal.querySelector('h2');
  let headerText = "Frequency Distribution";
  if (currentOption === "quality") {
    headerText = "Quality Distribution";
  } else if (currentOption === "enrichment") {
    headerText = "Enrichment Distribution";
  } else if (currentOption === "percentage") {
    headerText = "Percentage Distribution";
  } else if (currentOption === "motif") {
    headerText = "Motif Distribution";
  }
  if (modalHeader) {
    modalHeader.textContent = headerText;
  }
  setTimeout(() => {
    let dataForModal = lastParsedData;
    if (lastParsedData && lastParsedData.spreadsheets && (currentOption === 'enrichment' || currentOption === 'percentage')) {
      const filePicker = document.getElementById('file-picker');
      const subfolders = Object.keys(lastParsedData.spreadsheets);
      const selectedSubfolder = (filePicker && filePicker.value) || subfolders[0];
      dataForModal = lastParsedData.spreadsheets[selectedSubfolder];
    }
    renderFreqModalChart(dataForModal, currentOption);
  }, 100);
}

function openBubbleModal() {
  const modal = document.getElementById('bubbleModal');
  modal.style.display = 'block';
  modal.classList.add('show');
  setTimeout(() => {
    let dataForModal = lastParsedData;
    if (lastParsedData && lastParsedData.spreadsheets) {
      const filePicker = document.getElementById('file-picker');
      const subfolders = Object.keys(lastParsedData.spreadsheets);
      const selectedSubfolder = (filePicker && filePicker.value) || subfolders[0];
      dataForModal = lastParsedData.spreadsheets[selectedSubfolder];
    }
    renderBubbleModalChart(dataForModal);
  }, 100);
}

function openSpreadModal() {
  const modal = document.getElementById('spreadModal');
  modal.style.display = 'block';
  modal.classList.add('show');
  // Populate modal with spreadsheet data
  const modalContent = document.getElementById('spread-content-modal');
  if (!modalContent || !lastParsedData) return;

  // Helper to truncate text
  function truncateText(text, maxLength) {
    if (typeof text !== 'string') text = String(text);
    return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
  }

  // Determine if subfolders exist
  let subfolders = null;
  let selectedSubfolder = null;
  if (lastParsedData.spreadsheets) {
    subfolders = Object.keys(lastParsedData.spreadsheets);
    const filePicker = document.createElement('select');
    filePicker.id = 'modal-file-picker';
    filePicker.style.marginLeft = '12px';
    filePicker.style.padding = '5px 10px';
    filePicker.style.fontSize = '1em';
    subfolders.forEach(sub => {
      const opt = document.createElement('option');
      opt.value = sub;
      opt.textContent = sub;
      if (sub === (document.getElementById('file-picker')?.value || subfolders[0])) opt.selected = true;
      filePicker.appendChild(opt);
    });
    selectedSubfolder = filePicker.value || subfolders[0];
    // Header row with label and select inline
    let headerDiv = document.createElement('div');
    headerDiv.style.display = 'flex';
    headerDiv.style.alignItems = 'center';
    headerDiv.style.gap = '12px';
    headerDiv.style.marginBottom = '10px';
    let label = document.createElement('span');
    label.textContent = 'Peptide List';
    label.style.fontSize = '1.2em';
    label.style.fontWeight = 'bold';
    headerDiv.appendChild(label);
    headerDiv.appendChild(filePicker);
    modalContent.innerHTML = '';
    modalContent.appendChild(headerDiv);
    // Table container
    let tableContainer = document.createElement('div');
    tableContainer.id = 'modal-table-container';
    tableContainer.style.maxHeight = '400px';
    tableContainer.style.overflowY = 'auto';
    tableContainer.style.border = '1px solid #ddd';
    tableContainer.style.minHeight = 'fit-content';
    modalContent.appendChild(tableContainer);
    // Render table
    function renderTableFor(folder, option) {
      tableContainer.innerHTML = '';
      const data = lastParsedData.spreadsheets[folder][option];
      if (!data) {
        tableContainer.innerHTML = '<div style="padding:20px;text-align:center;color:#888;">No spreadsheet data available.</div>';
        return;
      }
      let tableHTML = '<table style="width:100%; border-collapse:collapse;"><thead><tr>';
      data[0].forEach(header => {
        tableHTML += `<th style="text-align:center; padding:10px; border:1px solid #ddd; background:#f5f5f5; white-space:nowrap;">${header}</th>`;
      });
      tableHTML += '</tr></thead><tbody>';
      for (let i = 1; i < Math.min(data.length, 100); i++) {
        tableHTML += '<tr>';
        data[i].forEach((cell, cellIndex) => {
          // Round numbers to 3 decimal places, but keep the first column (peptide names) as text
          const displayValue = cellIndex > 0 ? roundStringNumber(cell, "toFixed", 3) : cell;
          tableHTML += `<td style="text-align:center; padding:10px; border:1px solid #ddd; white-space:nowrap;">${truncateText(displayValue, 20)}</td>`;
        });
        tableHTML += '</tr>';
      }
      tableHTML += '</tbody></table>';
      tableContainer.innerHTML = tableHTML;
    }
    renderTableFor(selectedSubfolder, currentOption);
    filePicker.onchange = function() {
      renderTableFor(filePicker.value, currentOption);
    };
  } else if (lastParsedData[currentOption]) {
    // No subfolders, just show the table
    const data = lastParsedData[currentOption];
    let tableHTML = '<table style="width:100%; border-collapse:collapse;"><thead><tr>';
    data[0].forEach(header => {
      tableHTML += `<th style="text-align:center; padding:10px; border:1px solid #ddd; background:#f5f5f5; white-space:nowrap;">${header}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';
    for (let i = 1; i < Math.min(data.length, 100); i++) {
      tableHTML += '<tr>';
      data[i].forEach((cell, cellIndex) => {
        // Round numbers to 3 decimal places, but keep the first column (peptide names) as text
        const displayValue = cellIndex > 0 ? roundStringNumber(cell, "toFixed", 3) : cell;
        tableHTML += `<td style="text-align:center; padding:10px; border:1px solid #ddd; white-space:nowrap;">${truncateText(displayValue, 20)}</td>`;
      });
      tableHTML += '</tr>';
    }
    tableHTML += '</tbody></table>';
    modalContent.innerHTML = tableHTML;
  }
}

function openMotifListModal() {
  const modal = document.getElementById('motifListModal');
  modal.style.display = 'block';
  modal.classList.add('show');
  const modalContent = document.getElementById('motif-content-modal');
  if (!modalContent || !lastParsedData || !lastParsedData.motif || !lastParsedData.motif.motifs) return;
  const motifs = lastParsedData.motif.motifs;
  // Header row with label and search inline
  let headerDiv = document.createElement('div');
  headerDiv.style.display = 'flex';
  headerDiv.style.alignItems = 'center';
  headerDiv.style.gap = '12px';
  headerDiv.style.marginBottom = '10px';
  let label = document.createElement('span');
  label.textContent = 'Motif List';
  label.style.fontSize = '1.2em';
  label.style.fontWeight = 'bold';
  let searchInput = document.createElement('input');
  searchInput.type = 'text';
  searchInput.placeholder = 'Search motifs...';
  searchInput.style.padding = '5px 10px';
  searchInput.style.fontSize = '1em';
  headerDiv.appendChild(label);
  headerDiv.appendChild(searchInput);
  modalContent.innerHTML = '';
  modalContent.appendChild(headerDiv);
  // Table container
  let tableContainer = document.createElement('div');
  tableContainer.id = 'modal-motif-table-container';
  tableContainer.style.maxHeight = '400px';
  tableContainer.style.overflowY = 'auto';
  tableContainer.style.border = '1px solid #ddd';
  tableContainer.style.minHeight = 'fit-content';
  modalContent.appendChild(tableContainer);
  // Lazy load rendering
  const rowHeight = 36;
  const buffer = 10;
  let filteredMotifs = motifs;
  function renderRows(start, end) {
    let tableHTML = '<table style="width:100%; border-collapse:collapse;"><thead><tr>';
    tableHTML += '<th style="text-align:center; padding:10px; border:1px solid #ddd; background:#f5f5f5; white-space:nowrap;">Motif</th>';
    tableHTML += '<th style="text-align:center; padding:10px; border:1px solid #ddd; background:#f5f5f5; white-space:nowrap;">Count</th>';
    tableHTML += '</tr></thead><tbody>';
    for (let i = start; i < end && i < filteredMotifs.length; i++) {
      tableHTML += '<tr>';
      tableHTML += `<td style="text-align:center; padding:10px; border:1px solid #ddd; white-space:nowrap;">${filteredMotifs[i][0]}</td>`;
      tableHTML += `<td style="text-align:center; padding:10px; border:1px solid #ddd; white-space:nowrap;">${filteredMotifs[i][1]}</td>`;
      tableHTML += '</tr>';
    }
    tableHTML += '</tbody></table>';
    tableContainer.innerHTML = tableHTML;
  }
  function updateVisibleRows() {
    const scrollTop = tableContainer.scrollTop;
    const visibleRows = Math.ceil(tableContainer.clientHeight / rowHeight);
    const start = Math.max(0, Math.floor(scrollTop / rowHeight) - buffer);
    const end = start + visibleRows + buffer * 2;
    renderRows(start, end);
  }
  // Initial render
  updateVisibleRows();
  // Scroll handler
  tableContainer.onscroll = updateVisibleRows;
  // Search handler
  searchInput.oninput = function() {
    const term = searchInput.value.toLowerCase();
    filteredMotifs = motifs.filter(row => row[0].toLowerCase().includes(term));
    tableContainer.scrollTop = 0;
    updateVisibleRows();
  };
}

function openMotifLogoModal() {
  const modal = document.getElementById('motifLogoModal');
  modal.style.display = 'block';
  modal.classList.add('show');
  const modalImg = document.getElementById('motif-logo-modal');
  const motifLogo = document.getElementById('motifLogo');
  if (modalImg && motifLogo && motifLogo.src) {
    modalImg.src = motifLogo.src;
  }
}

function setupModalCloseHandlers() {
  const modals = document.querySelectorAll('.modal');
  const closeButtons = document.querySelectorAll('.close');
  closeButtons.forEach(button => {
    button.addEventListener('click', () => {
      const modal = button.closest('.modal');
      modal.style.display = 'none';
      modal.classList.remove('show');
      // Clean up modal chart instances
      if (modal.id === 'freqModal' && freqChartModalInstance) {
        freqChartModalInstance.destroy();
        freqChartModalInstance = null;
      }
      if (modal.id === 'bubbleModal' && bubbleChartModalInstance) {
        bubbleChartModalInstance.destroy();
        bubbleChartModalInstance = null;
      }
    });
  });
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
        // Clean up modal chart instances
        if (modal.id === 'freqModal' && freqChartModalInstance) {
          freqChartModalInstance.destroy();
          freqChartModalInstance = null;
        }
        if (modal.id === 'bubbleModal' && bubbleChartModalInstance) {
          bubbleChartModalInstance.destroy();
          bubbleChartModalInstance = null;
        }
      }
    });
  });
}

// Ensure modals are shown when clicking on cards
function setupModalCardClicks() {
  const bubbleCard = document.getElementById('bubbleCard');
  const freqCard = document.querySelector('.chart1');
  const spreadCard = document.getElementById('spreadCard');
  const motifListCard = document.getElementById('motifListCard');
  const motifLogoCard = document.getElementById('logoCard');
  if (bubbleCard) bubbleCard.onclick = openBubbleModal;
  if (freqCard) freqCard.onclick = openFreqModal;
  if (spreadCard) {
    spreadCard.onclick = function(event) {
      // Prevent modal if clicking the select or its children
      const filePicker = document.getElementById('file-picker');
      if (event.target === filePicker || filePicker.contains(event.target)) {
        event.stopPropagation();
        return;
      }
      openSpreadModal();
    };
  }
  if (motifListCard) motifListCard.onclick = openMotifListModal;
  if (motifLogoCard) motifLogoCard.onclick = openMotifLogoModal;
}

document.addEventListener('DOMContentLoaded', function() {
    // Existing default tab logic
    currentOption = 'percentage';
    setActiveNav(currentOption);
    setupNavEvents();
    // Fetch dataset data from backend
    const datasetId = window.dataset_id || (window.location.pathname.split('/').filter(Boolean).pop());
    const source = window.source || null;
    let apiUrl = `/api/dataset/${datasetId}/data`;
    if (source) apiUrl += `?source=${source}`;
    fetch(apiUrl)
        .then(res => res.json())
        .then(data => {
            lastParsedData = data;
            updateAll(lastParsedData);
        })
        .catch(err => {
            console.error('Failed to load dataset data:', err);
        });
    setupModalCardClicks();
    setupModalCloseHandlers(); // Ensure modal X buttons work
}); 