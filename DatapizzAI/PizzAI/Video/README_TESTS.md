# Video Scripts Test Suite

This directory contains test scripts to validate all code examples from the video series before recording.

## Test Files

### test_video_03_structured_multimodal.py
Tests all code from Video 3: Structured Responses and Multimodal Capabilities
- JSON prompting
- Pydantic structured responses
- Image processing (URL and base64)
- Audio processing (URL and base64)
- Multimodal memory conversations

### test_video_08_rag_implementation.py
Tests all code from Video 8: Complete RAG Implementation
- Client setup (OpenAI and embedder)
- Qdrant connection
- Collection creation
- Ingestion pipeline with DoclingParser
- DagPipeline retrieval
- Metadata filtering

### test_video_09_pipelines_monitoring.py
Tests all code from Video 9: Pipelines and Production Monitoring
- Pipeline types (Ingestion, Dag, Functional)
- Custom pipeline components
- ContextTracing integration
- OpenTelemetry setup
- Manual span creation
- Environment variable configuration

## Prerequisites

### General Requirements
```bash
# Install core dependencies
pip install datapizza-ai
pip install python-dotenv
pip install pydantic

# Set up environment variables
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Video 8 Specific Requirements
```bash
# Install Docling parser
pip install datapizza-ai-parsers-docling

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Video 9 Specific Requirements
```bash
# Install OpenTelemetry (if needed)
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-zipkin-json

# Optional: Start Zipkin for trace export testing
docker run -d -p 9411:9411 openzipkin/zipkin
```

## Running the Tests

### Test Individual Videos
```bash
# Test Video 3
python test_video_03_structured_multimodal.py

# Test Video 8 (make sure Qdrant is running)
python test_video_08_rag_implementation.py

# Test Video 9
python test_video_09_pipelines_monitoring.py
```

### Run All Tests
```bash
# Simple sequential run
python test_video_03_structured_multimodal.py
python test_video_08_rag_implementation.py
python test_video_09_pipelines_monitoring.py
```

## Test Output Interpretation

Each test produces output with these symbols:
- ✓ = Test passed
- ✗ = Test failed (check error message)
- ⊘ = Test skipped (missing prerequisites)
- ⚠ = Warning (non-critical issue)

## Common Issues and Solutions

### Video 3 Issues

**Issue**: "Media type not supported"
```
Solution: Make sure you're using a supported model (gpt-4o, gpt-4-turbo, etc.)
The model must support vision/audio capabilities.
```

**Issue**: Image/audio file not found
```
Solution: Update the file paths in the test script to point to valid media files.
Test images: Client/Example.png
Test audio: session.wav
```

### Video 8 Issues

**Issue**: "Connection refused to Qdrant"
```
Solution: Start Qdrant:
docker run -p 6333:6333 qdrant/qdrant
```

**Issue**: "DoclingParser not found"
```
Solution: Install the parser:
pip install datapizza-ai-parsers-docling
```

**Issue**: "No PDF found"
```
Solution: Place a sample PDF at:
/path/to/PizzAI/document.pdf
```

### Video 9 Issues

**Issue**: "ContextTracing not found"
```
Solution: Update datapizza-ai to the latest version:
pip install --upgrade datapizza-ai
```

**Issue**: "OpenTelemetry imports failed"
```
Solution: Install OpenTelemetry dependencies:
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-zipkin-json
```

## API Costs

Running these tests will make API calls. Approximate costs:
- Video 3: ~$0.05-0.10 (includes vision/audio processing)
- Video 8: ~$0.03-0.05 (embedding + generation)
- Video 9: ~$0.02-0.03 (basic generation)

Total: ~$0.10-0.20 per full test run

## What Gets Tested

### Import Validation
All scripts verify that imports work correctly before running tests.

### API Connectivity
Tests validate that API keys are present and functional.

### Code Syntax
All code examples are executed to catch syntax errors.

### Integration Points
Tests verify that components integrate correctly (e.g., Memory with multimodal, DAG connections).

### Error Handling
Tests catch and report errors with context.

## Before Recording Checklist

- [ ] All three test scripts run without ✗ errors
- [ ] Qdrant is running for Video 8
- [ ] Sample PDF is available for Video 8 ingestion demo
- [ ] Sample image is available for Video 3 demos
- [ ] Sample audio is available for Video 3 demos
- [ ] Environment variables are set (.env file configured)
- [ ] API keys have sufficient credits
- [ ] All dependencies are installed

## Notes

1. **Test Data**: The tests use real API calls. They will consume tokens and incur costs.

2. **Cleanup**: Video 8 tests clean up their test collection after running.

3. **Simplified Components**: Video 9 tests use simplified versions of custom components to focus on structure validation.

4. **Optional Features**: Some tests are marked as optional if they require additional services (like Zipkin).

5. **Continuous Updates**: As the datapizza-ai library evolves, these tests may need updates. Check the official documentation for the latest API changes.

## Support

If tests fail and you can't resolve the issue:
1. Check the official documentation: https://docs.datapizza.ai/
2. Review the error messages carefully
3. Ensure all prerequisites are met
4. Verify API keys and credentials
5. Check that external services (Qdrant, Zipkin) are running if required

## Version Information

These tests are designed for:
- datapizza-ai: 0.0.2+
- Python: 3.8+
- Qdrant: Latest Docker image
- OpenAI API: Current models (gpt-4o, gpt-4o-mini)

