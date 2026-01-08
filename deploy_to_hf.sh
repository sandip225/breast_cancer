#!/bin/bash
# Quick deployment script for Hugging Face Spaces

set -e  # Exit on error

echo "🚀 Deploying to Hugging Face Spaces..."
echo ""

# Configuration
HF_SPACE_URL="https://huggingface.co/spaces/Bhavanakhatri/breastcancerdetection"
HF_SPACE_DIR="hf_space_deploy"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Step 1: Checking prerequisites...${NC}"

# Check Git LFS
if ! command -v git-lfs &> /dev/null; then
    echo -e "${RED}❌ Git LFS not installed!${NC}"
    echo "Install it from: https://git-lfs.github.com/"
    exit 1
fi
echo -e "${GREEN}✅ Git LFS installed${NC}"

# Check model file
MODEL_FILE="backend/models/breast_cancer_model.keras"
if [ ! -f "$MODEL_FILE" ]; then
    echo -e "${RED}❌ Model file not found: $MODEL_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Model file found${NC}"

echo ""
echo -e "${BLUE}📋 Step 2: Cloning HF Space...${NC}"

# Remove old directory if exists
rm -rf "$HF_SPACE_DIR"

# Clone HF Space
git clone "$HF_SPACE_URL" "$HF_SPACE_DIR"
cd "$HF_SPACE_DIR"

echo ""
echo -e "${BLUE}📋 Step 3: Setting up Git LFS...${NC}"

# Initialize Git LFS
git lfs install
git lfs track "*.keras"

echo ""
echo -e "${BLUE}📋 Step 4: Copying files...${NC}"

# Copy backend files
cp ../app.py .
cp ../requirements.txt .
cp ../README.md .
cp ../.gitignore .
cp ../.gitattributes .
cp ../Dockerfile . 2>/dev/null || true

# Copy model
cp "../$MODEL_FILE" breast_cancer_model.keras

echo -e "${GREEN}✅ Files copied${NC}"

# Check model size
MODEL_SIZE=$(du -h breast_cancer_model.keras | cut -f1)
echo "Model size: $MODEL_SIZE"

echo ""
echo -e "${BLUE}📋 Step 5: Committing changes...${NC}"

# Git add
git add .gitattributes
git add .gitignore
git add app.py
git add requirements.txt
git add README.md
git add Dockerfile 2>/dev/null || true
git add breast_cancer_model.keras

# Commit
git commit -m "Deploy backend-only API with FastAPI

- Clean FastAPI backend
- Production-ready code
- REST API endpoints
- Swagger UI documentation
- Model included via Git LFS"

echo ""
echo -e "${BLUE}📋 Step 6: Pushing to HF Space...${NC}"

# Push
git push origin main

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "🌐 Your API will be available at:"
echo "   https://bhavanakhatri-breastcancerdetection.hf.space"
echo ""
echo "📚 API Documentation:"
echo "   https://bhavanakhatri-breastcancerdetection.hf.space/"
echo ""
echo "⏱️  Wait 10-15 minutes for build to complete"
echo ""
echo "🧪 Test health endpoint:"
echo "   curl https://bhavanakhatri-breastcancerdetection.hf.space/health"
echo ""

