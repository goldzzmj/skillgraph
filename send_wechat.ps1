$wshell = New-Object -ComObject WScript.Shell
$wshell.AppActivate('WeChat')
Start-Sleep -Seconds 2
$wshell.SendKeys('^f')
Start-Sleep -Seconds 1
$wshell.SendKeys('郑政隆')
Start-Sleep -Seconds 1
$wshell.SendKeys('{ENTER}')
Start-Sleep -Seconds 1
$wshell.SendKeys('我现在是使用openclaw的skills控制电脑微信，自动给你发的消息')
Start-Sleep -Seconds 1
$wshell.SendKeys('{ENTER}')
