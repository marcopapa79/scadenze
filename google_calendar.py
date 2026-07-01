"""
Modulo per esportare scadenze su Google Calendar
"""
from datetime import datetime, timedelta
import os.path
import pickle

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_DISPONIBILE = True
except ImportError:
    GOOGLE_DISPONIBILE = False

# Scope per creare eventi su Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

# File per salvare le credenziali
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'


def autentica_google_calendar():
    """
    Autentica l'utente con Google Calendar
    Restituisce il servizio Google Calendar autenticato
    """
    creds = None
    
    # Carica token salvato se esiste
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Se non ci sono credenziali valide, richiedi l'autenticazione
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"File {CREDENTIALS_FILE} non trovato!\n\n"
                    "Per usare Google Calendar:\n"
                    "1. Vai su https://console.cloud.google.com\n"
                    "2. Crea un progetto\n"
                    "3. Abilita Google Calendar API\n"
                    "4. Crea credenziali OAuth 2.0\n"
                    "5. Scarica il file credentials.json in questa cartella"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva il token per la prossima volta
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)


def trova_calendario_per_nome(service, nome_calendario):
    """
    Cerca un calendario per nome e restituisce il suo ID.
    Se non trovato, restituisce 'primary'.
    """
    try:
        calendari = service.calendarList().list().execute()
        for cal in calendari.get('items', []):
            if cal.get('summary', '').strip().lower() == nome_calendario.strip().lower():
                return cal['id']
    except Exception:
        pass
    return 'primary'


def crea_evento_scadenza(service, nome_scadenza, data_scadenza, descrizione="", calendario_id='primary', ora_inizio=None, ora_fine=None):
    """
    Crea un evento su Google Calendar per una scadenza
    
    Args:
        service: Servizio Google Calendar autenticato
        nome_scadenza: Nome della scadenza (può includere emoji e tipo)
        data_scadenza: Data in formato YYYY-MM-DD
        descrizione: Descrizione aggiuntiva (opzionale)
        calendario_id: ID del calendario (default: 'primary')
        ora_inizio: Ora inizio in formato HH:MM (opzionale)
        ora_fine: Ora fine in formato HH:MM (opzionale)
    
    Returns:
        Link all'evento creato
    """
    try:
        # Converti la data in formato Google Calendar
        evento = {
            'summary': nome_scadenza,
            'description': descrizione,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},           # 10 minuti prima
                    {'method': 'popup', 'minutes': 24 * 60},      # 1 giorno prima
                    {'method': 'popup', 'minutes': 24 * 60 * 3},  # 3 giorni prima
                ],
            },
            # Nessun colorId: usa il colore del calendario
        }
        
        # Se ci sono orari, crea un evento con orario specifico
        if ora_inizio:
            # Evento con orario
            data_ora_inizio = f"{data_scadenza}T{ora_inizio}:00"
            data_ora_fine = f"{data_scadenza}T{ora_fine or '23:59'}:00" if ora_fine else f"{data_scadenza}T{ora_inizio.split(':')[0]}:59:59"
            evento['start'] = {
                'dateTime': data_ora_inizio,
                'timeZone': 'Europe/Rome',
            }
            evento['end'] = {
                'dateTime': data_ora_fine,
                'timeZone': 'Europe/Rome',
            }
        else:
            # Evento tutto il giorno
            evento['start'] = {
                'date': data_scadenza,  # Evento tutto il giorno
                'timeZone': 'Europe/Rome',
            }
            evento['end'] = {
                'date': data_scadenza,
                'timeZone': 'Europe/Rome',
            }
        
        evento_creato = service.events().insert(calendarId=calendario_id, body=evento).execute()
        return evento_creato.get('htmlLink')
    
    except HttpError as error:
        print(f'Errore durante la creazione dell\'evento: {error}')
        return None


def esporta_singola_scadenza(nome_scadenza, data_scadenza, tipo_scadenza="Scadenza", veicolo="", ora_inizio=None, ora_fine=None):
    """
    Esporta una singola scadenza su Google Calendar
    
    Args:
        nome_scadenza: Nome della scadenza
        data_scadenza: Data in formato YYYY-MM-DD
        tipo_scadenza: Tipo (es. "Scadenza", "Visita", "Veicolo")
        veicolo: Nome del veicolo (opzionale)
        ora_inizio: Ora inizio in formato HH:MM (opzionale)
        ora_fine: Ora fine in formato HH:MM (opzionale)
    
    Returns:
        (bool successo, str messaggio)
    """
    if not GOOGLE_DISPONIBILE:
        return False, "Librerie Google non installate"
    
    try:
        service = autentica_google_calendar()
        
        # Trova il calendario "Famiglia"
        cal_id = trova_calendario_per_nome(service, 'Famiglia')
        
        # Costruisci descrizione
        descrizione = f"Tipo: {tipo_scadenza}"
        if veicolo:
            descrizione = f"Veicolo: {veicolo}\n{descrizione}"
        
        # Costruisci titolo evento con prefisso emoji e tipo appropriati
        if tipo_scadenza == "Visita":
            titolo = f"🏥 Visita: {nome_scadenza}"
        elif veicolo:
            titolo = f"⚠️ {nome_scadenza}"
        else:
            titolo = f"⚠️ Scadenza: {nome_scadenza}"
        
        link = crea_evento_scadenza(service, titolo, data_scadenza, descrizione, cal_id, ora_inizio, ora_fine)
        
        if link:
            return True, f"✅ '{nome_scadenza}' esportata su Google Calendar!"
        else:
            return False, "Errore durante la creazione dell'evento"
            
    except Exception as e:
        return False, f"Errore: {str(e)}"


def esporta_scadenze_veicolo(dati_veicolo, nome_veicolo):
    """
    Esporta tutte le scadenze di un veicolo su Google Calendar
    """
    if not GOOGLE_DISPONIBILE:
        return False, "Librerie Google non installate"
    
    try:
        service = autentica_google_calendar()
        cal_id = trova_calendario_per_nome(service, 'Famiglia')
        eventi_creati = []
        
        # Esporta scadenze temporali
        for nome_scadenza, data in dati_veicolo.get("scadenze_fisse", {}).items():
            descrizione = f"Veicolo: {nome_veicolo}\nTipo: Scadenza temporale\nComponente: {nome_scadenza}"
            link = crea_evento_scadenza(
                service, 
                f"{nome_veicolo} - {nome_scadenza}",
                data,
                descrizione,
                cal_id
            )
            if link:
                eventi_creati.append(nome_scadenza)
        
        # Esporta scadenze chilometriche (calcola data stimata)
        km_attuali = dati_veicolo.get("km_attuali", 0)
        km_medi_al_giorno = 50  # Stima: 50 km/giorno
        
        for nome_scadenza, info in dati_veicolo.get("scadenze_chilometriche", {}).items():
            km_mancanti = info["prossimo_km"] - km_attuali
            if km_mancanti > 0:
                giorni_stimati = int(km_mancanti / km_medi_al_giorno)
                data_stimata = (datetime.now() + timedelta(days=giorni_stimati)).strftime("%Y-%m-%d")
                
                descrizione = (
                    f"Veicolo: {nome_veicolo}\n"
                    f"Tipo: Scadenza chilometrica\n"
                    f"Componente: {nome_scadenza}\n"
                    f"Km attuali: {km_attuali}\n"
                    f"Prossimo tagliando: {info['prossimo_km']} km\n"
                    f"Km mancanti: {km_mancanti}\n"
                    f"⚠️ Data stimata (basata su 50 km/giorno)"
                )
                
                link = crea_evento_scadenza(
                    service,
                    f"{nome_veicolo} - {nome_scadenza} ({info['prossimo_km']} km)",
                    data_stimata,
                    descrizione,
                    cal_id
                )
                if link:
                    eventi_creati.append(f"{nome_scadenza} (stima)")
        
        return True, eventi_creati
    
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Errore: {str(e)}"


def esporta_scadenze_personali(scadenze_personali):
    """
    Esporta tutte le scadenze personali su Google Calendar
    """
    if not GOOGLE_DISPONIBILE:
        return False, "Librerie Google non installate"
    
    try:
        service = autentica_google_calendar()
        cal_id = trova_calendario_per_nome(service, 'Famiglia')
        eventi_creati = []
        
        for nome_scadenza, data in scadenze_personali.items():
            descrizione = f"Tipo: Scadenza personale\nCategoria: {nome_scadenza}"
            link = crea_evento_scadenza(
                service,
                nome_scadenza,
                data,
                descrizione,
                cal_id
            )
            if link:
                eventi_creati.append(nome_scadenza)
        
        return True, eventi_creati
    
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Errore: {str(e)}"


def esporta_tutto_su_calendar(dati_completi):
    """
    Esporta tutte le scadenze (veicoli + personali) su Google Calendar
    """
    if not GOOGLE_DISPONIBILE:
        return False, "Librerie Google non installate. Installa: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    
    risultati = {
        "veicoli": {},
        "personali": []
    }
    
    # Esporta veicoli
    for nome_veicolo, dati in dati_completi.get("veicoli", {}).items():
        successo, eventi = esporta_scadenze_veicolo(dati, nome_veicolo)
        if successo:
            risultati["veicoli"][nome_veicolo] = eventi
    
    # Esporta scadenze personali
    successo, eventi = esporta_scadenze_personali(dati_completi.get("scadenze_personali", {}))
    if successo:
        risultati["personali"] = eventi
    
    return True, risultati


if __name__ == "__main__":
    print("Modulo Google Calendar - Esportazione Scadenze")
    print("=" * 50)
    
    if GOOGLE_DISPONIBILE:
        print("✅ Librerie Google disponibili")
    else:
        print("❌ Librerie Google non installate")
        print("\nPer installare:")
        print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
