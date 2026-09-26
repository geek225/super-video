' ==============================================================================
' Lanceur Silencieux pour Windows - Super Video AI Studio
' Lance l'application directement en arriere-plan (sans fenetre noire d'invite de commande)
' ==============================================================================
Option Explicit

Dim FSO, WshShell, CurrentDir
Set FSO = CreateObject("Scripting.FileSystemObject")
CurrentDir = FSO.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CurrentDir

' Lancement invisible du script de demarrage (parametre 0 = masquage complet de la fenetre)
WshShell.Run "cmd.exe /c """ & CurrentDir & "\lancer.bat""", 0, False
