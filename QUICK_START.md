# Quick Start Guide - Codebase Copilot

Get up and running in under 5 minutes! 🚀

## Prerequisites

- Docker Desktop installed and running
- OpenAI API key (optional - can use local embeddings)

## Setup (2 minutes)

```bash
# 1. Run the setup script
./setup.sh

# 2. Add your OpenAI API key (or skip for local mode)
nano backend/.env
# Set: OPENAI_API_KEY=sk-your-key-here
# Or: USE_LOCAL_EMBEDDINGS=true

# 3. Start everything
make dev
```

## First Steps

1. **Open the app**: http://localhost:3000

2. **Add a repository**:
   - Click "Add Repository"
   - Enter URL: `https://github.com/facebook/react`
   - Leave other fields default
   - Click "Add Repository"

3. **Wait for indexing**:
   - Watch the sidebar - status will show "indexing"
   - Small repos: ~30 seconds
   - Medium repos (React): ~2-3 minutes
   - Large repos: 5-10 minutes

4. **Start chatting**:
   - Click the repo in the sidebar
   - Ask: "How does the reconciler work?"
   - See answer with precise file+line citations

## Common Commands

```bash
# Start services
make dev

# Stop services
make stop

# View logs
make logs

# Run tests
make test

# Run linters
make lint

# Run evaluations
make eval

# Clean everything
make clean
```

## Configuration Options

### With OpenAI (Recommended)
```bash
# backend/.env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Without OpenAI (Local Mode)
```bash
# backend/.env
USE_LOCAL_EMBEDDINGS=true
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Performance Tuning
```bash
# Faster indexing (fewer chunks)
CHUNK_SIZE=600
CHUNK_OVERLAP=50

# Better accuracy (more granular)
CHUNK_SIZE=300
CHUNK_OVERLAP=100

# More context per query
TOP_K_RETRIEVAL=12
```

## Troubleshooting

### Docker not starting?
```bash
# Check Docker is running
docker info

# Clean and rebuild
make clean
docker compose up --build
```

### Backend not responding?
```bash
# Check health
curl http://localhost:8000/api/health

# Check logs
docker compose logs backend
```

### Indexing stuck?
```bash
# Check logs for errors
docker compose logs -f backend

# Restart backend
docker compose restart backend
```

### "Database is locked"?
This is normal under heavy load - the app retries automatically.

### API key not working?
```bash
# Verify it's set
docker compose exec backend env | grep OPENAI

# Restart to pick up changes
docker compose restart backend
```

## Example Queries

Once you've indexed a repository, try these:

**Architecture questions:**
- "How is the application structured?"
- "What design patterns are used?"
- "How does authentication work?"

**Implementation details:**
- "Where is the database connection configured?"
- "How are API routes defined?"
- "What testing framework is used?"

**Code search:**
- "Show me the JWT token validation logic"
- "Where is error handling implemented?"
- "How are websocket connections managed?"

**Best practices:**
- "What security measures are in place?"
- "How is logging configured?"
- "What's the deployment process?"

## File Structure

```
codebase-copilot/
├── backend/          # Python FastAPI server
│   ├── app/         # Main application code
│   ├── tests/       # Unit tests
│   ├── eval/        # Evaluation suite
│   └── .env         # Configuration
├── frontend/        # Next.js React app
│   └── src/         # Source code
├── docker-compose.yml
├── Makefile         # Common commands
└── README.md        # Full documentation
```

## Next Steps

1. **Read the full README**: [README.md](README.md)
2. **Check optimization details**: [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md)
3. **See changelog**: [CHANGELOG.md](CHANGELOG.md)
4. **Try the eval suite**: `make eval`

## Tips & Tricks

**For better results:**
- Use specific questions with keywords
- Reference file names or function names when possible
- Ask follow-up questions in the same conversation

**For faster indexing:**
- Start with smaller repos (~1000 files)
- Increase CHUNK_SIZE for fewer chunks
- Use local embeddings for offline work

**For cost savings:**
- Use local embeddings (free, but slower)
- Tune TOP_K_RETRIEVAL lower (fewer tokens)
- Clear old conversations regularly

## Getting Help

- **Docs**: See README.md for comprehensive guide
- **Troubleshooting**: Check OPTIMIZATION_REPORT.md
- **Issues**: Check Docker logs first
- **Performance**: See configuration options above

---

**Need more help?** Check the full [README.md](README.md) or [create an issue](https://github.com/your-repo/issues).

Happy coding! 🎉
