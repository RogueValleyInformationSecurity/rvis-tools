import re
import argparse
from typing import Dict, List, Tuple
from colorama import init, Fore, Style

init(autoreset=True)

class VMXValidator:
    def __init__(self, vmx_content: str):
        self.vmx_content = vmx_content
        self.vmx_dict = self.parse_vmx()
        self.results = []

    def parse_vmx(self) -> Dict[str, str]:
        vmx_dict = {}
        seen_keys = set()
        for line in self.vmx_content.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                if key in seen_keys:
                    self.add_result('FAIL', f'Duplicate setting found: {key}', line.strip())
                seen_keys.add(key)
                vmx_dict[key] = value.strip().strip('"')
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
        self.check_hypervisor()
        self.check_bluetooth()
        self.check_floppy()
        self.check_side_channel_mitigations()
        self.check_3d_graphics()

    def add_result(self, status: str, message: str, vmx_line: str = ""):
        self.results.append((status, message, vmx_line))

    def check_hardware_version(self):
        version = self.vmx_dict.get('virtualHW.version', '')
        vmx_line = f"virtualHW.version = \"{version}\""
        
        # Check both guestOS and detailed data for Windows 11
        guest_os = self.vmx_dict.get('guestOS', '').lower()
        detailed_data = self.vmx_dict.get('guestinfo.detailed.data', '').lower()
        
        is_win11 = ('windows11' in guest_os) or ('windows 11' in detailed_data)
        required_version = "19" if is_win11 else "18"
        
        if version == required_version:
            self.add_result('PASS', f'Hardware Compatibility version is {version} (compatible with Fusion 13.x, 12.x and Workstation 17.x, 16.x)', vmx_line)
        else:
            expected = "19 for Windows 11" if is_win11 else "18"
            self.add_result('FAIL', f'Hardware Compatibility version should be {expected}, found {version}', vmx_line)

    def check_credentials_annotation(self):
        annotation = self.vmx_dict.get('annotation', '')
        vmx_line = f"annotation = \"{annotation}\""
        if annotation and ('user' in annotation.lower() or 'pass' in annotation.lower() or 'credentials' in annotation.lower()):
            self.add_result('PASS', 'Credentials noted in annotation', vmx_line)
        else:
            self.add_result('FAIL', 'Credentials must be noted in the annotation (string search for user/pass/credentials)', vmx_line)
            
    def check_display_name(self):
        display_name = self.vmx_dict.get('displayName', '')
        vmx_line = f"displayName = \"{display_name}\""
        if display_name:
            self.add_result('PASS', f'Display name is set to "{display_name}"', vmx_line)
        else:
            self.add_result('FAIL', 'Display name must be set and descriptive', vmx_line)

    def check_virtual_drives(self):
        vmdk_files = [(key, value) for key, value in self.vmx_dict.items() 
                     if any(key.startswith(prefix) for prefix in ['scsi', 'nvme', 'sata']) 
                     and value.endswith('.vmdk')]
        
        vmx_line = "\n".join([f"{key} = \"{value}\"" for key, value in vmdk_files])
        
        if not vmdk_files:
            self.add_result('FAIL', 'No VMDK files found', vmx_line)
            return

        for _, vmdk in vmdk_files:
            if '-cl' in vmdk or 'clone' in vmdk.lower():
                self.add_result('FAIL', f'VMDK filename contains clone reference: {vmdk}', vmx_line)
            if not re.match(r'^[A-Za-z0-9-]+\.vmdk$', vmdk):
                self.add_result('WARNING', f'VMDK filename may not be descriptive enough: {vmdk}', vmx_line)
            if any(str(i).zfill(3) in vmdk for i in range(10)):
                self.add_result('FAIL', f'VMDK appears to be segmented: {vmdk}', vmx_line)

    def check_cd_drive(self):
        cd_settings = []
        for key in self.vmx_dict:
            if key.endswith('.deviceType') and 'cdrom' in self.vmx_dict[key].lower():
                prefix = key.rsplit('.', 1)[0]
                connected = self.vmx_dict.get(f'{prefix}.startConnected', '').lower()
                cd_settings.append((prefix, connected))

        if not cd_settings:
            self.add_result('INFO', 'No CD/DVD drives found', '')
            return

        for prefix, connected in cd_settings:
            vmx_line = f"{prefix}.startConnected = \"{connected}\""
            if connected != 'false':
                self.add_result('FAIL', f'CD drive {prefix} must start disconnected', vmx_line)
            else:
                self.add_result('PASS', f'CD drive {prefix} starts disconnected', vmx_line)

    def check_shared_folders(self):
        shared_folders = [key for key in self.vmx_dict if key.startswith('shared')]
        vmx_line = "\n".join([f"{key} = \"{self.vmx_dict[key]}\"" for key in shared_folders]) if shared_folders else "No shared folders"
        if not shared_folders:
            self.add_result('PASS', 'No shared folders present', vmx_line)
        else:
            self.add_result('FAIL', 'Shared folders are present and must be removed', vmx_line)

    def check_sound_card(self):
        sound_present = any(key.lower().startswith('sound') and self.vmx_dict[key].lower() == 'true' 
                        for key in self.vmx_dict if key.lower().endswith('present'))
        sound_connected = 'connect at power on' in self.vmx_dict.get('sound.startconnected', '').lower()
        vmx_line = "\n".join([f"{key} = \"{self.vmx_dict[key]}\"" for key in self.vmx_dict if key.lower().startswith('sound')])
        
        if not sound_present:
            self.add_result('FAIL', 'Sound card must be present for accessibility features', vmx_line)
        else:
            self.add_result('PASS', 'Sound card is present and configured correctly', vmx_line)

    def check_ethernet_adapters(self):
        ethernet_settings = {key: value.lower() for key, value in self.vmx_dict.items() 
                            if key.startswith('ethernet') and 'connectiontype' in key.lower()}
        vmx_line = "\n".join([f"{key} = \"{value}\"" for key, value in ethernet_settings.items()])
        
        if not ethernet_settings:
            self.add_result('WARNING', 'No ethernet adapters found', '')
            return

        for key, value in ethernet_settings.items():
            if value not in ['nat', 'hostonly']:
                if value == 'bridged':
                    self.add_result('WARNING', f'{key} is set to bridged - requires SROC approval', f"{key} = \"{value}\"")
                else:
                    self.add_result('FAIL', f'{key} must be NAT or HOSTONLY', f"{key} = \"{value}\"")
            else:
                self.add_result('PASS', f'{key} is set to {value}', f"{key} = \"{value}\"")

        for key, value in ethernet_settings.items():
            if value not in ['nat', 'hostonly']:
                if value == 'bridged':
                    self.add_result('WARNING', f'{key} is set to bridged - requires SROC approval', f"{key} = \"{value}\"")
                else:
                    self.add_result('FAIL', f'{key} must be NAT or HOSTONLY', f"{key} = \"{value}\"")
            else:
                self.add_result('PASS', f'{key} is set to {value}', f"{key} = \"{value}\"")

    def check_usb_compatibility(self):
        usb_setting = self.vmx_dict.get('usb_xhci.present', '')
        vmx_line = f"usb_xhci.present = \"{usb_setting}\""
        if usb_setting.lower() == 'true':
            self.add_result('PASS', 'USB 3.1 compatibility enabled', vmx_line)
        else:
            self.add_result('FAIL', 'USB 3.1 compatibility must be enabled', vmx_line)

    def check_hypervisor(self):
        hypervisor_setting = self.vmx_dict.get('vhv.enable', '')
        vmx_line = f"vhv.enable = \"{hypervisor_setting}\""
        if hypervisor_setting.lower() == 'true':
            self.add_result('WARNING', 'Hypervisor applications enabled - requires SROC approval', vmx_line)
        elif hypervisor_setting.lower() == 'false':
            self.add_result('PASS', 'Hypervisor applications disabled', vmx_line)
        else:
            self.add_result('FAIL', 'Hypervisor setting must be explicitly set to FALSE', vmx_line)

    def check_bluetooth(self):
        bluetooth_setting = self.vmx_dict.get('usb.vbluetooth.startconnected', '')
        vmx_line = f"usb.vbluetooth.startconnected = \"{bluetooth_setting}\""
        if bluetooth_setting.lower() == 'false':
            self.add_result('PASS', 'Bluetooth auto-start disabled', vmx_line)
        else:
            self.add_result('FAIL', 'Bluetooth auto-start must be disabled', vmx_line)

    def check_floppy(self):
        floppy_present = self.vmx_dict.get('floppy0.present', '')
        vmx_line = f"floppy0.present = \"{floppy_present}\""
        if floppy_present.lower() == 'false':
            self.add_result('PASS', 'Floppy drive disabled', vmx_line)
        else:
            self.add_result('FAIL', 'Floppy drive must be disabled', vmx_line)

    def check_side_channel_mitigations(self):
        mitigations = self.vmx_dict.get('ulm.disableMitigations', '')
        vmx_line = f"ulm.disableMitigations = \"{mitigations}\""
        if mitigations.lower() == 'true':
            self.add_result('PASS', 'Side Channel Mitigations disabled for better performance', vmx_line)
        else:
            self.add_result('FAIL', 'Side Channel Mitigations must be disabled', vmx_line)

    def check_3d_graphics(self):
        graphics_setting = self.vmx_dict.get('mks.enable3d', '')
        vmx_line = f"mks.enable3d = \"{graphics_setting}\""
        if graphics_setting.lower() == 'false':
            self.add_result('PASS', '3D acceleration disabled for better display compatibility', vmx_line)
        else:
            self.add_result('FAIL', '3D acceleration must be disabled', vmx_line)

    def get_results(self) -> List[Tuple[str, str, str]]:
        return self.results

def validate_vmx(vmx_content: str) -> List[Tuple[str, str, str]]:
    validator = VMXValidator(vmx_content)
    validator.validate()
    return validator.get_results()

def print_results(results: List[Tuple[str, str, str]]):
    warning_count = sum(1 for status, _, _ in results if status == 'WARNING')
    fail_count = sum(1 for status, _, _ in results if status == 'FAIL')
    
    for status, message, vmx_line in results:
        if status == 'PASS':
            print(f"{Fore.GREEN}{status}: {message}")
        elif status == 'FAIL':
            print(f"{Fore.RED}{status}: {message}")
        elif status == 'WARNING':
            print(f"{Fore.YELLOW}{status}: {message}")
        elif status == 'INFO':
            print(f"{Fore.BLUE}{status}: {message}")
        
        if vmx_line:
            print(f"{Fore.CYAN}VMX: {vmx_line}{Style.RESET_ALL}")
        print()

    if warning_count or fail_count:
        print(f"\n{Fore.YELLOW}Summary:")
        if warning_count:
            print(f"{Fore.YELLOW}{warning_count} warning(s) found - may require SROC approval")
        if fail_count:
            print(f"{Fore.RED}{fail_count} check(s) failed - must be fixed")

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