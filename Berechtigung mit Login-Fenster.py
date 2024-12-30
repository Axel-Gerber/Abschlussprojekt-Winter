import PySimpleGUI as sg

# Funktion zur Überprüfung von Benutzername und Passwort
def authenticate_user(email, password):
    # Hier könntest du eine Datenbankabfrage oder einen anderen Authentifizierungsmechanismus einfügen
    # Zum Beispiel: Benutzername: "admin@example.com", Passwort: "admin123"
    if email == "admin@example.com" and password == "admin123":
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

# Haupt-GUI (hier wird die ursprüngliche GUI angezeigt)
layout = [
    [sg.Text("Ordnerpfad:"), sg.InputText(key="FolderPath", size=(50, 1))],
    [sg.Text("Benutzername:"), sg.InputText(key="UserName", size=(50, 1))],
    [sg.Text("Zugriffsrechte:")],
    [sg.Checkbox("vollzugriff", key="FullControl"), sg.Checkbox("ändern", key="Change"), sg.Checkbox("lesen", key="Read")],
    [sg.Button("Freigabe erstellen"), sg.Button("Abbrechen")]
]

window = sg.Window("Freigabe erstellen", layout)

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

        if not folder_path or not user_name or not access_right:
            sg.popup_warning("Eingabefehler", "Ordnerpfad, Benutzername und mindestens ein Zugriffsrecht müssen ausgefüllt werden")
        else:
            create_share(folder_path, user_name, access_right)

window.close()
