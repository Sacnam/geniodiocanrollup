"""
OpenAPI Schema Configuration
Generates comprehensive API documentation.
"""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with examples."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Genio Knowledge OS API",
        version="3.0.0",
        description="""
# Genio Knowledge OS

AI-powered knowledge management platform with three integrated modules:

## Modules

### 1. Stream (v1.0) - Feed Aggregator
- RSS/Atom feed aggregation with adaptive scheduling
- AI-powered content summarization
- Knowledge Delta scoring for novelty detection
- Daily Brief generation and delivery

### 2. Library (v2.0) - Document Management
- Multi-format document ingestion (EPUB, PDF, DOCX, HTML, MD)
- Personal Knowledge Graph (PKG) construction
- Semantic chunking and GraphRAG
- Interactive Concept Map visualization

### 3. Lab (v3.0) - Research Automation
- Scout Agents for proactive research
- Multi-source monitoring (feeds, documents, web, arXiv)
- Cross-document reasoning with PKG context
- Automated insight generation

## Authentication
All endpoints require JWT Bearer token authentication.

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limits
- Authenticated: 100 requests/minute
- Unauthenticated: 20 requests/minute

## Cost Optimization
All AI operations use 1536-dim embeddings (80% cheaper than 3072-dim).
Target cost: <$4/user/month.
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login or /auth/register"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add tags with descriptions
    openapi_schema["tags"] = [
        {
            "name": "auth",
            "description": "Authentication endpoints"
        },
        {
            "name": "feeds",
            "description": "RSS/Atom feed management"
        },
        {
            "name": "articles",
            "description": "Article reading with Knowledge Delta scoring"
        },
        {
            "name": "briefs",
            "description": "Daily Brief generation and preferences"
        },
        {
            "name": "billing",
            "description": "Subscription and billing management"
        },
        {
            "name": "documents",
            "description": "Document upload and management (Library module)"
        },
        {
            "name": "library-advanced",
            "description": "Advanced Library features: GraphRAG, PKG, Concept Maps"
        },
        {
            "name": "scouts",
            "description": "Scout Agents for automated research (Lab module)"
        }
    ]
    
    # Add examples to schemas
    if "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]
        
        # Article example
        if "ArticleResponse" in schemas:
            schemas["ArticleResponse"]["example"] = {
                "id": "article-123",
                "title": "The Future of AI",
                "url": "https://example.com/article",
                "delta_score": 0.85,
                "is_read": False,
                "global_summary": "AI is transforming industries..."
            }
        
        # Scout example
        if "ScoutResponse" in schemas:
            schemas["ScoutResponse"]["example"] = {
                "id": "scout-456",
                "name": "AI Research Monitor",
                "research_question": "What are the latest developments in AI safety?",
                "keywords": ["AI safety", "alignment", "governance"],
                "sources": ["feeds", "arxiv"],
                "status": "idle",
                "total_findings": 42
            }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def generate_openapi_json(app: FastAPI, output_path: str = "openapi.json"):
    """Generate OpenAPI JSON file for external documentation."""
    import json
    
    schema = custom_openapi(app)
    
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    return output_path
