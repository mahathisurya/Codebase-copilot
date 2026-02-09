# Testing Guide - Validating Optimizations

This guide helps you validate that all optimizations are working correctly.

## 🚀 Quick Validation (5 minutes)

### 1. Setup Test
```bash
# Should complete without errors
./setup.sh

# Verify files created
ls -la backend/.env frontend/.env
```

✅ **Expected**: Both .env files exist

### 2. Docker Test
```bash
# Start services
make dev

# Wait 30 seconds, then check health
curl http://localhost:8000/api/health
```

✅ **Expected**: JSON with `"ok": true` and system info

### 3. Frontend Test
```bash
# Open in browser
open http://localhost:3000
```

✅ **Expected**: Clean UI loads, no console errors

### 4. Backend Test
```bash
# Check API docs
open http://localhost:8000/docs
```

✅ **Expected**: Swagger UI with all endpoints

---

## 🔬 Comprehensive Testing (15 minutes)

### Test 1: Repository Ingestion

```bash
# 1. Open http://localhost:3000
# 2. Click "Add Repository"
# 3. Enter: https://github.com/microsoft/TypeScript-Website
# 4. Click "Add Repository"
```

✅ **Expected Results:**
- Dialog closes
- Repository appears in sidebar
- Status shows "queued" → "indexing" → "ready"
- Chunk count increases in real-time
- No errors in logs: `docker compose logs -f backend`

**Performance Check:**
- Small repo (<100 files): ~30 seconds
- Medium repo (100-500 files): 1-2 minutes
- Large repo (500+ files): 3-5 minutes

### Test 2: Chat Functionality

```bash
# 1. Click the indexed repository
# 2. Type: "What is this project about?"
# 3. Press Enter
```

✅ **Expected Results:**
- Loading spinner appears
- Answer displays with markdown formatting
- Citations appear in right panel
- Each citation shows file path and line numbers
- Clicking citation opens code viewer
- No JavaScript errors in console

**Quality Check:**
- Answer is relevant to the repository
- Citations are accurate (check a few)
- Confidence level is shown (low/medium/high)
- Response time: 2-5 seconds

### Test 3: Multi-Repository Support

```bash
# 1. Add a second repository
# 2. Switch between repos in sidebar
# 3. Verify chat history is separate
# 4. Verify citations are separate
```

✅ **Expected Results:**
- Each repo maintains its own chat history
- Citations update when switching repos
- No cross-contamination of data
- State persists on page reload (localStorage)

### Test 4: Error Handling

```bash
# Test invalid repo URL
# 1. Add repository with URL: "https://github.com/nonexistent/repo123"
# 2. Watch status
```

✅ **Expected Results:**
- Status shows "error"
- Error message is displayed
- System remains stable
- Can add other repos successfully

```bash
# Test without API key (if using OpenAI)
# 1. Clear OPENAI_API_KEY in backend/.env
# 2. Restart: docker compose restart backend
# 3. Try to index a repo
```

✅ **Expected Results:**
- Falls back to local embeddings
- Warning logged but continues
- Or clear error if local embeddings not available

### Test 5: Re-ranking Quality

```bash
# 1. Index a code repository
# 2. Ask: "authentication middleware"
# 3. Check citations
```

✅ **Expected Results:**
- Citations include files with "auth" or "middleware"
- Top results are more relevant than bottom results
- Re-ranking log in backend: `docker compose logs backend | grep "re-rank"`

---

## 🎯 Performance Validation

### Test 1: Indexing Speed

```bash
# Before: ~100 chunks/sec
# After: ~300 chunks/sec

# Watch logs during indexing
docker compose logs -f backend | grep "chunks"
```

✅ **Expected**: Chunk creation rate is 200-400/sec

### Test 2: Database Performance

```bash
# Check batch insert time in logs
docker compose logs backend | grep "Saved.*chunks"
```

✅ **Expected**: "Saved 1000 chunks" takes <200ms

### Test 3: Memory Usage

```bash
# Check container memory
docker stats --no-stream
```

✅ **Expected**: 
- Backend: <2GB for medium repo
- Frontend: <100MB
- Total system: <2.5GB

### Test 4: Query Latency

```bash
# Time a query
time curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "YOUR_REPO_ID",
    "messages": [{"role": "user", "content": "test"}],
    "top_k": 8
  }'
```

✅ **Expected**: <5 seconds for typical query

---

## 🔍 Code Quality Validation

### Test 1: Linting

```bash
# Backend
docker compose exec backend ruff check app/ tests/

# Frontend
docker compose exec frontend npm run lint
```

✅ **Expected**: No errors (warnings OK)

### Test 2: Type Checking

```bash
# Backend
docker compose exec backend mypy app/ --ignore-missing-imports

# Frontend
docker compose exec frontend npm run type-check
```

✅ **Expected**: No type errors

### Test 3: Unit Tests

```bash
# Run all tests
make test
```

✅ **Expected**: All tests pass, >60% coverage

---

## 🔐 Security Validation

### Test 1: API Key Protection

```bash
# Check .env not in git
git ls-files | grep "\.env$"
```

✅ **Expected**: Empty (no output)

### Test 2: Path Traversal Protection

```bash
# Try to access parent directory
curl "http://localhost:8000/api/repos/test/file?path=../../../../etc/passwd"
```

✅ **Expected**: 403 Forbidden or 404 Not Found

### Test 3: Input Validation

```bash
# Try invalid input
curl -X POST http://localhost:8000/api/repos \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "not-a-url"}'
```

✅ **Expected**: 422 Unprocessable Entity with validation error

---

## 📊 Evaluation Suite

### Test 1: Run Evaluations

```bash
# First, ensure a repo is indexed and ready
# Then run eval suite
make eval
```

✅ **Expected Results:**
- Loads sample_eval.json
- Runs queries against indexed repo
- Shows metrics table:
  - Retrieval Precision@K: >0.70
  - Citation Precision: >0.80
  - Faithfulness: >0.75
  - Avg Latency: <3000ms
- Saves results to eval/runs/*.json

### Test 2: Custom Evaluation

```bash
# Create custom eval dataset
cat > backend/eval/custom_eval.json << 'EOF'
{
  "description": "Custom test",
  "questions": [
    {
      "question": "How is configuration loaded?",
      "expected_files": ["config.py", "settings.py"],
      "category": "configuration"
    }
  ]
}
EOF

# Run custom eval
docker compose exec backend python -m eval.run \
  --repo-id YOUR_REPO_ID \
  --dataset eval/custom_eval.json
```

✅ **Expected**: Runs and produces metrics

---

## 🐛 Bug Fix Validation

### Bug Fix 1: Store Methods

```bash
# Open browser console while chatting
# Check for errors
```

✅ **Expected**: No "undefined method" errors

### Bug Fix 2: Citations Display

```bash
# 1. Ask a question
# 2. Check right panel for citations
# 3. Click a citation
```

✅ **Expected**: Citations appear, modal opens

### Bug Fix 3: CORS

```bash
# Check different CORS formats work
# Edit backend/.env, try both:
# CORS_ORIGINS=["http://localhost:3000"]
# CORS_ORIGINS=http://localhost:3000

docker compose restart backend
```

✅ **Expected**: Both formats work

### Bug Fix 4: Database Locks

```bash
# Stress test with concurrent requests
for i in {1..10}; do
  curl -X GET http://localhost:8000/api/repos &
done
wait
```

✅ **Expected**: No "database is locked" errors

---

## 📈 Optimization Validation

### Check 1: Batch Inserts

```bash
# Check logs during indexing
docker compose logs backend | grep "Saved.*chunks"
```

✅ **Expected**: See "Saved N chunks" messages (not individual inserts)

### Check 2: WAL Mode

```bash
# Check database pragmas
docker compose exec backend python -c "
import sqlite3
conn = sqlite3.connect('./data/copilot.db')
print(conn.execute('PRAGMA journal_mode').fetchone())
print(conn.execute('PRAGMA synchronous').fetchone())
"
```

✅ **Expected**: journal_mode=wal, synchronous=1 or 2

### Check 3: Re-ranking

```bash
# Check logs for re-ranking
docker compose logs backend | grep "re-rank"
```

✅ **Expected**: See "Retrieved and re-ranked N chunks" messages

### Check 4: Progress Tracking

```bash
# Watch logs during indexing
docker compose logs -f backend | grep "Progress"
```

✅ **Expected**: See progress percentages and counters

---

## 🎓 Feature Testing

### Feature 1: Health Check

```bash
curl http://localhost:8000/api/health | jq
```

✅ **Expected Output:**
```json
{
  "ok": true,
  "service": "codebase-copilot",
  "version": "1.0.0",
  "database": "healthy",
  "repos_count": 1,
  "data_dir_exists": true,
  "repos_dir_exists": true,
  "faiss_dir_exists": true,
  "openai_configured": true,
  "local_embeddings_enabled": false
}
```

### Feature 2: Setup Script

```bash
# Clean environment
rm -f backend/.env frontend/.env

# Run setup
./setup.sh

# Check created files
ls -la backend/.env frontend/.env backend/data backend/repos
```

✅ **Expected**: All files and directories created

### Feature 3: Local Embeddings

```bash
# Enable local mode
# Edit backend/.env:
# USE_LOCAL_EMBEDDINGS=true
# OPENAI_API_KEY=

docker compose restart backend

# Index a small repo
```

✅ **Expected**: Works without OpenAI, uses sentence-transformers

---

## 📋 Checklist Summary

Use this checklist to validate everything:

### Setup & Configuration
- [ ] Setup script runs successfully
- [ ] Environment files created
- [ ] Docker containers start
- [ ] Health check returns healthy
- [ ] Frontend loads without errors
- [ ] API docs accessible

### Core Functionality
- [ ] Repository ingestion works
- [ ] Indexing completes successfully
- [ ] Progress tracking visible
- [ ] Chat interface works
- [ ] Citations display correctly
- [ ] Code viewer opens
- [ ] Multi-repo support works

### Performance
- [ ] Indexing speed: 200-400 chunks/sec
- [ ] Database inserts: <200ms/1000 chunks
- [ ] Query latency: <5 seconds
- [ ] Memory usage: <2GB backend
- [ ] Re-ranking logs visible

### Code Quality
- [ ] No linting errors
- [ ] No type errors
- [ ] All tests pass
- [ ] >60% coverage maintained

### Security
- [ ] No .env in git
- [ ] Path traversal blocked
- [ ] Input validation works
- [ ] API key not exposed

### Optimizations
- [ ] Batch inserts working
- [ ] WAL mode enabled
- [ ] Re-ranking active
- [ ] Progress tracking shown
- [ ] Error recovery works

### Documentation
- [ ] README clear and accurate
- [ ] QUICK_START works
- [ ] OPTIMIZATION_REPORT detailed
- [ ] CHANGELOG updated

---

## 🚨 Known Issues (Expected Behavior)

### Not Bugs

1. **"Database is locked" warning**: Normal under heavy load, retries automatically
2. **Indexing seems slow**: Large repos take time, check progress logs
3. **Local embeddings slower**: Expected, 2-3x slower than OpenAI
4. **High memory briefly**: Normal during embedding creation, drops after

### If Something Fails

```bash
# Clean slate
make clean
docker compose down -v
docker compose build --no-cache
docker compose up

# Check logs
docker compose logs backend
docker compose logs frontend

# Verify setup
curl http://localhost:8000/api/health
```

---

## ✅ All Tests Pass?

Congratulations! Your optimizations are working perfectly. 🎉

**Next steps:**
1. Use it for real work
2. Index your actual repositories
3. Share with team
4. Deploy to production (when ready)

**Need help?** Check:
- [QUICK_START.md](QUICK_START.md)
- [README.md](README.md)
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md)
