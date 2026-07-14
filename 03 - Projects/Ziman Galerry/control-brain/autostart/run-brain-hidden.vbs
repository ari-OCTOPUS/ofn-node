' مغزِ کنترل را بی‌پنجره (در پس‌زمینه) اجرا می‌کند.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.Run """" & dir & "\run-brain.bat""", 0, False
