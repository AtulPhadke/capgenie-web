#!/bin/bash

# CapGenie Web2 Elastic Beanstalk Deployment Script

echo "🚀 Starting CapGenie Web2 deployment to AWS Elastic Beanstalk..."

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI not found. Please install it first:"
    echo "   pip install awsebcli"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from the web2 directory."
    exit 1
fi

# Initialize EB application if not already done
if [ ! -d ".elasticbeanstalk" ]; then
    echo "📝 Initializing Elastic Beanstalk application..."
    eb init capgenie-web2 --platform python-3.11 --region us-east-1
fi

# Create environment if it doesn't exist
if ! eb status &> /dev/null; then
    echo "🌍 Creating Elastic Beanstalk environment..."
    eb create capgenie-web2-env --instance-type t3.small --single-instance
else
    echo "🔄 Deploying to existing environment..."
    eb deploy
fi

echo "✅ Deployment completed!"
echo "🌐 Your application should be available at:"
eb status | grep CNAME 