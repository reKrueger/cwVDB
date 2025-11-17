# Windows Task Scheduler Setup Guide

## Automatische tägliche Updates einrichten

Diese Anleitung zeigt, wie du den Windows Task Scheduler einrichtest, um täglich automatisch die Vektordatenbank zu aktualisieren.

---

## Methode 1: Über PowerShell (Empfohlen)

Führe diesen Befehl in PowerShell **als Administrator** aus:

```powershell
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Github\cwVDB\run_incremental_update.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Daily incremental update of cwVDB vector database"
Register-ScheduledTask -TaskName "cwVDB Incremental Update" -InputObject $task
```

**Hinweis:** Passe den Pfad an, falls du cwVDB woanders installiert hast!

---

## Methode 2: Über Task Scheduler GUI

### Schritt 1: Task Scheduler öffnen
1. Windows-Taste drücken
2. "Task Scheduler" tippen
3. Task Scheduler öffnen

### Schritt 2: Neue Aufgabe erstellen
1. Rechtsklick auf "Task Scheduler Library"
2. "Create Task..." auswählen

### Schritt 3: General Tab
- **Name:** `cwVDB Incremental Update`
- **Description:** `Daily incremental update of cwVDB vector database`
- **Security options:**
  - [x] Run only when user is logged on
  - [ ] Run whether user is logged on or not (optional, für Hintergrund)
  - [x] Run with highest privileges (empfohlen)

### Schritt 4: Triggers Tab
1. "New..." klicken
2. **Begin the task:** `On a schedule`
3. **Settings:** `Daily`
4. **Start:** `6:00:00 AM` (oder deine bevorzugte Zeit)
5. **Recur every:** `1 days`
6. [x] **Enabled**
7. "OK" klicken

### Schritt 5: Actions Tab
1. "New..." klicken
2. **Action:** `Start a program`
3. **Program/script:** `PowerShell.exe`
4. **Add arguments:**
   ```
   -ExecutionPolicy Bypass -File "C:\Github\cwVDB\run_incremental_update.ps1"
   ```
5. **Start in:** `C:\Github\cwVDB`
6. "OK" klicken

### Schritt 6: Conditions Tab
- [ ] Start the task only if the computer is on AC power (optional)
- [x] Wake the computer to run this task (optional)
- [ ] Start only if the following network connection is available

### Schritt 7: Settings Tab
- [x] Allow task to be run on demand
- [x] Run task as soon as possible after a scheduled start is missed
- [x] If the task fails, restart every: `1 hour`, Attempt to restart up to: `3 times`
- [ ] Stop the task if it runs longer than: (deaktiviert)
- **If the running task does not end when requested:** `Do not start a new instance`

### Schritt 8: Speichern
1. "OK" klicken
2. Ggf. Passwort eingeben

---

## Task testen

### Sofort ausführen
1. Task Scheduler öffnen
2. "Task Scheduler Library" → "cwVDB Incremental Update"
3. Rechtsklick → "Run"
4. Status überprüfen

### Log überprüfen
```powershell
cd C:\Github\cwVDB
type logs\incremental_update_*.log
```

---

## Task verwalten

### Task deaktivieren
```powershell
Disable-ScheduledTask -TaskName "cwVDB Incremental Update"
```

### Task aktivieren
```powershell
Enable-ScheduledTask -TaskName "cwVDB Incremental Update"
```

### Task löschen
```powershell
Unregister-ScheduledTask -TaskName "cwVDB Incremental Update" -Confirm:$false
```

### Task Status anzeigen
```powershell
Get-ScheduledTask -TaskName "cwVDB Incremental Update" | Select-Object TaskName, State, LastRunTime, NextRunTime
```

---

## Troubleshooting

### Problem: Task läuft nicht
**Lösung:**
1. PowerShell als Administrator öffnen
2. Execution Policy setzen:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Problem: Task schlägt fehl
**Lösung:**
1. Log-Datei prüfen: `logs\incremental_update_*.log`
2. Manuell testen:
   ```powershell
   cd C:\Github\cwVDB
   .\run_incremental_update.ps1
   ```

### Problem: Python nicht gefunden
**Lösung:**
- Prüfen ob Virtual Environment aktiviert ist
- Prüfen ob Pfad in run_incremental_update.ps1 korrekt ist

### Problem: Git Changes werden nicht erkannt
**Lösung:**
1. Prüfen ob Source-Pfad ein Git Repository ist
2. `config.json` prüfen: `source_path` korrekt?
3. Manuelle Git-Prüfung:
   ```bash
   cd C:\source\cadlib\v_33.0
   git status
   ```

---

## Monitoring

### Email-Benachrichtigung bei Fehler (Optional)

Erweitere `run_incremental_update.ps1`:

```powershell
# Am Ende des Scripts:
if ($LASTEXITCODE -ne 0) {
    # Email senden bei Fehler
    $EmailParams = @{
        To = "deine.email@example.com"
        From = "cwvdb@localhost"
        Subject = "cwVDB Update Failed"
        Body = "Incremental update failed. Check logs."
        SmtpServer = "smtp.example.com"
    }
    Send-MailMessage @EmailParams
}
```

---

## Best Practices

1. **Timing:** Wähle eine Zeit, wenn der PC läuft aber nicht genutzt wird (z.B. 6:00 Uhr morgens)

2. **Logging:** Behalte Logs mindestens 30 Tage:
   ```powershell
   # Alte Logs löschen (älter als 30 Tage)
   Get-ChildItem logs\incremental_update_*.log | 
       Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
       Remove-Item
   ```

3. **Backup:** Sichere `vectordb/` Ordner wöchentlich

4. **Monitoring:** Prüfe einmal pro Woche die Logs

---

## Alternative: Cron-ähnliche Syntax mit schtasks

```cmd
schtasks /create /tn "cwVDB Incremental Update" /tr "PowerShell.exe -ExecutionPolicy Bypass -File C:\Github\cwVDB\run_incremental_update.ps1" /sc daily /st 06:00 /rl highest
```

---

## Zusammenfassung

Nach erfolgreicher Einrichtung:
- ✅ Task läuft täglich um 6:00 Uhr
- ✅ Inkrementelle Updates dauern 5-15 Minuten
- ✅ Logs werden in `logs/` gespeichert
- ✅ Vektordatenbank bleibt aktuell

Bei Fragen: `logs\incremental_update_*.log` prüfen!
