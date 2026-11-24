# Notification hook (Windows): show a desktop toast when Claude Code needs
# permission or input. The toast is sent under VS Code's AppUserModelID so it
# appears as "Visual Studio Code"; clicking it opens vscode://file/<cwd>,
# which focuses the VS Code window that has the project open.
# Falls back to PowerShell's identity if VS Code toasts are disabled.

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
try { $data = $raw | ConvertFrom-Json } catch { $data = $null }

$type = if ($data -and $data.notification_type) { [string]$data.notification_type } else { '' }
$titles = @{
    'permission_prompt'  = 'Claude Code: permission needed'
    'idle_prompt'        = 'Claude Code: waiting for your input'
    'elicitation_dialog' = 'Claude Code: input requested'
}
# Only notify when Claude actually waits for the user (unknown/missing type: notify).
if ($type -and -not $titles.ContainsKey($type)) { exit 0 }

$title = if ($titles.ContainsKey($type)) { $titles[$type] } else { 'Claude Code' }
$msg = if ($data -and $data.message) { [string]$data.message } else { 'Claude Code needs your attention' }
$cwd = if ($data -and $data.cwd) { [string]$data.cwd } else { '' }
if ($cwd) { $title += " - $(Split-Path $cwd -Leaf)" }

function Esc([string]$s) { [Security.SecurityElement]::Escape($s) }

$launch = ''
if ($cwd) {
    $uri = 'vscode://file/' + ($cwd -replace '\\', '/')
    $launch = " activationType=`"protocol`" launch=`"$(Esc $uri)`""
}
$xmlText = "<toast$launch><visual><binding template=`"ToastGeneric`">" +
    "<text>$(Esc $title)</text><text>$(Esc $msg)</text>" +
    "</binding></visual><audio src=`"ms-winsoundevent:Notification.Default`"/></toast>"

[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($xmlText)

$appIds = @(
    'Microsoft.VisualStudioCode',
    '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
)
# (Notifier.Setting is not readable from Windows PowerShell 5.1, so just try.)
foreach ($id in $appIds) {
    try {
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($id)
        $notifier.Show([Windows.UI.Notifications.ToastNotification]::new($xml))
        Write-Output "shown via $id"
        exit 0
    } catch {
        Write-Output "failed via ${id}: $($_.Exception.Message)"
    }
}
exit 0
