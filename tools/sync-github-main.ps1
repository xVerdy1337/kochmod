$ErrorActionPreference = 'Stop'
$source = 'D:\Temp\kochmodoi4-git-20261018'
$target = (Get-Location).Path
$backup = Join-Path $target ('tools/backups/pre-github-sync-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force $backup | Out-Null

# Keep a recoverable copy of the current content affected by upstream changes.
Copy-Item -LiteralPath (Join-Path $target 'common') -Destination (Join-Path $backup 'common') -Recurse
Copy-Item -LiteralPath (Join-Path $target 'history') -Destination (Join-Path $backup 'history') -Recurse
Copy-Item -LiteralPath (Join-Path $target 'interface') -Destination (Join-Path $backup 'interface') -Recurse
Copy-Item -LiteralPath (Join-Path $target 'localisation') -Destination (Join-Path $backup 'localisation') -Recurse
Copy-Item -LiteralPath (Join-Path $target 'map') -Destination (Join-Path $backup 'map') -Recurse
Copy-Item -LiteralPath (Join-Path $target 'README.md') -Destination (Join-Path $backup 'README.md')

$skip = @(
    'descriptor.mod',
    'common/country_tags/koch_countries.txt',
    'common/bookmarks/koch_empty_world.txt',
    'common/countries/koch_B09.txt',
    'history/countries/B09 - koch.txt',
    'interface/koch_portraits.gfx',
    'localisation/russian/koch_countries_l_russian.yml',
    'localisation/english/koch_countries_l_english.yml',
    'localisation/russian/koch_victory_points_l_russian.yml',
    'localisation/english/koch_victory_points_l_english.yml',
    'README.md'
)
Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($source.Length + 1).Replace('\','/')
    if ($skip -notcontains $relative -and $relative -notlike '.git/*') {
        $destination = Join-Path $target ($relative.Replace('/','\'))
        New-Item -ItemType Directory -Force (Split-Path -Parent $destination) | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    }
}

$nl = [Environment]::NewLine
$tags = Get-Content (Join-Path $source 'common/country_tags/koch_countries.txt') -Raw
if ($tags -notmatch '(?m)^B11\s*=') { $tags = $tags.TrimEnd() + $nl + 'B11 = "countries/koch_B11.txt"' + $nl }
[IO.File]::WriteAllText((Join-Path $target 'common/country_tags/koch_countries.txt'), $tags, [Text.UTF8Encoding]::new($false))

$bookmarks = Get-Content (Join-Path $source 'common/bookmarks/koch_empty_world.txt') -Raw
$localBookmarks = Get-Content (Join-Path $backup 'common/bookmarks/koch_empty_world.txt') -Raw
$b09Pattern = '(?ms)        "B09"\s*=\s*\{.*?        \}'
$localB09 = [regex]::Matches($localBookmarks, $b09Pattern)[0].Value
$bookmarks = [regex]::Replace($bookmarks, $b09Pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $localB09 })
$b11 = '        "B11" = {' + $nl + '            history = "KOCH_B11_DESC"' + $nl + '            ideology = democratic' + $nl + '            version = base_game' + $nl + '        }'
$bookmarks = $bookmarks -replace '(?m)(        "B07" = \{.*?        \}' + $nl + ')', ('$1' + $b11 + $nl)
[IO.File]::WriteAllText((Join-Path $target 'common/bookmarks/koch_empty_world.txt'), $bookmarks, [Text.UTF8Encoding]::new($false))

$localPortraits = Get-Content (Join-Path $backup 'interface/koch_portraits.gfx') -Raw
$upPortraits = Get-Content (Join-Path $source 'interface/koch_portraits.gfx') -Raw
$blocks = [regex]::Matches($upPortraits, '(?ms)    spriteType\s*=\s*\{.*?    \}') | ForEach-Object { $_.Value }
$mergedPortraits = $localPortraits
foreach ($block in $blocks) {
    $name = [regex]::Match($block, 'name\s*=\s*"([^"]+)"').Groups[1].Value
    if ($name -and $mergedPortraits -notmatch [regex]::Escape($name)) {
        $mergedPortraits = $mergedPortraits -replace '(?s)\}\s*$', ($block + $nl + '}' + $nl)
    }
}
[IO.File]::WriteAllText((Join-Path $target 'interface/koch_portraits.gfx'), $mergedPortraits, [Text.UTF8Encoding]::new($false))

function Merge-Loc($localPath, $upPath) {
    $localText = Get-Content $localPath -Raw
    $upText = Get-Content $upPath -Raw
    $lines = [ordered]@{}
    foreach ($line in ($localText -split "\r?\n")) { if ($line -match '^\s*([^\s:#]+):\d+\s+"') { $lines[$matches[1]] = $line } }
    foreach ($line in ($upText -split "\r?\n")) { if ($line -match '^\s*([^\s:#]+):\d+\s+"' -and -not $lines.Contains($matches[1])) { $lines[$matches[1]] = $line } }
    $header = if ($localText -match '(?m)^l_english:') { 'l_english:' } else { 'l_russian:' }
    [IO.File]::WriteAllText($localPath, $header + $nl + (($lines.Values -join $nl) + $nl), [Text.UTF8Encoding]::new($true))
}
Merge-Loc (Join-Path $target 'localisation/russian/koch_countries_l_russian.yml') (Join-Path $source 'localisation/russian/koch_countries_l_russian.yml')
Merge-Loc (Join-Path $target 'localisation/english/koch_countries_l_english.yml') (Join-Path $source 'localisation/english/koch_countries_l_english.yml')
Merge-Loc (Join-Path $target 'localisation/russian/koch_victory_points_l_russian.yml') (Join-Path $source 'localisation/russian/koch_victory_points_l_russian.yml')
Merge-Loc (Join-Path $target 'localisation/english/koch_victory_points_l_english.yml') (Join-Path $source 'localisation/english/koch_victory_points_l_english.yml')

$readme = Get-Content (Join-Path $source 'README.md') -Raw
$podikDoc = Get-Content (Join-Path $target 'docs/podik-republic.md') -Raw
if ($readme -notmatch 'Древо Подиковой республики') { $readme = $readme.TrimEnd() + $nl + $nl + '## Древо Подиковой республики' + $nl + $podikDoc }
[IO.File]::WriteAllText((Join-Path $target 'README.md'), $readme, [Text.UTF8Encoding]::new($false))
Write-Output "Synced upstream main; backup: $backup"
