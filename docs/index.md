# Transaction AI - Intelligent Financial Categorization

Welcome to the **Transaction AI** documentation! This system provides enterprise-grade financial transaction categorization with 98.7% accuracy, complete privacy, and full transparency.

## What is Transaction AI?

Transaction AI is an open-source, privacy-first system that automatically categorizes financial transactions using a novel ensemble approach combining:

- **MCC (Merchant Category Codes)** - Industry-standard merchant classification
- **Rule-based matching** - Pattern recognition and keyword matching
- **Machine Learning** - SetFit embedding-based classification
- **LLM fallback** - Llama 3.1 for ambiguous cases

## Key Features

### 🔒 Privacy First
- **100% on-premise** - No external API calls
- **Zero data sharing** - All processing happens locally
- **GDPR compliant** - Full data sovereignty

### 🎯 High Accuracy
- **98.7% overall accuracy** across all categories
- **85% auto-accept rate** - Minimal manual review needed
- **Ensemble voting** - Multiple methods for reliability

### 💡 Transparent & Explainable
- **Full decision transparency** - See why each prediction was made
- **5-level explainability** - From simple to detailed explanations
- **Open-source code** - Complete transparency (MIT License)

### ⚡ Production Ready
- **Docker deployment** - Quick setup with docker-compose
- **RESTful API** - Easy integration
- **Real-time processing** - <100ms response time
- **Monitoring included** - Prometheus & Grafana dashboards

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Rahul1269227/transaction-ai.git
cd transaction-ai

# Start the system
docker-compose up -d

# Test the API
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "STARBUCKS COFFEE $4.50"}'
```

## Use Cases

- **Personal Finance** - Automatic expense tracking and budgeting
- **SMB Accounting** - Automated bookkeeping for small businesses
- **Banking Apps** - Transaction categorization for mobile banking
- **Tax Preparation** - Categorize transactions for tax filing
- **Research** - Financial behavior analysis and economic research

## Why Choose Transaction AI?

| Feature | Transaction AI | Commercial APIs |
|---------|---------------|-----------------|
| **Cost** | Free (self-hosted) | $24K-300K/year |
| **Privacy** | 100% on-premise | Data sent to cloud |
| **Accuracy** | 98.7% | 85-95% |
| **Customization** | Full control | Limited |
| **Transparency** | Open-source | Black box |
| **Rate Limits** | Unlimited | 100-1K req/min |

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                  TRANSACTION INPUT                        │
│              "STARBUCKS COFFEE $4.50"                     │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│               ENSEMBLE CATEGORIZER                        │
│  ┌───────────┬────────────┬──────────┬────────────┐     │
│  │   MCC     │   Rules    │    ML    │    LLM     │     │
│  │ Lookup    │  Matching  │ SetFit   │  Llama 3.1 │     │
│  │  95%      │    90%     │   88%    │   (skip)   │     │
│  └─────┬─────┴──────┬─────┴─────┬────┴──────┬─────┘     │
│        │            │           │           │           │
│        └────────────┴───────────┴───────────┘           │
│                      │                                   │
│              ENSEMBLE VOTING                             │
│          (Unanimous: 3/3 agree)                         │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│                  FINAL PREDICTION                         │
│  Category: food_dining                                    │
│  Confidence: 95%                                          │
│  Method: ensemble_unanimous                               │
│  Requires Review: false                                   │
└──────────────────────────────────────────────────────────┘
```

## Documentation Structure

This documentation is organized into three main sections:

### 📚 Core Documentation
Foundational information about the system architecture, data strategy, and responsible AI practices.

### 🚀 Innovation & Features
Details about novel technical approaches, explainability, continuous learning, and bias mitigation.

### 📊 Impact & Metrics
Business impact, scalability metrics, evaluation results, and broader societal impact.

## Community & Support

- **GitHub**: [Rahul1269227/transaction-ai](https://github.com/Rahul1269227/transaction-ai)
- **Discussions**: [Community Forum](https://github.com/Rahul1269227/transaction-ai/discussions)
- **Issues**: [Bug Reports & Features](https://github.com/Rahul1269227/transaction-ai/issues)

## License

Transaction AI is released under the [MIT License](https://github.com/Rahul1269227/transaction-ai/blob/main/LICENSE), enabling anyone - from solo developers to Fortune 500 companies - to deploy enterprise-grade AI without vendor lock-in or prohibitive costs.

## Next Steps

- Read the [Problem Understanding & Objectives](1.1_Problem_Understanding_and_Objectives.md)
- Explore the [Technical Architecture](1.2_Technical_Architecture_and_Design_Approach.md)
- Check out the [Benchmarks](BENCHMARKS.md)
- Review the [API Documentation](https://github.com/Rahul1269227/transaction-ai#api-documentation)
