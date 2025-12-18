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