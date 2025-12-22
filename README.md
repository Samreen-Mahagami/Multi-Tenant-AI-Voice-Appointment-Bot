# AI Voice Appointment Bot

## Intelligent Voice Assistant with Amazon Bedrock Agents

**Technology Stack:**
- **Telephony:** FreeSWITCH + mod_audio_stream
- **Speech-to-Text:** Amazon Transcribe Streaming
- **Text-to-Speech:** Amazon Polly
- **AI Orchestration:** Amazon Bedrock Agents
- **Foundation Model:** Anthropic Claude 3 Haiku (or Amazon Nova)
- **Action Groups:** AWS Lambda (Python)
- **Infrastructure:** AWS CDK (TypeScript) + Docker Compose (local services)

**Scope:** Real-time call path with fully managed AI agent orchestration for medical appointment booking

## Project Goal

Build a production-quality AI voice receptionist for medical practices demonstrating AWS-native AI orchestration:

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
   
   **Browser Voice Client:**
   ```bash
   # Open in browser
   http://localhost:8000/simple_voice_test.html
   ```
   
   **Or use the advanced client:**
   ```bash
   http://localhost:8000/browser_voice_client.html
   ```

## Testing

### Voice Client Options

1. **simple_voice_test.html** - Quick voice testing interface
   - Select hospital (1001, 1002, 1003)
   - Click to speak
   - Real-time AI responses

2. **browser_voice_client.html** - Advanced testing interface
   - Full audio visualization
   - Detailed connection status
   - Extended debugging features

## Architecture

The system uses Amazon Bedrock Agents as the central orchestrator, eliminating the need for custom conversation management code. The agent automatically handles multi-turn conversations, maintains session state, and invokes Lambda action groups for appointment operations.

## Example Conversation Flow

```
Caller: "Hi, I'd like to see a doctor"
        ↓
[Transcribe] → "Hi, I'd like to see a doctor"
        ↓
[Bedrock Agent] → Reasoning: User wants appointment, need to ask for date
        ↓
[Agent Response] → "I'd be happy to help you book an appointment. What day works best for you?"
        ↓
[Polly] → Audio playback

Caller: "Tomorrow morning"
        ↓
[Transcribe] → "Tomorrow morning"
        ↓
[Bedrock Agent] → Reasoning: Have date preference, invoke search_slots action
        ↓
[Lambda: search_slots] → Returns available slots
        ↓
[Agent Response] → "I found slots at 9 AM, 9:30 AM, and 10 AM. Which works for you?"
        ↓
[Polly] → Audio playback

... continues until booking complete ...
```

## Documentation

- [Conversation Flow Examples](CONVERSATION_FLOW_EXAMPLE.md)
- [Quick Summary](docs/QUICK_SUMMARY.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)