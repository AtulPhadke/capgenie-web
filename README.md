# CapGenie Web Interface

This is the web interface for CapGenie, a software pipeline for analyzing AAV9 reads in NextGenSequencing (NGS) files.

## Features

- **Real-time Analysis**: Run CapGenie in the background with live progress updates
- **Multiple Analysis Types**: Support for capsid selection, quality analysis, enrichment calculations, motif analysis, barcode evaluation, and visualization
- **File Upload**: Upload entire dataset folders with automatic file organization
- **Progress Tracking**: Real-time progress updates with detailed output from CapGenie
- **Results Viewing**: View processed results with interactive visualizations

## Prerequisites

1. **CapGenie Installation**: CapGenie must be installed and available in your PATH
2. **Python Dependencies**: Install required Python packages
   ```bash
   pip install flask pandas numpy werkzeug
   ```

## Running the Web Interface

1. **Start the Flask server**:
   ```bash
   cd web2/
   python app.py
   ```

2. **Access the interface**:
   Open your browser and navigate to `http://localhost:5001`

## Usage

### Creating a New Dataset

1. **Navigate to "New Dataset"** in the web interface
2. **Select a Dataset Folder**: Choose a folder containing your FASTQ files and any CSV files for analysis
3. **Enter Dataset Name**: Provide a descriptive name for your dataset
4. **Select Analysis Options**:
   - **Capsid Library Selections**: Analyze AAV9 sequences (requires CSV file in dataset folder)
   - **Quality Analysis & Denoising**: Remove low-quality reads with configurable threshold
   - **Enrichment Values**: Calculate peptide growth based on pre-insert library (requires FASTQ file)
   - **Motif Analysis**: Search for sequence motifs and patterns
   - **Barcode Evaluation**: Evaluate pooled vector barcodes (requires separate CSV file upload)
   - **Visualization**: Generate bubble charts and frequency distribution graphs
5. **Start Analysis**: Click "Start Analysis" to begin processing

### Real-time Progress

- **Progress Bar**: Shows overall completion percentage
- **File Progress**: Displays current file being processed and total file count
- **CapGenie Output**: Real-time output from the CapGenie command line tool
- **Status Updates**: Live status messages and step indicators

### Viewing Results

Once processing is complete, you'll be automatically redirected to the results page where you can:
- View processed data in spreadsheet format
- See enrichment and percentage calculations
- Access generated visualizations
- Download results

## API Endpoints

- `POST /api/upload` - Upload dataset files
- `POST /api/process_dataset` - Start dataset processing
- `GET /api/processing_status/<dataset_id>` - Get processing status
- `GET /api/processing_output/<dataset_id>` - Get real-time output
- `GET /api/datasets` - List available datasets
- `GET /api/dataset/<dataset_id>/data` - Get processed data

## File Structure

```
web2/
├── app.py                 # Main Flask application
├── templates/            # HTML templates
│   ├── new_dataset.html  # Dataset creation page
│   ├── running.html      # Processing status page
│   └── view_dataset.html # Results viewing page
├── static/               # Static assets
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── imgs/            # Images
├── datasets/            # Uploaded datasets (created automatically)
└── uploads/             # Temporary uploads (created automatically)
```

## Troubleshooting

### Processing Errors
- Check the real-time output for detailed error messages
- Ensure your dataset folder contains the required file types
- Verify that CSV files are properly formatted for the selected analysis types

### File Upload Issues
- Ensure your dataset folder contains FASTQ files (.fastq or .fq)
- For capsid analysis, include a CSV file in the dataset folder
- For barcode evaluation, upload a separate CSV file using the file input
- Check file permissions and available disk space

## Development

The web interface uses:
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Real-time Updates**: Polling-based status updates
- **File Processing**: Background threading with subprocess management

## License

This project is part of the CapGenie software suite. Please refer to the main project license for details. 