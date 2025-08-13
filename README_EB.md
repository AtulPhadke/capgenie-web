# CapGenie Web2 - AWS Elastic Beanstalk Deployment

This document provides instructions for deploying the CapGenie Web2 Flask application to AWS Elastic Beanstalk.

## Prerequisites

1. **AWS Account**: You need an active AWS account with appropriate permissions
2. **AWS CLI**: Install and configure AWS CLI
3. **EB CLI**: Install the Elastic Beanstalk Command Line Interface
4. **Python 3.11**: Ensure you have Python 3.11 installed locally

## Installation

### 1. Install EB CLI
```bash
pip install awsebcli
```

### 2. Configure AWS Credentials
```bash
aws configure
```

## Deployment

### Option 1: Using the Deployment Script (Recommended)
```bash
cd web2
./deploy.sh
```

### Option 2: Manual Deployment

1. **Initialize EB Application**:
   ```bash
   cd web2
   eb init capgenie-web2 --platform python-3.11 --region us-east-1
   ```

2. **Create Environment**:
   ```bash
   eb create capgenie-web2-env --instance-type t3.small --single-instance
   ```

3. **Deploy Updates**:
   ```bash
   eb deploy
   ```

## Configuration Files

### `.ebextensions/01_flask.config`
- Configures WSGI path and environment variables
- Sets up static file serving
- Configures instance type and environment type

### `.ebextensions/02_packages.config`
- Installs required system packages for data processing
- Includes development tools and libraries

### `.ebextensions/03_commands.config`
- Creates necessary directories on deployment
- Sets proper permissions for file uploads

### `application.py`
- WSGI entry point for Elastic Beanstalk
- Imports the Flask app from `app.py`

### `Procfile`
- Defines the web process using Gunicorn
- Binds to port 8000 (EB standard)

## Environment Variables

The following environment variables are automatically set:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`

## File Structure

```
web2/
├── .ebextensions/          # EB configuration files
├── static/                 # Static assets (CSS, JS, images)
├── templates/              # HTML templates
├── misc/                   # CSV files and other data
├── app.py                  # Main Flask application
├── application.py          # WSGI entry point
├── requirements.txt        # Python dependencies
├── Procfile               # Process definition
├── .ebignore              # Files to exclude from deployment
└── deploy.sh              # Deployment script
```

## Monitoring and Logs

### View Application Logs
```bash
eb logs
```

### Monitor Application Status
```bash
eb status
```

### Open Application in Browser
```bash
eb open
```

## Troubleshooting

### Common Issues

1. **Port Configuration**: The app runs on port 8000 in production (EB standard)
2. **File Permissions**: Ensure upload directories have proper permissions
3. **Memory Issues**: Consider upgrading to t3.medium if processing large datasets
4. **Timeout Issues**: Increase timeout settings for long-running processes

### Scaling Considerations

- **Single Instance**: Good for development and testing
- **Load Balancer**: Consider for production with multiple users
- **Auto Scaling**: Enable for handling variable load

## Security Notes

- Update `SECRET_KEY` in production
- Consider using AWS Secrets Manager for sensitive data
- Enable HTTPS in production
- Configure proper IAM roles and permissions

## Cost Optimization

- Use t3.small for development/testing
- Consider Spot Instances for cost savings
- Monitor usage and adjust instance types as needed
- Use S3 for file storage instead of instance storage for large files

## Support

For issues with the deployment:
1. Check EB logs: `eb logs`
2. Verify configuration files
3. Test locally before deploying
4. Review AWS EB documentation 