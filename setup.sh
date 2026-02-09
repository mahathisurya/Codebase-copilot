#!/bin/bash
set -e

echo "🚀 Setting up Codebase Copilot..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Copy environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your OPENAI_API_KEY"
else
    echo "✅ backend/.env already exists"
fi

if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend/.env from template..."
    cp frontend/.env.example frontend/.env
else
    echo "✅ frontend/.env already exists"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p backend/data
mkdir -p backend/repos
mkdir -p backend/eval/runs

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your OPENAI_API_KEY (or set USE_LOCAL_EMBEDDINGS=true)"
echo "2. Run: make dev"
echo "3. Visit http://localhost:3000"
echo ""
echo "For more information, see README.md"
