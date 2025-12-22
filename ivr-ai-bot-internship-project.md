# Internship Project: Multi-Tenant AI Voice Appointment Bot

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

---

## Table of Contents

1. [Project Goal](#1-project-goal)
2. [Explicit Exclusions](#2-explicit-exclusions)
3. [System Architecture](#3-system-architecture)
4. [Amazon Bedrock Agents Deep Dive](#4-amazon-bedrock-agents-deep-dive)
5. [Repository Layout](#5-repository-layout)
6. [Prerequisites](#6-prerequisites)
7. [Infrastructure Setup (CDK)](#7-infrastructure-setup-cdk)
8. [Lambda Action Groups](#8-lambda-action-groups)
9. [Service Implementations](#9-service-implementations)
10. [Bedrock Agent Configuration](#10-bedrock-agent-configuration)
11. [Execution Steps](#11-execution-steps)
12. [Testing & Validation](#12-testing--validation)
13. [Milestones & Grading](#13-milestones--grading)
14. [Troubleshooting Guide](#14-troubleshooting-guide)
15. [Deliverables](#15-deliverables)


---

## 1. Project Goal

Build a production-quality AI voice receptionist using AWS-native AI orchestration:

### 1.1 Core Capabilities

| Capability | AWS Service |
|------------|-------------|
| **Speech Recognition** | Amazon Transcribe Streaming |
| **AI Orchestration** | Amazon Bedrock Agents |
| **Foundation Model** | Claude 3 Haiku / Amazon Nova Lite |
| **Tool Execution** | AWS Lambda (Action Groups) |
| **Voice Synthesis** | Amazon Polly |
| **Telephony** | FreeSWITCH |

### 1.2 Why Bedrock Agents?

| Feature | Benefit |
|---------|---------|
| **Fully Managed** | No orchestration code to maintain |
| **Native Tool Calling** | Action Groups with OpenAPI schemas |
| **Session Memory** | Built-in conversation state management |
| **Guardrails** | Content filtering and PII redaction |
| **Observability** | CloudWatch integration out of the box |
| **Multi-turn** | Handles complex conversation flows automatically |

### 1.3 Conversation Flow Example

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

---

## 2. Explicit Exclusions

**DO NOT implement:**
- Post-call storage, recording, or analytics
- Knowledge Base integration (keep focus on action groups)
- Custom guardrails configuration
- Multi-region deployment
- VPC endpoints for Bedrock (use public endpoints for simplicity)

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  AWS CLOUD                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        AMAZON BEDROCK AGENTS                             │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │                    APPOINTMENT BOOKING AGENT                     │    │    │
│  │  │                                                                  │    │    │
│  │  │  Foundation Model: Claude 3 Haiku                               │    │    │
│  │  │                                                                  │    │    │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │    │    │
│  │  │  │ search_slots │ │confirm_appt  │ │ handoff_to_human     │    │    │    │
│  │  │  │ Action Group │ │ Action Group │ │ Action Group         │    │    │    │
│  │  │  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘    │    │    │
│  │  │         │                │                    │                 │    │    │
│  │  └─────────┼────────────────┼────────────────────┼─────────────────┘    │    │
│  │            │                │                    │                      │    │
│  └────────────┼────────────────┼────────────────────┼──────────────────────┘    │
│               │                │                    │                           │
│               ▼                ▼                    ▼                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         AWS LAMBDA                                       │    │
│  │                                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │    │
│  │  │ SearchSlots     │  │ ConfirmAppt     │  │ HandoffHuman    │          │    │
│  │  │ Function        │  │ Function        │  │ Function        │          │    │
│  │  │                 │  │                 │  │                 │          │    │
│  │  │ Calls:          │  │ Calls:          │  │ Returns:        │          │    │
│  │  │ Appointment Svc │  │ Appointment Svc │  │ Handoff Signal  │          │    │
│  │  └────────┬────────┘  └────────┬────────┘  └─────────────────┘          │    │
│  │           │                    │                                         │    │
│  └───────────┼────────────────────┼─────────────────────────────────────────┘    │
│              │                    │                                              │
│  ┌───────────┼────────────────────┼─────────────────────────────────────────┐    │
│  │           ▼                    ▼          DOCKER (ECS/EC2)               │    │
│  │  ┌─────────────────────────────────────┐                                 │    │
│  │  │       Appointment Service (Go)       │◀── HTTP ──┐                    │    │
│  │  │       - Search slots                 │           │                    │    │
│  │  │       - Confirm bookings             │           │                    │    │
│  │  └─────────────────────────────────────┘           │                    │    │
│  │                                                     │                    │    │
│  │  ┌─────────────────────────────────────┐           │                    │    │
│  │  │       Tenant Config Service (Go)     │◀──────────┤                    │    │
│  │  │       - DID → Tenant mapping         │           │                    │    │
│  │  └─────────────────────────────────────┘           │                    │    │
│  │                                                     │                    │    │
│  │  ┌─────────────────────────────────────┐           │                    │    │
│  │  │       Media Gateway (Go)             │───────────┘                    │    │
│  │  │       - WebSocket from FreeSWITCH    │                                │    │
│  │  │       - Transcribe Streaming         │──────▶ Amazon Transcribe       │    │
│  │  │       - Polly TTS                    │──────▶ Amazon Polly            │    │
│  │  │       - Bedrock Agent Client         │──────▶ Bedrock InvokeAgent     │    │
│  │  └─────────────────────────────────────┘                                 │    │
│  │                     ▲                                                    │    │
│  │                     │ WebSocket                                          │    │
│  │  ┌──────────────────┴──────────────────┐                                 │    │
│  │  │          FreeSWITCH                  │                                │    │
│  │  │          - SIP endpoint              │                                │    │
│  │  │          - mod_audio_stream          │                                │    │
│  │  └─────────────────────────────────────┘                                 │    │
│  │                     ▲                                                    │    │
│  └─────────────────────┼────────────────────────────────────────────────────┘    │
│                        │                                                         │
└────────────────────────┼─────────────────────────────────────────────────────────┘
                         │ SIP
                         │
                    ┌────┴────┐
                    │ Caller  │
                    │(Phone)  │
                    └─────────┘
```

### 3.2 Bedrock Agent Invocation Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Media Gateway  │     │  Bedrock Agent  │     │  Lambda Action  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  InvokeAgent          │                       │
         │  (sessionId,          │                       │
         │   inputText)          │                       │
         │──────────────────────▶│                       │
         │                       │                       │
         │                       │ [FM Reasoning]        │
         │                       │ "Need to search       │
         │                       │  for slots"           │
         │                       │                       │
         │                       │  Invoke Action        │
         │                       │──────────────────────▶│
         │                       │                       │
         │                       │                       │ [Execute Lambda]
         │                       │                       │ Call Appointment Svc
         │                       │                       │
         │                       │  Action Result        │
         │                       │◀──────────────────────│
         │                       │                       │
         │                       │ [FM Reasoning]        │
         │                       │ "Format response      │
         │                       │  with slot options"   │
         │                       │                       │
         │  Agent Response       │                       │
         │  (completion text)    │                       │
         │◀──────────────────────│                       │
         │                       │                       │
         │ [Send to Polly]       │                       │
         │ [Play to caller]      │                       │
         │                       │                       │
```

### 3.3 Session Management

Bedrock Agents handles session state automatically:

```
Session ID: {callId}
    │
    ├── Turn 1: "I want to book an appointment"
    │   └── Agent remembers: User wants appointment
    │
    ├── Turn 2: "Tomorrow morning"
    │   └── Agent remembers: Date=tomorrow, Time=morning
    │
    ├── Turn 3: "The 9:30 slot"
    │   └── Agent remembers: Selected slot S2
    │
    ├── Turn 4: "John Smith"
    │   └── Agent remembers: Name=John Smith
    │
    └── Turn 5: "john@example.com"
        └── Agent has all info → Calls confirm_appointment
```

---

## 4. Amazon Bedrock Agents Deep Dive

### 4.1 Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | The orchestrator that uses an FM to reason and take actions |
| **Action Group** | A collection of actions (tools) the agent can invoke |
| **Action** | A single capability defined by OpenAPI schema |
| **Session** | Conversation context maintained across turns |
| **Agent Alias** | A versioned deployment of the agent |
| **Instruction** | System prompt that defines agent behavior |

### 4.2 Action Group Types

| Type | Description | Our Use |
|------|-------------|---------|
| **Lambda** | Invoke Lambda function | ✅ Primary approach |
| **Return Control** | Return to client for execution | Not used |
| **API Schema** | Direct API call (preview) | Not used |

### 4.3 Agent Instructions (System Prompt)

```
You are a friendly and professional AI receptionist for a medical clinic.

YOUR ROLE:
- Help callers book appointments
- Be warm, concise, and efficient
- Keep responses under 40 words (this is a phone conversation)

BOOKING PROCESS:
1. When caller wants an appointment, ask for preferred date/time
2. Use search_slots to find availability
3. Present 2-3 options clearly
4. When they choose, ask for their name
5. Then ask for email
6. Use confirm_appointment to book
7. Provide confirmation number

IMPORTANT RULES:
- Never provide medical advice
- If caller asks for human, use handoff_to_human immediately
- Speak naturally - avoid bullet points or lists
- Say times like "nine thirty AM" not "9:30 AM"

CURRENT CONTEXT:
- Clinic: {{tenant_name}}
- Specialties: {{specialties}}
```

### 4.4 OpenAPI Schema for Action Groups

```yaml
openapi: 3.0.0
info:
  title: Appointment Booking Actions
  version: 1.0.0

paths:
  /search_slots:
    post:
      operationId: searchSlots
      summary: Search for available appointment slots
      description: Use this when the caller wants to book an appointment and you need to find available times. Requires at least a date preference.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tenant_id:
                  type: string
                  description: The tenant/clinic identifier
                date:
                  type: string
                  description: Preferred date (tomorrow, next monday, 2024-12-20)
                time_preference:
                  type: string
                  enum: [morning, afternoon, evening, any]
                  description: Preferred time of day
              required:
                - tenant_id
                - date
      responses:
        '200':
          description: Available slots
          content:
            application/json:
              schema:
                type: object
                properties:
                  slots:
                    type: array
                    items:
                      type: object
                      properties:
                        slot_id:
                          type: string
                        start_time:
                          type: string
                        doctor_name:
                          type: string

  /confirm_appointment:
    post:
      operationId: confirmAppointment
      summary: Book a confirmed appointment
      description: Use this only when you have ALL required information - slot_id, patient_name, and patient_email.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tenant_id:
                  type: string
                slot_id:
                  type: string
                  description: Slot ID from search results
                patient_name:
                  type: string
                  description: Full name of the patient
                patient_email:
                  type: string
                  description: Email for confirmation
              required:
                - tenant_id
                - slot_id
                - patient_name
                - patient_email
      responses:
        '200':
          description: Booking confirmation
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  confirmation_ref:
                    type: string

  /handoff_to_human:
    post:
      operationId: handoffToHuman
      summary: Transfer call to human receptionist
      description: Use when caller explicitly requests human, or conversation is not progressing.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
                  description: Why handoff is needed
              required:
                - reason
      responses:
        '200':
          description: Handoff initiated
```

---

## 5. Repository Layout

```
ivr-internship/
│
├── README.md
├── .env.example
│
├── infrastructure/                    # AWS CDK
│   ├── package.json
│   ├── tsconfig.json
│   ├── cdk.json
│   ├── bin/
│   │   └── infrastructure.ts
│   └── lib/
│       ├── bedrock-agent-stack.ts
│       ├── lambda-stack.ts
│       └── constructs/
│           └── appointment-agent.ts
│
├── lambda/                            # Action Group Lambdas
│   ├── search-slots/
│   │   ├── index.py
│   │   └── requirements.txt
│   ├── confirm-appointment/
│   │   ├── index.py
│   │   └── requirements.txt
│   └── handoff-human/
│       ├── index.py
│       └── requirements.txt
│
├── docker-compose.yml                 # Local services
│
├── freeswitch/
│   └── conf/
│       ├── dialplan/
│       │   └── public.xml
│       ├── directory/
│       │   └── default/
│       │       └── 1000.xml
│       └── autoload_configs/
│           ├── event_socket.conf.xml
│           └── modules.conf.xml
│
├── tenant-config-go/
│   ├── Dockerfile
│   ├── go.mod
│   ├── main.go
│   └── tenants.yaml
│
├── appointment-service-go/
│   ├── Dockerfile
│   ├── go.mod
│   └── main.go
│
├── media-gateway-go/
│   ├── Dockerfile
│   ├── go.mod
│   ├── main.go
│   ├── handle_ws.go
│   ├── bedrock_client.go             # Bedrock Agent integration
│   ├── polly.go
│   ├── esl_client.go
│   └── transcribe_stream.go
│
├── scripts/
│   ├── deploy.sh
│   ├── test_agent.sh
│   └── local_dev.sh
│
└── docs/
    ├── architecture.png
    └── bedrock-setup.md
```

---

## 6. Prerequisites

### 6.1 AWS Account Requirements

| Service | Required Access |
|---------|-----------------|
| Amazon Bedrock | Model access enabled for Claude 3 Haiku |
| AWS Lambda | Create/invoke functions |
| IAM | Create roles and policies |
| CloudWatch | Logs access |
| Amazon Transcribe | Streaming transcription |
| Amazon Polly | Speech synthesis |

### 6.2 Enable Bedrock Model Access

```bash
# Via AWS Console:
# 1. Go to Amazon Bedrock → Model access
# 2. Request access to: Anthropic Claude 3 Haiku
# 3. Wait for approval (usually instant for Haiku)

# Verify via CLI:
aws bedrock list-foundation-models \
    --query "modelSummaries[?modelId=='anthropic.claude-3-haiku-20240307-v1:0']"
```

### 6.3 Local Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 18+ | CDK |
| AWS CDK | 2.x | Infrastructure deployment |
| Docker | 24+ | Local services |
| AWS CLI | 2.x | AWS access |
| Go | 1.22+ | Local development |
| Python | 3.11+ | Lambda functions |

### 6.4 Install CDK

```bash
npm install -g aws-cdk
cdk --version
```

---

## 7. Infrastructure Setup (CDK)

### 7.1 CDK Project Setup

Create `infrastructure/package.json`:

```json
{
  "name": "ivr-infrastructure",
  "version": "1.0.0",
  "bin": {
    "infrastructure": "bin/infrastructure.js"
  },
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "cdk": "cdk",
    "deploy": "cdk deploy --all",
    "destroy": "cdk destroy --all"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "typescript": "~5.3.0",
    "aws-cdk": "^2.170.0"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.170.0",
    "constructs": "^10.0.0"
  }
}
```

Create `infrastructure/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "outDir": "./dist",
    "rootDir": "./"
  },
  "exclude": ["node_modules", "cdk.out"]
}
```

Create `infrastructure/cdk.json`:

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/infrastructure.ts",
  "watch": {
    "include": ["**"],
    "exclude": [
      "README.md",
      "cdk*.json",
      "**/*.d.ts",
      "**/*.js",
      "tsconfig.json",
      "package*.json",
      "node_modules",
      "cdk.out"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeVersionProps": true,
    "@aws-cdk/core:checkSecretUsage": true
  }
}
```

### 7.2 CDK Entry Point

Create `infrastructure/bin/infrastructure.ts`:

```typescript
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BedrockAgentStack } from '../lib/bedrock-agent-stack';
import { LambdaStack } from '../lib/lambda-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

// Deploy Lambda functions first
const lambdaStack = new LambdaStack(app, 'IvrLambdaStack', { env });

// Deploy Bedrock Agent
const agentStack = new BedrockAgentStack(app, 'IvrBedrockAgentStack', {
  env,
  searchSlotsFunction: lambdaStack.searchSlotsFunction,
  confirmAppointmentFunction: lambdaStack.confirmAppointmentFunction,
  handoffHumanFunction: lambdaStack.handoffHumanFunction,
});

agentStack.addDependency(lambdaStack);

app.synth();
```

### 7.3 Lambda Stack

Create `infrastructure/lib/lambda-stack.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

export class LambdaStack extends cdk.Stack {
  public readonly searchSlotsFunction: lambda.Function;
  public readonly confirmAppointmentFunction: lambda.Function;
  public readonly handoffHumanFunction: lambda.Function;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Common Lambda configuration
    const commonProps: Partial<lambda.FunctionProps> = {
      runtime: lambda.Runtime.PYTHON_3_11,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        APPOINTMENT_SERVICE_URL: cdk.Fn.importValue('AppointmentServiceUrl') || 
          'http://appointment-service-go:7002',
        TENANT_CONFIG_URL: cdk.Fn.importValue('TenantConfigUrl') || 
          'http://tenant-config-go:7001',
      },
    };

    // Search Slots Lambda
    this.searchSlotsFunction = new lambda.Function(this, 'SearchSlotsFunction', {
      ...commonProps,
      functionName: 'ivr-search-slots',
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/search-slots')),
      description: 'Search for available appointment slots',
    });

    // Confirm Appointment Lambda
    this.confirmAppointmentFunction = new lambda.Function(this, 'ConfirmAppointmentFunction', {
      ...commonProps,
      functionName: 'ivr-confirm-appointment',
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/confirm-appointment')),
      description: 'Confirm and book an appointment',
    });

    // Handoff to Human Lambda
    this.handoffHumanFunction = new lambda.Function(this, 'HandoffHumanFunction', {
      ...commonProps,
      functionName: 'ivr-handoff-human',
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/handoff-human')),
      description: 'Initiate handoff to human receptionist',
    });

    // Output Lambda ARNs
    new cdk.CfnOutput(this, 'SearchSlotsFunctionArn', {
      value: this.searchSlotsFunction.functionArn,
      exportName: 'SearchSlotsFunctionArn',
    });

    new cdk.CfnOutput(this, 'ConfirmAppointmentFunctionArn', {
      value: this.confirmAppointmentFunction.functionArn,
      exportName: 'ConfirmAppointmentFunctionArn',
    });

    new cdk.CfnOutput(this, 'HandoffHumanFunctionArn', {
      value: this.handoffHumanFunction.functionArn,
      exportName: 'HandoffHumanFunctionArn',
    });
  }
}
```

### 7.4 Bedrock Agent Stack

Create `infrastructure/lib/bedrock-agent-stack.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

interface BedrockAgentStackProps extends cdk.StackProps {
  searchSlotsFunction: lambda.Function;
  confirmAppointmentFunction: lambda.Function;
  handoffHumanFunction: lambda.Function;
}

export class BedrockAgentStack extends cdk.Stack {
  public readonly agentId: string;
  public readonly agentAliasId: string;

  constructor(scope: Construct, id: string, props: BedrockAgentStackProps) {
    super(scope, id, props);

    // Agent execution role
    const agentRole = new iam.Role(this, 'BedrockAgentRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'Role for IVR Appointment Booking Agent',
    });

    // Grant Bedrock model invocation
    agentRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0`,
      ],
    }));

    // Agent instructions
    const agentInstruction = `You are a friendly and professional AI receptionist for medical clinics.

YOUR ROLE:
- Help callers book medical appointments
- Be warm, concise, and professional
- Keep responses SHORT (under 40 words) - this is a phone conversation

BOOKING PROCESS:
1. When caller wants an appointment, ask for their preferred date and time
2. Use the searchSlots action to find available times
3. Present 2-3 slot options clearly (say times like "nine thirty AM")
4. When they choose a slot, ask for their full name
5. Then ask for their email address
6. Use confirmAppointment action to book (only when you have slot_id, name, AND email)
7. Tell them the confirmation number and say goodbye

CRITICAL RULES:
- NEVER provide medical advice - suggest they speak to a doctor
- If caller asks for a human or seems frustrated, use handoffToHuman immediately
- Always confirm details before booking
- Speak naturally - no bullet points or numbered lists
- Keep the conversation flowing naturally

If you don't understand something, ask for clarification politely.`;

    // Create the Bedrock Agent
    const agent = new bedrock.CfnAgent(this, 'AppointmentBookingAgent', {
      agentName: 'ivr-appointment-booking-agent',
      description: 'AI receptionist for booking medical appointments via phone',
      foundationModel: 'anthropic.claude-3-haiku-20240307-v1:0',
      instruction: agentInstruction,
      agentResourceRoleArn: agentRole.roleArn,
      idleSessionTtlInSeconds: 600, // 10 minutes
      
      // Action Groups
      actionGroups: [
        {
          actionGroupName: 'AppointmentActions',
          description: 'Actions for searching and booking appointments',
          actionGroupExecutor: {
            lambda: props.searchSlotsFunction.functionArn,
          },
          apiSchema: {
            payload: this.getOpenApiSchema(),
          },
        },
      ],
    });

    // Grant Lambda invoke permissions to the agent
    props.searchSlotsFunction.grantInvoke(agentRole);
    props.confirmAppointmentFunction.grantInvoke(agentRole);
    props.handoffHumanFunction.grantInvoke(agentRole);

    // Also grant Bedrock service permission to invoke Lambdas
    [props.searchSlotsFunction, props.confirmAppointmentFunction, props.handoffHumanFunction].forEach(fn => {
      fn.addPermission('BedrockInvoke', {
        principal: new iam.ServicePrincipal('bedrock.amazonaws.com'),
        sourceArn: `arn:aws:bedrock:${this.region}:${this.account}:agent/*`,
      });
    });

    // Create Agent Alias (required for invoking the agent)
    const agentAlias = new bedrock.CfnAgentAlias(this, 'AgentAlias', {
      agentId: agent.attrAgentId,
      agentAliasName: 'live',
      description: 'Production alias for the appointment booking agent',
    });

    agentAlias.addDependency(agent);

    // Store IDs
    this.agentId = agent.attrAgentId;
    this.agentAliasId = agentAlias.attrAgentAliasId;

    // Outputs
    new cdk.CfnOutput(this, 'AgentId', {
      value: agent.attrAgentId,
      exportName: 'IvrAgentId',
      description: 'Bedrock Agent ID',
    });

    new cdk.CfnOutput(this, 'AgentAliasId', {
      value: agentAlias.attrAgentAliasId,
      exportName: 'IvrAgentAliasId',
      description: 'Bedrock Agent Alias ID',
    });
  }

  private getOpenApiSchema(): string {
    return `
openapi: 3.0.0
info:
  title: Appointment Booking API
  version: 1.0.0
  description: Actions for the appointment booking agent

paths:
  /searchSlots:
    post:
      operationId: searchSlots
      summary: Search for available appointment slots
      description: Search for available appointment slots for a given date and time preference. Use this when the caller wants to book an appointment.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tenant_id:
                  type: string
                  description: The clinic/tenant identifier
                date:
                  type: string
                  description: The preferred date (e.g., tomorrow, next monday, 2024-12-25)
                time_preference:
                  type: string
                  enum: [morning, afternoon, evening, any]
                  description: Preferred time of day for the appointment
              required:
                - tenant_id
                - date
      responses:
        '200':
          description: List of available slots
          content:
            application/json:
              schema:
                type: object
                properties:
                  slots:
                    type: array
                    items:
                      type: object
                      properties:
                        slot_id:
                          type: string
                        start_time:
                          type: string
                        end_time:
                          type: string
                        doctor_name:
                          type: string

  /confirmAppointment:
    post:
      operationId: confirmAppointment
      summary: Book a confirmed appointment
      description: Book an appointment for the caller. Only use this when you have collected the slot_id, patient name, AND email address.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tenant_id:
                  type: string
                  description: The clinic/tenant identifier
                slot_id:
                  type: string
                  description: The selected slot ID from searchSlots results
                patient_name:
                  type: string
                  description: Full name of the patient
                patient_email:
                  type: string
                  description: Email address for sending confirmation
              required:
                - tenant_id
                - slot_id
                - patient_name
                - patient_email
      responses:
        '200':
          description: Booking confirmation
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [BOOKED, FAILED]
                  confirmation_ref:
                    type: string
                  error:
                    type: string

  /handoffToHuman:
    post:
      operationId: handoffToHuman
      summary: Transfer call to human receptionist
      description: Use this when the caller explicitly asks to speak with a human, or when the conversation is not progressing after multiple attempts.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
                  description: Brief reason for the handoff
              required:
                - reason
      responses:
        '200':
          description: Handoff initiated
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  message:
                    type: string
`;
  }
}
```

---

## 8. Lambda Action Groups

### 8.1 Search Slots Lambda

Create `lambda/search-slots/index.py`:

```python
"""
Lambda function for searching available appointment slots.
Called by Bedrock Agent as an action group.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Any

APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL', 'http://appointment-service-go:7002')


def handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent action group handler for searchSlots.
    
    Event structure from Bedrock:
    {
        "actionGroup": "AppointmentActions",
        "apiPath": "/searchSlots",
        "httpMethod": "POST",
        "requestBody": {
            "content": {
                "application/json": {
                    "properties": [
                        {"name": "tenant_id", "value": "clinic_a"},
                        {"name": "date", "value": "tomorrow"},
                        {"name": "time_preference", "value": "morning"}
                    ]
                }
            }
        },
        "sessionAttributes": {...},
        "promptSessionAttributes": {...}
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract parameters from Bedrock Agent event
        params = extract_parameters(event)
        tenant_id = params.get('tenant_id', 'default')
        date = params.get('date', 'tomorrow')
        time_preference = params.get('time_preference', 'any')
        
        print(f"Searching slots: tenant={tenant_id}, date={date}, time_pref={time_preference}")
        
        # Call appointment service
        slots = search_slots(tenant_id, date, time_preference)
        
        # Format response for Bedrock Agent
        if slots:
            slots_text = format_slots_for_agent(slots)
            response_body = {
                "slots": slots,
                "message": f"Found {len(slots)} available slots: {slots_text}"
            }
        else:
            response_body = {
                "slots": [],
                "message": "No available slots found for the requested time. Please try a different date or time."
            }
        
        return create_response(event, 200, response_body)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(event, 500, {
            "error": str(e),
            "message": "Sorry, I couldn't search for appointments right now. Please try again."
        })


def extract_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock Agent event structure."""
    params = {}
    
    try:
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        properties = json_content.get('properties', [])
        
        for prop in properties:
            name = prop.get('name')
            value = prop.get('value')
            if name and value:
                params[name] = value
                
    except Exception as e:
        print(f"Error extracting parameters: {e}")
    
    return params


def search_slots(tenant_id: str, date: str, time_preference: str) -> list:
    """Call appointment service to search for slots."""
    
    url = f"{APPOINTMENT_SERVICE_URL}/v1/slots/search"
    
    payload = json.dumps({
        "tenantId": tenant_id,
        "date": date,
        "timePreference": time_preference
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('slots', [])
    except urllib.error.URLError as e:
        print(f"Failed to call appointment service: {e}")
        # Return mock data for testing
        return generate_mock_slots(tenant_id, date, time_preference)


def generate_mock_slots(tenant_id: str, date: str, time_preference: str) -> list:
    """Generate mock slots for testing when service is unavailable."""
    base_time = datetime.now() + timedelta(days=1)
    
    if time_preference == 'morning':
        hours = [9, 9, 10]
        minutes = [0, 30, 0]
    elif time_preference == 'afternoon':
        hours = [14, 14, 15]
        minutes = [0, 30, 0]
    else:
        hours = [9, 14, 16]
        minutes = [30, 0, 30]
    
    slots = []
    for i, (h, m) in enumerate(zip(hours, minutes)):
        slot_time = base_time.replace(hour=h, minute=m, second=0, microsecond=0)
        slots.append({
            "slot_id": f"{tenant_id}-{slot_time.strftime('%Y%m%d')}-{h:02d}{m:02d}",
            "start_time": slot_time.isoformat(),
            "end_time": (slot_time + timedelta(minutes=30)).isoformat(),
            "doctor_name": f"Dr. {'Sharma' if i == 0 else 'Patel' if i == 1 else 'Kumar'}"
        })
    
    return slots


def format_slots_for_agent(slots: list) -> str:
    """Format slots as natural language for agent response."""
    formatted = []
    for i, slot in enumerate(slots[:3], 1):
        try:
            dt = datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M %p').lstrip('0')
            formatted.append(f"{time_str}")
        except:
            formatted.append(slot.get('start_time', 'Unknown'))
    
    return ", ".join(formatted)


def create_response(event: dict, status_code: int, body: dict) -> dict:
    """Create response in Bedrock Agent expected format."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            }
        }
    }
```

Create `lambda/search-slots/requirements.txt`:

```
# No external dependencies - using stdlib only
```

### 8.2 Confirm Appointment Lambda

Create `lambda/confirm-appointment/index.py`:

```python
"""
Lambda function for confirming/booking appointments.
Called by Bedrock Agent as an action group.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any
import random
import string

APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL', 'http://appointment-service-go:7002')


def handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent action group handler for confirmAppointment.
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        params = extract_parameters(event)
        tenant_id = params.get('tenant_id', 'default')
        slot_id = params.get('slot_id', '')
        patient_name = params.get('patient_name', '')
        patient_email = params.get('patient_email', '')
        
        print(f"Confirming appointment: tenant={tenant_id}, slot={slot_id}, name={patient_name}, email={patient_email}")
        
        # Validate required fields
        missing_fields = []
        if not slot_id:
            missing_fields.append("slot_id")
        if not patient_name:
            missing_fields.append("patient_name")
        if not patient_email:
            missing_fields.append("patient_email")
        
        if missing_fields:
            return create_response(event, 400, {
                "status": "FAILED",
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "message": f"I still need the following information: {', '.join(missing_fields).replace('_', ' ')}"
            })
        
        # Call appointment service
        result = confirm_appointment(tenant_id, slot_id, patient_name, patient_email)
        
        if result.get('status') == 'BOOKED':
            conf_ref = result.get('confirmation_ref', '')
            return create_response(event, 200, {
                "status": "BOOKED",
                "confirmation_ref": conf_ref,
                "message": f"Appointment confirmed! Confirmation number is {conf_ref}. A confirmation email will be sent to {patient_email}."
            })
        else:
            return create_response(event, 200, {
                "status": "FAILED",
                "error": result.get('error', 'Booking failed'),
                "message": "I'm sorry, I couldn't book that slot. It may have been taken. Would you like to search for other available times?"
            })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(event, 500, {
            "status": "FAILED",
            "error": str(e),
            "message": "Sorry, I couldn't complete the booking right now. Please try again."
        })


def extract_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock Agent event structure."""
    params = {}
    
    try:
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        properties = json_content.get('properties', [])
        
        for prop in properties:
            name = prop.get('name')
            value = prop.get('value')
            if name and value:
                params[name] = value
                
    except Exception as e:
        print(f"Error extracting parameters: {e}")
    
    return params


def confirm_appointment(tenant_id: str, slot_id: str, patient_name: str, patient_email: str) -> dict:
    """Call appointment service to confirm booking."""
    
    url = f"{APPOINTMENT_SERVICE_URL}/v1/appointments/confirm"
    
    payload = json.dumps({
        "tenantId": tenant_id,
        "slotId": slot_id,
        "patientName": patient_name,
        "patientEmail": patient_email
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Failed to call appointment service: {e}")
        # Return mock success for testing
        return {
            "status": "BOOKED",
            "confirmation_ref": generate_confirmation_ref(tenant_id)
        }


def generate_confirmation_ref(tenant_id: str) -> str:
    """Generate a mock confirmation reference."""
    prefix = tenant_id[:4].upper() if tenant_id else "APPT"
    date_part = datetime.now().strftime("%m%d")
    random_part = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{date_part}-{random_part}"


def create_response(event: dict, status_code: int, body: dict) -> dict:
    """Create response in Bedrock Agent expected format."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            }
        }
    }
```

Create `lambda/confirm-appointment/requirements.txt`:

```
# No external dependencies - using stdlib only
```

### 8.3 Handoff to Human Lambda

Create `lambda/handoff-human/index.py`:

```python
"""
Lambda function for initiating handoff to human receptionist.
Called by Bedrock Agent as an action group.
"""

import json
from typing import Any


def handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent action group handler for handoffToHuman.
    
    In a production system, this would:
    1. Notify the human receptionist queue
    2. Transfer the call via FreeSWITCH
    3. Log the handoff reason for analytics
    
    For this internship project, we simply signal the handoff.
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        params = extract_parameters(event)
        reason = params.get('reason', 'Caller requested human assistance')
        
        print(f"Handoff to human requested. Reason: {reason}")
        
        # In production: would trigger actual call transfer here
        # For now, we return a response that signals the Media Gateway
        # to handle the handoff
        
        response_body = {
            "status": "HANDOFF_INITIATED",
            "reason": reason,
            "message": "I'll connect you with a human receptionist right away. Please hold for just a moment.",
            "action": "TRANSFER_TO_HUMAN"
        }
        
        return create_response(event, 200, response_body)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(event, 500, {
            "status": "FAILED",
            "error": str(e),
            "message": "I'm having trouble connecting you. Please hold while I try again."
        })


def extract_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock Agent event structure."""
    params = {}
    
    try:
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        properties = json_content.get('properties', [])
        
        for prop in properties:
            name = prop.get('name')
            value = prop.get('value')
            if name and value:
                params[name] = value
                
    except Exception as e:
        print(f"Error extracting parameters: {e}")
    
    return params


def create_response(event: dict, status_code: int, body: dict) -> dict:
    """Create response in Bedrock Agent expected format."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            }
        }
    }
```

Create `lambda/handoff-human/requirements.txt`:

```
# No external dependencies - using stdlib only
```

---

## 9. Service Implementations

### 9.1 Docker Compose (Local Services)

Create `docker-compose.yml`:

```yaml
version: "3.9"

networks:
  ivr-network:
    driver: bridge

volumes:
  freeswitch-sounds:

services:
  # ===========================================
  # TENANT CONFIG SERVICE
  # ===========================================
  tenant-config-go:
    build: ./tenant-config-go
    container_name: tenant-config-go
    networks:
      - ivr-network
    ports:
      - "7001:7001"
    volumes:
      - ./tenant-config-go/tenants.yaml:/app/tenants.yaml:ro
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:7001/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  # ===========================================
  # APPOINTMENT SERVICE
  # ===========================================
  appointment-service-go:
    build: ./appointment-service-go
    container_name: appointment-service-go
    networks:
      - ivr-network
    ports:
      - "7002:7002"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:7002/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  # ===========================================
  # MEDIA GATEWAY
  # ===========================================
  media-gateway-go:
    build: ./media-gateway-go
    container_name: media-gateway-go
    networks:
      - ivr-network
    ports:
      - "8080:8080"
    environment:
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}
      - BEDROCK_AGENT_ID=${BEDROCK_AGENT_ID}
      - BEDROCK_AGENT_ALIAS_ID=${BEDROCK_AGENT_ALIAS_ID}
      - TENANT_CONFIG_URL=http://tenant-config-go:7001
      - FREESWITCH_ESL_HOST=freeswitch
      - FREESWITCH_ESL_PORT=8021
      - FREESWITCH_ESL_PASSWORD=ClueCon
    volumes:
      - ~/.aws:/root/.aws:ro
    depends_on:
      tenant-config-go:
        condition: service_healthy
      appointment-service-go:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  # ===========================================
  # FREESWITCH
  # ===========================================
  freeswitch:
    image: signalwire/freeswitch:latest
    container_name: freeswitch
    networks:
      - ivr-network
    ports:
      - "5060:5060/udp"
      - "5060:5060/tcp"
      - "5080:5080/udp"
      - "8021:8021/tcp"
      - "16384-16484:16384-16484/udp"
    volumes:
      - ./freeswitch/conf/dialplan:/etc/freeswitch/dialplan:ro
      - ./freeswitch/conf/directory:/etc/freeswitch/directory:ro
      - ./freeswitch/conf/autoload_configs/event_socket.conf.xml:/etc/freeswitch/autoload_configs/event_socket.conf.xml:ro
      - ./freeswitch/conf/autoload_configs/modules.conf.xml:/etc/freeswitch/autoload_configs/modules.conf.xml:ro
      - freeswitch-sounds:/usr/share/freeswitch/sounds
    depends_on:
      media-gateway-go:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "fs_cli", "-x", "status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

### 9.2 Environment File

Create `.env.example`:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Bedrock Agent Configuration (populated after CDK deployment)
BEDROCK_AGENT_ID=
BEDROCK_AGENT_ALIAS_ID=

# Service URLs (for Lambda functions)
APPOINTMENT_SERVICE_URL=http://appointment-service-go:7002
TENANT_CONFIG_URL=http://tenant-config-go:7001
```

### 9.3 Media Gateway with Bedrock Agent Client

Create `media-gateway-go/bedrock_client.go`:

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/bedrockagentruntime"
	"github.com/aws/aws-sdk-go-v2/service/bedrockagentruntime/types"
)

var (
	bedrockClient   *bedrockagentruntime.Client
	bedrockAgentId  string
	bedrockAliasId  string
)

func initBedrockClient(ctx context.Context) error {
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return fmt.Errorf("failed to load AWS config: %w", err)
	}

	bedrockClient = bedrockagentruntime.NewFromConfig(cfg)
	bedrockAgentId = os.Getenv("BEDROCK_AGENT_ID")
	bedrockAliasId = os.Getenv("BEDROCK_AGENT_ALIAS_ID")

	if bedrockAgentId == "" || bedrockAliasId == "" {
		return fmt.Errorf("BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set")
	}

	log.Printf("Bedrock client initialized: agentId=%s, aliasId=%s", bedrockAgentId, bedrockAliasId)
	return nil
}

// BedrockAgentResponse represents the response from invoking the agent
type BedrockAgentResponse struct {
	Completion      string `json:"completion"`
	SessionId       string `json:"sessionId"`
	RequiresHandoff bool   `json:"requiresHandoff"`
	HandoffReason   string `json:"handoffReason,omitempty"`
}

// InvokeBedrockAgent calls the Bedrock Agent and returns the response
func InvokeBedrockAgent(ctx context.Context, sessionId, inputText string, sessionAttrs map[string]string) (*BedrockAgentResponse, error) {
	if bedrockClient == nil {
		return nil, fmt.Errorf("bedrock client not initialized")
	}

	log.Printf("[%s] Invoking Bedrock Agent with input: %s", sessionId, inputText)

	input := &bedrockagentruntime.InvokeAgentInput{
		AgentId:      aws.String(bedrockAgentId),
		AgentAliasId: aws.String(bedrockAliasId),
		SessionId:    aws.String(sessionId),
		InputText:    aws.String(inputText),
	}

	// Add session attributes if provided
	if len(sessionAttrs) > 0 {
		input.SessionState = &types.SessionState{
			SessionAttributes: sessionAttrs,
		}
	}

	output, err := bedrockClient.InvokeAgent(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to invoke agent: %w", err)
	}

	// Process the streaming response
	response := &BedrockAgentResponse{
		SessionId: sessionId,
	}

	var completionBuilder strings.Builder

	// Read from the event stream
	stream := output.GetStream()
	defer stream.Close()

	for event := range stream.Events() {
		switch v := event.(type) {
		case *types.ResponseStreamMemberChunk:
			// Append text chunks to build the full response
			if v.Value.Bytes != nil {
				completionBuilder.Write(v.Value.Bytes)
			}

		case *types.ResponseStreamMemberTrace:
			// Log trace information for debugging
			if v.Value.Trace != nil {
				logAgentTrace(sessionId, v.Value.Trace)
			}

		case *types.ResponseStreamMemberReturnControl:
			// Agent wants to return control (e.g., for handoff)
			log.Printf("[%s] Agent returning control", sessionId)
			response.RequiresHandoff = true
			response.HandoffReason = "Agent requested control return"
		}
	}

	// Check for stream errors
	if err := stream.Err(); err != nil {
		return nil, fmt.Errorf("stream error: %w", err)
	}

	response.Completion = strings.TrimSpace(completionBuilder.String())

	// Check if the response indicates a handoff
	if containsHandoffSignal(response.Completion) {
		response.RequiresHandoff = true
		response.HandoffReason = "Agent initiated handoff"
	}

	log.Printf("[%s] Agent response: %s", sessionId, response.Completion)

	return response, nil
}

func logAgentTrace(sessionId string, trace *types.Trace) {
	// Log orchestration trace for debugging
	if trace.OrchestrationTrace != nil {
		ot := trace.OrchestrationTrace
		
		if ot.ModelInvocationInput != nil {
			log.Printf("[%s] Trace - Model invocation input received", sessionId)
		}
		
		if ot.Rationale != nil && ot.Rationale.Text != nil {
			log.Printf("[%s] Trace - Rationale: %s", sessionId, *ot.Rationale.Text)
		}
		
		if ot.InvocationInput != nil {
			if ot.InvocationInput.ActionGroupInvocationInput != nil {
				agi := ot.InvocationInput.ActionGroupInvocationInput
				log.Printf("[%s] Trace - Action invocation: %s / %s", 
					sessionId, 
					aws.ToString(agi.ActionGroupName),
					aws.ToString(agi.ApiPath))
			}
		}
		
		if ot.Observation != nil {
			if ot.Observation.ActionGroupInvocationOutput != nil {
				log.Printf("[%s] Trace - Action output received", sessionId)
			}
			if ot.Observation.FinalResponse != nil {
				log.Printf("[%s] Trace - Final response generated", sessionId)
			}
		}
	}
}

func containsHandoffSignal(text string) bool {
	handoffPhrases := []string{
		"connect you with a human",
		"transfer you to",
		"human receptionist",
		"TRANSFER_TO_HUMAN",
		"HANDOFF_INITIATED",
	}

	lowerText := strings.ToLower(text)
	for _, phrase := range handoffPhrases {
		if strings.Contains(lowerText, strings.ToLower(phrase)) {
			return true
		}
	}
	return false
}

// EndBedrockSession explicitly ends a session (optional - sessions auto-expire)
func EndBedrockSession(sessionId string) {
	log.Printf("[%s] Session ended", sessionId)
	// Bedrock Agent sessions auto-expire based on IdleSessionTTL
	// No explicit end session API call needed
}
```

### 9.4 Updated handle_ws.go (Using Bedrock Agent)

Create `media-gateway-go/handle_ws.go`:

```go
package main

import (
	"context"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  16384,
	WriteBufferSize: 16384,
}

// TenantInfo holds tenant configuration
type TenantInfo struct {
	TenantId     string `json:"tenantId"`
	DisplayName  string `json:"displayName"`
	PollyVoiceId string `json:"pollyVoiceId"`
	PollyEngine  string `json:"pollyEngine"`
	Greeting     string `json:"greeting"`
}

// CallSession represents an active call
type CallSession struct {
	CallID      string
	DID         string
	Tenant      *TenantInfo
	Ctx         context.Context
	Cancel      context.CancelFunc
	WS          *websocket.Conn
	BotSpeaking atomic.Bool
	AudioCh     chan []byte
	WriteMu     sync.Mutex
}

func HandleAudioWS(w http.ResponseWriter, r *http.Request) {
	callID := r.URL.Query().Get("callId")
	did := r.URL.Query().Get("did")

	if callID == "" || did == "" {
		log.Printf("Missing callId or did in request")
		http.Error(w, "missing callId or did", http.StatusBadRequest)
		return
	}

	log.Printf("New WebSocket connection: callId=%s, did=%s", callID, did)

	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}

	ctx, cancel := context.WithCancel(context.Background())

	// Resolve tenant from DID
	tenant, err := resolveTenant(ctx, did)
	if err != nil {
		log.Printf("Failed to resolve tenant for DID %s: %v", did, err)
		tenant = &TenantInfo{
			TenantId:     "default",
			DisplayName:  "Medical Clinic",
			PollyVoiceId: "Joanna",
			PollyEngine:  "neural",
			Greeting:     "Hello! How can I help you today?",
		}
	}

	session := &CallSession{
		CallID:  callID,
		DID:     did,
		Tenant:  tenant,
		Ctx:     ctx,
		Cancel:  cancel,
		WS:      ws,
		AudioCh: make(chan []byte, 128),
	}

	defer func() {
		cancel()
		close(session.AudioCh)
		ws.Close()
		EndBedrockSession(callID)
		log.Printf("Call ended: %s", callID)
	}()

	// Start Transcribe streaming in background
	go session.startTranscribeStream()

	// Send initial greeting
	go func() {
		time.Sleep(500 * time.Millisecond)
		session.processInitialGreeting()
	}()

	// Read audio frames from FreeSWITCH
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		ws.SetReadDeadline(time.Now().Add(30 * time.Second))
		mt, data, err := ws.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("WebSocket read error: %v", err)
			}
			return
		}

		if mt != websocket.BinaryMessage {
			continue
		}

		select {
		case session.AudioCh <- data:
		default:
		}
	}
}

func (s *CallSession) startTranscribeStream() {
	err := StartTranscribe(
		s.Ctx,
		transcribeClient,
		s.AudioCh,
		func(text string) {
			log.Printf("[%s] Final transcript: %s", s.CallID, text)
			if text != "" {
				s.processAgentTurn(text)
			}
		},
		func() {
			if s.BotSpeaking.Load() {
				log.Printf("[%s] Barge-in detected", s.CallID)
				s.BotSpeaking.Store(false)
				ESLUuidBreak(s.CallID, eslConfig)
			}
		},
	)

	if err != nil {
		log.Printf("[%s] Transcribe error: %v", s.CallID, err)
	}
}

func (s *CallSession) processInitialGreeting() {
	// Use tenant-specific greeting for first turn
	// The Bedrock Agent will handle subsequent turns
	
	// Create session attributes with tenant context
	sessionAttrs := map[string]string{
		"tenant_id":    s.Tenant.TenantId,
		"tenant_name":  s.Tenant.DisplayName,
		"polly_voice":  s.Tenant.PollyVoiceId,
		"polly_engine": s.Tenant.PollyEngine,
	}

	// First turn: Send empty input to trigger agent's greeting
	// Or use the configured greeting directly
	resp, err := InvokeBedrockAgent(s.Ctx, s.CallID, "Start conversation", sessionAttrs)
	
	var greeting string
	if err != nil {
		log.Printf("[%s] Failed to get agent greeting: %v", s.CallID, err)
		greeting = s.Tenant.Greeting
	} else if resp.Completion != "" {
		greeting = resp.Completion
	} else {
		greeting = s.Tenant.Greeting
	}

	s.speakResponse(greeting)
}

func (s *CallSession) processAgentTurn(userText string) {
	sessionAttrs := map[string]string{
		"tenant_id":   s.Tenant.TenantId,
		"tenant_name": s.Tenant.DisplayName,
	}

	resp, err := InvokeBedrockAgent(s.Ctx, s.CallID, userText, sessionAttrs)
	if err != nil {
		log.Printf("[%s] Agent error: %v", s.CallID, err)
		s.speakResponse("I'm sorry, I'm having trouble right now. Could you please repeat that?")
		return
	}

	if resp.Completion != "" {
		s.speakResponse(resp.Completion)
	}

	if resp.RequiresHandoff {
		log.Printf("[%s] Handoff required: %s", s.CallID, resp.HandoffReason)
		// In production, would initiate actual call transfer here
		time.Sleep(2 * time.Second)
		s.Cancel()
	}

	// Check for end-of-call signals
	if containsEndCallSignal(resp.Completion) {
		log.Printf("[%s] End of call detected", s.CallID)
		time.Sleep(3 * time.Second) // Let final speech play
		s.Cancel()
	}
}

func (s *CallSession) speakResponse(text string) {
	s.BotSpeaking.Store(true)
	defer s.BotSpeaking.Store(false)

	log.Printf("[%s] Speaking: %s", s.CallID, text)

	// Optimize text for speech
	optimizedText := optimizeForSpeech(text)

	audioStream, err := PollyPCMStream(s.Ctx, pollyClient, s.Tenant.PollyVoiceId, s.Tenant.PollyEngine, optimizedText)
	if err != nil {
		log.Printf("[%s] Polly error: %v", s.CallID, err)
		return
	}
	defer audioStream.Close()

	buf := make([]byte, 3200) // ~200ms at 8kHz 16-bit mono
	for {
		if !s.BotSpeaking.Load() {
			log.Printf("[%s] Playback interrupted", s.CallID)
			break
		}

		n, err := audioStream.Read(buf)
		if n > 0 {
			s.WriteMu.Lock()
			writeErr := s.WS.WriteMessage(websocket.BinaryMessage, buf[:n])
			s.WriteMu.Unlock()

			if writeErr != nil {
				log.Printf("[%s] WebSocket write error: %v", s.CallID, writeErr)
				break
			}
		}

		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("[%s] Audio read error: %v", s.CallID, err)
			break
		}

		time.Sleep(20 * time.Millisecond)
	}
}

func resolveTenant(ctx context.Context, did string) (*TenantInfo, error) {
	url := tenantConfigURL + "/v1/tenants/resolve?did=" + did

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("tenant not found: status %d", resp.StatusCode)
	}

	var tenant TenantInfo
	if err := json.NewDecoder(resp.Body).Decode(&tenant); err != nil {
		return nil, err
	}

	return &tenant, nil
}

func containsEndCallSignal(text string) bool {
	endPhrases := []string{
		"have a great day",
		"goodbye",
		"take care",
		"thank you for calling",
	}

	lowerText := strings.ToLower(text)
	for _, phrase := range endPhrases {
		if strings.Contains(lowerText, phrase) {
			return true
		}
	}
	return false
}

func optimizeForSpeech(text string) string {
	// Remove any markdown or formatting
	text = strings.ReplaceAll(text, "**", "")
	text = strings.ReplaceAll(text, "*", "")
	text = strings.ReplaceAll(text, "#", "")
	
	// Convert common abbreviations
	text = strings.ReplaceAll(text, "Dr.", "Doctor")
	text = strings.ReplaceAll(text, "Mr.", "Mister")
	text = strings.ReplaceAll(text, "Mrs.", "Missus")
	text = strings.ReplaceAll(text, "Ms.", "Miss")
	
	return strings.TrimSpace(text)
}
```

### 9.5 Updated main.go (Media Gateway)

Create `media-gateway-go/main.go`:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/polly"
	"github.com/aws/aws-sdk-go-v2/service/transcribestreaming"
)

var (
	transcribeClient *transcribestreaming.Client
	pollyClient      *polly.Client
	eslConfig        ESLConfig
	tenantConfigURL  string
)

type ESLConfig struct {
	Host     string
	Port     string
	Password string
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Println("Starting Media Gateway with Bedrock Agent integration...")

	ctx := context.Background()

	// Load AWS config
	awsCfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Fatalf("Failed to load AWS config: %v", err)
	}

	// Initialize AWS clients
	transcribeClient = transcribestreaming.NewFromConfig(awsCfg)
	pollyClient = polly.NewFromConfig(awsCfg)

	// Initialize Bedrock client
	if err := initBedrockClient(ctx); err != nil {
		log.Fatalf("Failed to initialize Bedrock client: %v", err)
	}

	// Load configuration from environment
	eslConfig = ESLConfig{
		Host:     getEnv("FREESWITCH_ESL_HOST", "freeswitch"),
		Port:     getEnv("FREESWITCH_ESL_PORT", "8021"),
		Password: getEnv("FREESWITCH_ESL_PASSWORD", "ClueCon"),
	}

	tenantConfigURL = getEnv("TENANT_CONFIG_URL", "http://tenant-config-go:7001")

	// Setup HTTP server
	mux := http.NewServeMux()
	mux.HandleFunc("/health", handleHealth)
	mux.HandleFunc("/ws/audio", HandleAudioWS)

	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	// Graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
		<-sigChan

		log.Println("Shutting down...")
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		server.Shutdown(ctx)
	}()

	log.Println("Media Gateway listening on :8080")
	log.Printf("Bedrock Agent ID: %s", bedrockAgentId)
	log.Printf("Bedrock Agent Alias: %s", bedrockAliasId)

	if err := server.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(fmt.Sprintf(`{"status":"healthy","agentId":"%s"}`, bedrockAgentId)))
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
```

### 9.6 go.mod for Media Gateway

Create `media-gateway-go/go.mod`:

```go
module media-gateway-go

go 1.22

require (
	github.com/aws/aws-sdk-go-v2 v1.30.0
	github.com/aws/aws-sdk-go-v2/config v1.27.24
	github.com/aws/aws-sdk-go-v2/service/bedrockagentruntime v1.20.0
	github.com/aws/aws-sdk-go-v2/service/polly v1.28.0
	github.com/aws/aws-sdk-go-v2/service/transcribestreaming v1.26.0
	github.com/gorilla/websocket v1.5.3
)
```

---

## 10. Bedrock Agent Configuration

### 10.1 Post-Deployment Setup

After CDK deployment, you need to:

1. **Prepare the Agent**
```bash
# Get Agent ID from CDK output
AGENT_ID=$(aws cloudformation describe-stacks \
  --stack-name IvrBedrockAgentStack \
  --query "Stacks[0].Outputs[?OutputKey=='AgentId'].OutputValue" \
  --output text)

# Prepare the agent (required after changes)
aws bedrock-agent prepare-agent --agent-id $AGENT_ID
```

2. **Update Environment Variables**
```bash
# Get Agent Alias ID
ALIAS_ID=$(aws cloudformation describe-stacks \
  --stack-name IvrBedrockAgentStack \
  --query "Stacks[0].Outputs[?OutputKey=='AgentAliasId'].OutputValue" \
  --output text)

# Update .env file
echo "BEDROCK_AGENT_ID=$AGENT_ID" >> .env
echo "BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID" >> .env
```

### 10.2 Testing the Agent (Console)

You can test the agent directly in AWS Console:

1. Go to Amazon Bedrock → Agents
2. Select your agent
3. Click "Test" in the right panel
4. Try conversations:
   - "I want to book an appointment"
   - "Tomorrow morning please"
   - "The 9:30 slot"
   - "My name is John Smith"
   - "john@example.com"

### 10.3 Testing via CLI

```bash
# Test agent invocation
aws bedrock-agent-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --agent-alias-id $ALIAS_ID \
  --session-id "test-session-001" \
  --input-text "I want to book an appointment for tomorrow morning"
```

---

## 11. Execution Steps

### Step 1: Deploy Infrastructure

```bash
cd infrastructure
npm install
npm run build

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy stacks
cdk deploy --all
```

### Step 2: Prepare Bedrock Agent

```bash
# Get outputs and prepare agent
./scripts/deploy.sh
```

### Step 3: Update Environment

```bash
# Copy template and fill in values from CDK outputs
cp .env.example .env
# Edit .env with BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID
```

### Step 4: Start Local Services

```bash
docker compose up --build
```

### Step 5: Configure Softphone

| Setting | Value |
|---------|-------|
| Username | 1000 |
| Password | 1234 |
| Server | localhost:5060 |
| Transport | UDP |

### Step 6: Make Test Calls

```bash
# Dial 1001 for Clinic A
# Dial 1002 for Clinic B
```

---

## 12. Testing & Validation

### 12.1 Test Script

Create `scripts/test_agent.sh`:

```bash
#!/bin/bash
set -e

echo "Testing Bedrock Agent..."

# Load environment
source .env

# Test 1: Agent greeting
echo "Test 1: Initial greeting"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id "test-$(date +%s)" \
  --input-text "Hello" \
  --output text

# Test 2: Booking flow
SESSION_ID="booking-test-$(date +%s)"
echo ""
echo "Test 2: Booking flow (session: $SESSION_ID)"

echo "Turn 1: Request appointment"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "I want to book an appointment for tomorrow morning" \
  --output text

sleep 2

echo ""
echo "Turn 2: Select slot"
aws bedrock-agent-runtime invoke-agent \
  --agent-id $BEDROCK_AGENT_ID \
  --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
  --session-id $SESSION_ID \
  --input-text "The 9:30 AM slot please" \
  --output text

echo ""
echo "Tests completed!"
```

### 12.2 Integration Test

Create `scripts/test_integration.sh`:

```bash
#!/bin/bash
set -e

echo "Running Integration Tests..."

# Test local services
echo "1. Testing Tenant Config..."
curl -s http://localhost:7001/health | jq .

echo "2. Testing Appointment Service..."
curl -s http://localhost:7002/health | jq .

echo "3. Testing Media Gateway..."
curl -s http://localhost:8080/health | jq .

echo "4. Testing slot search..."
curl -s -X POST http://localhost:7002/v1/slots/search \
  -H "Content-Type: application/json" \
  -d '{"tenantId":"clinic_a","date":"tomorrow","timePreference":"morning"}' | jq .

echo ""
echo "All integration tests passed!"
```

---

## 13. Milestones & Grading

### Milestone A: Infrastructure (20%)
| Criteria | Points |
|----------|--------|
| CDK deploys successfully | 5 |
| Lambda functions created | 5 |
| Bedrock Agent configured | 5 |
| IAM permissions correct | 5 |

### Milestone B: Bedrock Agent (25%)
| Criteria | Points |
|----------|--------|
| Agent understands booking intent | 5 |
| Action groups invoke correctly | 10 |
| Multi-turn conversation works | 5 |
| Session state maintained | 5 |

### Milestone C: Telephony (20%)
| Criteria | Points |
|----------|--------|
| FreeSWITCH routes calls | 5 |
| Audio streams correctly | 5 |
| Transcribe produces transcripts | 5 |
| Polly generates audio | 5 |

### Milestone D: Integration (20%)
| Criteria | Points |
|----------|--------|
| End-to-end booking works | 10 |
| Barge-in functions | 5 |
| Multi-tenant routing | 5 |

### Milestone E: Quality (15%)
| Criteria | Points |
|----------|--------|
| Clean code | 5 |
| Error handling | 5 |
| Documentation | 5 |

---

## 14. Troubleshooting Guide

### Common Issues

#### 1. "Agent not found" error
```bash
# Verify agent exists
aws bedrock-agent list-agents

# Check agent status
aws bedrock-agent get-agent --agent-id $BEDROCK_AGENT_ID
```

#### 2. "Access denied" invoking agent
```bash
# Ensure IAM permissions include:
# - bedrock:InvokeAgent
# - bedrock:InvokeModel
```

#### 3. Lambda action not invoked
- Check Lambda permissions include Bedrock service principal
- Verify OpenAPI schema matches Lambda handler expectations
- Check CloudWatch logs for Lambda errors

#### 4. Agent returns empty response
```bash
# Prepare agent after any changes
aws bedrock-agent prepare-agent --agent-id $BEDROCK_AGENT_ID

# Wait for PREPARED status
aws bedrock-agent get-agent --agent-id $BEDROCK_AGENT_ID \
  --query "agent.agentStatus"
```

---

## 15. Deliverables

1. **Repository** with all code
2. **Working CDK deployment**
3. **Demo video** showing:
   - CDK deployment
   - Agent test in console
   - Full phone conversation
4. **Documentation**:
   - Setup instructions
   - Architecture diagram
   - Cost analysis

---

