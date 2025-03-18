import boto3
import json
import os

iam_client = boto3.client('iam')

def get_role_details(role_name):
    """Fetch IAM Role details"""
    try:
        return iam_client.get_role(RoleName=role_name)['Role']
    except Exception as e:
        print(f"[ERROR] IAM Role {role_name} not found: {e}")
        return None

def get_policies(role_name):
    """Fetch Managed & Inline Policies"""
    try:
        attached = iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        inline = iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
        return attached, inline
    except Exception as e:
        print(f"[WARNING] Could not retrieve policies for {role_name}: {e}")
        return [], []

def generate_terraform(role_name):
    """Generate Terraform Config"""
    role = get_role_details(role_name)
    if not role:
        return

    output_dir = f"terraform/modules/iam_role/"
    policies_dir = os.path.join(output_dir, "policies", role_name)
    os.makedirs(policies_dir, exist_ok=True)

    # Generate Assume Role Policy
    assume_policy = role.get('AssumeRolePolicyDocument', {})
    assume_policy_file = f"{policies_dir}/{role_name}_assume_policy.json"
    with open(assume_policy_file, 'w') as f:
        json.dump(assume_policy, f, indent=2)

    tf_code = f"""
resource "aws_iam_role" "{role_name}" {{
  name               = "{role_name}"
  assume_role_policy = file("{assume_policy_file}")
"""
    # Attach Managed Policies
    managed_policies, inline_policies = get_policies(role_name)
    for policy in managed_policies:
        policy_arn = policy['PolicyArn']
        tf_code += f"""
resource "aws_iam_role_policy_attachment" "{role_name}_{policy_arn.split('/')[-1]}" {{
  role       = aws_iam_role.{role_name}.name
  policy_arn = "{policy_arn}"
}}
"""

    # Attach Inline Policies
    for policy_name in inline_policies:
        inline_policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        policy_file = f"{policies_dir}/{role_name}_{policy_name}_inline.json"
        with open(policy_file, 'w') as f:
            json.dump(inline_policy['PolicyDocument'], f, indent=2)

        tf_code += f"""
resource "aws_iam_role_policy" "{role_name}_{policy_name}" {{
  name   = "{policy_name}"
  role   = aws_iam_role.{role_name}.name
  policy = file("{policy_file}")
}}
"""
    tf_code += "\n}"

    with open(f"{output_dir}/main.tf", 'w') as f:
        f.write(tf_code)

    print(f"Terraform configuration saved in {output_dir}/main.tf")

if __name__ == "__main__":
    role_name = os.getenv('ROLE_NAME', 'default-role')
    generate_terraform(role_name)
