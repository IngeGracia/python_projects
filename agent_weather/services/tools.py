import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class Tools:
    def __init__(self):
        self.SCOPES = ["https://www.googleapis.com/auth/calendar"]
        self.CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "app_credentials.json")
        self.TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "token.json")

    def get_calendar_service(self):
        creds = None

        #Revisar si existe el token y cargarlo
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)

        #No hay credenciales validas, hacer proceso de autorizacion o refrescar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    raise FileNotFoundError(f"No se encontró el archivo de credenciales!")
                flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)

            #Guardar el token generado
            with open(self.TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        #Regresar el servicio ya hecho
        return build("calendar", "v3", credentials=creds)

    def check_availability(self, time_ini:str, time_end:str):
        # print(f"Llamando herramienta check_availability con ({time_ini}, {time_end})")
        body = {
            "timeMin": time_ini,
            "timeMax": time_end,
            "items": [
                {"id": "f56a303b702603a7338aed7bd58c456f6051eaab8d1e8bca7ebd0b38aba6791e@group.calendar.google.com"}
            ]
        }
        service = self.get_calendar_service()
        result = service.freebusy().query(body=body).execute()

        busy = result.get("calendars", {}).get("f56a303b702603a7338aed7bd58c456f6051eaab8d1e8bca7ebd0b38aba6791e@group.calendar.google.com", {}).get("busy", [])
        return {
            "id_calendar": "f56a303b702603a7338aed7bd58c456f6051eaab8d1e8bca7ebd0b38aba6791e@group.calendar.google.com",
            "time_ini": time_ini,
            "time_end": time_end,
            "busy": busy,
            "is_free": (len(busy)==0)
        }
        
    def create_event(self, summary:str, start:str, end:str, description:str=""):
        # print(f"Llamando herramienta create_event con ({summary}, {start}, {end}, {description})")
        body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start,
                "timeZone": "America/Hermosillo"
            },
            "end": {
                "dateTime": end,
                "timeZone": "America/Hermosillo"
            }
        }
        service = self.get_calendar_service()
        result = service.events().insert(
            calendarId="f56a303b702603a7338aed7bd58c456f6051eaab8d1e8bca7ebd0b38aba6791e@group.calendar.google.com", 
            body=body
        ).execute()

        return {
            "id_calendar": "f56a303b702603a7338aed7bd58c456f6051eaab8d1e8bca7ebd0b38aba6791e@group.calendar.google.com",
            "id_event": result["id"],
            "summary": summary,
            "start": start,
            "end": end,
            "description": description
        }


if __name__ == "__main__":
    tools = Tools()
    time_ini = "2026-04-14T15:00:00-07:00"
    time_end = "2026-04-14T15:30:00-07:00"
    print(tools.check_availability(time_ini, time_end))
