#!/bin/bash
#
# Genio Knowledge OS - Complete App Setup Script
# Run this script to set up the full enterprise application
#

set -e

echo "🚀 Genio Knowledge OS - Complete Setup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Start infrastructure
echo "🐳 Starting infrastructure services..."
docker-compose up -d postgres redis qdrant elasticsearch

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check PostgreSQL
until docker-compose exec -T postgres pg_isready -U genio; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL ready${NC}"

# Check Elasticsearch
until curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green"\|"status":"yellow"'; do
    echo "Waiting for Elasticsearch..."
    sleep 2
done
echo -e "${GREEN}✓ Elasticsearch ready${NC}"

echo ""
echo "🗄️  Running database migrations..."
cd backend

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Run migrations
echo "Upgrading database to latest version..."
alembic upgrade head

echo -e "${GREEN}✓ Migrations complete${NC}"
echo ""

# Verify tables
echo "🔍 Verifying database schema..."
python3 << 'EOF'
import psycopg2
import sys

required_tables = [
    'users', 'feeds', 'articles', 'user_article_context',
    'tags', 'article_tags', 'document_tags',
    'saved_views', 'comments', 'comment_likes',
    'keyboard_shortcuts', 'analytics_snapshots',
    'brief_templates', 'share_links', 'teams', 'team_members',
    'two_factor_auth', 'webauthn_credentials', 'sso_connections',
    'plugins', 'user_plugins'
]

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='genio',
    user='genio',
    password='genio_password'
)

cur = conn.cursor()
missing = []

for table in required_tables:
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table,))
    exists = cur.fetchone()[0]
    if not exists:
        missing.append(table)
    else:
        print(f"  ✓ {table}")

cur.close()
conn.close()

if missing:
    print(f"\n❌ Missing tables: {', '.join(missing)}")
    sys.exit(1)
else:
    print(f"\n✓ All {len(required_tables)} tables verified")
EOF

echo ""
echo "📦 Building application containers..."
cd ..
docker-compose build

echo ""
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo "🌐 Access the application:"
echo "   • Frontend: http://localhost"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Elasticsearch: http://localhost:9200"
echo ""
echo "🚀 To start the full application:"
echo "   docker-compose up -d"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "⚠️  Remember to set your environment variables:"
echo "   - OPENAI_API_KEY"
echo "   - GEMINI_API_KEY"
echo "   - SENDGRID_API_KEY (for email)"
echo ""
