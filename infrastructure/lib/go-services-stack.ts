import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class GoServicesStack extends cdk.Stack {
  public readonly tenantConfigUrl: string;
  public readonly appointmentServiceUrl: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ===========================================
    // TENANT CONFIG SERVICE (Lambda Function)
    // ===========================================
    
    const tenantConfigFunction = new lambda.DockerImageFunction(this, 'TenantConfigFunction', {
      code: lambda.DockerImageCode.fromImageAsset('../tenant-config-go', {
        file: 'Dockerfile.lambda',
        cmd: ['index.handler']
      }),
      functionName: 'ivr-tenant-config-service',
      description: 'Multi-tenant configuration service for IVR system',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        CONFIG_PATH: '/var/task/tenants.yaml',
        AWS_LAMBDA_EXEC_WRAPPER: '/opt/bootstrap'
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    // API Gateway for Tenant Config Service
    const tenantConfigApi = new apigateway.RestApi(this, 'TenantConfigApi', {
      restApiName: 'IVR Tenant Config Service',
      description: 'API for tenant configuration and DID resolution',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    const tenantConfigIntegration = new apigateway.LambdaIntegration(tenantConfigFunction, {
      requestTemplates: { 'application/json': '{ "statusCode": "200" }' },
    });

    // Add proxy resource to handle all paths
    const tenantConfigProxy = tenantConfigApi.root.addResource('{proxy+}');
    tenantConfigProxy.addMethod('ANY', tenantConfigIntegration);
    tenantConfigApi.root.addMethod('ANY', tenantConfigIntegration);

    // ===========================================
    // APPOINTMENT SERVICE (Lambda Function)
    // ===========================================
    
    const appointmentServiceFunction = new lambda.DockerImageFunction(this, 'AppointmentServiceFunction', {
      code: lambda.DockerImageCode.fromImageAsset('../appointment-service-go', {
        file: 'Dockerfile.lambda',
        cmd: ['index.handler']
      }),
      functionName: 'ivr-appointment-service',
      description: 'Appointment booking and slot management service',
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      environment: {
        TENANT_CONFIG_URL: tenantConfigApi.url,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    // API Gateway for Appointment Service
    const appointmentServiceApi = new apigateway.RestApi(this, 'AppointmentServiceApi', {
      restApiName: 'IVR Appointment Service',
      description: 'API for appointment booking and slot management',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    const appointmentServiceIntegration = new apigateway.LambdaIntegration(appointmentServiceFunction, {
      requestTemplates: { 'application/json': '{ "statusCode": "200" }' },
    });

    // Add proxy resource to handle all paths
    const appointmentServiceProxy = appointmentServiceApi.root.addResource('{proxy+}');
    appointmentServiceProxy.addMethod('ANY', appointmentServiceIntegration);
    appointmentServiceApi.root.addMethod('ANY', appointmentServiceIntegration);

    // ===========================================
    // OUTPUTS
    // ===========================================
    
    this.tenantConfigUrl = tenantConfigApi.url;
    this.appointmentServiceUrl = appointmentServiceApi.url;

    new cdk.CfnOutput(this, 'TenantConfigServiceUrl', {
      value: this.tenantConfigUrl,
      description: 'URL for the Tenant Configuration Service API',
      exportName: 'IVR-TenantConfigServiceUrl',
    });

    new cdk.CfnOutput(this, 'AppointmentServiceUrl', {
      value: this.appointmentServiceUrl,
      description: 'URL for the Appointment Service API',
      exportName: 'IVR-AppointmentServiceUrl',
    });

    new cdk.CfnOutput(this, 'TenantConfigFunctionName', {
      value: tenantConfigFunction.functionName,
      description: 'Name of the Tenant Config Lambda function',
    });

    new cdk.CfnOutput(this, 'AppointmentServiceFunctionName', {
      value: appointmentServiceFunction.functionName,
      description: 'Name of the Appointment Service Lambda function',
    });
  }
}