# Multi-Tenant AI Voice Appointment Bot

## DID-Based Intelligent Voice Assistant with Amazon Bedrock Agents

**Technology Stack:**
- **Telephony:** FreeSWITCH + mod_audio_stream
- **Speech-to-Text:** Amazon Transcribe Streaming
- **Text-to-Speech:** Amazon Polly
- **AI Orchestration:** Amazon Bedrock Agents
- **Foundation Model:** Anthropic Claude 3 Haiku (or Amazon Nova)
- **Action Groups:** AWS Lambda (Python)
- **Infrastructure:** AWS CDK (TypeScript) + Docker Compose (local services)

**Scope:** Real-time call path with fully managed AI agent orchestration

## Project Goal

Build a production-quality AI voice receptionist demonstrating AWS-native AI orchestration:

### Core Capabilities

| Capability | AWS Service |
|------------|-------------|
| **Speech Recognition** | Amazon Transcribe Streaming |
| **AI Orchestration** | Amazon Bedrock Agents |
| **Foundation Model** | Claude 3 Haiku / Amazon Nova Lite |
| **Tool Execution** | AWS Lambda (Action Groups) |
| **Voice Synthesis** | Amazon Polly |
| **Telephony** | FreeSWITCH |

### Why Bedrock Agents?

| Feature | Benefit |
|---------|---------|
| **Fully Managed** | No orchestration code to maintain |
| **Native Tool Calling** | Action Groups with OpenAPI schemas |
| **Session Memory** | Built-in conversation state management |
| **Guardrails** | Content filtering and PII redaction |
| **Observability** | CloudWatch integration out of the box |
| **Multi-turn** | Handles complex conversation flows automatically |

## Quick Start

1. **Prerequisites**
   - AWS Account with Bedrock model access
   - Node.js 18+, AWS CDK 2.x
   - Docker 24+, Go 1.22+, Python 3.11+

2. **Deploy Infrastructure**
   ```bash
   cd infrastructure
   npm install && npm run build
   cdk bootstrap
   cdk deploy --all
   ```

3. **Start Local Services**
   ```bash
   cp .env.example .env
   # Update .env with CDK outputs
   docker compose up --build
   ```

4. **Test the System**
   ```bash
   ./scripts/test_agent.sh
   ```

## Architecture

The system uses Amazon Bedrock Agents as the central orchestrator, eliminating the need for custom conversation management code. The agent automatically handles multi-turn conversations, maintains session state, and invokes Lambda action groups for appointment operations.

## Documentation

- [Setup Guide](docs/setup.md)
- [Architecture Details](docs/architecture.md)
- [Testing Guide](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)