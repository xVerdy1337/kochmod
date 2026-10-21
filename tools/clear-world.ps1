param(
    [string]$GameRoot = 'C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV'
)
$ErrorActionPreference = 'Stop'
$modRoot = Split-Path $PSScriptRoot -Parent
$utf8 = [System.Text.UTF8Encoding]::new($false)

function Get-BlockEnd($tokens, [int]$start) {
    $depth = 0
    for ($i = $start; $i -lt $tokens.Count; $i++) {
        if ($tokens[$i].Value -eq '{') { $depth++ }
        if ($tokens[$i].Value -eq '}') {
            $depth--
            if ($depth -eq 0) { return $i }
        }
    }
    throw 'Unbalanced script block'
}

function Get-CleanHistory([string]$source, $tokens, [int]$start, [int]$end) {
    $parts = [System.Collections.Generic.List[string]]::new()
    $i = $start + 1
    while ($i -lt $end) {
        $key = $tokens[$i].Value
        if ($tokens[$i + 1].Value -ne '=') { throw "Unexpected history token: $key" }
        $value = $i + 2
        $last = $value
        if ($tokens[$value].Value -eq '{') { $last = Get-BlockEnd $tokens $value }
        if ($key -in @('buildings', 'victory_points')) {
            $offset = $tokens[$i].Index
            $length = $tokens[$last].Index + $tokens[$last].Length - $offset
            $parts.Add($source.Substring($offset, $length))
        } elseif ($key -match '^\d+\.\d+\.\d+(\.\d+)?$' -and $tokens[$value].Value -eq '{') {
            $nested = Get-CleanHistory $source $tokens $value $last
            if ($nested.Trim().Length -gt 0) { $parts.Add("$key = {`n$nested`n}") }
        }
        $i = $last + 1
    }
    return ($parts -join "`n")
}

$sourceDir = Join-Path $GameRoot 'history/states'
$targetDir = Join-Path $modRoot 'history/states'
$files = @(Get-ChildItem -LiteralPath $sourceDir -Filter '*.txt' -File)
if ($files.Count -eq 0) { throw 'No source states found' }
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
foreach ($file in $files) {
    $source = [System.IO.File]::ReadAllText($file.FullName)
    $tokens = @([regex]::Matches($source, '#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#"]+') | Where-Object { -not $_.Value.StartsWith('#') })
    $history = -1
    for ($i = 0; $i -lt $tokens.Count - 2; $i++) {
        if ($tokens[$i].Value -eq 'history' -and $tokens[$i + 1].Value -eq '=') { $history = $i; break }
    }
    if ($history -lt 0) { throw "Missing history: $($file.Name)" }
    $start = $history + 2
    if ($tokens[$start].Value -ne '{') { throw 'Expected history block' }
    $end = Get-BlockEnd $tokens $start
    $clean = Get-CleanHistory $source $tokens $start $end
    $result = $source.Substring(0, $tokens[$start].Index) + "{`n$clean`n}" + $source.Substring($tokens[$end].Index + 1)
    if ($result -match '\b(owner|controller|add_core_of|add_claim_by|transfer_state)\s*=') { throw "Political data remains: $($file.Name)" }
    [System.IO.File]::WriteAllText((Join-Path $targetDir $file.Name), $result, $utf8)
}
Write-Output "Cleaned $($files.Count) states. Geography, resources, population, buildings and victory points preserved."
