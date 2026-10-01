Option Explicit
Dim shell, files, folder, powershell, command, status, failure
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
powershell = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"
command = """" & powershell & """ -NoProfile -ExecutionPolicy Bypass -File """ & folder & "\start_source.ps1"""
On Error Resume Next
status = shell.Run(command, 0, True)
If Err.Number <> 0 Then
    failure = Err.Description
    Err.Clear
    status = 1
End If
On Error GoTo 0
If status <> 0 And status <> 2 Then
    failure = "DokuReader konnte nicht gestartet werden." & vbCrLf & failure & vbCrLf & "Bitte debug.bat starten."
    WriteFailure failure
    MsgBox failure, vbCritical, "DokuReader - Startfehler"
End If
If status <> 0 Then WScript.Quit 1

Sub WriteFailure(message)
    Dim localFolder, logs, stream
    On Error Resume Next
    localFolder = CreateObject("Shell.Application").NameSpace(&H1C).Self.Path
    If Len(localFolder) = 0 Then Exit Sub
    If Not files.FolderExists(localFolder & "\DokuReader") Then files.CreateFolder localFolder & "\DokuReader"
    logs = localFolder & "\DokuReader\logs"
    If Not files.FolderExists(logs) Then files.CreateFolder logs
    Set stream = CreateObject("ADODB.Stream")
    stream.Type = 2
    stream.Charset = "utf-8"
    stream.Open
    stream.WriteText message
    stream.SaveToFile logs & "\starter-error.log", 2
    stream.Close
    On Error GoTo 0
End Sub
