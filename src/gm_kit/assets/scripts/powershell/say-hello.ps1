param(
    [Parameter(Mandatory = $true)][string]$Greeting,
    [Parameter(Mandatory = $true)][string]$Sequence,
    [Parameter(Mandatory = $true)][string]$TemplatesDir,
    [Parameter(Mandatory = $true)][string]$OutputDir
)

function Render-Template {
    param(
        [string]$TemplatePath,
        [string]$Greeting,
        [string]$Sequence
    )
    $content = Get-Content -Raw -LiteralPath $TemplatePath
    $content = [Regex]::Replace($content, '{{\s*greeting\s*}}', { param($match) $Greeting })
    return [Regex]::Replace($content, '{{\s*sequence\s*}}', { param($match) $Sequence })
}

$templatePath = Join-Path $TemplatesDir "hello-gmkit-template.md"
$outputDirPath = Join-Path $OutputDir "greetings"
$outputPath = Join-Path $outputDirPath ("greeting{0}.md" -f $Sequence)

New-Item -ItemType Directory -Force -Path $outputDirPath | Out-Null

$rendered = Render-Template -TemplatePath $templatePath -Greeting $Greeting -Sequence $Sequence
Set-Content -LiteralPath $outputPath -Value $rendered -NoNewline
Write-Output $rendered
