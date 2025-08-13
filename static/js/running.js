// Get dataset ID from URL
const datasetId = window.location.pathname.split('/').pop();

// Elements
const progressText = document.getElementById('progress_text');
const progressFill = document.getElementById('progress-fill');
const currentFile = document.getElementById('current-file');
const fileCount = document.getElementById('file-count');
const fileProgress = document.getElementById('file-progress');
const outputContent = document.getElementById('output-content');
const outputContainer = document.getElementById('output-container');

// Output formatting
function formatOutput(message) {
  const timestamp = new Date(message.timestamp).toLocaleTimeString();
  let color = '#333';
  
  switch (message.type) {
    case 'info':
      color = '#007acc';
      break;
    case 'warning':
      color = '#ffc107';
      break;
    case 'error':
      color = '#dc3545';
      break;
    case 'success':
      color = '#28a745';
      break;
    case 'output':
      color = '#666';
      break;
  }
  
  return `<div style="color: ${color}; margin-bottom: 0.2rem;">
    <span style="color: #999;">[${timestamp}]</span> ${message.message}
  </div>`;
}

// Poll for processing status and output
async function checkProcessingStatus() {
  try {
    // Get status
    const statusResponse = await fetch(`/api/processing_status/${datasetId}`);
    const status = await statusResponse.json();
    
    // Get output
    const outputResponse = await fetch(`/api/processing_output/${datasetId}`);
    const output = await outputResponse.json();
    
    // Update status
    progressText.textContent = status.message;
    progressFill.style.width = status.progress + '%';
    
    // Update file progress if available
    if (status.total_files > 0) {
      fileProgress.style.display = 'block';
      currentFile.textContent = status.current_file || 'Processing files...';
      fileCount.textContent = `${status.processed_files || 0}/${status.total_files} files`;
    }
    
    // Update output
    if (output.output && output.output.length > 0) {
      output.output.forEach(message => {
        outputContent.innerHTML += formatOutput(message);
      });
      // Auto-scroll to bottom
      outputContainer.scrollTop = outputContainer.scrollHeight;
    }
    
    // Update step indicators based on progress
    updateStepIndicators(status.progress);
    
    // Handle completion or error
    if (status.status === 'completed') {
      progressText.textContent = 'Analysis completed successfully!';
      progressFill.style.width = '100%';
      progressFill.style.background = '#28a745';
      
      setTimeout(() => {
        // Redirect to cache version if available, otherwise web version
        if (status.cache_available) {
          window.location.href = `/view_dataset/cache/${datasetId}`;
        } else {
          window.location.href = `/view_dataset/web/${datasetId}`;
        }
      }, 3000);
      return;
    } else if (status.status === 'error') {
      progressText.textContent = 'Error: ' + status.message;
      progressFill.style.width = '0%';
      progressFill.style.background = '#dc3545';
      return;
    }
    
    // Continue polling
    setTimeout(checkProcessingStatus, 1000);
    
  } catch (error) {
    console.error('Error checking processing status:', error);
    progressText.textContent = 'Error checking status: ' + error.message;
    setTimeout(checkProcessingStatus, 2000);
  }
}

// Update step indicators
function updateStepIndicators(progress) {
  const stepElements = ['step-upload', 'step-process', 'step-visualize', 'step-complete'];
  const progressThresholds = [25, 50, 75, 100];
  
  stepElements.forEach((stepId, index) => {
    const stepElement = document.getElementById(stepId);
    if (progress >= progressThresholds[index]) {
      stepElement.classList.add('completed');
      stepElement.classList.remove('active');
    } else if (progress >= progressThresholds[index] - 12.5) {
      stepElement.classList.add('active');
      stepElement.classList.remove('completed');
    } else {
      stepElement.classList.remove('active', 'completed');
    }
  });
}

// Start polling when page loads
document.addEventListener('DOMContentLoaded', () => {
  checkProcessingStatus();
}); 