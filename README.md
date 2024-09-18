# rvis-tools
Publicly-available tools from Rogue Valley Information Security

## honeyport.ps1

Intended for unattend use inside various Windows clients inside an Active Directory domain.

Dependencies: None. 

Inputs: `$Port`, `$Log`, and `$CanaryToken` should each be updated to match your environment's needs.

Outputs: Alerts triggered via https://canarytokens.org/ and local log file with additional details.

## Get-InternalSubnets.ps1

Intended for use at an administrative Windows console inside an Active Directory domain.

Dependencies: Inside an administrative PowerShell prompt on Windows 8.1 and above:

```powershell
Install-WindowsFeature RSAT-AD-Powershell
Install-WindowsFeature RSAT-DHCP
```

Inputs: None needed.

Outputs: Subnet ranges from domain-joined DHCP servers, as well as the unique set of /24 subnets from domain-joined computers.

This tool will also write warnings about AD-registered DHCP servers that can't be remotely queried. Usually this would mean non-Windows DHCP servers.

## validate-vmx.py

Intended for validating VMware VMX files before submission to automated processes.

Inputs: Path to VMX file.

Outputs: Pass/Fail/Info messages about the VMX file.