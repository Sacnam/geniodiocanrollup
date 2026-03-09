#!/bin/bash
# Production Deployment Script (T072)
# Genio Knowledge OS - Full Stack Deployment

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPO_API="genio-api"
ECR_REPO_FRONTEND="genio-frontend"
ECS_CLUSTER="genio-production"
ECS_SERVICE_API="genio-api-service"
ECS_SERVICE_WORKER="genio-worker-service"
ECS_SERVICE_FRONTEND="genio-frontend-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Genio Knowledge OS - Production Deployment ===${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI required${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker required${NC}"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${YELLOW}Terraform not found - infrastructure must be pre-created${NC}"; }

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Step 1: Run tests
echo -e "${YELLOW}Step 1: Running tests...${NC}"
cd ../backend
python -m pytest tests/ -v --tb=short || { echo -e "${RED}Tests failed${NC}"; exit 1; }
cd ../frontend
npm run test -- --watchAll=false || { echo -e "${RED}Frontend tests failed${NC}"; exit 1; }
cd ../deploy
echo -e "${GREEN}✓ Tests passed${NC}"
echo ""

# Step 2: Security scan
echo -e "${YELLOW}Step 2: Security scan...${NC}"
cd ../backend
# Check for secrets
if grep -r "sk-" --include="*.py" . 2>/dev/null | grep -v ".pyc"; then
    echo -e "${RED}WARNING: Potential secrets found in code${NC}"
    exit 1
fi
# Dependency audit
pip-audit || echo -e "${YELLOW}pip-audit warnings${NC}"
cd ../deploy
echo -e "${GREEN}✓ Security scan complete${NC}"
echo ""

# Step 3: Database migration check
echo -e "${YELLOW}Step 3: Checking database migrations...${NC}"
cd ../backend
alembic check || { echo -e "${RED}Migration check failed${NC}"; exit 1; }
cd ../deploy
echo -e "${GREEN}✓ Migrations ready${NC}"
echo ""

# Step 4: Build and push Docker images
echo -e "${YELLOW}Step 4: Building Docker images...${NC}"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# Build API
echo "Building API image..."
cd ../backend
docker build -t $ECR_REPO_API:latest .
docker tag $ECR_REPO_API:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_API:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_API:latest

# Build Frontend
echo "Building Frontend image..."
cd ../frontend
docker build -t $ECR_REPO_FRONTEND:latest .
docker tag $ECR_REPO_FRONTEND:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_FRONTEND:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_FRONTEND:latest

cd ../deploy
echo -e "${GREEN}✓ Images built and pushed${NC}"
echo ""

# Step 5: Deploy to ECS
echo -e "${YELLOW}Step 5: Deploying to ECS...${NC}"

# Force new deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE_API --force-new-deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE_WORKER --force-new-deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE_FRONTEND --force-new-deployment

echo -e "${GREEN}✓ ECS deployment initiated${NC}"
echo ""

# Step 6: Wait for deployment
echo -e "${YELLOW}Step 6: Waiting for deployment to stabilize...${NC}"
sleep 30

# Check service status
aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE_API $ECS_SERVICE_WORKER $ECS_SERVICE_FRONTEND

echo -e "${GREEN}✓ Deployment stable${NC}"
echo ""

# Step 7: Health checks
echo -e "${YELLOW}Step 7: Running health checks...${NC}"

# Get load balancer DNS
LB_DNS=$(aws elbv2 describe-load-balancers --names "genio-production" --query 'LoadBalancers[0].DNSName' --output text)

# Health check
for i in {1..5}; do
    if curl -sf "http://$LB_DNS/health" > /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        break
    fi
    if [ $i -eq 5 ]; then
        echo -e "${RED}✗ Health check failed${NC}"
        exit 1
    fi
    sleep 10
done

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Application URLs:"
echo "  - API: http://$LB_DNS"
echo "  - Health: http://$LB_DNS/health"
echo "  - Metrics: http://$LB_DNS/metrics"
echo ""
echo "Run the following to check logs:"
echo "  aws logs tail /ecs/genio-api --follow"
