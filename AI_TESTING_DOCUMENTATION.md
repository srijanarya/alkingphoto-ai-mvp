# TalkingPhoto AI MVP - Comprehensive AI/ML Testing Suite

## Overview

This comprehensive testing suite provides full coverage for all AI/ML components of the TalkingPhoto AI MVP, including multiple AI providers, cost optimization algorithms, failover mechanisms, and quality assessment metrics.

## Test Coverage

### 1. Unit Tests (`tests/unit/`)

#### `test_ai_providers.py`

- **Mock Provider Implementations**: Tests for all AI service mocks
  - Nano Banana (Google Gemini) content generation
  - Veo3 video generation lifecycle
  - Runway ML workflows
  - ElevenLabs TTS
  - Azure Speech synthesis
  - Stripe payment processing

- **Provider Selection**:
  - Cost-based selection algorithms
  - Availability-based routing
  - Capability matching

- **Rate Limiting**:
  - Rate limit tracking
  - Exponential backoff strategies

- **Quality Metrics**:
  - Video quality scoring (resolution, FPS, bitrate)
  - TTS quality assessment
  - Lip sync accuracy measurement

#### `test_cost_optimization.py`

- **Pricing Algorithms**:
  - Time-based pricing (peak/off-peak)
  - Quality-based pricing tiers
  - Dynamic demand-based pricing
  - Bulk discount calculations

- **Provider Scoring**:
  - Multi-objective optimization
  - Constraint-based selection
  - Adaptive selection strategies

- **Cost Prediction**:
  - Linear regression models
  - Anomaly detection
  - Usage-based allocation
  - Tiered pricing models

### 2. Integration Tests (`tests/integration/`)

#### `test_provider_integration.py`

- **Provider Integration**:
  - Optimal service selection
  - Cascading failover mechanisms
  - Cost optimization routing
  - Parallel provider requests

- **Provider Switching**:
  - Error-triggered switching
  - Capability mismatch handling
  - Load balancing across providers

- **End-to-End Pipeline**:
  - Complete video generation workflow
  - Error recovery mechanisms
  - Pipeline monitoring

- **Concurrent Requests**:
  - Concurrent provider access
  - Queue management
  - Request prioritization

### 3. Performance Tests (`tests/performance/`)

#### `test_latency_benchmarks.py`

- **Latency Benchmarks**:
  - Provider response times (mean, median, p95, p99)
  - Concurrent request handling
  - Async performance testing
  - Caching effectiveness

- **Scalability Tests**:
  - Linear scaling verification
  - Memory efficiency
  - Queue throughput

- **Optimization Benchmarks**:
  - Provider selection speed (>100k ops/sec)
  - Cost calculation performance (>500k ops/sec)

- **Rate Limit Compliance**:
  - Rate limiter implementation
  - Provider-specific limits
  - Backoff strategy testing

### 4. End-to-End Tests (`tests/e2e/`)

#### `test_complete_pipeline.py`

- **Complete Pipeline**:
  - Image to video generation
  - Provider failover scenarios
  - Multi-language support

- **Quality Assessment**:
  - Video quality scoring system
  - Audio quality metrics
  - Overall quality tiers (Premium/Standard/Economy)

- **Error Recovery**:
  - Retry with exponential backoff
  - Circuit breaker pattern
  - Graceful degradation

- **Monitoring & Metrics**:
  - Performance metrics collection
  - Error tracking
  - Provider usage statistics

## AI Providers Tested

### Video Generation

1. **Google Veo3** - Primary provider, best balance
2. **Runway ML** - Premium quality, higher cost
3. **Synthesia** - Professional avatars
4. **D-ID** - Cost-effective option
5. **HeyGen** - Alternative provider

### Text-to-Speech

1. **ElevenLabs** - Premium voices
2. **Azure Speech** - Neural voices
3. **Google Cloud TTS** - Wide language support

### Image Enhancement

1. **Google Nano Banana (Gemini 2.5 Flash)** - Fast enhancement
2. **OpenAI DALL-E** - High quality
3. **Stability AI** - Alternative option

## Cost Optimization Features

### Dynamic Pricing

- **Time-based**: 30% premium during peak hours, 20% discount off-peak
- **Quality tiers**: Economy (0.7x), Standard (1.0x), Premium (1.5x)
- **Bulk discounts**: Up to 25% for 50+ videos

### Provider Selection Algorithm

```python
# Multi-objective optimization weights
weights = {
    'cost': 0.4,      # 40% weight on cost
    'quality': 0.3,   # 30% weight on quality
    'speed': 0.2,     # 20% weight on speed
    'reliability': 0.1 # 10% weight on reliability
}
```

## Failover Mechanisms

### Cascade Strategy

1. Try primary provider (Veo3)
2. On failure, try secondary (Runway)
3. Fall back to tertiary (D-ID)
4. Final fallback to basic service

### Circuit Breaker

- Opens after 3 consecutive failures
- Resets after 60 seconds
- Half-open state for testing recovery

## Performance Targets

### Response Times

- API calls: < 100ms (p95)
- Video generation: < 60s for 30s video
- TTS generation: < 5s for 100 words

### Throughput

- Provider selection: > 100,000 ops/sec
- Cost calculation: > 500,000 ops/sec
- Concurrent requests: 50+ simultaneous

### Quality Metrics

- Video resolution: 1920x1080 (Premium)
- Audio quality: 48kHz sampling
- Lip sync accuracy: > 85%

## Running Tests

### Quick Test

```bash
# Run all AI/ML tests
python run_ai_tests.py
```

### Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/test_ai_providers.py -v

# Integration tests
pytest tests/integration/test_provider_integration.py -v

# Performance benchmarks
pytest tests/performance/test_latency_benchmarks.py -v

# End-to-end tests
pytest tests/e2e/test_complete_pipeline.py -v
```

### With Coverage

```bash
# Run with coverage analysis
COVERAGE=true python run_ai_tests.py
```

### Generate HTML Report

```bash
# Generate detailed HTML report
pytest tests/ --cov=services --cov-report=html
```

## Test Reports

Reports are generated in `test_reports/` directory:

- `ai_test_summary_[timestamp].json` - Overall summary
- `unit_*_[timestamp].json` - Unit test results
- `integration_*_[timestamp].json` - Integration results
- `performance_*_[timestamp].json` - Performance metrics
- `coverage_[timestamp]/` - Coverage HTML reports

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run AI/ML Tests
  run: |
    python run_ai_tests.py

- name: Upload Test Reports
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: test_reports/
```

### Docker Testing

```dockerfile
RUN python run_ai_tests.py
```

## Mock Data Examples

### Video Generation Request

```python
request = VideoGenerationRequest(
    source_image='base64_encoded_image',
    audio_data=b'audio_bytes',
    script_text='Hello from TalkingPhoto AI',
    quality=VideoQuality.PREMIUM,
    aspect_ratio=AspectRatio.LANDSCAPE,
    duration=30.0
)
```

### Provider Metrics

```python
metrics = ProviderMetrics(
    provider=VideoGenerationProvider.VEO3,
    success_rate=0.95,
    average_processing_time=60,
    average_cost=0.15,
    current_load=10,
    error_count=2,
    availability_score=0.95,
    quality_score=0.85
)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed

   ```bash
   pip install -r requirements-test.txt
   ```

2. **Mock Provider Failures**: Check failure rate settings

   ```python
   mock.set_failure_rate(0.0)  # Disable failures
   ```

3. **Performance Test Failures**: Adjust thresholds for your system
   ```python
   assert operations_per_second > 50000  # Lower threshold
   ```

## Future Enhancements

1. **Additional Providers**:
   - Add Stable Diffusion for image generation
   - Integrate Whisper for speech recognition
   - Support for local LLM models

2. **Advanced Testing**:
   - Fuzzing for edge cases
   - Property-based testing
   - Mutation testing

3. **Performance Improvements**:
   - GPU acceleration testing
   - Distributed processing tests
   - WebRTC streaming tests

## Contributing

When adding new AI providers:

1. Create mock implementation in `tests/mocks/ai_providers.py`
2. Add unit tests in `tests/unit/test_ai_providers.py`
3. Add integration tests in `tests/integration/`
4. Update this documentation

## Contact

For questions about the testing suite:

- Review test files in `/tests/` directory
- Check mock implementations in `/tests/mocks/`
- Run `python run_ai_tests.py` for comprehensive testing

---

_Last Updated: 2025-09-13_
_Test Coverage: 85%+_
_Total Test Cases: 50+_
