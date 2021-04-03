#Requires -Version 4

Import-Module DhcpServer -ErrorAction SilentlyContinue -ErrorVariable DHCPError 
If ($DHCPError) {
    Write-Warning "DHCP PowerShell module not available. Please install it using the command:
Install-WindowsFeature RSAT-DHCP"
}
 
Import-Module ActiveDirectory -ErrorAction SilentlyContinue -ErrorVariable ADError 
If ($ADError) {
    Write-Warning "ActiveDirectory PowerShell module not available. Please install it using the command:
Install-WindowsFeature RSAT-AD-PowerShell"
}

If ($DHCPError -or $ADError) {
    Write-Warning "Dependency error. Please install dependencies and run this script again."
    Exit -1
}

function Convert-IpAddressToMaskLength([string] $dottedIpAddressString)
{
  # Source: https://d-fens.ch/2013/11/01/nobrainer-using-powershell-to-convert-an-ipv4-subnet-mask-length-into-a-subnet-mask-address/
  $result = 0; 
  # ensure we have a valid IP address
  [IPAddress] $ip = $dottedIpAddressString;
  $octets = $ip.IPAddressToString.Split('.');
  foreach($octet in $octets)
  {
    while(0 -ne $octet) 
    {
      $octet = ($octet -shl 1) -band [byte]::MaxValue
      $result++; 
    }
  }
  return $result;
}

# Get subnets by DHCP scopes in the current Active Directory domain

$All_Subnets = @()
$DHCP_Subnets = @()
$Computer_Subnets = @()

$AllDHCPServers = Get-DhcpServerInDC
$WorkingDHCPServers = @()
$BadDHCPServers = @()

# Test each DHCP server to make sure it can be queried remotely
Foreach ($DHCPServer in $AllDHCPServers ) {
    try {
        Get-DhcpServerv4Scope -ComputerName $DHCPServer.DnsName >$null
        $WorkingDHCPServers += $DHCPServer.DnsName
    } catch {
        Write-Warning( "DHCP server " + $DHCPserver.DnsName + " could not be queried remotely!")
        $BadDHCPServers += $DHCPServer.DnsName
    }
}

Foreach ($DHCPServer in $WorkingDHCPServers) {
    Get-DhcpServerv4Scope -ComputerName $DHCPServer | ForEach-Object {
    $DHCP_Subnets += '{0}/{1}' -f $_.ScopeId, $(Convert-IpAddressToMaskLength($_.SubnetMask)) } 
}

# Get subnets by active computers in the current Active Directory domain (pretending that each IP is part of a /24)

$DomainComputers = Get-ADComputer -Filter * -Properties ipv4Address

$Computer_Subnets = $DomainComputers | ForEach-Object {
  if ($_.IPv4Address) { # If AD object has an IP address assigned...
    ([IPAddress] (([IPAddress] $_.IPv4Address).Address -band ([IPAddress] "255.255.255.0").Address)).IPAddressToString # Pretend it's a /24, find the subnet IP
    }
  } | Sort-Object -Unique | ForEach-Object { # Get the unique list
    "$_"+"/24"}

$All_Subnets = ( ($Computer_Subnets, $DHCP_Subnets) | Sort-Object -Unique)

$All_Subnets | Out-Host
