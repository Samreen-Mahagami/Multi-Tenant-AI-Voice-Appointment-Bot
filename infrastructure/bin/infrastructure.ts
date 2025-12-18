#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BedrockAgentStack } from '../lib/bedrock-agent-stack';
import { LambdaStack } from '../lib/lambda-stack';
import { GoServicesStack } from '../lib/go-services-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

// Deploy Go backend services first
const goServicesStack = new GoServicesStack(app, 'IvrGoServicesStack', { env });

// Deploy Lambda functions (with updated environment variables)
const lambdaStack = new LambdaStack(app, 'IvrLambdaStack', { 
  env,
  appointmentServiceUrl: goServicesStack.appointmentServiceUrl,
});

// Deploy Bedrock Agent
const agentStack = new BedrockAgentStack(app, 'IvrBedrockAgentStack', {
  env,
  searchSlotsFunction: lambdaStack.searchSlotsFunction,
  confirmAppointmentFunction: lambdaStack.confirmAppointmentFunction,
  handoffHumanFunction: lambdaStack.handoffHumanFunction,
});

lambdaStack.addDependency(goServicesStack);
agentStack.addDependency(lambdaStack);

app.synth();