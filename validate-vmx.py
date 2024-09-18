import re
import argparse
from typing import Dict, List, Tuple
from colorama import init, Fore, Style

init(autoreset=True)  # Initialize colorama

class VMXValidator:
    def __init__(self, vmx_content: str):
        self.vmx_content = vmx_content
        self.vmx_dict = self.parse_vmx()
        self.results = []

    def parse_vmx(self) -> Dict[str, str]:
        vmx_dict = {}
        for line in self.vmx_content.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                vmx_dict[key.strip()] = value.strip().strip('"')
        return vmx_dict

    def validate(self):
        self.check_hardware_version()
        self.check_credentials_annotation()
        self.check_display_name()
        self.check_virtual_drives()
        self.check_cd_drive()
        self.check_shared_folders()
        self.check_sound_card()
        self.check_ethernet_adapters()
        self.check_usb_compatibility()
        self.check_macos_mitigations()
        self.check_3d_graphics()
        self.check_bluetooth()

    def add_result(self, status: str, message: str, vmx_line: str = ""):
        self.results.append((status, message, vmx_line))

    def check_hardware_version(self):
        version = self.vmx_dict.get('virtualHW.version', '')
        vmx_line = f"virtualHW.version = \"{version}\""
        if version == '18':
            self.add_result('PASS', 'Hardware Compatibility version is 18', vmx_line)
        else:
            self.add_result('FAIL', f'Hardware Compatibility version should be 18, found {version}', vmx_line)

    def check_credentials_annotation(self):
        annotation = self.vmx_dict.get('annotation', '')
        vmx_line = f"annotation = \"{annotation}\""
        if annotation:
            self.add_result('PASS', 'Credentials noted in annotation', vmx_line)
        else:
            self.add_result('FAIL', 'Credentials must be noted in the annotation', vmx_line)

    def check_display_name(self):
        display_name = self.vmx_dict.get('displayName', '')
        nvram = self.vmx_dict.get('nvram', '')
        vmx_line = f"displayName = \"{display_name}\"\nnvram = \"{nvram}\""
        if 'clone' not in display_name.lower() and 'clone' not in nvram.lower():
            self.add_result('PASS', 'Display name and nvram do not contain "clone"', vmx_line)
        else:
            self.add_result('FAIL', 'Display name or nvram contains "clone"', vmx_line)

    def check_virtual_drives(self):
        vmdk_files = [value for key, value in self.vmx_dict.items() if key.startswith('scsi') and value.endswith('.vmdk')]
        vmx_line = "\n".join([f"{key} = \"{value}\"" for key, value in self.vmx_dict.items() if key.startswith('scsi') and value.endswith('.vmdk')])
        if vmdk_files:
            self.add_result('INFO', f"Virtual Drive: {vmdk_files[0]}", vmx_line)
        else:
            self.add_result('FAIL', 'No VMDK files found', vmx_line)

    def check_cd_drive(self):
        cd_drive = self.vmx_dict.get('ide0:0.startConnected', '')
        vmx_line = f"ide0:0.startConnected = \"{cd_drive}\""
        if cd_drive.lower() == 'false':
            self.add_result('PASS', 'CD drive starts disconnected', vmx_line)
        else:
            self.add_result('FAIL', 'CD drive must start disconnected', vmx_line)

    def check_shared_folders(self):
        shared_folders = [key for key in self.vmx_dict if key.startswith('sharedFolder')]
        vmx_line = "\n".join([f"{key} = \"{self.vmx_dict[key]}\"" for key in shared_folders]) if shared_folders else "No shared folders"
        if not shared_folders:
            self.add_result('PASS', 'No shared folders present', vmx_line)
        else:
            self.add_result('FAIL', 'Shared folders are present', vmx_line)

    def check_sound_card(self):
        sound_present = any(key.startswith('sound') for key in self.vmx_dict)
        vmx_line = "\n".join([f"{key} = \"{self.vmx_dict[key]}\"" for key in self.vmx_dict if key.startswith('sound')]) if sound_present else "No sound card settings"
        if sound_present:
            self.add_result('PASS', 'Sound card is present', vmx_line)
        else:
            self.add_result('FAIL', 'Sound card is missing', vmx_line)

    def check_ethernet_adapters(self):
        ethernet_settings = {key: value for key, value in self.vmx_dict.items() if key.startswith('ethernet') and key.endswith('connectionType')}
        vmx_line = "\n".join([f"{key} = \"{value}\"" for key, value in ethernet_settings.items()])
        for key, value in ethernet_settings.items():
            if value.lower() not in ['nat', 'hostonly']:
                self.add_result('FAIL', f'{key} is not NAT or HOSTONLY', f"{key} = \"{value}\"")
            else:
                self.add_result('PASS', f'{key} is valid', f"{key} = \"{value}\"")

    def check_usb_compatibility(self):
        usb_setting = self.vmx_dict.get('usb_xhci.present', '')
        vmx_line = f"usb_xhci.present = \"{usb_setting}\""
        if usb_setting.lower() == 'true':
            self.add_result('PASS', 'USB 3.1 compatibility ensured', vmx_line)
        else:
            self.add_result('FAIL', 'USB 3.1 compatibility not ensured', vmx_line)

    def check_macos_mitigations(self):
        mitigations = self.vmx_dict.get('ulm.disableMitigations', '')
        vmx_line = f"ulm.disableMitigations = \"{mitigations}\""
        if mitigations.lower() == 'true':
            self.add_result('PASS', 'macOS Side Channel Mitigations disabled', vmx_line)
        else:
            self.add_result('FAIL', 'macOS Side Channel Mitigations not disabled', vmx_line)

    def check_3d_graphics(self):
        graphics_setting = self.vmx_dict.get('mks.enable3d', '')
        vmx_line = f"mks.enable3d = \"{graphics_setting}\""
        if graphics_setting.lower() == 'false':
            self.add_result('PASS', '3D graphics acceleration disabled', vmx_line)
        else:
            self.add_result('FAIL', '3D graphics acceleration not disabled', vmx_line)

    def check_bluetooth(self):
        bluetooth_setting = self.vmx_dict.get('usb.vbluetooth.startconnected', '')
        vmx_line = f"usb.vbluetooth.startconnected = \"{bluetooth_setting}\""
        if bluetooth_setting.lower() == 'false':
            self.add_result('PASS', 'Bluetooth auto-start disabled', vmx_line)
        else:
            self.add_result('FAIL', 'Bluetooth auto-start not disabled', vmx_line)

    def get_results(self) -> List[Tuple[str, str, str]]:
        return self.results

def validate_vmx(vmx_content: str) -> List[Tuple[str, str, str]]:
    validator = VMXValidator(vmx_content)
    validator.validate()
    return validator.get_results()

def print_results(results: List[Tuple[str, str, str]]):
    for status, message, vmx_line in results:
        if status == 'PASS':
            print(f"{Fore.GREEN}{status}: {message}")
        elif status == 'FAIL':
            print(f"{Fore.RED}{status}: {message}")
        elif status == 'INFO':
            print(f"{Fore.BLUE}{status}: {message}")
        else:
            print(f"{Fore.YELLOW}{status}: {message}")
        
        print(f"{Fore.CYAN}VMX: {vmx_line}{Style.RESET_ALL}")
        print()  # Add a newline for readability

def main():
    parser = argparse.ArgumentParser(description="Validate a VMware .vmx file.")
    parser.add_argument("vmx_file", help="Path to the .vmx file to validate")
    args = parser.parse_args()

    try:
        with open(args.vmx_file, 'r') as file:
            vmx_content = file.read()
        
        results = validate_vmx(vmx_content)
        print_results(results)
    except FileNotFoundError:
        print(f"{Fore.RED}Error: The file '{args.vmx_file}' was not found.")
    except IOError as e:
        print(f"{Fore.RED}Error reading the file: {e}")

if __name__ == "__main__":
    main()