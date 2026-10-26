Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
}[0]

Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()

$baseDir = "C:\Users\MSI\Desktop\Research\Profit Folder\data-source\crop-calendar-images"
$files = Get-ChildItem -Path $baseDir -Recurse -File -Include *.jpg, *.jpeg, *.png

$report = @()

foreach ($f in $files) {
    $rel = $f.FullName.Substring($baseDir.Length + 1)
    try {
        $fileObj = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName)) ([Windows.Storage.StorageFile])
        $stream = Await ($fileObj.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $ocrResult = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        
        $lines = @($ocrResult.Lines)
        $textSample = ($lines | Select-Object -First 6 | ForEach-Object { $_.Text }) -join " | "
        
        $hasActivities = $false
        $hasFertilizer = $false
        $hasVarieties = $false
        $hasDiseases = $false
        
        foreach ($l in $lines) {
            $t = $l.Text.ToLower()
            if ($t -match 'activities|land preparation|nursery|planting|harvesting') { $hasActivities = $true }
            if ($t -match 'fertilizer|urea|tsp|mop|basal') { $hasFertilizer = $true }
            if ($t -match 'variety|varieties|duration|days') { $hasVarieties = $true }
            if ($t -match 'pest|disease|thrips|caterpillar') { $hasDiseases = $true }
        }
        
        Write-Output ("FILE: " + $rel)
        Write-Output ("  Dimensions: " + $bitmap.PixelWidth + "x" + $bitmap.PixelHeight)
        Write-Output ("  OCR Lines: " + $lines.Count)
        Write-Output ("  Sample: " + $textSample)
        Write-Output ("  Sections: Activities=" + $hasActivities + ", Fertilizer=" + $hasFertilizer + ", Varieties=" + $hasVarieties + ", Diseases=" + $hasDiseases)
        Write-Output ("--------------------------------------------------")
    } catch {
        Write-Output ("ERROR on " + $rel + ": " + $_.Exception.Message)
    }
}
