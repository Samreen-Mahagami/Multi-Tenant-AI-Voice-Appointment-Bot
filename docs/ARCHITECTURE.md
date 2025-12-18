# Multi-Tenant AI Voice Appointment Bot - Architecture

## Phase 1: Current Implementation (COMPLETED ✅)

### AI Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  AWS CLOUD                                       │
│                               Account: 089580247707                              │
│                                Region: us-east-1                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        AMAZON BEDROCK AGENTS                             │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │                    APPOINTMENT BOOKING AGENT                     │    │    │
│  │  │                                                                  │    │    │
│  │  │  Agent ID: S2MOVY5G8J                                           │    │    │
│  │  │  Alias ID: XOOC4XVDXZ                                           │    │    │
│  │  │  Model: Claude 3 Haiku                                          │    │    │
│  │  │  Status: PREPARED ✅                                            │    │    │
│  │  │                                                                  │    │    │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │    │    │
│  │  │  │ searchSlots  │ │confirmAppt   │ │ handoffToHuman       │    │    │    │
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
│  │  │ ivr-search-     │  │ ivr-confirm-    │  │ ivr-handoff-    │          │    │
│  │  │ slots           │  │ appointment     │  │ human           │          │    │
│  │  │                 │  │                 │  │                 │          │    │
│  │  │ Status: ✅      │  │ Status: ✅      │  │ Status: ✅      │          │    │
│  │  │ Returns: Mock   │  │ Returns: Mock   │  │ Returns: Signal │          │    │
│  │  │ Appointment     │  │ Confirmation    │  │ for Transfer    │          │    │
│  │  │ Slots           │  │ Numbers         │  │                 │          │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘          │    │
│  │                                                                          │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

                                    ▲
                                    │
                              Text Input/Output
                                    │
                            ┌───────────────┐
                            │  Test Client  │
                            │  (AWS CLI)    │
                            └───────────────┘
```

### Current Data Flow

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│             │    │                 │    │                 │    │                 │
│ Text Input  │───▶│ Bedrock Agent   │───▶│ Lambda Function │───▶│ Mock Response   │
│             │    │                 │    │                 │    │                 │
│ "Book appt" │    │ - Understands   │    │ - searchSlots   │    │ - 3 time slots  │
│             │    │ - Reasons       │    │ - confirmAppt   │    │ - Confirmation  │
│             │    │ - Decides       │    │ - handoffHuman  │    │ - Transfer msg  │
│             │    │ - Responds      │    │                 │    │                 │
└─────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Complete System Architecture (Target)

### Full Voice Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  CALLER                                          │
│                              (Phone System)                                      │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │ SIP Call
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TELEPHONY LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                          FREESWITCH                                      │    │
│  │                                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │    │
│  │  │ SIP Endpoint    │  │ Dialplan        │  │ mod_audio_stream│          │    │
│  │  │                 │  │                 │  │                 │          │    │
│  │  │ - Receives calls│  │ - Routes by DID │  │ - Streams audio │          │    │
│  │  │ - Manages audio │  │ - Multi-tenant  │  │ - WebSocket     │          │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────┬───────┘          │    │
│  │                                                      │                  │    │
│  └──────────────────────────────────────────────────────┼──────────────────┘    │
│                                                         │                       │
└─────────────────────────────────────────────────────────┼───────────────────────┘
                                                          │ WebSocket Audio
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            MEDIA GATEWAY (Go)                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ WebSocket       │  │ Session Manager │  │ Audio Processor │                  │
│  │ Handler         │  │                 │  │                 │                  │
│  │                 │  │ - Call tracking │  │ - Format convert│                  │
│  │ - Receives audio│  │ - State mgmt    │  │ - Barge-in      │                  │
│  │ - Sends audio   │  │ - Tenant lookup │  │ - Buffer mgmt   │                  │
│  └─────────┬───────┘  └─────────────────┘  └─────────┬───────┘                  │
│            │                                         │                          │
│            ▼                                         ▼                          │
│  ┌─────────────────┐                       ┌─────────────────┐                  │
│  │ Transcribe      │                       │ Polly Client    │                  │
│  │ Client          │                       │                 │                  │
│  │                 │                       │ - Text to Speech│                  │
│  │ - Speech to Text│                       │ - Neural voices │                  │
│  │ - Real-time     │                       │ - Streaming     │                  │
│  └─────────┬───────┘                       └─────────▲───────┘                  │
│            │                                         │                          │
│            ▼                                         │                          │
│  ┌─────────────────┐                                 │                          │
│  │ Bedrock Agent   │─────────────────────────────────┘                          │
│  │ Client          │                                                            │
│  │                 │                                                            │
│  │ - Send text     │                                                            │
│  │ - Receive resp  │                                                            │
│  │ - Session mgmt  │                                                            │
│  └─────────┬───────┘                                                            │
│            │                                                                    │
└────────────┼────────────────────────────────────────────────────────────────────┘
             │ HTTP/HTTPS
             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Amazon          │  │ Amazon Bedrock  │  │ Amazon Polly    │                  │
│  │ Transcribe      │  │ Agents          │  │                 │                  │
│  │                 │  │                 │  │ - Neural TTS    │                  │
│  │ - Streaming STT │  │ - Claude 3      │  │ - Multiple      │                  │
│  │ - Real-time     │  │ - Conversation  │  │   voices        │                  │
│  │ - Punctuation   │  │ - Tool calling  │  │ - SSML support  │                  │
│  └─────────────────┘  └─────────┬───────┘  └─────────────────┘                  │
│                                 │                                               │
│                                 ▼                                               │
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
└──────────────┼────────────────────┼──────────────────────────────────────────────┘
               │ HTTP               │ HTTP
               ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND SERVICES (Go)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐│
│  │       Appointment Service            │  │       Tenant Config Service         ││
│  │                                     │  │                                     ││
│  │  ┌─────────────────────────────┐    │  │  ┌─────────────────────────────┐    ││
│  │  │ Slot Management             │    │  │  │ DID → Tenant Mapping        │    ││
│  │  │ - Search availability       │    │  │  │ - Clinic configurations     │    ││
│  │  │ - Book appointments         │    │  │  │ - Voice preferences         │    ││
│  │  │ - Generate confirmations    │    │  │  │ - Business hours            │    ││
│  │  └─────────────────────────────┘    │  │  └─────────────────────────────┘    ││
│  │                                     │  │                                     ││
│  │  ┌─────────────────────────────┐    │  │  ┌─────────────────────────────┐    ││
│  │  │ Database                    │    │  │  │ Configuration Store         │    ││
│  │  │ - Appointments table        │    │  │  │ - YAML/JSON configs         │    ││
│  │  │ - Doctors table             │    │  │  │ - Runtime updates           │    ││
│  │  │ - Slots table               │    │  │  │ - Multi-tenant isolation    │    ││
│  │  └─────────────────────────────┘    │  │  └─────────────────────────────┘    ││
│  └─────────────────────────────────────┘  └─────────────────────────────────────┘│
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Tenant Call Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│ Caller A    │───▶│ DID: 1001   │───▶│ Tenant: A   │───▶│ Dr. Smith   │
│ 555-0001    │    │ (Clinic A)  │    │ Config      │    │ Appointments│
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│ Caller B    │───▶│ DID: 1002   │───▶│ Tenant: B   │───▶│ Dr. Johnson │
│ 555-0002    │    │ (Clinic B)  │    │ Config      │    │ Appointments│
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## Component Interaction Diagram

### Real-Time Call Processing

```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Caller  │  │FreeSWITCH│  │ Media   │  │Transcribe│  │Bedrock  │  │ Lambda  │
│         │  │         │  │Gateway  │  │         │  │ Agent   │  │Functions│
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │            │            │
     │ SIP Call   │            │            │            │            │
     │───────────▶│            │            │            │            │
     │            │ WebSocket  │            │            │            │
     │            │───────────▶│            │            │            │
     │            │            │ Audio      │            │            │
     │ Audio ─────┼───────────▶│───────────▶│            │            │
     │            │            │            │ Text       │            │
     │            │            │            │───────────▶│            │
     │            │            │            │            │ Action     │
     │            │            │            │            │───────────▶│
     │            │            │            │            │ Result     │
     │            │            │            │            │◀───────────│
     │            │            │            │ Response   │            │
     │            │            │            │◀───────────│            │
     │            │            │ TTS Req    │            │            │
     │            │            │───────────▶│            │            │
     │            │            │ Audio      │            │            │
     │            │ Audio      │◀───────────│            │            │
     │ Audio ◀────┼────────────│            │            │            │
     │            │            │            │            │            │
```

### Session State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                    BEDROCK AGENT SESSION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Session ID: call-12345                                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Turn 1: "I want an appointment"                         │    │
│  │ → Agent: Calls searchSlots                              │    │
│  │ → Response: "Available at 9 AM, 10 AM"                 │    │
│  │ → Memory: [intent=book, slots=[9AM,10AM]]               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Turn 2: "9 AM please"                                   │    │
│  │ → Agent: Remembers slots from Turn 1                   │    │
│  │ → Response: "What's your name?"                         │    │
│  │ → Memory: [intent=book, selected_slot=9AM]              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Turn 3: "John Smith"                                    │    │
│  │ → Agent: Remembers slot selection                      │    │
│  │ → Response: "Your email?"                               │    │
│  │ → Memory: [slot=9AM, name="John Smith"]                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Turn 4: "john@example.com"                              │    │
│  │ → Agent: Has all info, calls confirmAppointment        │    │
│  │ → Response: "Confirmed! Ref: ABC-123"                   │    │
│  │ → Memory: [booking_complete=true, ref="ABC-123"]        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Infrastructure as Code (CDK)

```
┌─────────────────────────────────────────────────────────────────┐
│                        CDK APPLICATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   LAMBDA STACK                          │    │
│  │                                                         │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │    │
│  │  │ SearchSlots │ │ConfirmAppt  │ │HandoffHuman │       │    │
│  │  │ Lambda      │ │ Lambda      │ │ Lambda      │       │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │    │
│  │                                                         │    │
│  │  Exports: Function ARNs                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼ (dependency)                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                BEDROCK AGENT STACK                      │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ IAM Role                                        │    │    │
│  │  │ - Bedrock model permissions                     │    │    │
│  │  │ - Lambda invoke permissions                     │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ Bedrock Agent                                   │    │    │
│  │  │ - Instructions (system prompt)                  │    │    │
│  │  │ - Action groups (OpenAPI schema)                │    │    │
│  │  │ - Lambda function connections                   │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ Agent Alias                                     │    │    │
│  │  │ - Production endpoint                           │    │    │
│  │  │ - Version management                            │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                         │    │
│  │  Exports: Agent ID, Alias ID                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (deploys to)
┌─────────────────────────────────────────────────────────────────┐
│                      AWS CLOUDFORMATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Stack: IvrLambdaStack                                          │
│  Stack: IvrBedrockAgentStack                                    │
│                                                                 │
│  Resources: 10+ AWS resources created                           │
│  Status: CREATE_COMPLETE ✅                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### IAM Permissions Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY BOUNDARIES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 BEDROCK AGENT ROLE                      │    │
│  │                                                         │    │
│  │  Permissions:                                           │    │
│  │  ✅ bedrock:InvokeModel (Claude 3 Haiku only)          │    │
│  │  ✅ lambda:InvokeFunction (3 specific functions)       │    │
│  │  ✅ logs:CreateLogGroup, logs:CreateLogStream          │    │
│  │  ✅ logs:PutLogEvents                                  │    │
│  │                                                         │    │
│  │  Trusted Entity: bedrock.amazonaws.com                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼ (assumes)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 LAMBDA EXECUTION ROLES                  │    │
│  │                                                         │    │
│  │  Each Lambda has its own role with:                    │    │
│  │  ✅ logs:CreateLogGroup, logs:CreateLogStream          │    │
│  │  ✅ logs:PutLogEvents                                  │    │
│  │  ✅ Network access to backend services                 │    │
│  │                                                         │    │
│  │  Trusted Entity: lambda.amazonaws.com                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 RESOURCE POLICIES                       │    │
│  │                                                         │    │
│  │  Lambda Functions:                                      │    │
│  │  ✅ Allow bedrock.amazonaws.com to invoke              │    │
│  │  ✅ Source ARN: arn:aws:bedrock:*:*:agent/*            │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance & Scaling

### Latency Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                      RESPONSE TIME ANALYSIS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Audio Input → Transcribe:           ~100-300ms                 │
│  Transcribe → Bedrock Agent:         ~50ms                     │
│  Agent Processing:                   ~500-1500ms               │
│  ├─ Model Inference:                 ~300-800ms                │
│  ├─ Lambda Invocation:               ~100-500ms                │
│  └─ Response Generation:             ~100-200ms                │
│  Agent → Polly:                      ~50ms                     │
│  Polly TTS Generation:               ~200-500ms                │
│  Audio Playback Start:               ~100ms                    │
│                                                                 │
│  Total End-to-End:                   ~1000-2500ms              │
│  Target: <2000ms for good UX                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Scaling Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                        SCALING BEHAVIOR                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Component          │ Scaling Method    │ Limits               │
│  ──────────────────────────────────────────────────────────────│
│  Bedrock Agent      │ Fully Managed     │ 1000+ concurrent     │
│  Lambda Functions   │ Auto-scaling      │ 1000 concurrent      │
│  Transcribe         │ Fully Managed     │ No practical limit   │
│  Polly              │ Fully Managed     │ No practical limit   │
│  FreeSWITCH         │ Manual scaling    │ ~500 calls/instance  │
│  Media Gateway      │ Horizontal        │ ~100 calls/instance  │
│                                                                 │
│  Bottleneck: Media Gateway & FreeSWITCH (Phase 2)              │
│  Solution: Load balancer + multiple instances                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Analysis

### Current Phase 1 Costs

```
┌─────────────────────────────────────────────────────────────────┐
│                         COST BREAKDOWN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Service              │ Unit Cost        │ Monthly Est.        │
│  ──────────────────────────────────────────────────────────────│
│  Bedrock Agent        │ $0.001/session   │ $10 (10K sessions)  │
│  Claude 3 Haiku       │ $0.0003/1K tok   │ $15 (50K tokens)    │
│  Lambda Invocations   │ $0.0000002/req   │ $1 (5M requests)    │
│  Lambda Compute       │ $0.0000166667/GB │ $5 (300 GB-sec)     │
│  CloudWatch Logs      │ $0.50/GB         │ $2 (4 GB logs)      │
│                                                                 │
│  Total Phase 1:                          │ ~$33/month          │
│                                                                 │
│  Note: Very low cost for AI infrastructure                     │
│  Scales with actual usage (pay per use)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Projected Full System Costs

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL SYSTEM COST PROJECTION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Additional Services  │ Unit Cost        │ Monthly Est.        │
│  ──────────────────────────────────────────────────────────────│
│  Transcribe Streaming │ $0.024/min       │ $240 (10K minutes)  │
│  Polly Neural TTS     │ $0.016/1K chars  │ $80 (5M characters) │
│  EC2 (Media Gateway)  │ $0.0464/hour     │ $35 (t3.medium)     │
│  EC2 (FreeSWITCH)     │ $0.0928/hour     │ $70 (t3.large)      │
│  RDS (Appointments)   │ $0.017/hour      │ $13 (db.t3.micro)   │
│  Data Transfer        │ $0.09/GB         │ $20 (200 GB)        │
│                                                                 │
│  Total Full System:                      │ ~$491/month         │
│                                                                 │
│  Per Call Cost: ~$0.05 (10K calls/month)                      │
│  Break-even vs human: ~200 calls/month                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Development Phases

### Phase 1: AI Infrastructure ✅ COMPLETE

- [x] Bedrock Agent setup
- [x] Lambda functions
- [x] CDK infrastructure
- [x] Testing framework
- [x] Documentation

### Phase 2: Backend Services (NEXT)

- [ ] Go appointment service
- [ ] Go tenant config service
- [ ] Database setup
- [ ] API endpoints
- [ ] Docker containers

### Phase 3: Media Gateway

- [ ] Go media gateway
- [ ] Transcribe integration
- [ ] Polly integration
- [ ] Bedrock client
- [ ] WebSocket handling

### Phase 4: Telephony

- [ ] FreeSWITCH configuration
- [ ] SIP setup
- [ ] Audio routing
- [ ] Multi-tenant dialplan

### Phase 5: Integration & Testing

- [ ] End-to-end testing
- [ ] Load testing
- [ ] Production deployment
- [ ] Monitoring setup

---

This architecture provides a complete view of both the current implementation and the target system, showing how all components work together to create a production-ready AI voice appointment bot.