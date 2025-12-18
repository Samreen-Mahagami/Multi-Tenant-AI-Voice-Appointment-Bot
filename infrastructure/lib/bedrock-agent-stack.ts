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