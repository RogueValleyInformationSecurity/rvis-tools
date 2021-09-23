$VerbosePreference="Continue"

$Port=2121
$Log="honeyport-log.txt" # Feel free to change this to an absolute path, such as "C:\Windows\Temp\honeyport-log.txt"
$KeepListening=$false # Feel free to set this to $false for testing one connection at a time
$CanaryToken="p1iaiqibbtkr0bamjoq46gkgm.canarytokens.com"

function Get-TimeStamp {
    
    return "[{0:MM/dd/yy} {0:HH:mm:ss}]" -f (Get-Date)
    
}

$EndPoint=[System.Net.IPEndPoint]::new([System.Net.IPAddress]::any,$Port)
$Listener=[System.Net.Sockets.TcpListener]::new($EndPoint)

try {
    do  {
        $Listener.Start()
        Write-Output "Started honeyport on port $Port on $(Get-Timestamp)"
        Write-Output "Started honeyport on port $Port on $(Get-Timestamp)" | Out-File -Append $Log 
        while (!$Listener.Pending) { Start-Sleep -Milliseconds 100 }

        $Client=$Listener.AcceptTcpClient()
        Write-Output "Incoming connection logged from $($Client.Client.RemoteEndPoint.Address):$($Client.Client.RemoteEndPoint.Port) on $(Get-Timestamp)"
        Write-Output "Incoming connection logged from $($Client.Client.RemoteEndPoint.Address):$($Client.Client.RemoteEndPoint.Port) on $(Get-Timestamp)" | Out-File -Append $Log 
        Resolve-DnsName -Name $CanaryToken >$null
        Write-Output "Resolved $CanaryToken on $(Get-Timestamp)"
        Write-Output "Resolved $CanaryToken on $(Get-Timestamp)" | Out-File -Append $Log 

        $Client.Close()
    }
    while ($KeepListening)
    $Listener.Stop()
}
finally {
    Write-Host "Closed honeyport on $(Get-Timestamp)"
    Write-Host "Closed honeyport on $(Get-Timestamp)" | Out-File -Append $Log
}
