param(
    [Parameter(Mandatory=$true)][ValidateSet("probe","start","stop","status","clients")][string]$Action,
    [string]$Json = "{}"
)

$ErrorActionPreference = "Stop"

function Emit($ok, $message = "", $extra = @{}) {
    $obj = [ordered]@{ ok = [bool]$ok; message = $message }
    foreach ($k in $extra.Keys) { $obj[$k] = $extra[$k] }
    $obj | ConvertTo-Json -Compress -Depth 8
}

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime

    # Convert WinRT IAsyncOperation<T> to a blocking .NET Task.
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    })[0]

    $asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1
    })[0]

    function AwaitOperation($operation, $resultType) {
        $method = $asTaskGeneric.MakeGenericMethod($resultType)
        $task = $method.Invoke($null, @($operation))
        $task.Wait(-1) | Out-Null
        return $task.Result
    }

    function AwaitAction($action) {
        $task = $asTaskAction.Invoke($null, @($action))
        $task.Wait(-1) | Out-Null
    }

    $profile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
    if ($null -eq $profile) { throw "Windows has no active Internet connection profile." }

    $managerType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
    $capability = $managerType::GetTetheringCapabilityFromConnectionProfile($profile)
    $capabilityName = [string]$capability

    if ($Action -eq "probe") {
        $state = "Unknown"
        try {
            $mgr = $managerType::CreateFromConnectionProfile($profile)
            $state = [string]$mgr.TetheringOperationalState
            $clients = 0
            try { $clients = $mgr.ClientCount } catch {}
            Emit $true "Windows Mobile Hotspot API detected." @{ capability = $capabilityName; state = $state; clientCount = $clients }
        } catch {
            Emit $false "Windows tethering API unavailable: $($_.Exception.Message)" @{ capability = $capabilityName; state = $state }
            exit 2
        }
        exit 0
    }

    $manager = $managerType::CreateFromConnectionProfile($profile)

    if ($Action -eq "status") {
        $cfg = $manager.GetCurrentAccessPointConfiguration()
        $clients = 0
        try { $clients = $manager.ClientCount } catch {}
        Emit $true "Windows Mobile Hotspot status." @{ capability = $capabilityName; state = [string]$manager.TetheringOperationalState; ssid = [string]$cfg.Ssid; clientCount = $clients; maxClients = [int]$manager.MaxClientCount }
        exit 0
    }

    if ($Action -eq "clients") {
        $items = @()
        try {
            foreach ($client in $manager.GetTetheringClients()) {
                $hosts = @()
                foreach ($host in $client.HostNames) { $hosts += [string]$host.DisplayName }
                $items += [ordered]@{ mac = [string]$client.MacAddress; hosts = $hosts }
            }
        } catch {}
        Emit $true "Connected tethering clients." @{ clients = $items }
        exit 0
    }

    if ($Action -eq "stop") {
        if ([string]$manager.TetheringOperationalState -eq "Off") {
            Emit $true "Windows Mobile Hotspot is already off."; exit 0
        }
        $resultType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
        $result = AwaitOperation ($manager.StopTetheringAsync()) $resultType
        if ([string]$result.Status -ne "Success" -and [string]$result.Status -ne "AlreadyOff") {
            throw "Stop failed: $([string]$result.Status) $([string]$result.AdditionalErrorMessage)"
        }
        Emit $true "Windows Mobile Hotspot stopped." @{ status = [string]$result.Status }
        exit 0
    }

    if ($Action -eq "start") {
        $p = $Json | ConvertFrom-Json
        if ([string]::IsNullOrWhiteSpace($p.ssid)) { throw "SSID is required." }
        if ([string]::IsNullOrWhiteSpace($p.password)) { throw "Password is required." }

        # Windows 10 supports persistent SSID/passphrase configuration.
        $cfg = New-Object 'Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration'
        $cfg.Ssid = [string]$p.ssid
        $cfg.Passphrase = [string]$p.password
        AwaitAction ($manager.ConfigureAccessPointAsync($cfg))

        $resultType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
        $result = AwaitOperation ($manager.StartTetheringAsync()) $resultType
        $status = [string]$result.Status
        if ($status -ne "Success" -and $status -ne "AlreadyOn") {
            $detail = [string]$result.AdditionalErrorMessage
            throw "Start failed: $status $detail"
        }
        Emit $true "Windows Mobile Hotspot started." @{ status = $status; ssid = [string]$p.ssid }
        exit 0
    }

    throw "Unsupported action: $Action"
} catch {
    Emit $false $_.Exception.Message
    exit 1
}
