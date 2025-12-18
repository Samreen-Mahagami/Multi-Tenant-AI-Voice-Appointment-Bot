import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class VoiceStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Lambda function for voice processing
    const voiceProcessorFunction = new lambda.Function(this, 'VoiceProcessorFunction', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('../lambda/voice-processor'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        BEDROCK_AGENT_ID: 'S2MOVY5G8J',
        BEDROCK_AGENT_ALIAS_ID: 'XOOC4XVDXZ',
        TENANT_CONFIG_URL: 'https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod',
        APPOINTMENT_SERVICE_URL: 'https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod'
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    // IAM role for voice processor
    voiceProcessorFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeAgent',
        'bedrock:InvokeModel',
        'polly:SynthesizeSpeech',
        'transcribe:StartTranscriptionJob',
        'transcribe:GetTranscriptionJob',
        'connect:*'
      ],
      resources: ['*']
    }));

    // Output the function ARN for Connect integration
    new cdk.CfnOutput(this, 'VoiceProcessorFunctionArn', {
      value: voiceProcessorFunction.functionArn,
      description: 'ARN of the voice processor Lambda function'
    });

    new cdk.CfnOutput(this, 'VoiceProcessorFunctionName', {
      value: voiceProcessorFunction.functionName,
      description: 'Name of the voice processor Lambda function'
    });
  }
}