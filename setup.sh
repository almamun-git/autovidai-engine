#!/bin/bash

# Automatic Video Generating AI Engine - Quick Setup Script
# This script helps you set up the project quickly

echo "🚀 Automatic Video Generating AI Engine - Quick Setup"
echo "======================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip3 install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file and add your API keys!"
    echo "   You can edit it by running: nano .env"
    echo ""
    echo "   Required API keys:"
    echo "   - GEMINI_API_KEY (https://makersuite.google.com/app/apikey)"
    echo "   - PEXELS_API_KEY (https://www.pexels.com/api/)"
    echo "   - ELEVENLABS_API_KEY (https://elevenlabs.io/)"
    echo "   - SHOTSTACK_API_KEY (https://dashboard.shotstack.io/register)"
else
    echo "✅ .env file exists"
fi
echo ""

# Create temp directory if it doesn't exist
if [ ! -d "temp" ]; then
    echo "📁 Creating temp directory..."
    mkdir temp
    echo "✅ Temp directory created"
else
    echo "✅ Temp directory already exists"
fi
echo ""

echo "=================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure your .env file has all API keys"
echo "2. Run the pipeline: python3 main.py"
echo ""
echo "To activate the virtual environment later:"
echo "  source venv/bin/activate"
echo ""
