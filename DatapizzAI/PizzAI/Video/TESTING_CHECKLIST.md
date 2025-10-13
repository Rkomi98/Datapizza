# Video Scripts Testing Checklist

## ✅ Completed Tasks

### 1. Video 3: Structured Responses and Multimodal
- ✅ Added audio media section (URL and base64)
- ✅ Updated timing (6.5 min → 8 min)
- ✅ Updated conclusion to mention audio
- ✅ Syntax validation: **7/7 code blocks passed**

### 2. Video 8: Complete RAG Implementation  
- ✅ Updated to match official RAG documentation
- ✅ Replaced manual steps with IngestionPipeline
- ✅ Rebuilt retrieval using DagPipeline
- ✅ Added proper VectorConfig usage
- ✅ Syntax validation: **5/5 code blocks passed**

### 3. Video 9: Pipelines and Production Monitoring
- ✅ Updated tracing import path
- ✅ Added rich console output examples
- ✅ Added environment variable documentation
- ✅ Updated OpenTelemetry integration
- ✅ Syntax validation: **7/7 code blocks passed**

## 🎉 Overall Status: **19/19 code blocks validated**

---

## 📋 Pre-Recording Checklist

### Environment Setup

```bash
# 1. Install datapizza-ai (from custom repository)
pip install datapizza-ai --index-url https://repository.datapizza.tech/repository/datapizza-pypi/simple

# 2. Install additional parsers for Video 8
pip install datapizza-ai-parsers-docling

# 3. Install OpenTelemetry for Video 9
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-zipkin-json

# 4. Set up environment variables
echo "OPENAI_API_KEY=your_key_here" > .env
```

### Services (for Video 8 & 9)

```bash
# Start Qdrant for Video 8
docker run -p 6333:6333 qdrant/qdrant

# Optional: Start Zipkin for Video 9
docker run -d -p 9411:9411 openzipkin/zipkin
```

### Quick Validation (No API Calls)

```bash
# Run syntax-only validation
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/Video
python validate_syntax_only.py
```

Expected output: ✅ All syntax checks passed!

### Full Testing (With API Calls)

```bash
# Test Video 3 (costs ~$0.05-0.10)
python test_video_03_structured_multimodal.py

# Test Video 8 (costs ~$0.03-0.05, requires Qdrant)
python test_video_08_rag_implementation.py

# Test Video 9 (costs ~$0.02-0.03)
python test_video_09_pipelines_monitoring.py
```

---

## 📁 Test Files Created

| File | Purpose |
|------|---------|
| `test_video_03_structured_multimodal.py` | Tests all Video 3 code with real API calls |
| `test_video_08_rag_implementation.py` | Tests all Video 8 RAG code with Qdrant |
| `test_video_09_pipelines_monitoring.py` | Tests all Video 9 pipeline/monitoring code |
| `validate_syntax_only.py` | Quick syntax check without API calls |
| `README_TESTS.md` | Comprehensive testing documentation |
| `CODE_REVIEW_SUMMARY.md` | Detailed review of all changes |
| `TESTING_CHECKLIST.md` | This file |

---

## 🎬 Before Recording Each Video

### Video 3: Structured Responses and Multimodal

**Preparation:**
- [ ] OPENAI_API_KEY is set
- [ ] Model supports vision/audio (gpt-4o or gpt-4-turbo)
- [ ] Test image file available (or use NASA URL)
- [ ] Test audio file available
- [ ] Run: `python test_video_03_structured_multimodal.py`

**Demo Files Needed:**
- Image: `Client/Example.png` or NASA URL (already in script)
- Audio: `session.wav` or create a test file

**Key Points to Show:**
1. JSON prompting (show how it can fail)
2. Pydantic models (show IDE autocomplete!)
3. Image analysis with NASA Mars lander
4. Audio transcription
5. Multi-turn conversation with image in memory

### Video 8: Complete RAG Implementation

**Preparation:**
- [ ] OPENAI_API_KEY is set
- [ ] Qdrant is running: `docker ps | grep qdrant`
- [ ] DoclingParser installed
- [ ] Sample PDF with good content ready
- [ ] Run: `python test_video_08_rag_implementation.py`

**Demo Files Needed:**
- PDF: `document.pdf` (choose something with interesting content)

**Key Points to Show:**
1. Qdrant dashboard at localhost:6333
2. IngestionPipeline processing the PDF
3. Chunks being stored (show in Qdrant UI)
4. DagPipeline flow (explain each connection)
5. Generated answer using retrieved context
6. Metadata filtering

### Video 9: Pipelines and Production Monitoring

**Preparation:**
- [ ] OPENAI_API_KEY is set
- [ ] datapizza-ai with tracing support
- [ ] OpenTelemetry packages installed
- [ ] (Optional) Zipkin running for export demo
- [ ] Run: `python test_video_09_pipelines_monitoring.py`

**Key Points to Show:**
1. Three pipeline types explained
2. ContextTracing with rich table output
3. Environment variable for detailed logging
4. Manual span creation
5. (Optional) Zipkin dashboard with traces

---

## ⚠️ Known Issues & Workarounds

### Video 3
**Issue**: NASA image URL might be slow or unavailable
**Workaround**: Have a local backup image ready

**Issue**: Audio models might be rate-limited
**Workaround**: Use smaller audio files or retry with backoff

### Video 8
**Issue**: Qdrant connection refused
**Workaround**: Ensure Docker is running and port 6333 is available

**Issue**: DoclingParser installation fails
**Workaround**: Check if running on supported OS, try alternative parser

**Issue**: PDF parsing is slow
**Workaround**: Use a smaller PDF for demo

### Video 9
**Issue**: Tracing output doesn't show rich table
**Workaround**: Ensure terminal supports rich formatting

**Issue**: Zipkin not receiving traces
**Workaround**: Check exporter configuration and Zipkin logs

---

## 💰 API Cost Estimates

| Video | Per Run | 3 Takes | Notes |
|-------|---------|---------|-------|
| Video 3 | $0.05-0.10 | $0.15-0.30 | Multimodal is expensive |
| Video 8 | $0.03-0.05 | $0.09-0.15 | Embedding + generation |
| Video 9 | $0.02-0.03 | $0.06-0.09 | Minimal calls |
| **Total** | **$0.10-0.18** | **$0.30-0.54** | Per complete set |

Budget for recording: ~$2-3 for 10 complete runs

---

## 📊 Validation Results

### Syntax Validation
```
Video 3: 7/7 code blocks ✓
Video 8: 5/5 code blocks ✓
Video 9: 7/7 code blocks ✓
Total: 19/19 code blocks ✓
```

### Full Test Results
Run the test scripts to get detailed results. Expected output format:
```
============================================================
TEST X: Description
============================================================
✓ Test passed
✗ Test failed: error message
⊘ Test skipped: missing prerequisite
⚠ Warning: non-critical issue
```

---

## 🚀 Quick Start

**Minimum viable testing:**
```bash
# 1. Quick syntax check (no dependencies)
python validate_syntax_only.py

# 2. If you have datapizza-ai installed, test Video 3
python test_video_03_structured_multimodal.py
```

**Full testing setup:**
```bash
# 1. Install everything
pip install datapizza-ai datapizza-ai-parsers-docling opentelemetry-api opentelemetry-sdk

# 2. Start services
docker run -p 6333:6333 qdrant/qdrant

# 3. Run all tests
python test_video_03_structured_multimodal.py
python test_video_08_rag_implementation.py
python test_video_09_pipelines_monitoring.py
```

---

## 📝 Notes

1. **Syntax validation passed** for all code blocks - no Python errors
2. **Full API tests** require proper environment setup
3. **All changes** match official datapizza-ai documentation
4. **Test scripts** provide detailed output for debugging
5. **Cost-aware**: Tests use minimal tokens where possible

---

## 🆘 If Something Goes Wrong

1. **Check syntax first**: Run `validate_syntax_only.py`
2. **Verify environment**: Check API keys, services running
3. **Read test output**: Error messages are descriptive
4. **Check documentation**: https://docs.datapizza.ai/
5. **Test incrementally**: Start with Video 3, then 8, then 9

---

**Last Updated**: October 13, 2025  
**Status**: ✅ Ready for recording preparation  
**Next Step**: Install dependencies and run full tests

