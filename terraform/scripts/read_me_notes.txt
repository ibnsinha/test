## Deprecated IAM Runner Role Remediation

### Overview

As part of the initial Runner setup in AWS, we previously had three IAM runners tied to each account. With recent re-architecture, we have optimized our setup and consolidated to just one runner. This document outlines the cleanup activities needed to remove unnecessary resources and details the approach for future management.

---

### Current IAM Runner Roles

Below are the IAM runner roles identified for cleanup:

- `runner-role1`
- `runner-role2`
- `runner-role3`
- `runner-role4`

---

### Action Items

- **Roles to import and destroy**:
  - `runner-role1`
  - `runner-role2`
  - `runner-role3`

  We will perform Terraform import operations for these roles, then subsequently destroy them. If these roles are needed again in the future, we can recreate them using existing Terraform modules.

- **Role to import and modify**:
  - `runner-role4`

  For this role, we will perform a Terraform import and then update the trust policy.

---

### IAM Role Import Module Workflow

The IAM Role Import module in the GitLab project provides an automated workflow:

- **Step 1: Setup and Initialization**
  - A GitLab project is created per IAM role to import.
  - The project clones the IAM role module and prepares a `terraform.tfvars` file containing required variables.

- **Step 2: Python Script Execution**
  - `assume_role.py`: Assumes target IAM roles.
  - `custom-policies.py`: Checks if the IAM role exists, retrieves custom and managed policy ARNs.
  - `generate_tfvars.py`: Prepares the `terraform.tfvars` file needed for Terraform execution.

- **Step 3: Pipeline Execution**
  - The pipeline checks if the IAM role exists:
    - If present, performs a Terraform import.
    - Decides based on the `RUN_DESTROY` variable whether to create or destroy the role.
  - Generated `terraform.tfvars` files match exactly the IAM role state post-import/destroy.
  - Destroyed roles, if needed again, can be recreated using the same Terraform configuration.

---

### Directory Structure

```
IAM-IMPORT/
├── modules/
│   └── iam_role/
│       ├── main.tf
│       └── variables.tf
├── scripts/
│   ├── assume_role.py
│   ├── custom-policies.py
│   ├── generate_tfvars.py
│   └── setup_plan.sh
├── iam_role.tf
├── provider.tf
├── README.md
├── terraform.tf
└── variables.tf
```

---

### Important Notes

- Ensure the `terraform.tfvars` file is accurate post-import or destroy operations.
- Changes to the IAM roles after import must first update `terraform.tfvars`, then re-run Terraform.
- Regular maintenance and documentation updates are necessary after each IAM role change to maintain consistency.


High-Level Summary
This project implements a modular and automated approach to manage IAM roles using Terraform and GitLab CI/CD. The core idea is to use a reusable IAM role import module, which supports importing, modifying, or destroying existing IAM roles in AWS.

Each IAM role that needs to be imported or managed will have a dedicated GitLab project.

The GitLab project will include:

The shared IAM role Terraform module (imported or cloned locally).

A tailored terraform.tfvars file describing the target IAM role.

Terraform configuration files to drive the module.

The module supports:

Importing IAM role metadata and policies.

Applying updates to trust relationships and policies.

Destroying roles when no longer needed.

If the user has read-only access, a Python script (generate_tfvars.py) can be used to generate a terraform.tfvars file based on an existing role's configuration.



=========================

## Implementation Plan

### Step 1: Project Setup
- Clone the `IAM-IMPORT` module or copy the required `iam_role` module into the `modules/` directory of your project.
- Create the following root-level files in your project directory:
  - `iam_role.tf`
  - `provider.tf`
  - `backend.tf`
  - `variables.tf`
  - `terraform.tfvars`

### Step 2: Configure Provider and Backend
- Define your AWS provider settings in `provider.tf`.
- Configure remote state storage (e.g., S3) in `backend.tf` to manage state across environments.

### Step 3: Reference the Module
- In `iam_role.tf`, invoke the IAM role module using the following structure:

```hcl
module "runner_role_import" {
  source          = "./modules/iam_role"
  role_name       = var.role_name
  assume_role_arn = var.assume_role_arn
  run_destroy     = var.run_destroy
  tags            = var.common_tags
}
```

### Step 4: Define Inputs
- Declare required variables in `variables.tf`.
- Provide actual values in `terraform.tfvars`.

### Step 5: Generate `terraform.tfvars` from Existing IAM Role
- If a user has read-only access to AWS IAM, they can use the Python script `generate_tfvars.py` (from the IAM-IMPORT module) to automatically generate a valid `terraform.tfvars` file.
- This script inspects the specified IAM role and builds the `terraform.tfvars` content based on existing configuration and policies.

### Step 6: Run Terraform Workflow
- Initialize the project: `terraform init`
- Review the plan: `terraform plan -var-file=terraform.tfvars`
- Apply or destroy based on `run_destroy` flag:
  - Apply: `terraform apply -var-file=terraform.tfvars`
  - Destroy: `terraform destroy -var-file=terraform.tfvars`

---

## Directory Structure

```
Importing-Runner-Role/
├── modules/
│   └── iam_role/
│       ├── main.tf
│       └── variables.tf
│
├── iam_role.tf                 
├── provider.tf
├── backend.tf
├── variables.tf
├── terraform.tfvars
└── README.md
```

---

## README.md (Suggested Content)

### Variables Reference

| Variable Name                 | Type          | Description                                                                                     | Required | Default |
|------------------------------|---------------|-------------------------------------------------------------------------------------------------|----------|---------|
| `role_name`                  | `string`      | Name of the IAM role to create or manage                                                        | Yes      | N/A     |
| `assume_role_policy`         | `string`      | The trust relationship policy document for the IAM role                                         | Yes      | N/A     |
| `permission_boundary`        | `string`      | ARN of the permission boundary policy                                                           | No       | `""`    |
| `managed_arns`               | `list(string)`| List of AWS managed policy ARNs to attach                                                       | No       | `[]`    |
| `tags`                       | `map(string)` | Tags to associate with the IAM role                                                             | No       | `{}`    |
| `instance_profile_name`      | `string`      | Instance profile name to associate with the IAM role                                            | No       | `""`    |
| `instance_profile_tags`      | `map(string)` | Tags to associate with the instance profile                                                     | No       | `{}`    |
| `customer_managed_policies`  | `map(object)` | Map of customer-managed policies with name, description, and list of policy statements          | No       | `{}`    |
| `inline_policy_AuditOnlyPolicy` | `string`   | JSON for an optional inline policy named `AuditOnlyPolicy`                                     | No       | `""`    |

### Importing-Runner-Role

This Terraform project is used to import or manage an IAM role using a reusable `iam_role` module.

### Usage

1. Clone this repository.
2. Update the `terraform.tfvars` file with required values.
3. Run Terraform commands to import or apply the role.

```bash
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

To destroy the IAM role, set `run_destroy = true` in `terraform.tfvars` and run:

```bash
terraform destroy -var-file=terraform.tfvars
```

### Optional: Auto-Generate `terraform.tfvars`

If you only have read-only access to the target IAM role, you can use the `generate_tfvars.py` script provided in the IAM-IMPORT module to automatically generate your `terraform.tfvars` file:

```bash
python3 scripts/generate_tfvars.py --role-name example-role
```

---

### `terraform.tfvars` Example

```hcl
role_name = "example-role"

assume_role_policy = <<EOT
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      }
    }
  ]
}
EOT

permission_boundary = "arn:aws:iam::aws:policy/AdministratorAccess"

managed_arns = [
  "arn:aws:iam::aws:policy/ReadOnlyAccess",
  "arn:aws:iam::aws:policy/CloudWatchFullAccess"
]

tags = {
  Environment = "Production"
  Team        = "DevOps"
  CostCenter  = "1234"
}

instance_profile_name = "example-instance-profile"

instance_profile_tags = {
  Owner = "mdsinha"
  App   = "internal-tools"
}

customer_managed_policies = {
  "example-policy-rds" = {
    name        = "example-policy-rds"
    description = "IAM policy for RDS access"
    statements = [
      {
        Effect   = "Allow"
        Action   = [
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = "arn:aws-us-gov:kms:us-gov-west-1:account:key/12345678"
        Sid      = "RDSKMSAccess"
      }
    ]
  },

  "example-policy-gitlab" = {
    name        = "example-policy-gitlab"
    description = "IAM policy for GitLab runner"
    statements = [
      {
        Effect   = "Allow"
        Action   = [
          "ssm:List*",
          "ssm:AddTagsToResource",
          "ssm:*Parameter*",
          "iam:GetGroupPolicy",
          "iam:UpdateRoleDescription",
          "iam:UpdateRole"
        ]
        Resource = "*"
        Sid      = "SSMAndIAMPermissions"
      },
      {
        Effect   = "Allow"
        Action   = [
          "cloudformation:ValidateTemplate"
        ]
        Resource = "*"
        Sid      = "CloudFormationValidation"
      }
    ]
  }
}

inline_policy_AuditOnlyPolicy = <<EOT
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudtrail:LookupEvents",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOT
```

---

