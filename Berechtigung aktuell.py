import PySimpleGUI as sg
import subprocess
import os
import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import threading

# Funktion zur Überprüfung von Benutzername und Passwort
def authenticate_user(email, password):
    # Hier könntest du eine Datenbankabfrage oder einen anderen Authentifizierungsmechanismus einfügen
    # Zum Beispiel: Benutzername: "admin@example.com", Passwort: "admin123"
    if email == "testmailadress1@web.de" and password == "admin123":
        return True
    else:
        return False

# Layout des Login-Fensters
login_layout = [
    [sg.Text("Bitte einloggen", font=("Helvetica", 16))],
    [sg.Text("E-Mail-Adresse:", size=(15, 1)), sg.InputText(key="Email", size=(30, 1))],
    [sg.Text("Passwort:", size=(15, 1)), sg.InputText(key="Password", password_char="*", size=(30, 1))],
    [sg.Button("Einloggen"), sg.Button("Abbrechen")]
]

# Login-Fenster erstellen
login_window = sg.Window("Login", login_layout)

# Login-Schleife
while True:
    login_event, login_values = login_window.read()
    if login_event == sg.WIN_CLOSED or login_event == "Abbrechen":
        login_window.close()
        exit()

    if login_event == "Einloggen":
        email = login_values["Email"]
        password = login_values["Password"]

        if authenticate_user(email, password):
            sg.popup("Erfolg", "Login erfolgreich")
            login_window.close()
            break
        else:
            sg.popup_error("Fehler", "Ungültige E-Mail-Adresse oder Passwort")

# Funktion zum Versenden von E-Mails
def send_email(receiver_email, folder_path, access_right):
    sender_email = "testmailadress1@web.de"  # Absender-E-Mail-Adresse
    sender_password = "Testmail123##"         # Passwort für den E-Mail-Dienst
    smtp_server = "smtp.web.de"          # SMTP-Server des E-Mail-Dienstes
    smtp_port = 587                           # Port für den SMTP-Server (meistens 587)

    subject = "Neue Berechtigung erhalten"
    body = f"""
Hallo {receiver_email},

Sie haben eine neue Berechtigung erhalten.

Details:
- Ordnerpfad: {folder_path}
- Berechtigung: {access_right}

Vielen Dank,
Ihr Team
"""

    try:
        # E-Mail-Objekt erstellen
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        # Nachrichtentext hinzufügen
        msg.attach(MIMEText(body, "plain"))

        # Verbindung zum SMTP-Server herstellen und E-Mail senden
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Verschlüsselte Verbindung starten
            server.login(sender_email, sender_password)
            server.send_message(msg)

        sg.popup("E-Mail-Benachrichtigung", f"E-Mail wurde erfolgreich an {receiver_email} gesendet.")
    except Exception as e:
        sg.popup_error("E-Mail-Fehler", f"Fehler beim Senden der E-Mail: {e}")

# Funktion zum Entfernen der Berechtigung nach Ablauf der Dauer
def remove_permission(folder_path, user_name):
    powershell_script = f"""
$acl = Get-Acl -Path "{folder_path}"
$accessRules = $acl.Access | Where-Object {{ $_.IdentityReference -eq "{user_name}" }}
foreach ($rule in $accessRules) {{
    $acl.RemoveAccessRule($rule)
}}
Set-Acl -Path "{folder_path}" -AclObject $acl
Write-Output "Berechtigungen für Benutzer '{user_name}' entfernt."
"""
    try:
        subprocess.run(["powershell", "-Command", powershell_script], capture_output=True, text=True, shell=True)
        sg.popup("Berechtigungen entfernt", f"Die Berechtigungen für {user_name} wurden nach 10 Tagen entfernt.")
    except Exception as e:
        sg.popup_error("Fehler", f"Fehler beim Entfernen der Berechtigungen: {e}")

# Funktion zum Ausführen des PowerShell-Skripts
def create_share(folder_path, user_name, access_right, temporary):
    share_name = os.path.basename(folder_path)

    powershell_script = f"""
if (-Not (Test-Path -Path "{folder_path}")) {{
    New-Item -ItemType Directory -Path "{folder_path}"
    Write-Output "Ordner '{folder_path}' erstellt."
}}

New-SmbShare -Name "{share_name}" -Path "{folder_path}" -FullAccess "{user_name}"

Write-Output "Freigabe '{share_name}' für Ordner '{folder_path}' erstellt und Benutzer '{user_name}' mit '{access_right}' Zugriff hinzugefügt."

$acl = Get-Acl -Path "{folder_path}"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("{user_name}", "{access_right}", "ContainerInherit, ObjectInherit", "None", "Allow")
$acl.SetAccessRule($accessRule)
Set-Acl -Path "{folder_path}" -AclObject $acl

Write-Output "NTFS-Berechtigungen für Benutzer '{user_name}' auf Ordner '{folder_path}' gesetzt."
"""

    try:
        result = subprocess.run(["powershell", "-Command", powershell_script], capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            sg.popup_error("Fehler", f"Fehler beim Ausführen des PowerShell-Skripts:\n{result.stderr}")
        else:
            sg.popup("Erfolg", "Freigabe wurde erfolgreich erstellt")
            save_to_database(folder_path, user_name, access_right, temporary)
            send_email(user_name, folder_path, access_right)

            if temporary:
                expiration_date = datetime.now() + timedelta(days=10)
                threading.Timer(10 * 24 * 60 * 60, remove_permission, args=(folder_path, user_name)).start()
                sg.popup("Hinweis", f"Die Berechtigung wird automatisch am {expiration_date.strftime('%d.%m.%Y %H:%M:%S')} entfernt.")
    except subprocess.CalledProcessError as e:
        sg.popup_error("Fehler", f"Fehler beim Ausführen des PowerShell-Skripts: {e}")

# Funktion zum Speichern der Daten in der MySQL-Datenbank
def save_to_database(folder_path, user_name, access_right, temporary):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='benutzerverwaltung2',
            user='root',
            password='root123',
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            cursor = connection.cursor()

            # Mapping der Berechtigungen zu Rollen
            role_map = {
                "FullControl": "Administrator",
                "Change": "Superadviser",
                "Read": "Standard"
            }
            role = role_map.get(access_right, "Unbekannt")

            # Dauer setzen
            duration = "10 Tage" if temporary else "Permanent"

            # Einträge in die Tabellen einfügen
            cursor.execute("""
                INSERT INTO dauer (Dauer)
                VALUES (%s)
                ON DUPLICATE KEY UPDATE Dauer=Dauer
            """, (duration,))

            cursor.execute("""
                INSERT INTO rolle (Rolle)
                VALUES (%s)
                ON DUPLICATE KEY UPDATE Rolle=Rolle
            """, (role,))

            cursor.execute("""
                INSERT INTO verzeichnis (Verzeichnis, User, Berechtigung, Rolle, Dauer)
                VALUES (%s, %s, %s, %s, %s)
            """, (folder_path, user_name, access_right, role, duration))

            connection.commit()
            sg.popup("Datenbank", "Daten erfolgreich gespeichert")
    except Error as e:
        sg.popup_error("Datenbankfehler", f"Fehler beim Speichern in der Datenbank: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Layout der GUI
layout = [
    [sg.Text("Ordnerpfad:"), sg.InputText(key="FolderPath", size=(50, 1))],
    [sg.Text("Benutzername (E-Mail):"), sg.InputText(key="UserName", size=(50, 1))],
    [sg.Text("Zugriffsrechte:")],
    [sg.Checkbox("vollzugriff", key="FullControl"), sg.Checkbox("ändern", key="Change"), sg.Checkbox("lesen", key="Read")],
    [sg.Checkbox("Berechtigung für 10 Tage begrenzen", key="Temporary")],
    [sg.Button("Freigabe erstellen"), sg.Button("Abbrechen")]
]

# Fenster erstellen
window = sg.Window("Freigabe erstellen", layout)

# Schleife für die GUI
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Abbrechen":
        break
    if event == "Freigabe erstellen":
        folder_path = values["FolderPath"]
        user_name = values["UserName"]

        access_rights = []
        if values["FullControl"]:
            access_rights.append("FullControl")
        if values["Change"]:
            access_rights.append("Change")
        if values["Read"]:
            access_rights.append("Read")

        access_right = ','.join(access_rights)
        temporary = values["Temporary"]

        if not folder_path or not user_name or not access_right:
            sg.popup_warning("Eingabefehler", "Ordnerpfad, Benutzername und mindestens ein Zugriffsrecht müssen ausgefüllt werden")
        else:
            create_share(folder_path, user_name, access_right, temporary)

# Fenster schließen
window.close()

