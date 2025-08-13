// Global wizard state
let currentStep = 1;
let totalSteps = 6;
let wizardOptions = {
  analysisType: null,
  enrichment: false,
  enrichmentFile: null,
  denoise: false,
  threshold: 15,
  graphs: false,
  motif: false,
  folderFiles: null,
  csvFile: null,
  datasetName: null
};

// Initialize wizard on page load
document.addEventListener('DOMContentLoaded', function() {
  setupWizard();
  setupStepOptions();
  setupNavigation();
  setupModals();
  updateProgress();
});

function setupWizard() {
  // Show first step
  showStep(1);
  
  // Setup dataset name validation
  const datasetNameInput = document.getElementById('dataset-name');
  const errorText = document.getElementById('error-text');
  
  datasetNameInput.addEventListener('input', function() {
    if (this.value.trim()) {
      errorText.style.display = 'none';
      wizardOptions.datasetName = this.value.trim();
    } else {
      errorText.style.display = 'block';
    }
  });
}

function setupStepOptions() {
  // Step 1: Folder Selection
  const folderSelectionOption = document.getElementById('folder-selection');
  const folderInput = document.getElementById('dataset-folder');
  
  folderSelectionOption.addEventListener('click', function() {
    folderInput.click();
  });
  
  folderInput.addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      wizardOptions.folderFiles = files;
      folderSelectionOption.classList.add('selected');
      
      // Update option text
      const optionText = folderSelectionOption.querySelector('.option-text p');
      optionText.textContent = `Selected ${files.length} files`;
      
      // Show directory structure
      showDirectoryStructure(files);
    }
  });
  
  // Step 2: Analysis Type
  document.getElementById('barcode-option').addEventListener('click', function() {
    selectOption('barcode-option', 'selection-option');
    wizardOptions.analysisType = 'barcode';
    
    // Prompt for CSV file
    const csvInput = document.getElementById('barcode-csv-file');
    csvInput.click();
  });
  
  document.getElementById('selection-option').addEventListener('click', function() {
    selectOption('selection-option', 'barcode-option');
    wizardOptions.analysisType = 'selection';
  });
  
  // CSV file input for barcode analysis
  document.getElementById('barcode-csv-file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
      wizardOptions.csvFile = file;
      const optionText = document.querySelector('#barcode-option .option-text p');
      optionText.textContent = `CSV file selected: ${file.name}`;
    }
  });
  
  // Step 3: Enrichment
  document.getElementById('enrichment-yes').addEventListener('click', function() {
    selectOption('enrichment-yes', 'enrichment-no');
    wizardOptions.enrichment = true;
    
    // Show file selector and populate with FASTQ files from dataset
    showEnrichmentFileSelector();
  });
  
  document.getElementById('enrichment-no').addEventListener('click', function() {
    selectOption('enrichment-no', 'enrichment-yes');
    wizardOptions.enrichment = false;
    wizardOptions.enrichmentFile = null;
    wizardOptions.enrichmentFilePath = null;
    
    // Hide file selector
    const fileSelector = document.getElementById('enrichment-file-selector');
    fileSelector.style.display = 'none';
  });
  
  // Handle enrichment file selection
  document.getElementById('enrichment-file-select').addEventListener('change', function(e) {
    const selectedPath = e.target.value;
    if (selectedPath) {
      wizardOptions.enrichmentFilePath = selectedPath;
      const optionText = document.querySelector('#enrichment-yes .option-text p');
      const fileName = selectedPath.split('/').pop();
      optionText.textContent = `Selected: ${fileName}`;
    }
  });
  
  // Step 4: Denoise
  document.getElementById('denoise-yes').addEventListener('click', function(e) {
    // Don't trigger selection if clicking on threshold controls
    if (e.target.closest('.threshold-controls')) {
      return;
    }
    selectOption('denoise-yes', 'denoise-no');
    wizardOptions.denoise = true;
  });
  
  document.getElementById('denoise-no').addEventListener('click', function() {
    selectOption('denoise-no', 'denoise-yes');
    wizardOptions.denoise = false;
  });
  
  // Prevent threshold controls from triggering option selection
  const thresholdControls = document.querySelector('.threshold-controls');
  if (thresholdControls) {
    thresholdControls.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  }
  
  // Step 5: Graphs
  document.getElementById('graphs-yes').addEventListener('click', function() {
    selectOption('graphs-yes', 'graphs-no');
    wizardOptions.graphs = true;
  });
  
  document.getElementById('graphs-no').addEventListener('click', function() {
    selectOption('graphs-no', 'graphs-yes');
    wizardOptions.graphs = false;
  });
  
  // Step 6: Motifs
  document.getElementById('motif-yes').addEventListener('click', function() {
    selectOption('motif-yes', 'motif-no');
    wizardOptions.motif = true;
  });
  
  document.getElementById('motif-no').addEventListener('click', function() {
    selectOption('motif-no', 'motif-yes');
    wizardOptions.motif = false;
  });
}

function setupNavigation() {
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const finishBtn = document.getElementById('finish-btn');
  
  prevBtn.addEventListener('click', prevStep);
  nextBtn.addEventListener('click', nextStep);
  finishBtn.addEventListener('click', submitDataset);
}

function setupModals() {
  // Barcode info modal
  const barcodeInfoModal = document.getElementById('barcode-info-modal');
  const barcodeInfoModalClose = document.getElementById('barcode-info-modal-close');
  const barcodeInfoModalCloseBtn = document.getElementById('barcode-info-modal-close-btn');
  
  // Selection info modal
  const selectionInfoModal = document.getElementById('selection-info-modal');
  const selectionInfoModalClose = document.getElementById('selection-info-modal-close');
  const selectionInfoModalCloseBtn = document.getElementById('selection-info-modal-close-btn');
  
  // Denoise info modal
  const denoiseInfoModal = document.getElementById('denoise-info-modal');
  const denoiseInfoModalClose = document.getElementById('denoise-info-modal-close');
  const denoiseInfoModalCloseBtn = document.getElementById('denoise-info-modal-close-btn');
  
  // Motif info modal
  const motifInfoModal = document.getElementById('motif-info-modal');
  const motifInfoModalClose = document.getElementById('motif-info-modal-close');
  const motifInfoModalCloseBtn = document.getElementById('motif-info-modal-close-btn');
  
  // Info button handlers
  document.getElementById('barcode-info-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    barcodeInfoModal.classList.add('show');
  });
  
  document.getElementById('selection-info-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    selectionInfoModal.classList.add('show');
  });
  
  document.getElementById('denoise-info-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    denoiseInfoModal.classList.add('show');
  });
  
  document.getElementById('motif-info-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    motifInfoModal.classList.add('show');
  });
  
  // Modal close handlers
  barcodeInfoModalClose.addEventListener('click', () => {
    barcodeInfoModal.classList.remove('show');
  });
  
  barcodeInfoModalCloseBtn.addEventListener('click', () => {
    barcodeInfoModal.classList.remove('show');
  });
  
  selectionInfoModalClose.addEventListener('click', () => {
    selectionInfoModal.classList.remove('show');
  });
  
  selectionInfoModalCloseBtn.addEventListener('click', () => {
    selectionInfoModal.classList.remove('show');
  });
  
  denoiseInfoModalClose.addEventListener('click', () => {
    denoiseInfoModal.classList.remove('show');
  });
  
  denoiseInfoModalCloseBtn.addEventListener('click', () => {
    denoiseInfoModal.classList.remove('show');
  });
  
  motifInfoModalClose.addEventListener('click', () => {
    motifInfoModal.classList.remove('show');
  });
  
  motifInfoModalCloseBtn.addEventListener('click', () => {
    motifInfoModal.classList.remove('show');
  });
  
  // Close modals when clicking outside
  [barcodeInfoModal, selectionInfoModal, denoiseInfoModal, motifInfoModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('show');
      }
    });
  });
}

function selectOption(selectedId, unselectedId) {
  document.getElementById(selectedId).classList.add('selected');
  document.getElementById(unselectedId).classList.remove('selected');
}

function showStep(stepNumber) {
  // Hide all steps
  document.querySelectorAll('.wizard-step').forEach(step => {
    step.classList.remove('active');
  });
  
  // Show current step
  const currentStepElement = document.getElementById(`step-${stepNumber}`);
  if (currentStepElement) {
    currentStepElement.classList.add('active');
  }
  
  // Update progress bar
  updateProgress();
  
  // Update navigation buttons
  updateNavigation();
}

function updateProgress() {
  const progressFill = document.getElementById('progress-fill');
  const steps = document.querySelectorAll('.step');
  
  // Update progress bar
  const progressPercentage = (currentStep / totalSteps) * 100;
  progressFill.style.width = `${progressPercentage}%`;
  
  // Update step indicators
  steps.forEach((step, index) => {
    const stepNumber = index + 1;
    step.classList.remove('active', 'completed');
    
    if (stepNumber === currentStep) {
      step.classList.add('active');
    } else if (stepNumber < currentStep) {
      step.classList.add('completed');
    }
  });
}

function updateNavigation() {
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const finishBtn = document.getElementById('finish-btn');
  
  // Show/hide previous button
  if (currentStep === 1) {
    prevBtn.style.display = 'none';
  } else {
    prevBtn.style.display = 'inline-block';
  }
  
  // Show/hide next and finish buttons
  if (currentStep === totalSteps) {
    nextBtn.style.display = 'none';
    finishBtn.style.display = 'inline-block';
  } else {
    nextBtn.style.display = 'inline-block';
    finishBtn.style.display = 'none';
  }
}

function nextStep() {
  if (!validateCurrentStep()) {
    return;
  }
  
  if (currentStep < totalSteps) {
    currentStep++;
    showStep(currentStep);
  }
}

function prevStep() {
  if (currentStep > 1) {
    currentStep--;
    showStep(currentStep);
  }
}

function validateCurrentStep() {
  const datasetName = document.getElementById('dataset-name').value.trim();
  
  // Always check dataset name
  if (!datasetName) {
    document.getElementById('error-text').style.display = 'block';
    document.getElementById('dataset-name').focus();
    return false;
  }
  
  switch (currentStep) {
    case 1: // Folder Selection
      if (!wizardOptions.folderFiles || wizardOptions.folderFiles.length === 0) {
        alert('Please select a dataset folder');
        return false;
      }
      break;
      
    case 2: // Analysis Type
      if (!wizardOptions.analysisType) {
        alert('Please select an analysis type');
        return false;
      }
      
      if (wizardOptions.analysisType === 'barcode' && !wizardOptions.csvFile) {
        alert('Please select a CSV file for barcode analysis');
        return false;
      }
      break;
      
    case 3: // Enrichment
      if (wizardOptions.enrichment && !wizardOptions.enrichmentFilePath) {
        alert('Please select a FASTQ file for enrichment calculation');
        return false;
      }
      break;
      
    // Steps 4, 5, 6 don't require validation as they have default values
  }
  
  return true;
}

function showDirectoryStructure(files) {
  const dirPanel = document.getElementById('dir-structure-panel');
  const dirTree = document.getElementById('dir-tree');
  
  if (!files || files.length === 0) {
    dirPanel.style.display = 'none';
    return;
  }
  
  // Build directory tree
  const tree = {};
  files.forEach(file => {
    const parts = file.webkitRelativePath.split('/');
    let node = tree;
    
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        // File
        if (!node[part]) node[part] = { isFile: true, size: file.size };
      } else {
        // Directory
        if (!node[part]) node[part] = {};
        node = node[part];
      }
    }
  });
  
  // Render tree
  dirTree.innerHTML = renderTree(tree);
  dirPanel.style.display = 'block';
}

function renderTree(node, depth = 0) {
  let html = '<ul>';
  
  for (const [key, value] of Object.entries(node)) {
    if (value.isFile) {
      const size = formatFileSize(value.size);
      html += `<li>${'  '.repeat(depth)}📄 ${key} (${size})</li>`;
    } else {
      html += `<li>${'  '.repeat(depth)}📁 ${key}`;
      html += renderTree(value, depth + 1);
      html += '</li>';
    }
  }
  
  html += '</ul>';
  return html;
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showEnrichmentFileSelector() {
  const fileSelector = document.getElementById('enrichment-file-selector');
  const fileSelect = document.getElementById('enrichment-file-select');
  
  // Clear previous options
  fileSelect.innerHTML = '<option value="">Choose a FASTQ file...</option>';
  
  // Check if we have uploaded files
  if (!wizardOptions.folderFiles || wizardOptions.folderFiles.length === 0) {
    fileSelect.innerHTML = '<option value="">No dataset files available</option>';
    fileSelector.style.display = 'block';
    return;
  }
  
  // Find FASTQ files in the uploaded dataset
  const fastqFiles = [];
  wizardOptions.folderFiles.forEach(file => {
    if (file.name.toLowerCase().endsWith('.fastq') || file.name.toLowerCase().endsWith('.fq')) {
      // Use the webkitRelativePath to get the relative path within the dataset
      const relativePath = file.webkitRelativePath;
      // Remove the top-level folder name
      const pathParts = relativePath.split('/');
      const cleanPath = pathParts.length > 1 ? pathParts.slice(1).join('/') : relativePath;
      
      fastqFiles.push({
        name: file.name,
        path: cleanPath,
        size: file.size
      });
    }
  });
  
  // Populate the select with FASTQ files
  if (fastqFiles.length > 0) {
    fastqFiles.forEach(file => {
      const option = document.createElement('option');
      option.value = file.path;
      option.textContent = `${file.name} (${formatFileSize(file.size)})`;
      fileSelect.appendChild(option);
    });
  } else {
    fileSelect.innerHTML = '<option value="">No FASTQ files found in dataset</option>';
  }
  
  // Show the file selector
  fileSelector.style.display = 'block';
}

// Threshold controls
function changeThreshold(delta) {
  const thresholdElement = document.getElementById('threshold-value');
  let currentValue = parseInt(thresholdElement.textContent);
  currentValue = Math.max(5, Math.min(35, currentValue + delta));
  thresholdElement.textContent = currentValue;
  wizardOptions.threshold = currentValue;
}

async function submitDataset() {
  if (!validateCurrentStep()) {
    return;
  }
  
  // Hide wizard and show progress
  document.querySelector('.wizard-container').style.display = 'none';
  document.getElementById('progress-section').style.display = 'block';
  
  try {
    // Prepare form data
    const formData = new FormData();
    formData.append('dataset_name', wizardOptions.datasetName);
    
    // Add folder files
    if (wizardOptions.folderFiles) {
      wizardOptions.folderFiles.forEach(file => {
        formData.append('files', file);
      });
    }
    
    // Add CSV file for barcode analysis (enrichment files are already in dataset)
    if (wizardOptions.csvFile) {
      formData.append('files', wizardOptions.csvFile);
    }
    
    // Prepare options to match GUI desktop utility format
    const options = {
      analysis_type: wizardOptions.analysisType,
      enrichment: wizardOptions.enrichment,
      enrichment_file_path: wizardOptions.enrichmentFilePath,
      denoise: wizardOptions.denoise,
      threshold: wizardOptions.threshold,
      graphs: wizardOptions.graphs,
      motif: wizardOptions.motif
    };
    
    formData.append('options', JSON.stringify(options));
    
    // Update progress
    updateProgressText('Uploading files...', 10);
    
    // Upload dataset
    const uploadResponse = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    
    const uploadResult = await uploadResponse.json();
    
    if (!uploadResult.success) {
      throw new Error(uploadResult.error || 'Upload failed');
    }
    
    updateProgressText('Starting analysis...', 30);
    
    // Start processing
    const processResponse = await fetch('/api/process_dataset', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        dataset_id: uploadResult.dataset_id,
        options: options
      })
    });
    
    const processResult = await processResponse.json();
    
    if (!processResult.success) {
      throw new Error(processResult.error || 'Failed to start processing');
    }
    
    updateProgressText('Redirecting to processing page...', 100);
    
    // Redirect to running page
    setTimeout(() => {
      window.location.href = `/running/${uploadResult.dataset_id}`;
    }, 1000);
    
  } catch (error) {
    console.error('Error submitting dataset:', error);
    updateProgressText(`Error: ${error.message}`, 0);
    
    // Show error and allow retry
    setTimeout(() => {
      if (confirm('An error occurred. Would you like to try again?')) {
        document.querySelector('.wizard-container').style.display = 'block';
        document.getElementById('progress-section').style.display = 'none';
      }
    }, 2000);
  }
}

function updateProgressText(text, percentage) {
  document.getElementById('progress-text').textContent = text;
  document.getElementById('processing-progress').style.width = `${percentage}%`;
} 