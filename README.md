# rvis-tools
Publicly-available tools from Rogue Valley Information Security

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
