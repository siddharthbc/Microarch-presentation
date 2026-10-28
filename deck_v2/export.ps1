param([Parameter(Mandatory=$true)][string]$Pptx,[string]$Pdf="",[string]$PngDir="",[int]$PngWidth=1600)
$ErrorActionPreference="Stop"
try { Unblock-File -Path $Pptx -ErrorAction SilentlyContinue } catch {}
$app=$null;$deck=$null;$ownsApp=$false
$Pptx=(Resolve-Path -LiteralPath $Pptx).Path
try {
  try { $app=[Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application') }
  catch { $app=New-Object -ComObject PowerPoint.Application; $ownsApp=$true }
  # Export a separate, read-only copy without disturbing the user's open deck.
  $deck=$app.Presentations.Open($Pptx,-1,0,0)
  if($Pdf){ $deck.SaveAs($Pdf,32) }
  if($PngDir){ New-Item -ItemType Directory -Path $PngDir -Force | Out-Null
    $deck.Export($PngDir,"PNG",$PngWidth,[int]($PngWidth*9/16)) }
  Write-Output "Exported $($deck.Slides.Count) slides."
} finally {
  if($null -ne $deck){ $deck.Close() }
  if($ownsApp -and $null -ne $app -and $app.Presentations.Count -eq 0){ $app.Quit() }
}
