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

    $session = $manager.GetCurrentSession()
    if (-not $session) {
        $sessions = $manager.GetSessions()
        if ($sessions -and $sessions.Count -gt 0) {
            # Find a playing session first, or the first active session (e.g. paused)
            foreach ($s in $sessions) {
                $pi = $s.GetPlaybackInfo()
                if ($pi -and ($pi.PlaybackStatus.ToString() -eq "Playing")) {
                    $session = $s
                    break
                }
            }
            if (-not $session) {
                $session = $sessions[0]
            }
        }
    }
    if ($session) {
        $playbackInfo = $session.GetPlaybackInfo()
        $status = if ($playbackInfo) { $playbackInfo.PlaybackStatus.ToString() } else { "Unknown" }
        $propsOp = $session.TryGetMediaPropertiesAsync()
        $props = Await $propsOp ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
        
        $thumb = $props.Thumbnail
        $thumbFile = "c:\Dev\keyboard\now_playing_art.jpg"
        $hasThumb = $false
        if ($thumb) {
            try {
                $streamOp = $thumb.OpenReadAsync()
                $stream = Await $streamOp ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
                $reader = New-Object Windows.Storage.Streams.DataReader($stream)
                $loadOp = $reader.LoadAsync([uint32]$stream.Size)
                $bytesLoaded = Await $loadOp ([uint32])
                $bytes = New-Object byte[] $bytesLoaded
                $reader.ReadBytes($bytes)
                $reader.Close()
                [System.IO.File]::WriteAllBytes($thumbFile, $bytes)
                $hasThumb = $true
            } catch {}
        }
        
        [PSCustomObject]@{
            Status = $status
            Title = $props.Title
            Artist = $props.Artist
            Album = $props.AlbumTitle
            HasThumbnail = $hasThumb
        } | ConvertTo-Json -Compress
    } else {
        Write-Output '{"Status":"None"}'
    }
} catch {
    Write-Output '{"Status":"None"}'
}
