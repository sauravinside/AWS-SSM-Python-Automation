import boto3
import json
import time

# Load Configuration
with open("config/config.json") as f:
    config = json.load(f)

SSM_CLIENT = boto3.client("ssm", region_name="us-east-1")

def get_managed_instances():
    """Fetch EC2 instances managed by AWS SSM."""
    response = SSM_CLIENT.describe_instance_information()
    return [inst["InstanceId"] for inst in response["InstanceInformationList"]]

def detect_os_and_install_ssm(instance_ids):
    """Detect OS and install SSM Agent accordingly."""
    
    # Detect OS using AWS SSM DescribeInstanceInformation
    response = SSM_CLIENT.describe_instance_information()
    os_mapping = {}

    for instance in response["InstanceInformationList"]:
        os_mapping[instance["InstanceId"]] = instance["PlatformName"]

    missing_instances = [inst for inst in instance_ids if inst not in os_mapping]

    if missing_instances:
        print(f"Installing SSM Agent on: {missing_instances}")
        
        for instance_id in missing_instances:
            os_type = os_mapping.get(instance_id, "Unknown")
            print(f"Instance {instance_id} OS: {os_type}")

            if "Amazon Linux" in os_type or "Red Hat" in os_type:
                install_command = [
                    "sudo yum install -y amazon-ssm-agent",
                    "sudo systemctl enable amazon-ssm-agent",
                    "sudo systemctl start amazon-ssm-agent"
                ]
            elif "Ubuntu" in os_type or "Debian" in os_type:
                install_command = [
                    "sudo snap install amazon-ssm-agent --classic",
                    "sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent",
                    "sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent"
                ]
            elif "Windows" in os_type:
                install_command = [
                    "powershell.exe -Command \"Start-BitsTransfer -Source https://s3.amazonaws.com/ec2-windows-downloads/latest/SSMAgent_latest.zip -Destination C:\\SSMAgent_latest.zip\"",
                    "powershell.exe -Command \"Expand-Archive -Path C:\\SSMAgent_latest.zip -DestinationPath C:\\Program Files\\Amazon\\SSM\"",
                    "powershell.exe -Command \"& 'C:\\Program Files\\Amazon\\SSM\\amazon-ssm-agent.exe'\""
                ]
            else:
                print(f"Unknown OS for instance {instance_id}. Skipping.")
                continue

            SSM_CLIENT.send_command(
                DocumentName="AWS-RunShellScript",
                InstanceIds=[instance_id],
                Parameters={"commands": install_command},
                Comment=f"Installing SSM Agent on {os_type}",
            )

        time.sleep(10)  # Wait for installation

def execute_script_on_instances(instance_ids, script_name):
    """Execute a shell script on specified instances using AWS SSM."""
    response = SSM_CLIENT.send_command(
        DocumentName="AWS-RunShellScript",
        InstanceIds=instance_ids,
        Parameters={"commands": [f"sh {script_name}"]},
        Comment=f"Executing {script_name}",
    )
    return response

def main():
    instance_ids = config["instance_ids"]
    script_name = config["script_name"]
    batch_size = config["batch_size"]

    if not instance_ids:
        print("No instance IDs provided.")
        return

    print(f"Ensuring SSM Agent is installed on: {instance_ids}")
    check_and_install_ssm(instance_ids)

    for i in range(0, len(instance_ids), batch_size):
        batch = instance_ids[i:i + batch_size]
        print(f"Executing script {script_name} on: {batch}")
        execute_script_on_instances(batch, script_name)

if __name__ == "__main__":
    main()
