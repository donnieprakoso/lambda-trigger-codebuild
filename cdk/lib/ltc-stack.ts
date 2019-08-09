import cdk = require('@aws-cdk/core');
import lambda = require('@aws-cdk/aws-lambda');
import apigateway = require('@aws-cdk/aws-apigateway');
import iam = require('@aws-cdk/aws-iam');

export class LtcStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const fn_lambda = new lambda.Function(this, 'ltc-lambda', {
      runtime: lambda.Runtime.PYTHON_3_7,
      handler: 'app.handler',
      code: lambda.Code.asset('../lambda-function'),
      
      environment: {
        CODEBUILD_PROJECTNAME:'donnieID_dev',
        CODEBUILD_STAGES_BUILD:'{"refs/heads/dev":{"branch":"dev","buildspec":"_deployment/staging/buildspec-staging-release.yml"},"refs/heads/master":{"branch":"master","buildspec":"_deployment/production/buildspec-production-release.yaml"}}',
        GITHUB_SHA1_SECRET:'fbe61f5368965f3e98419589477a2ff8'
      },
      
    });
    
    fn_lambda.addToRolePolicy(new iam.PolicyStatement({
      resources: ["*"],
      actions: ["codebuild:StartBuild"]
    })); 

    const api = new apigateway.LambdaRestApi(this, 'ltc-apigateway', {
      handler: fn_lambda,
      proxy: true
    });


      
    }
  }
