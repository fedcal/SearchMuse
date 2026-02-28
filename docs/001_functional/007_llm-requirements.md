# SearchMuse LLM Requirements

## Overview

SearchMuse uses local language models via Ollama to handle intelligent tasks without sending data to external services. This document covers model selection, installation, configuration, and optimization.

## Ollama Installation

### Prerequisites
- Docker or native installation support
- For GPU acceleration: NVIDIA CUDA toolkit (optional but recommended)
- 8GB RAM minimum (16GB recommended)

### Installation Steps

#### Option 1: Docker (Recommended)
```bash
# Pull Ollama image
docker pull ollama/ollama

# Run Ollama service
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  ollama/ollama

# Pull a model (see model selection below)
docker exec ollama ollama pull mistral
```

#### Option 2: Native Installation
```bash
# macOS
brew install ollama

# Ubuntu/Linux
curl https://ollama.ai/install.sh | sh

# Windows
# Download installer from https://ollama.ai

# Start service
ollama serve
```

### Verify Installation
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Response example:
# {"models":[{"name":"mistral:latest","size":4109298059}]}
```

---

## Recommended Models

### Model 1: Mistral (Default - Recommended for Most Users)

**Model ID**: `mistral`
**Size**: 7.3B parameters
**Recommended For**: Production use, balanced speed and quality

**Strengths**:
- Fast inference (2-5 tokens/second)
- Good reasoning and code understanding
- Excellent English fluency
- Low resource requirements
- Great cost-performance ratio

**Requirements**:
- RAM: 8GB minimum, 16GB recommended
- Storage: 5GB
- GPU: Optional (4GB VRAM if available)
- Inference time: 2-5 seconds per task

**Installation**:
```bash
ollama pull mistral
```

**Configuration**:
```yaml
llm:
  model: mistral
  parameters:
    temperature: 0.7
    top_p: 0.9
    top_k: 40
```

**Best For**:
- General research queries
- First-time users
- Resource-constrained environments
- Production deployments

---

### Model 2: Llama 3 (Large - Better Reasoning)

**Model ID**: `llama3` or `llama3:70b`
**Size**: 8B or 70B parameters
**Recommended For**: Complex analysis, deep reasoning required

**Strengths**:
- Superior reasoning capabilities
- Better handling of complex queries
- Excellent instruction following
- Strong performance on nuanced tasks
- Large context window (8K tokens)

**Requirements**:
- RAM: 16GB minimum, 32GB recommended
- Storage: 7GB (8B) or 40GB (70B)
- GPU: Strongly recommended (8GB+ VRAM)
- Inference time: 3-8 seconds per task

**Installation**:
```bash
# 8B version (7GB)
ollama pull llama3

# 70B version (40GB, requires powerful GPU)
ollama pull llama3:70b
```

**Configuration**:
```yaml
llm:
  model: llama3
  parameters:
    temperature: 0.5
    top_p: 0.95
    num_ctx: 8192
```

**Best For**:
- Complex research topics
- Multi-document synthesis
- Detailed gap analysis
- Academic research

---

### Model 3: Phi 3 (Lightweight - Fastest)

**Model ID**: `phi3` or `phi3.5`
**Size**: 3.8B parameters
**Recommended For**: Fast iteration, resource-limited systems

**Strengths**:
- Very fast inference (5-10 tokens/second)
- Minimal resource usage
- Good quality for size
- Excellent for constrained environments
- Can run on older hardware

**Requirements**:
- RAM: 4GB minimum, 8GB recommended
- Storage: 2.5GB
- GPU: Optional
- Inference time: 1-2 seconds per task

**Installation**:
```bash
ollama pull phi3
```

**Configuration**:
```yaml
llm:
  model: phi3
  parameters:
    temperature: 0.7
    top_p: 0.9
```

**Best For**:
- Quick fact-finding
- Simple queries
- Laptops and budget systems
- Real-time interactive use

---

## Hardware Requirements by Model

| Model | Model Size | RAM | Storage | GPU | Speed |
|-------|-----------|-----|---------|-----|-------|
| phi3 | 3.8B | 4GB | 2.5GB | None | 5-10 t/s |
| mistral | 7.3B | 8GB | 5GB | Optional | 2-5 t/s |
| llama3 | 8B | 16GB | 7GB | 8GB | 3-8 t/s |
| llama3 | 70B | 32GB+ | 40GB | 24GB+ | 1-3 t/s |

### GPU Acceleration

GPU acceleration significantly improves performance:

```yaml
llm:
  use_gpu: true
  gpu_layers: "all"  # Offload all layers to GPU
  main_gpu: 0        # Which GPU to use (0 = first)
```

**Speedup by GPU**:
- NVIDIA RTX 3080 (10GB): 3-5x speedup
- NVIDIA RTX 4090 (24GB): 5-10x speedup
- Apple M1/M2 (GPU): 2-3x speedup

---

## Temperature and Parameters

Temperature controls output creativity and randomness.

### Temperature Settings by Task

#### Strategy Generation (temperature: 0.7)
Creative exploration of search strategies. Medium randomness encourages diverse approaches.

```yaml
strategy_generation:
  temperature: 0.7
  top_p: 0.9
  top_k: 40
```

Example prompt:
```
Generate diverse search strategies for: "machine learning interpretability"
Include unconventional approaches.
```

#### Relevance Assessment (temperature: 0.3)
Deterministic evaluation of source relevance. Low temperature ensures consistent scoring.

```yaml
relevance_assessment:
  temperature: 0.3
  top_p: 0.95
  top_k: 100
```

Example prompt:
```
Score this source's relevance to the query on 0.0-1.0 scale.
Be strict and consistent.
```

#### Coverage Assessment (temperature: 0.2)
Strict evaluation of research completeness. Very low temperature for consistency.

```yaml
coverage_assessment:
  temperature: 0.2
  top_p: 0.95
  top_k: 100
```

#### Result Synthesis (temperature: 0.5)
Balance between creativity and consistency. Moderate temperature for readable prose.

```yaml
result_synthesis:
  temperature: 0.5
  top_p: 0.9
  top_k: 50
```

---

## Prompt Templates

### Strategy Generation Prompt

```
You are a research strategy expert. Given a query, generate an optimal search strategy.

Query: "{query}"

{history}

Generate a JSON response with:
{
  "search_terms": ["term1", "term2", ...],
  "domain_preferences": ["site:github.com", "-site:pinterest.com", ...],
  "rationale": "Why this strategy..."
}

Be specific and actionable.
```

### Relevance Assessment Prompt

```
Assess source relevance to the query.

Query: "{query}"

Source Title: "{title}"
Source Content (first 500 words):
{content}

On a 0.0-1.0 scale, rate relevance. Consider:
- Direct answer to query
- Authority and expertise
- Recency (for time-sensitive topics)
- Clarity and comprehensiveness

Return JSON:
{
  "relevance_score": 0.X,
  "explanation": "..."
}

Be strict. Score <= 0.4 for tangentially related content.
```

### Coverage Assessment Prompt

```
Assess research coverage completeness.

Original Query: "{query}"

Retrieved {num_sources} sources:
{sources_summary}

Evaluate coverage (0.0-1.0). Consider:
- All major subtopics addressed
- Diverse perspectives included
- Sufficient depth per topic
- Currency of sources

Identify gaps:
{
  "coverage_score": 0.X,
  "gaps": ["gap1", "gap2", ...],
  "confidence": 0.X
}

Be critical. 0.7 = adequate, 0.9+ = comprehensive.
```

### Result Synthesis Prompt

```
Synthesize research into a coherent answer.

Query: "{query}"

Sources (with content):
{all_sources}

Generate a comprehensive answer that:
1. Directly addresses the query
2. Uses information from multiple sources
3. Cites sources as [1], [2], etc.
4. Flows naturally and logically
5. Includes specific examples and data

Format as markdown with inline citations.
```

---

## Custom Model Configuration

### Use a Different Model

To use a model other than the defaults:

1. **Pull the model**:
```bash
ollama pull neural-chat  # or any other model
```

2. **Update configuration**:
```yaml
llm:
  model: neural-chat
  base_url: http://localhost:11434
  timeout: 60
```

3. **Test the model**:
```bash
# Verify model is available
ollama list

# Manual test
curl http://localhost:11434/api/generate \
  -d '{
    "model": "neural-chat",
    "prompt": "Hello!",
    "stream": false
  }'
```

### Available Models on Ollama Library

```
Mistral family:
  - mistral (7B, recommended)
  - mistral-medium
  - neural-chat (fine-tuned mistral)

Llama family:
  - llama3 (8B and 70B)
  - llama2 (7B, 13B, 70B)
  - llama2-uncensored

Other popular:
  - dolphin-mixtral
  - neural-chat
  - zephyr
  - orca-mini
  - solar
```

Full list: https://ollama.ai/library

---

## Fine-Tuning (Advanced)

For specialized use cases, fine-tune a model:

```bash
# Create training data in JSONL format
# {"prompt": "...", "response": "..."}

# Fine-tune using Ollama extensions
# (Requires additional setup)
ollama create custom-model --context models/base --train data.jsonl
```

Fine-tuning is optional and advanced. Start with base models.

---

## Performance Optimization

### Batch Processing

Process multiple requests efficiently:

```python
def process_batch(queries: List[str]) -> List[str]:
    """Process multiple queries in parallel."""

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(llm.generate, query)
            for query in queries
        ]
        return [f.result() for f in futures]
```

### Caching Responses

Reuse LLM responses for identical inputs:

```yaml
llm:
  cache:
    enabled: true
    ttl: 3600  # seconds
    backend: sqlite  # or redis
```

### Streaming Responses

For interactive use, stream token-by-token:

```python
def generate_streaming(prompt: str):
    for token in llm.generate_stream(prompt):
        yield token
        print(token, end="", flush=True)
```

---

## Troubleshooting

### Model Not Responding

```bash
# Check if Ollama service is running
curl http://localhost:11434/api/tags

# If fails, restart Ollama
ollama serve

# Verify model is installed
ollama list
```

### Out of Memory

```bash
# Use smaller model
ollama pull mistral  # instead of llama3

# Reduce batch size
llm:
  batch_size: 1

# Reduce context size
llm:
  context_size: 2048  # instead of 8192
```

### Slow Performance

```bash
# Enable GPU acceleration
llm:
  use_gpu: true

# Use faster model
ollama pull phi3  # instead of mistral

# Reduce precision
llm:
  quantization: q4  # instead of q8
```

---

## Monitoring and Logging

```yaml
logging:
  llm_requests: true
  log_level: INFO
  log_file: logs/llm.log

monitoring:
  track_latency: true
  track_token_usage: true
  track_memory: true
```

View logs:
```bash
tail -f logs/llm.log | grep "strategy_generation"
```

---

## Configuration Template

```yaml
# searchmuse_config.yaml
llm:
  # Model selection
  provider: ollama
  model: mistral  # or llama3, phi3
  base_url: http://localhost:11434

  # Connection
  timeout: 60
  max_retries: 3
  retry_delay: 1

  # Performance
  use_gpu: true
  gpu_layers: all
  batch_size: 1

  # Temperature by task
  temperatures:
    strategy: 0.7
    relevance: 0.3
    coverage: 0.2
    synthesis: 0.5

  # Caching
  cache:
    enabled: true
    backend: sqlite
    ttl: 3600

  # Logging
  logging:
    enabled: true
    level: INFO
```

Use this configuration to customize SearchMuse for your environment.
