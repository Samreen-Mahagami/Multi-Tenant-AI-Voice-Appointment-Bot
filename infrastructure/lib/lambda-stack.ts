import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

interface LambdaStackProps extends cdk.StackProps {
  appointmentServiceUrl?: string;
}

export class LambdaStack extends cdk.Stack {
  public readonly searchSlotsFunction: lambda.Function;
  public readonly confirmAppointmentFunction: lambda.Function;
  public readonly handoffHumanFunction: lambda.Function;

  constructor(scope: Construct, id: string, props?: LambdaStackProps) {
    super(scope, id, props);

    // Common Lambda configuration
    const commonProps = {
      runtime: lambda.Runtime.PYTHON_3_11,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        APPOINTMENT_SERVICE_URL: props?.appointmentServiceUrl || 'http://localhost:7002',
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