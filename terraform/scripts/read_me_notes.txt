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
