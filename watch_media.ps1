Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

try {
    [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType = WindowsRuntime] | Out-Null
    $managerOp = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
    $manager = Await $managerOp ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])

    $lastOut = ""
    while ($true) {
        try {
            $s = $manager.GetCurrentSession()
            if (-not $s) {
                $all = $manager.GetSessions()
                if ($all -and $all.Count -gt 0) {
                    foreach ($item in $all) {
                        $pi = $item.GetPlaybackInfo()
                        if ($pi -and $pi.PlaybackStatus.ToString() -eq "Playing") {
                            $s = $item
                            break
                        }
                    }
                    if (-not $s) { $s = $all[0] }
                }
            }
            if ($s) {
                $p = $s.GetPlaybackInfo()
                $status = if ($p) { $p.PlaybackStatus.ToString() } else { "None" }
                $propsOp = $s.TryGetMediaPropertiesAsync()
                $props = Await $propsOp ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
                $out = "$status|$($props.Title)|$($props.Artist)|$($props.AlbumTitle)"
            } else {
                $out = "None|||"
            }
            if ($out -ne $lastOut) {
                [Console]::WriteLine($out)
                $lastOut = $out
            }
        } catch {}
        Start-Sleep -Milliseconds 80
    }
} catch {
    [Console]::WriteLine("ERROR|" + $_)
}

