from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import json
import shutil
import tempfile
import zipfile
from werkzeug.utils import secure_filename
import subprocess
import threading
import time
import uuid
import glob
import pandas as pd
import math
import numpy as np
import base64
import queue
import re
from datetime import datetime
import auth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATASETS_FOLDER'] = 'datasets'
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # Find user by ID
    for user in auth.USERS.values():
        if user.id == int(user_id):
            return user
    return None

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)
os.makedirs('misc', exist_ok=True)  # For CSV files used in barcode evaluation

# Use a Linux-compatible cache path for production
CACHE_ROOT = os.path.expanduser('~/.cache/capgenie')

# Global variable to store processing status and output
processing_status = {}
processing_output = {}  # Store real-time output for each dataset

# Security: Track access attempts to prevent enumeration
from collections import defaultdict
access_attempts = defaultdict(list)  # user_id -> [timestamp, ...]
MAX_FAILED_ATTEMPTS = 10  # Max failed dataset access attempts per hour
ATTEMPT_WINDOW = 3600  # 1 hour in seconds

def df_to_json_array(df):
    # Replace all NaN, inf, -inf with None for JSON serialization
    df = df.replace([np.nan, np.inf, -np.inf], None)
    return [df.columns.tolist()] + df.values.tolist()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = auth.verify_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user and clean up any remaining datasets for security"""
    # Clean up any remaining datasets for this user session for security
    cleanup_all_user_datasets()
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/new_dataset')
@login_required
def new_dataset():
    """New dataset creation page"""
    return render_template('new_dataset.html')

@app.route('/view_dataset/<dataset_id>')
@login_required
def view_dataset(dataset_id):
    """Legacy view dataset page - redirects to appropriate source"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        flash('Dataset not found or access denied.', 'error')
        return redirect(url_for('index'))
    
    # Check metadata to determine the best source
    metadata_path = os.path.join('misc', 'datasets', dataset_id, 'metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Use cache if available, otherwise web
        if metadata.get('cache_available', False):
            return redirect(url_for('view_dataset_any', source='cache', dataset_id=dataset_id))
        else:
            return redirect(url_for('view_dataset_any', source='web', dataset_id=dataset_id))
    
    # Fallback: try web first, then cache
    web_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
    if os.path.exists(web_path):
        return redirect(url_for('view_dataset_any', source='web', dataset_id=dataset_id))
    
    cache_path = os.path.join(CACHE_ROOT, dataset_id)
    if os.path.exists(cache_path):
        return redirect(url_for('view_dataset_any', source='cache', dataset_id=dataset_id))
    
    # Dataset not found anywhere
    return redirect(url_for('index'))

@app.route('/running/<dataset_id>')
@login_required
def running(dataset_id):
    """Processing status page"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        flash('Dataset not found or access denied.', 'error')
        return redirect(url_for('index'))
    
    return render_template('running.html', dataset_id=dataset_id)

@app.route('/view_datasets')
@login_required
def view_datasets():
    """Upload page for new datasets"""
    return render_template('view_datasets.html')

def check_access_rate_limit(user_id):
    """Check if user has exceeded failed access attempts"""
    current_time = time.time()
    user_attempts = access_attempts[user_id]
    
    # Remove old attempts (older than 1 hour)
    user_attempts[:] = [t for t in user_attempts if current_time - t < ATTEMPT_WINDOW]
    
    # Check if user has exceeded limit
    return len(user_attempts) < MAX_FAILED_ATTEMPTS

def record_failed_access(user_id):
    """Record a failed access attempt"""
    access_attempts[user_id].append(time.time())

def verify_dataset_ownership(dataset_id):
    """Verify that the current user owns the specified dataset"""
    if not current_user.is_authenticated:
        print(f"SECURITY: Unauthenticated access attempt to dataset {dataset_id}")
        return False
    
    # Rate limiting check
    if not check_access_rate_limit(current_user.id):
        print(f"SECURITY ALERT: User {current_user.username} rate limited for excessive failed access attempts")
        return False
    
    metadata_path = os.path.join('misc', 'datasets', dataset_id, 'metadata.json')
    if not os.path.exists(metadata_path):
        print(f"SECURITY: User {current_user.username} attempted to access non-existent dataset {dataset_id}")
        record_failed_access(current_user.id)
        return False
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Check if current user is the owner
        owner_id = metadata.get('owner_id')
        if owner_id == current_user.id:
            return True
        
        # Log unauthorized access attempts and record for rate limiting
        owner_username = metadata.get('owner_username', 'unknown')
        print(f"SECURITY ALERT: User {current_user.username} attempted to access dataset {dataset_id} owned by {owner_username}")
        record_failed_access(current_user.id)
        
        # For backwards compatibility with datasets created before user ownership
        # If no owner_id exists, deny access for security
        return False
        
    except Exception as e:
        print(f"Error verifying dataset ownership for {dataset_id}: {e}")
        record_failed_access(current_user.id)
        return False

def cleanup_all_user_datasets():
    """Clean up all datasets owned by current user for security (called on logout or session end)"""
    if not current_user.is_authenticated:
        return
        
    try:
        user_id = current_user.id
        datasets_to_cleanup = []
        
        # Find all datasets owned by current user
        misc_datasets_dir = os.path.join('misc', 'datasets')
        if os.path.exists(misc_datasets_dir):
            for dataset_id in os.listdir(misc_datasets_dir):
                metadata_path = os.path.join(misc_datasets_dir, dataset_id)
                if os.path.isdir(metadata_path):
                    try:
                        metadata_file = os.path.join(metadata_path, 'metadata.json')
                        if os.path.exists(metadata_file):
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            
                            # Only clean up datasets owned by current user
                            if metadata.get('owner_id') == user_id:
                                datasets_to_cleanup.append((dataset_id, metadata))
                    except Exception as e:
                        print(f"Error reading metadata for {dataset_id}: {e}")
        
        # Clean up user's datasets
        for dataset_id, metadata in datasets_to_cleanup:
            try:
                # Clean up dataset files
                dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
                if os.path.exists(dataset_path):
                    shutil.rmtree(dataset_path)
                
                # Clean up cache files
                cache_path = os.path.join(CACHE_ROOT, dataset_id)
                if os.path.exists(cache_path):
                    shutil.rmtree(cache_path)
                
                # Clean up CSV files
                csv_files = metadata.get('csv_files', [])
                for csv_file in csv_files:
                    if os.path.exists(csv_file):
                        os.remove(csv_file)
                
                # Clean up metadata
                metadata_path = os.path.join(misc_datasets_dir, dataset_id)
                if os.path.exists(metadata_path):
                    shutil.rmtree(metadata_path)
                
                # Clear processing status for this dataset
                if dataset_id in processing_status:
                    del processing_status[dataset_id]
                if dataset_id in processing_output:
                    del processing_output[dataset_id]
                    
                print(f"Cleaned up dataset {dataset_id} for user {current_user.username}")
                
            except Exception as e:
                print(f"Error cleaning up dataset {dataset_id}: {e}")
        
        print(f"All datasets for user {current_user.username} cleaned up for security")
    except Exception as e:
        print(f"Error during user dataset cleanup: {e}")

def determine_available_sections(dataset_path):
    """Determine which analysis sections are available based on actual data content"""
    sections = {
        'enrichment': False,
        'percentage': False,
        'quality': False,
        'motif': False
    }
    
    # Check for spreadsheets directory (required for enrichment and percentage)
    spreadsheets_dir = os.path.join(dataset_path, 'spreadsheets')
    if os.path.exists(spreadsheets_dir):
        subfolders = [f for f in os.listdir(spreadsheets_dir) if os.path.isdir(os.path.join(spreadsheets_dir, f))]
        
        # Check if any subfolder has enrichment data
        has_enrichment = False
        has_percentage = False
        
        for subfolder in subfolders:
            subfolder_path = os.path.join(spreadsheets_dir, subfolder)
            files = [f for f in os.listdir(subfolder_path) if f.startswith('average_') and f.endswith('.xlsx')]
            
            # Check for enrichment files
            enrichment_file = next((f for f in files if 'enrichment' in f), None)
            if enrichment_file:
                has_enrichment = True
            
            # Check for percentage files
            percentage_file = next((f for f in files if 'enrichment' not in f), None)
            if percentage_file:
                has_percentage = True
        
        sections['enrichment'] = has_enrichment
        sections['percentage'] = has_percentage
    
    # Check for quality data (instruction.json with denoise info)
    instruction_path = os.path.join(dataset_path, 'instruction.json')
    if os.path.exists(instruction_path):
        try:
            with open(instruction_path, 'r') as f:
                instruction_data = json.load(f)
                sections['quality'] = instruction_data.get('denoise') is not None
        except Exception:
            sections['quality'] = False
    
    # Check for motif data (motifs.json and motif_logo.png)
    motifs_json = os.path.join(dataset_path, 'motifs.json')
    motif_logo = os.path.join(dataset_path, 'motif_logo.png')
    sections['motif'] = os.path.exists(motifs_json) and os.path.exists(motif_logo)
    
    return sections

@app.route('/view_dataset/<source>/<dataset_id>')
@login_required
def view_dataset_any(source, dataset_id):
    """View dataset from either web or cache folder"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        flash('Dataset not found or access denied.', 'error')
        return redirect(url_for('index'))
    
    if source == 'web':
        dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
    elif source == 'cache':
        dataset_path = os.path.join(CACHE_ROOT, dataset_id)
    else:
        return redirect(url_for('view_datasets'))
    if not os.path.exists(dataset_path):
        return redirect(url_for('view_datasets'))
    
    # Determine which sections are actually available based on data content
    sections = determine_available_sections(dataset_path)
    
    # Get dataset title from metadata.json in misc/datasets/ (for both web and cache datasets)
    metadata_path = os.path.join('misc', 'datasets', dataset_id, 'metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        dataset_title = metadata.get('name', dataset_id)
    else:
        dataset_title = dataset_id
    return render_template('view_dataset.html', dataset_id=dataset_id, dataset_path=dataset_path, sections=sections, source=source, dataset_title=dataset_title)



@app.route('/download')
@login_required
def download():
    return render_template('download.html')

@app.route('/documentation')
@login_required
def documentation():
    """Documentation page"""
    return render_template('documentation.html')

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_files():
    """Handle file uploads for new dataset"""
    try:
        dataset_name = request.form.get('dataset_name', '').strip()
        if not dataset_name:
            return jsonify({'error': 'Dataset name is required'}), 400

        # Create unique dataset ID
        dataset_id = str(uuid.uuid4())
        dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
        os.makedirs(dataset_path, exist_ok=True)

        # Create misc/datasets directory if it doesn't exist
        misc_datasets_dir = os.path.join('misc', 'datasets')
        os.makedirs(misc_datasets_dir, exist_ok=True)
        
        # Save dataset metadata in misc/datasets/{dataset_id}/
        metadata_dir = os.path.join(misc_datasets_dir, dataset_id)
        os.makedirs(metadata_dir, exist_ok=True)
        
        metadata = {
            'name': dataset_name,
            'created_at': time.time(),
            'status': 'uploading',
            'dataset_path': dataset_path,
            'owner_id': current_user.id,  # Add user ownership
            'owner_username': current_user.username  # For easier debugging
        }

        with open(os.path.join(metadata_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        # Handle file uploads
        files = request.files.getlist('files')
        uploaded_files = []
        csv_files = []

        for file in files:
            if file.filename:
                # Get the original path from the form data
                original_path = file.filename  # This will be the webkitRelativePath
                
                # Remove the top-level folder name from the path
                path_parts = original_path.split('/')
                if len(path_parts) > 1:
                    # Skip the first part (folder name) and join the rest
                    relative_path = '/'.join(path_parts[1:])
                else:
                    relative_path = original_path
                
                # Handle CSV files separately - save to misc folder
                if file.filename.lower().endswith('.csv'):
                    # Save CSV files to misc folder for barcode evaluation
                    csv_filename = secure_filename(file.filename)
                    csv_path = os.path.join('misc', csv_filename)
                    file.save(csv_path)
                    csv_files.append(csv_path)
                    uploaded_files.append(f'misc/{csv_filename}')
                else:
                    # Save other files (including enrichment files) to dataset directory
                    file_path = os.path.join(dataset_path, relative_path)
                    
                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Save the file with its relative path
                    file.save(file_path)
                    uploaded_files.append(relative_path)

        # Update metadata with uploaded files and CSV files
        metadata['files'] = uploaded_files
        metadata['csv_files'] = csv_files
        metadata['status'] = 'ready'

        with open(os.path.join(metadata_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        return jsonify({
            'success': True,
            'dataset_id': dataset_id,
            'message': f'Dataset "{dataset_name}" created successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_dataset', methods=['POST'])
@login_required
def process_dataset():
    """Start processing a dataset"""
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        options = data.get('options', {})
        
        # SECURITY: Verify user owns this dataset
        if not verify_dataset_ownership(dataset_id):
            return jsonify({'error': 'Dataset not found or access denied'}), 403

        dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
        if not os.path.exists(dataset_path):
            return jsonify({'error': 'Dataset not found'}), 404

        # Initialize processing status and output queue
        processing_status[dataset_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Initializing...',
            'start_time': time.time(),
            'current_file': '',
            'total_files': 0,
            'processed_files': 0
        }
        processing_output[dataset_id] = queue.Queue()

        # Start processing in background thread
        thread = threading.Thread(target=process_dataset_background, args=(dataset_id, options))
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'Processing started'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def build_capgenie_command(dataset_id, dataset_path, options, output_queue):
    """Build CapGenie CLI command using the same logic as GUI desktop utility"""
    command = ['capgenie']
    
    # Add dataset path (folder flag)
    command.extend(['-f', dataset_path])
    
    # Add CSV file for barcode analysis
    if options.get('analysis_type') == 'barcode':
        # Load metadata from misc/datasets/{dataset_id}/ to get CSV file path
        metadata_path = os.path.join('misc', 'datasets', dataset_id, 'metadata.json')
        csv_file_path = None
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                csv_files = metadata.get('csv_files', [])
                if csv_files:
                    csv_file_path = csv_files[0]  # Use the first CSV file (should be in misc/)
        
        if csv_file_path and os.path.exists(csv_file_path):
            command.extend(['-cf', csv_file_path])
            command.extend(['-m', '0'])  # Default to exact matches
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'info',
                'message': f'Using barcode CSV file: {os.path.basename(csv_file_path)}'
            })
        else:
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'warning',
                'message': 'Barcode analysis selected but no CSV file found in misc folder'
            })
    
    elif options.get('analysis_type') == 'selection':
        # Add unknown variants search for selection analysis
        command.append('-unk')
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': 'Selection analysis enabled (unknown variants search)'
        })
    
    # Add enrichment file if specified
    if options.get('enrichment'):
        enrichment_file_path = None
        
        # Use the specific file path selected by the user
        if options.get('enrichment_file_path'):
            enrichment_file_path = os.path.join(dataset_path, options.get('enrichment_file_path'))
        
        if enrichment_file_path and os.path.exists(enrichment_file_path):
            command.extend(['-e', enrichment_file_path])
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'info',
                'message': f'Using enrichment file: {os.path.basename(enrichment_file_path)}'
            })
        else:
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'warning',
                'message': 'Enrichment enabled but selected file not found in dataset'
            })
    
    # Add quality threshold if denoising is enabled
    if options.get('denoise'):
        threshold = options.get('threshold', 15)
        command.extend(['-qual', str(threshold)])
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': f'Quality threshold set to: {threshold}'
        })
    
    # Add visualization flags
    if options.get('graphs'):
        command.append('-b')  # bubble charts
        command.append('-fd')  # frequency distribution
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': 'Visualization enabled (bubble charts and frequency distribution)'
        })
    
    # Add motif analysis flag
    if options.get('motif'):
        command.append('-mot')
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': 'Motif analysis enabled'
        })
    
    # Add session name using dataset_id
    command.extend(['-ses', dataset_id])
    
    output_queue.put({
        'timestamp': datetime.now().isoformat(),
        'type': 'info',
        'message': f'Final CapGenie command: {" ".join(command)}'
    })
    
    return command

def process_dataset_background(dataset_id, options):
    """Background processing function with real-time output capture"""
    try:
        dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
        output_queue = processing_output[dataset_id]
        
        # Update initial status
        processing_status[dataset_id].update({
            'message': 'Preparing analysis...',
            'progress': 5
        })
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': 'Starting CapGenie analysis...'
        })

        # Count total files for progress tracking
        total_files = 0
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(('.fastq', '.fq')):
                    total_files += 1
        
        processing_status[dataset_id]['total_files'] = total_files
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': f'Found {total_files} FASTQ files to process'
        })

        # Build CapGenie CLI command using the same logic as GUI
        command = build_capgenie_command(dataset_id, dataset_path, options, output_queue)
        
        output_queue.put({
            'timestamp': datetime.now().isoformat(),
            'type': 'info',
            'message': f'Command: {" ".join(command)}'
        })

        # Start the subprocess with real-time output capture
        processing_status[dataset_id].update({
            'message': 'Starting CapGenie analysis...',
            'progress': 10
        })

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Read output in real-time
        file_processing_pattern = re.compile(r'Currently processing (.+?) \(')
        file_complete_pattern = re.compile(r'Finished (.+)')
        dir_created_pattern = re.compile(r'Created (.+)')
        enrichment_pattern = re.compile(r'Calculated enrichment: (.+)')
        bubble_pattern = re.compile(r'Created bubble charts: (.+)')
        freq_pattern = re.compile(r'Created frequency distribution charts: (.+)')
        motif_pattern = re.compile(r'Finding Motifs|Creating Motif Logo|Motif Logo saved to: (.+)')

        processed_files = 0
        
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                
            # Add to output queue
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'output',
                'message': line
            })

            # Parse progress from output
            match = file_processing_pattern.search(line)
            if match:
                current_file = match.group(1)
                processing_status[dataset_id]['current_file'] = current_file
                processing_status[dataset_id]['message'] = f'Processing {current_file}...'
                
                # Calculate progress based on files
                if total_files > 0:
                    progress = 10 + (processed_files / total_files) * 70
                    processing_status[dataset_id]['progress'] = min(80, progress)
                    
            elif file_complete_pattern.search(line):
                processed_files += 1
                processing_status[dataset_id]['processed_files'] = processed_files
                
                if total_files > 0:
                    progress = 10 + (processed_files / total_files) * 70
                    processing_status[dataset_id]['progress'] = min(80, progress)
                    
            elif dir_created_pattern.search(line):
                processing_status[dataset_id]['message'] = 'Setting up analysis directories...'
                processing_status[dataset_id]['progress'] = 15
                
            elif enrichment_pattern.search(line):
                processing_status[dataset_id]['message'] = 'Calculating enrichment values...'
                processing_status[dataset_id]['progress'] = 85
                
            elif bubble_pattern.search(line) or freq_pattern.search(line):
                processing_status[dataset_id]['message'] = 'Generating visualizations...'
                processing_status[dataset_id]['progress'] = 90
                
            elif motif_pattern.search(line):
                processing_status[dataset_id]['message'] = 'Analyzing motifs...'
                processing_status[dataset_id]['progress'] = 75

        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0:
            # Check if results are in cache
            cache_path = os.path.join(CACHE_ROOT, dataset_id)
            cache_available = os.path.exists(cache_path)
            
            processing_status[dataset_id].update({
                'status': 'completed',
                'message': 'Analysis completed successfully!',
                'progress': 100,
                'cache_available': cache_available,
                'cache_path': cache_path if cache_available else None
            })
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'success',
                'message': f'CapGenie analysis completed successfully! Results {"available in cache" if cache_available else "saved to dataset folder"}.'
            })
        else:
            processing_status[dataset_id].update({
                'status': 'error',
                'message': f'CapGenie process failed with return code {return_code}',
                'progress': 0
            })
            output_queue.put({
                'timestamp': datetime.now().isoformat(),
                'type': 'error',
                'message': f'CapGenie process failed with return code {return_code}'
            })

        # Update metadata in misc/datasets/{dataset_id}/
        metadata_path = os.path.join('misc', 'datasets', dataset_id, 'metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            metadata['status'] = 'completed' if return_code == 0 else 'error'
            metadata['completed_at'] = time.time()
            metadata['options'] = options
            metadata['return_code'] = return_code
            
            # Add cache information if successful
            if return_code == 0:
                cache_path = os.path.join(CACHE_ROOT, dataset_id)
                if os.path.exists(cache_path):
                    metadata['cache_available'] = True
                    metadata['cache_path'] = cache_path
                else:
                    metadata['cache_available'] = False
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)

        # Clean up output queue after a delay to allow final messages to be retrieved
        def cleanup_queue():
            time.sleep(5)  # Wait 5 seconds for final output retrieval
            if dataset_id in processing_output:
                del processing_output[dataset_id]
        
        cleanup_thread = threading.Thread(target=cleanup_queue)
        cleanup_thread.daemon = True
        cleanup_thread.start()

    except Exception as e:
        processing_status[dataset_id].update({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'progress': 0
        })
        if dataset_id in processing_output:
            processing_output[dataset_id].put({
                'timestamp': datetime.now().isoformat(),
                'type': 'error',
                'message': f'Processing error: {str(e)}'
            })

@app.route('/api/processing_status/<dataset_id>')
@login_required
def get_processing_status(dataset_id):
    """Get processing status for a dataset"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        return jsonify({'error': 'Access denied'}), 403
    status = processing_status.get(dataset_id, {
        'status': 'unknown',
        'progress': 0,
        'message': 'Status unknown'
    })
    return jsonify(status)

@app.route('/api/processing_output/<dataset_id>')
@login_required
def get_processing_output(dataset_id):
    """Get real-time output from processing"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        return jsonify({'error': 'Access denied'}), 403
    try:
        output_queue = processing_output.get(dataset_id)
        if not output_queue:
            return jsonify({'output': []})
        
        # Get all available output messages
        output_messages = []
        while not output_queue.empty():
            try:
                message = output_queue.get_nowait()
                output_messages.append(message)
            except queue.Empty:
                break
        
        return jsonify({'output': output_messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/datasets')
@login_required
def get_datasets():
    """Get list of available datasets for the current user only"""
    datasets = []

    # Look for metadata in misc/datasets/ directory
    misc_datasets_dir = os.path.join('misc', 'datasets')
    if os.path.exists(misc_datasets_dir):
        for dataset_id in os.listdir(misc_datasets_dir):
            metadata_path = os.path.join(misc_datasets_dir, dataset_id, 'metadata.json')

            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    # SECURITY: Only show datasets owned by current user
                    if metadata.get('owner_id') != current_user.id:
                        continue

                    # Verify the actual dataset folder still exists
                    dataset_path = metadata.get('dataset_path', os.path.join(app.config['DATASETS_FOLDER'], dataset_id))
                    if os.path.exists(dataset_path):
                        # Determine the best source (cache if available, otherwise web)
                        cache_available = metadata.get('cache_available', False)
                        source = 'cache' if cache_available else 'web'
                        
                        datasets.append({
                            'id': dataset_id,
                            'name': metadata.get('name', 'Unknown'),
                            'status': metadata.get('status', 'unknown'),
                            'created_at': metadata.get('created_at', 0),
                            'source': source,
                            'cache_available': cache_available
                        })
                except:
                    continue

    # Sort by creation date (newest first)
    datasets.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(datasets)

@app.route('/api/dataset/<dataset_id>/data')
@login_required
def get_dataset_data(dataset_id):
    """Get processed data for a dataset (web or cache)"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        return jsonify({'error': 'Access denied'}), 403
    try:
        source = request.args.get('source')
        dataset_path = None
        metadata = None
        # Try web uploads first if source is not specified or is web
        if source is None or source == 'web':
            web_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
            if os.path.exists(web_path):
                dataset_path = web_path
                # Look for metadata in misc/datasets/ directory
                metadata_path = os.path.join('misc', 'datasets', dataset_id, 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
        # If not found or source is cache, try cache folder
        if (dataset_path is None or not os.path.exists(dataset_path)) or (source == 'cache'):
            cache_path = os.path.join(CACHE_ROOT, dataset_id)
            if os.path.exists(cache_path):
                dataset_path = cache_path
                metadata = None  # No metadata.json in cache
        if dataset_path is None or not os.path.exists(dataset_path):
            return jsonify({'error': 'Dataset not found'}), 404
        # If metadata exists, check status
        if metadata and metadata.get('status') != 'ready':
            return jsonify({'error': 'Dataset processing not complete'}), 400
        import pandas as pd
        # For cache datasets, mimic FinishedDataset.parse() for all subfolders
        if dataset_path.startswith(CACHE_ROOT):
            spreadsheets_dir = os.path.join(dataset_path, 'spreadsheets')
            if not os.path.exists(spreadsheets_dir):
                return jsonify({'error': 'No spreadsheets found'}), 404
            subfolders = [f for f in os.listdir(spreadsheets_dir) if os.path.isdir(os.path.join(spreadsheets_dir, f))]
            if not subfolders:
                return jsonify({'error': 'No spreadsheet subfolders found'}), 404

            spreadsheets = {}
            max_values = {}
            subfolders_dict = {}

            for subfolder in subfolders:
                subfolder_path = os.path.join(spreadsheets_dir, subfolder)
                files = [f for f in os.listdir(subfolder_path) if f.startswith('average_') and f.endswith('.xlsx')]
                enrichment_file = next((f for f in files if 'enrichment' in f), None)
                percentage_file = next((f for f in files if 'enrichment' not in f), None)
                enrichment = None
                percentage = None
                if enrichment_file:
                    df = pd.read_excel(os.path.join(subfolder_path, enrichment_file))
                    enrichment = df_to_json_array(df)
                if percentage_file:
                    df = pd.read_excel(os.path.join(subfolder_path, percentage_file))
                    percentage = df_to_json_array(df)
                spreadsheets[subfolder] = {
                    'enrichment': enrichment,
                    'percentage': percentage
                }
                # Max values logic (like getMax in JS)
                def get_max(s_data):
                    if s_data and len(s_data) > 1:
                        top_peptide_val = s_data[1][-1]
                        top_peptide_name = s_data[1][0]
                        return {top_peptide_name: top_peptide_val}
                    return None
                max_values[subfolder] = {
                    'enrichment': get_max(enrichment),
                    'percentage': get_max(percentage)
                }
                subfolders_dict[subfolder] = files

            # Quality: from instruction.json if present
            quality = None
            instruction_path = os.path.join(dataset_path, 'instruction.json')
            if os.path.exists(instruction_path):
                try:
                    with open(instruction_path, 'r') as f:
                        quality = json.load(f).get('denoise')
                except Exception:
                    quality = None
            # Motif: from motifs.json and motif_logo.png if present
            motif = None
            motifs_json = os.path.join(dataset_path, 'motifs.json')
            motif_logo = os.path.join(dataset_path, 'motif_logo.png')
            if os.path.exists(motifs_json) and os.path.exists(motif_logo):
                try:
                    with open(motifs_json, 'r') as f:
                        motifs_data = json.load(f)
                    with open(motif_logo, 'rb') as imgf:
                        base64_img = 'data:image/png;base64,' + base64.b64encode(imgf.read()).decode('utf-8')
                    motif = {'motifs': motifs_data.get('0'), 'img': base64_img}
                except Exception:
                    motif = None

            result = {
                'subfolders': subfolders_dict,
                'max_values': max_values,
                'spreadsheets': spreadsheets,
                'quality': quality,
                'motif': motif
            }
            return jsonify(result)
        
        # For web datasets, use the same logic as cache datasets
        spreadsheets_dir = os.path.join(dataset_path, 'spreadsheets')
        if not os.path.exists(spreadsheets_dir):
            return jsonify({'error': 'No spreadsheets found'}), 404
        subfolders = [f for f in os.listdir(spreadsheets_dir) if os.path.isdir(os.path.join(spreadsheets_dir, f))]
        if not subfolders:
            return jsonify({'error': 'No spreadsheet subfolders found'}), 404

        spreadsheets = {}
        max_values = {}
        subfolders_dict = {}

        for subfolder in subfolders:
            subfolder_path = os.path.join(spreadsheets_dir, subfolder)
            files = [f for f in os.listdir(subfolder_path) if f.startswith('average_') and f.endswith('.xlsx')]
            enrichment_file = next((f for f in files if 'enrichment' in f), None)
            percentage_file = next((f for f in files if 'enrichment' not in f), None)
            enrichment = None
            percentage = None
            if enrichment_file:
                df = pd.read_excel(os.path.join(subfolder_path, enrichment_file))
                enrichment = df_to_json_array(df)
            if percentage_file:
                df = pd.read_excel(os.path.join(subfolder_path, percentage_file))
                percentage = df_to_json_array(df)
            spreadsheets[subfolder] = {
                'enrichment': enrichment,
                'percentage': percentage
            }
            # Max values logic (like getMax in JS)
            def get_max(s_data):
                if s_data and len(s_data) > 1:
                    top_peptide_val = s_data[1][-1]
                    top_peptide_name = s_data[1][0]
                    return {top_peptide_name: top_peptide_val}
                return None
            max_values[subfolder] = {
                'enrichment': get_max(enrichment),
                'percentage': get_max(percentage)
            }
            subfolders_dict[subfolder] = files

        # Quality: from instruction.json if present
        quality = None
        instruction_path = os.path.join(dataset_path, 'instruction.json')
        if os.path.exists(instruction_path):
            try:
                with open(instruction_path, 'r') as f:
                    quality = json.load(f).get('denoise')
            except Exception:
                quality = None
        # Motif: from motifs.json and motif_logo.png if present
        motif = None
        motifs_json = os.path.join(dataset_path, 'motifs.json')
        motif_logo = os.path.join(dataset_path, 'motif_logo.png')
        if os.path.exists(motifs_json) and os.path.exists(motif_logo):
            try:
                with open(motifs_json, 'r') as f:
                    motifs_data = json.load(f)
                with open(motif_logo, 'rb') as imgf:
                    base64_img = 'data:image/png;base64,' + base64.b64encode(imgf.read()).decode('utf-8')
                motif = {'motifs': motifs_data.get('0'), 'img': base64_img}
            except Exception:
                motif = None

        result = {
            'subfolders': subfolders_dict,
            'max_values': max_values,
            'spreadsheets': spreadsheets,
            'quality': quality,
            'motif': motif
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def uploaded_files(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/cleanup_dataset/<dataset_id>', methods=['POST'])
@login_required
def cleanup_dataset(dataset_id):
    """Securely clean up dataset and all related files when user exits"""
    # SECURITY: Verify user owns this dataset
    if not verify_dataset_ownership(dataset_id):
        return jsonify({'error': 'Access denied'}), 403
    try:
        # Get metadata to find all related files
        metadata_path = os.path.join('misc', 'datasets', dataset_id)
        csv_files_to_remove = []
        
        if os.path.exists(os.path.join(metadata_path, 'metadata.json')):
            with open(os.path.join(metadata_path, 'metadata.json'), 'r') as f:
                metadata = json.load(f)
                csv_files_to_remove = metadata.get('csv_files', [])
        
        success = False
        
        # 1. Remove web dataset directory
        dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
        if os.path.exists(dataset_path):
            shutil.rmtree(dataset_path)
            success = True
            
        # 2. Remove cache dataset directory (for security)
        cache_path = os.path.join(CACHE_ROOT, dataset_id)
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
            success = True
            
        # 3. Remove associated CSV files from misc folder
        for csv_file in csv_files_to_remove:
            if os.path.exists(csv_file):
                os.remove(csv_file)
                success = True
                
        # 4. Remove metadata directory
        if os.path.exists(metadata_path):
            shutil.rmtree(metadata_path)
            success = True
            
        # 5. Clear any processing status for this dataset
        if dataset_id in processing_status:
            del processing_status[dataset_id]
            
        if dataset_id in processing_output:
            del processing_output[dataset_id]
            
        if success:
            return jsonify({'success': True, 'message': 'Dataset and all related files cleaned up securely'})
        else:
            return jsonify({'error': 'Dataset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def periodic_security_cleanup():
    """Periodic cleanup of old datasets for security (runs every hour)"""
    import threading
    import time
    
    def cleanup_task():
        while True:
            try:
                current_time = time.time()
                # Clean up datasets older than 2 hours for security
                misc_datasets_dir = os.path.join('misc', 'datasets')
                if os.path.exists(misc_datasets_dir):
                    for dataset_id in os.listdir(misc_datasets_dir):
                        metadata_path = os.path.join(misc_datasets_dir, dataset_id, 'metadata.json')
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r') as f:
                                    metadata = json.load(f)
                                created_at = metadata.get('created_at', current_time)
                                
                                # If dataset is older than 2 hours, clean it up (security measure)
                                if current_time - created_at > 7200:  # 2 hours
                                    owner_username = metadata.get('owner_username', 'unknown')
                                    print(f"Cleaning up old dataset {dataset_id} (owner: {owner_username}) for security")
                                    
                                    # Clean up dataset files
                                    dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
                                    if os.path.exists(dataset_path):
                                        shutil.rmtree(dataset_path)
                                    
                                    cache_path = os.path.join(CACHE_ROOT, dataset_id)
                                    if os.path.exists(cache_path):
                                        shutil.rmtree(cache_path)
                                    
                                    # Clean up CSV files
                                    csv_files = metadata.get('csv_files', [])
                                    for csv_file in csv_files:
                                        if os.path.exists(csv_file):
                                            os.remove(csv_file)
                                    
                                    # Clean up metadata
                                    metadata_dir = os.path.join(misc_datasets_dir, dataset_id)
                                    if os.path.exists(metadata_dir):
                                        shutil.rmtree(metadata_dir)
                                        
                                    # Clear processing status
                                    if dataset_id in processing_status:
                                        del processing_status[dataset_id]
                                    if dataset_id in processing_output:
                                        del processing_output[dataset_id]
                                        
                            except Exception as e:
                                print(f"Error during periodic cleanup of {dataset_id}: {e}")
                
                # Sleep for 1 hour before next cleanup
                time.sleep(3600)
            except Exception as e:
                print(f"Error in periodic cleanup task: {e}")
                time.sleep(3600)  # Continue after error
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

if __name__ == '__main__':
    # Start periodic security cleanup (only in development)
    if os.environ.get('FLASK_ENV') == 'development':
        periodic_security_cleanup()
    app.run(debug=True, host='0.0.0.0', port=5001) 