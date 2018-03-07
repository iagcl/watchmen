# Watchmen
### (AWS account compliance using centrally managed Config Rules)...

***
## Overview...
**Watchmen** provides the framework to centralise the lambda functions used by AWS config rules into a single AWS account so that they can be managed easily and efficiently using automation.

Essentially we deploy our **Watchmen** stack to a dedicated AWS account. We then get our other AWS accounts (**Citizens**) to deploy a Citizen stack which provides Watchmen with a role that will allow us to deploy and manage config rules in their account. These config rules will be pointing to lambdas in the Watchmen account. When the config rule is trigged, Watchmen will run the lambda but will assume another role in the Citizen account so that it reports on resources in the Citizen accounts.

***
## What is Watchmen?
Watchmen is an AWS CloudFormation stack comprising of:
* **Lambda** functions written in Python that process AWS resources and determine if they are compliant or non-compliant based on certain rules logic.
* **Monitoring** stack using CloudWatch to monitor the Lambda functions.
* **ElasticSearch** stack to ingest the logs from the Lambda functions so they can be easily visualised and searched.
* **Reporting** stack using additional lambda functions to report on the status of each Citizen's Config Rules and import into DynamoDB.
* **Citizen Update** stack using a SNS topic and additional lambda function to manage the AWS Config rules in each Citizen account.
* Other stuff that makes everything work (IAM roles, polices, lambda permissions, etc).

## Citizens...
To enable the monitoring of a Citizen AWS account, we deploy a stack comprising of:
* IAM roles that allow us to deploy config rules and query AWS Config for statuses of resources.
* Config Rules that display in AWS Config whether resources are compliant or non-compliant.

## Further Information
More detailed information is provided on our github wiki:
https://github.com/iagcl/watchmen/wiki
