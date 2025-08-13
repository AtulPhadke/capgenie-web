const container = document.getElementById("folder_container");

function sortListByFilter(list, filterString) {
    if (!filterString) {
      return list;
    }
  
    const filteredList = list.filter(item => item.toLowerCase().includes(filterString.toLowerCase()));
  
    filteredList.sort((a, b) => {
      const indexA = a.toLowerCase().indexOf(filterString.toLowerCase());
      const indexB = b.toLowerCase().indexOf(filterString.toLowerCase());
  
      if (indexA < indexB) return -1;
      if (indexA > indexB) return 1;
      return a.localeCompare(b);
    });
  
    return filteredList;
  }

async function filter_folders(filter_str) {
    container.innerHTML = "<strong>Previous Datasets</strong>";

    try {
        const response = await fetch('/api/datasets');
        const datasets = await response.json();
        
        console.log(datasets);

        sortListByFilter(datasets.map(d => d.name), filter_str).forEach((name, index) => {
            const dataset = datasets.find(d => d.name === name);
            const folder = document.createElement("div");
            folder.className = "dataset-item";
        
            folder.innerHTML = `
              <div class="folder-icon">
                <img src="/static/imgs/folder_icon.png" alt="Folder Icon"/>
                <span class="folder-name">${name}</span>
              </div>
              <img class="dropdown" src="/static/imgs/drop_down.png"/>
            `;

            folder.addEventListener("click", function() {
              // Use the appropriate source (cache if available, otherwise web)
              const source = dataset.source || 'web';
              window.location.href = `/view_dataset/${source}/${dataset.id}`;
            });
        
            container.appendChild(folder);
        });
    } catch (error) {
        console.error('Error fetching datasets:', error);
    }
}

filter_folders("");

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search_bar');
    searchInput.addEventListener('input', function(event) {
        filter_folders(event.target.value);
        console.log(event.target.value);
    });
});

const new_dataset_button = document.getElementById("new-btn");
new_dataset_button.addEventListener("click", async () => {
  console.log("new dataset");
  window.location.href = '/new_dataset';
}); 