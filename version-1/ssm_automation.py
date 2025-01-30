import boto3
import yaml
import os
import time
import json
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

class SSMAutomation:
    def __init__(self, config_path: str):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Setup AWS clients
        self.ssm_client = boto3.client('ssm', region_name=self.config['aws']['region'])
        self.ec2_client = boto3.client('ec2', region_name=self.config['aws']['region'])
        
        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        output_dir = self.config['execution']['output_dir']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        log_file = os.path.join(output_dir, f'ssm_automation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def read_script_content(self, script_name: str) -> str:
        """Read script content from file"""
        try:
            with open(script_name, 'r') as file:
                return file.read()
        except Exception as e:
            self.logger.error(f"Error reading script {script_name}: {str(e)}")
            raise

    def check_ssm_agent(self, instance_id: str) -> bool:
        """Check if SSM agent is installed and connected."""
        try:
            response = self.ssm_client.describe_instance_information(
                Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
            )
            return len(response['InstanceInformationList']) > 0
        except Exception as e:
            self.logger.error(f"Error checking SSM agent for instance {instance_id}: {str(e)}")
            return False

    def get_os_type(self, instance_id: str) -> str:
        """Determine OS type of the instance."""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            platform = response['Reservations'][0]['Instances'][0].get('Platform', '')
            image_id = response['Reservations'][0]['Instances'][0]['ImageId']
            
            image_info = self.ec2_client.describe_images(ImageIds=[image_id])
            
            if platform == 'windows':
                return 'windows'
            elif 'amazon' in image_info['Images'][0]['Name'].lower():
                return 'amazon-linux'
            elif 'ubuntu' in image_info['Images'][0]['Name'].lower():
                return 'ubuntu'
            else:
                return 'unknown'
        except Exception as e:
            self.logger.error(f"Error determining OS type for instance {instance_id}: {str(e)}")
            return 'unknown'

    def run_script_on_instance(self, instance_id: str, script_config: Dict) -> Dict:
        """Run a script on a single instance"""
        try:
            script_content = self.read_script_content(script_config['name'])
            
            response = self.ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={'commands': [script_content]},
                TimeoutSeconds=script_config.get('timeout', self.config['execution']['default_timeout'])
            )
            
            command_id = response['Command']['CommandId']
            retries = script_config.get('retry_count', 0)
            
            while retries >= 0:
                time.sleep(5)
                try:
                    status = self.ssm_client.get_command_invocation(
                        CommandId=command_id,
                        InstanceId=instance_id
                    )
                    if status['Status'] in ['Success']:
                        return {
                            'status': 'Success',
                            'output': status.get('StandardOutputContent', ''),
                            'error': status.get('StandardErrorContent', '')
                        }
                    elif status['Status'] in ['Failed']:
                        retries -= 1
                        if retries >= 0:
                            self.logger.warning(f"Retrying script execution on instance {instance_id}")
                            continue
                        return {
                            'status': 'Failed',
                            'output': status.get('StandardOutputContent', ''),
                            'error': status.get('StandardErrorContent', '')
                        }
                except Exception as e:
                    self.logger.error(f"Error checking command status: {str(e)}")
                    retries -= 1
                    
            return {'status': 'Failed', 'error': 'Maximum retries exceeded'}
            
        except Exception as e:
            self.logger.error(f"Error running script on instance {instance_id}: {str(e)}")
            return {'status': 'Failed', 'error': str(e)}

    def execute_scripts(self, instance_ids: List[str]) -> Dict:
        """Execute all configured scripts on specified instances"""
        results = {}
        
        for script_config in self.config['scripts']:
            self.logger.info(f"Executing script: {script_config['name']}")
            script_results = {}
            
            if script_config.get('parallel_execution', False):
                with ThreadPoolExecutor(max_workers=self.config['execution']['max_parallel']) as executor:
                    future_to_instance = {
                        executor.submit(self.run_script_on_instance, instance_id, script_config): instance_id 
                        for instance_id in instance_ids
                    }
                    for future in future_to_instance:
                        instance_id = future_to_instance[future]
                        try:
                            script_results[instance_id] = future.result()
                        except Exception as e:
                            script_results[instance_id] = {
                                'status': 'Failed',
                                'error': str(e)
                            }
            else:
                for instance_id in instance_ids:
                    script_results[instance_id] = self.run_script_on_instance(instance_id, script_config)
            
            results[script_config['name']] = script_results
            
        return results

def main():
    # Initialize automation with config
    automation = SSMAutomation('config.yaml')
    
    # Get instance IDs (either from config or other sources)
    instance_ids = automation.config['instances']['ids']
    if not instance_ids:
        # Here you could add logic to get instances from Terraform output
        # For now, we'll use the ones from config
        automation.logger.info("No instance IDs specified, checking tags...")
        if automation.config['instances']['tags']:
            # Add logic to get instances by tags
            pass
    
    if not instance_ids:
        automation.logger.error("No target instances found!")
        return
    
    # Execute scripts
    results = automation.execute_scripts(instance_ids)
    
    # Log results
    for script_name, script_results in results.items():
        automation.logger.info(f"\nResults for {script_name}:")
        for instance_id, result in script_results.items():
            automation.logger.info(f"\nInstance {instance_id}:")
            automation.logger.info(f"Status: {result['status']}")
            if result['status'] == 'Success':
                automation.logger.info(f"Output: {result['output']}")
            else:
                automation.logger.error(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()