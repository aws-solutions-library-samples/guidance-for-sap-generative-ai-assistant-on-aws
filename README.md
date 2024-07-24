# Guidance to create Generative AI Assistant for SAP Data

## Table of Contents (required)

1. [Overview](#overview)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
    - [Operating System](#operating-system)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)

## Overview

SAP business users across every industry manually analyze data, write executive summaries, and perform repetitive tasks. SAP Business User Productivity solutions on AWS improve productivity by querying business data in natural language, making it easy to query, removing the need to understand SAP data structures, navigate complex reports and remember SAP transaction codes. With the use of natural language, personas like C-Suite executives, managers, auditors and on-the-go users can effortlessly gain valuable insights, retrieve summaries, or perform ad-hoc tasks such as e-mail generation and status checks.
This Guidance demonstrates how to improve business user productivity and experience using real-time data summaries, task automation, seamless natural language interactions. It uses Amazon Bedrock for generative AI and Amazon Lex for conversational AI assistant. This Guidance is designed to be extensible, allowing you to seamlessly incorporate additional components or integrate with other AWS services

Below is the reference architecture for Generative AI assistance: 


![reference architecture for Generative AI assistance](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/1.Architecture.jpeg?raw=true)

### Cost

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.


|AWS service	|Dimensions	|Cost [USD]	|
|---	|---	|---	|
|Amazon Lex	|	|	|
|AWS Lambda	|	|	|
|Amazon Athena	|	|	|
|Amazon Bedrock	|	|	|
|Amazon S3	|	|	|
|AWS Glue	|	|	|
|	|	|	|

## Prerequisites

Access to set-up AWS services: Amazon Lex, AWS lambda, Amazon Athena, Amazon Bedrock, Amazon S3 and AWS Glue from AWS Console
Amazon S3 bucket is created to store SAP data.
SAP source data is extracted in Amazon S3 bucket. The source data can be extracted using different approaches highlighted in the [Guidance for SAP Data Integration and Management on AWS](https://aws.amazon.com/solutions/guidance/sap-data-integration-and-management-on-aws/?did=sl_card&trk=sl_card).
Please take note of s3 path where data is stored example: s3://amazonjr-covid-glue-databucket/athenaresults/


## Deployment Steps


1. **Creation of glue database catalogue**

For data stored in Amazon S3, use AWS Glue crawler to create dabase catalogue. Follow the instruction as per the [blog](https://aws.amazon.com/blogs/big-data/introducing-aws-glue-crawlers-using-aws-lake-formation-permission-management/). 
You can schedule recreation of database catalogue to update database catalogue

Please make sure you are able to query the data using Amazon Athena
Please take note of: DATABASENAME and SCHEMANAME.

2. **Creating access for Amazon Bedrock**

Go to Amazon Bedrock —> Model Access —> Modify Model Access and select Claude:

![Model Access](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/2.Amazon%20Bedrock%20Claude%20Selection.jpeg?raw=true)

Click Next and click submit. It may take few minutes for access for model to get updated then you will able to access the Model.


3. **AWS Lambda Layer Creation**

**Create S3 bucket** : YOURSLAMBDALAYERS3 in your AWS Account.
Download following lambda layers to S3 bucket of your account.

* langchainlayer : store it in s3 as: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip)

* [pyAthena](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/SQLAlchemy.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/pyAthena/python.zip

* [SQLAlchemy](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/pyAthena.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/SQLAlchemy/python.zip

1. Navigate to [AWS Lambda - Layers](https://console.aws.amazon.com/lambda/#/layers), then click **Create layer**
2. Type the following in to the Lambda Layer screen, then click **Create**
3.Name: langchainlayer
4. Description: langchainlayer
5. Choose: **Upload a file from Amazon S3: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip**
6. Compatible architectures: **x86_64**
7. Compatible runtimes: **Python 3.10**

![lambda layer creation](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/3.LambdaLayerCreation.jpeg?raw=true)


Repeat above steps 1-7 for pyAthena and  SQLAlchemy



4. **Create Lambda Function**

* Navigate to [AWS Lambda - Functions](https://console.aws.amazon.com/lambda/#/functions), then click **Create function**
* Type the following information, then click **Create function**
* Select **Author from scratch**
* Function Name: SAPGenAIAssitant
* Runtime: **Python 3.10**
* Architectures: **x86_64**
  
![create lambda function](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/4.%20Lambda%20Function%20Creation.jpeg?raw=true)

* Add [helpers.py](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/code/helpers.py) file in Code source and remember to change the athena connection parameters based on your AWS account configuration

![add code to lambda](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/5.LambdaHelperFileCreation.jpeg?raw=true)
 
* Add [lambda_fuction.py](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/code/lambda_function.py), then click **Deploy**


 

1. Click **Layers**
2. Click **Add a layer**
3. Type the following information, then click **Add**

    * Layer source: **Custom layers**
    * Custom layers: **LangChainLayer**
    * Version: **Choose the Latest**
  
![add layer](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/6.LambdaLayerAddition.jpeg?raw=true)

Repeat above steps to add layers for **pyAthena** and **SQLAlchemy**

    1. Go to **Configuration - General Configuration**, then click **Edit**
    2. Change timeout from 3 seconds to **10 minutes**, then click **Save**

![configuration settings](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/7.LambdaEditConfiguraitonIncreaseTimeOut.jpeg?raw=true)

**Create Role**

   * Go to **Configuration - Permissions**, then click at the role name **SAPGenAIAssistant-role-xxxxxxx**

![role name configuration](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/8.LambdaEditConfiguraitonEditRole.jpeg?raw=true)

   * Click **Add permissions**, click dropdown **Create inline policy**
   * Click **JSON**, then add [SAPGenAIPolicy](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/code/SAPGenAIPolicy) to **Policy editor**, then click **Next**

   * Type **SAPGenAIPolicy** as policy name then Click **Create policy**



1. **Create Amazon Lex Bot**

1.Navigate to [Amazon Lex](https://us-east-1.console.aws.amazon.com/lexv2/home?region=us-east-1)
2.Click Create bot
3.Choose create blank bot and Provide Bot name and configurations and click Next:

Select language as English and click Done to create Bot.

4.Provide name to NewIntent as greeting_intent and update description “this is hello intent” 

Proivde at least one utterance as “hi” and save intent


1. Navigate to Versions >Version: Draft>All languages>Language: English (US)>Intents
2. Click on FallbackIntent and Activate Fulfillment and click Save Intent and Click Build:


1. Click on Test
2. Select Lambda function created and select $Latest and save:


Type questions to test the response:


1. **Create Strimlit App for Lex**

Follow [aws-lex-web-ui](https://github.com/aws-samples/aws-lex-web-ui)  guidance to create strimlit App 



## Running the Guidance



## Next Steps



## Cleanup



## FAQ



## Authors




----





***Optional***

8. [FAQ, known issues, additional considerations, and limitations](#faq-known-issues-additional-considerations-and-limitations-optional)
9. [Revisions](#revisions-optional)
10. [Notices](#notices-optional)
11. [Authors](#authors-optional)

## Overview (required)

1. Provide a brief overview explaining the what, why, or how of your Guidance. You can answer any one of the following to help you write this:

    - **Why did you build this Guidance?**
    - **What problem does this Guidance solve?**

2. Include the architecture diagram image, as well as the steps explaining the high-level overview and flow of the architecture. 
    - To add a screenshot, create an ‘assets/images’ folder in your repository and upload your screenshot to it. Then, using the relative file path, add it to your README. 

### Cost ( required )

This section is for a high-level cost estimate. Think of a likely straightforward scenario with reasonable assumptions based on the problem the Guidance is trying to solve. Provide an in-depth cost breakdown table in this section below ( you should use AWS Pricing Calculator to generate cost breakdown ).

Start this section with the following boilerplate text:

_You are responsible for the cost of the AWS services used while running this Guidance. As of <month> <year>, the cost for running this Guidance with the default settings in the <Default AWS Region (Most likely will be US East (N. Virginia)) > is approximately $<n.nn> per month for processing ( <nnnnn> records )._

Replace this amount with the approximate cost for running your Guidance in the default Region. This estimate should be per month and for processing/serving resonable number of requests/entities.

Suggest you keep this boilerplate text:
_We recommend creating a [Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) through [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this Guidance._

### Sample Cost Table ( required )

**Note : Once you have created a sample cost table using AWS Pricing Calculator, copy the cost breakdown to below table and upload a PDF of the cost estimation on BuilderSpace. Do not add the link to the pricing calculator in the ReadMe.**

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.

| AWS service  | Dimensions | Cost [USD] |
| ----------- | ------------ | ------------ |
| Amazon API Gateway | 1,000,000 REST API calls per month  | $ 3.50month |
| Amazon Cognito | 1,000 active users per month without advanced security feature | $ 0.00 |

## Prerequisites (required)

### Operating System (required)

- Talk about the base Operating System (OS) and environment that can be used to run or deploy this Guidance, such as *Mac, Linux, or Windows*. Include all installable packages or modules required for the deployment. 
- By default, assume Amazon Linux 2/Amazon Linux 2023 AMI as the base environment. All packages that are not available by default in AMI must be listed out.  Include the specific version number of the package or module.

**Example:**
“These deployment instructions are optimized to best work on **<Amazon Linux 2 AMI>**.  Deployment in another OS may require additional steps.”

- Include install commands for packages, if applicable.


### Third-party tools (If applicable)

*List any installable third-party tools required for deployment.*


### AWS account requirements (If applicable)

*List out pre-requisites required on the AWS account if applicable, this includes enabling AWS regions, requiring ACM certificate.*

**Example:** “This deployment requires you have public ACM certificate available in your AWS account”

**Example resources:**
- ACM certificate 
- DNS record
- S3 bucket
- VPC
- IAM role with specific permissions
- Enabling a Region or service etc.


### aws cdk bootstrap (if sample code has aws-cdk)

<If using aws-cdk, include steps for account bootstrap for new cdk users.>

**Example blurb:** “This Guidance uses aws-cdk. If you are using aws-cdk for first time, please perform the below bootstrapping....”

### Service limits  (if applicable)

<Talk about any critical service limits that affect the regular functioning of the Guidance. If the Guidance requires service limit increase, include the service name, limit name and link to the service quotas page.>

### Supported Regions (if applicable)

<If the Guidance is built for specific AWS Regions, or if the services used in the Guidance do not support all Regions, please specify the Region this Guidance is best suited for>


## Deployment Steps (required)

Deployment steps must be numbered, comprehensive, and usable to customers at any level of AWS expertise. The steps must include the precise commands to run, and describe the action it performs.

* All steps must be numbered.
* If the step requires manual actions from the AWS console, include a screenshot if possible.
* The steps must start with the following command to clone the repo. ```git clone xxxxxxx```
* If applicable, provide instructions to create the Python virtual environment, and installing the packages using ```requirement.txt```.
* If applicable, provide instructions to capture the deployed resource ARN or ID using the CLI command (recommended), or console action.

 
**Example:**

1. Clone the repo using command ```git clone xxxxxxxxxx```
2. cd to the repo folder ```cd <repo-name>```
3. Install packages in requirements using command ```pip install requirement.txt```
4. Edit content of **file-name** and replace **s3-bucket** with the bucket name in your account.
5. Run this command to deploy the stack ```cdk deploy``` 
6. Capture the domain name created by running this CLI command ```aws apigateway ............```



## Deployment Validation  (required)

<Provide steps to validate a successful deployment, such as terminal output, verifying that the resource is created, status of the CloudFormation template, etc.>


**Examples:**

* Open CloudFormation console and verify the status of the template with the name starting with xxxxxx.
* If deployment is successful, you should see an active database instance with the name starting with <xxxxx> in        the RDS console.
*  Run the following CLI command to validate the deployment: ```aws cloudformation describe xxxxxxxxxxxxx```



## Running the Guidance (required)

<Provide instructions to run the Guidance with the sample data or input provided, and interpret the output received.> 

This section should include:

* Guidance inputs
* Commands to run
* Expected output (provide screenshot if possible)
* Output description



## Next Steps (required)

Provide suggestions and recommendations about how customers can modify the parameters and the components of the Guidance to further enhance it according to their requirements.


## Cleanup (required)

- Include detailed instructions, commands, and console actions to delete the deployed Guidance.
- If the Guidance requires manual deletion of resources, such as the content of an S3 bucket, please specify.



## FAQ, known issues, additional considerations, and limitations (optional)


**Known issues (optional)**

<If there are common known issues, or errors that can occur during the Guidance deployment, describe the issue and resolution steps here>


**Additional considerations (if applicable)**

<Include considerations the customer must know while using the Guidance, such as anti-patterns, or billing considerations.>

**Examples:**

- “This Guidance creates a public AWS bucket required for the use-case.”
- “This Guidance created an Amazon SageMaker notebook that is billed per hour irrespective of usage.”
- “This Guidance creates unauthenticated public API endpoints.”


Provide a link to the *GitHub issues page* for users to provide feedback.


**Example:** *“For any feedback, questions, or suggestions, please use the issues tab under this repo.”*

## Revisions (optional)

Document all notable changes to this project.

Consider formatting this section based on Keep a Changelog, and adhering to Semantic Versioning.

## Notices (optional)

Include a legal disclaimer

**Example:**
*Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.*


## Authors (optional)

Name of code contributors
