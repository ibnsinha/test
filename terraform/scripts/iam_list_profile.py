import boto3

# Initialize the IAM client
iam_client = boto3.client('iam')

def get_instance_profiles_for_role(role_name):
    """
    Retrieve and print instance profiles associated with the specified IAM role.
    
    :param role_name: The name of the IAM role
    """
    try:
        response = iam_client.list_instance_profiles_for_role(RoleName=role_name)
        instance_profiles = response.get('InstanceProfiles', [])
        if not instance_profiles:
            print(f"No instance profiles found for role '{role_name}'.")
        else:
            for profile in instance_profiles:
                print(f"Instance Profile Name: {profile['InstanceProfileName']}")
                print(f"ARN: {profile['Arn']}")
                print("-" * 40)
    except iam_client.exceptions.NoSuchEntityException:
        print(f"The role '{role_name}' does not exist.")

if __name__ == "__main__":
    # Replace 'YourRoleName' with the IAM role name you want to query.
    get_instance_profiles_for_role("YourRoleName")

