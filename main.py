import calendar
import glob
import json
import os
import re
import shutil
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont
from ricorrenze import prossima_occorrenza, occorrenze_nel_periodo

try:
    import notifiche
    NOTIFICHE_DISPONIBILI = True
except ImportError:
    NOTIFICHE_DISPONIBILI = False
    print("Modulo notifiche non disponibile. Installa plyer: pip install plyer")

try:
    import google_calendar
    GOOGLE_CALENDAR_DISPONIBILE = google_calendar.GOOGLE_DISPONIBILE
except ImportError:
    GOOGLE_CALENDAR_DISPONIBILE = False
    print("Modulo google_calendar non disponibile")

try:
    import immagine_settimana
    IMMAGINE_DISPONIBILE = True
except ImportError:
    IMMAGINE_DISPONIBILE = False
    print("Modulo immagine non disponibile. Installa Pillow: pip install Pillow")

# Configurazione soglie di avviso
SOGLIA_KM_PREAVVISO = 3500
SOGLIA_GIORNI_PREAVVISO = 30

# Tutti i file stanno nella cartella del programma, da qualunque cartella lo si avvii
CARTELLA_PROGRAMMA = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(CARTELLA_PROGRAMMA, "stato_veicolo.json")
# Copie di sicurezza giornaliere del file dati (una al giorno, tenute per GIORNI_BACKUP giorni)
CARTELLA_BACKUP = os.path.join(CARTELLA_PROGRAMMA, "backup")
GIORNI_BACKUP = 30

# Colore di sfondo delle finestre (versione classica). Prima era "#f0f0f0" (grigio chiaro).
# Esempi: "#dcdfe3" grigio un po' più scuro, "#cfd8dc" grigio-azzurro, "#b0bec5" grigio-azzurro scuro
COLORE_SFONDO = "#f0f0f0"

# Velocità di scorrimento della scheda Scadenze Personali
SCROLL_PIXEL_PER_UNITA = 20   # pixel per unità di scroll
SCROLL_UNITA_PER_SCATTO = 3   # unità per ogni scatto della rotellina (3 x 20 = 60 px)

# Riepilogo da copiare (pulsante "Copia settimana"): quanti giorni a partire da oggi
GIORNI_RIEPILOGO = 7
NOMI_GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# Sezioni dell'immagine "Copia immagine": (chiave, titolo, colore), nell'ordine mostrato
SEZIONI_RIEPILOGO = [
    ("visite", "Visite Mediche prenotate", "#009688"),
    ("da_prenotare", "Visite da prenotare entro il", "#FF9800"),
    ("scadenze", "Scadenze (Casa, ISEE, IMU, Documenti, Altro)", "#2196F3"),
    ("feste", "Feste e Compleanni", "#E91E63"),
    ("veicoli", "Veicoli", "#F44336"),
]
FILE_IMMAGINE_RIEPILOGO = os.path.join(CARTELLA_PROGRAMMA, "riepilogo_settimana.png")
# Vista proposta all'apertura di "Copia immagine": "calendario" oppure "elenco"
VISTA_IMMAGINE_PREDEFINITA = "calendario"
# Nomi brevi delle sezioni per la legenda del calendario
LEGENDA_BREVE = {
    "visite": "Visite",
    "da_prenotare": "Visite da prenotare",
    "scadenze": "Scadenze",
    "feste": "Feste e compleanni",
    "veicoli": "Veicoli",
}

# Giorni della settimana: (etichetta italiana, codice BYDAY per Google Calendar)
GIORNI_SETTIMANA = [
    ("Lun", "MO"), ("Mar", "TU"), ("Mer", "WE"), ("Gio", "TH"),
    ("Ven", "FR"), ("Sab", "SA"), ("Dom", "SU"),
]


def inizializza_db():
    default_data = {
        "veicoli": {
            "Corolla (GD028MR)": {
                "nome_veicolo": "Corolla",
                "targa": "GD028MR",
                "km_attuali": 88375,
                "scadenze_fisse": {
                    "Bollo": "2026-08-31",
                    "Assicurazione": "2026-11-27",
                    "Revisione": "2027-12-31",
                },
                "scadenze_chilometriche": {
                    "Tagliando": {"ultimo_km": 0, "prossimo_km": 91400},
                    "Freni": {"ultimo_km": 0, "prossimo_km": 120000},
                    "Gomme Anteriori": {"ultimo_km": 71071, "prossimo_km": 110000},
                },
            }
        },
        "veicolo_selezionato": "Corolla (GD028MR)",
        "scadenze_personali": {
            "ISEE": "2027-01-15",
            "IMU Casa": "2026-12-16",
            "Canone RAI": "2027-01-31"
        }
    }
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)


def carica_dati():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _backup_giornaliero():
    """Prima del primo salvataggio del giorno copia il file dati in backup/ (tiene gli ultimi GIORNI_BACKUP)."""
    if not os.path.exists(DB_FILE):
        return
    try:
        os.makedirs(CARTELLA_BACKUP, exist_ok=True)
        copia = os.path.join(CARTELLA_BACKUP, f"stato_veicolo_{date.today():%Y-%m-%d}.json")
        if not os.path.exists(copia):
            shutil.copy2(DB_FILE, copia)
            vecchie = sorted(glob.glob(os.path.join(CARTELLA_BACKUP, "stato_veicolo_*.json")))
            for file_vecchio in vecchie[:-GIORNI_BACKUP]:
                os.remove(file_vecchio)
    except OSError as e:
        print(f"Copia di sicurezza non riuscita: {e}")


def salva_dati(dati):
    """Salva in modo sicuro: scrive prima un file temporaneo e poi lo sostituisce all'originale.

    Se il PC si spegne o l'app si blocca a metà, stato_veicolo.json resta quello di prima
    invece di rimanere vuoto o rovinato.
    """
    _backup_giornaliero()
    temporaneo = DB_FILE + ".tmp"
    with open(temporaneo, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporaneo, DB_FILE)


def data_iso_a_italiana(data_iso):
    """Converte data da formato ISO (YYYY-MM-DD) a formato italiano (DD-MM-YYYY)"""
    try:
        if not data_iso or data_iso == "HH:MM":
            return data_iso
        data_obj = datetime.strptime(data_iso, "%Y-%m-%d")
        return data_obj.strftime("%d-%m-%Y")
    except:
        return data_iso


def data_italiana_a_iso(data_ita):
    """Converte data da formato italiano (DD-MM-YYYY) a formato ISO (YYYY-MM-DD)"""
    try:
        if not data_ita or data_ita == "HH:MM":
            return data_ita
        data_obj = datetime.strptime(data_ita, "%d-%m-%Y")
        return data_obj.strftime("%Y-%m-%d")
    except:
        return data_ita


def interpreta_data(testo, riferimento):
    """Interpreta una data scritta a mano: GG/MM/AAAA, GG/MM/AA oppure GG/MM.

    Accetta anche '-' e '.' come separatori. Senza anno sceglie l'anno che rende
    la data più vicina a `riferimento` (es. a ottobre "5/1" = 5 gennaio dell'anno dopo).
    Restituisce un oggetto date oppure None se la data non è valida.
    """
    parti = testo.strip().replace("-", "/").replace(".", "/").split("/")
    if len(parti) not in (2, 3) or not all(p.isdigit() for p in parti):
        return None
    giorno, mese = int(parti[0]), int(parti[1])
    if len(parti) == 3:
        anno = int(parti[2])
        if len(parti[2]) <= 2:
            anno += 2000
        try:
            return date(anno, mese, giorno)
        except ValueError:
            return None
    candidati = []
    for anno in range(riferimento.year - 4, riferimento.year + 5):  # +-4 anni: copre anche il 29/02
        try:
            candidati.append(date(anno, mese, giorno))
        except ValueError:
            pass
    return min(candidati, key=lambda d: abs((d - riferimento).days)) if candidati else None


def interpreta_scadenza_medicinale(testo):
    """Data di scadenza di un medicinale: GG-MM-AAAA oppure solo MM-AAAA / MM-AA come sulle confezioni.

    Con solo mese e anno la scadenza è l'ultimo giorno del mese.
    Restituisce (date, solo_mese) oppure (None, False) se non valida.
    """
    parti = testo.strip().replace("-", "/").replace(".", "/").split("/")
    if len(parti) == 2 and all(p.isdigit() for p in parti) and len(parti[1]) in (2, 4):
        mese, anno = int(parti[0]), int(parti[1])
        if len(parti[1]) == 2:
            anno += 2000
        if 1 <= mese <= 12:
            ultimo_giorno = calendar.monthrange(anno, mese)[1]
            return date(anno, mese, ultimo_giorno), True
        return None, False
    if len(parti) == 3:
        giorno = interpreta_data(testo, date.today())
        return (giorno, False) if giorno else (None, False)
    return None, False


def interpreta_durata(testo):
    """Durata dopo l'apertura: '28', '28 giorni', '28gg', '6 mesi', '6m', '1 anno', '4 settimane'.

    Restituisce (numero, "giorni" | "mesi") oppure None se non valida. Anni e settimane
    vengono convertiti in mesi e giorni.
    """
    t = testo.strip().lower().rstrip(".")
    m = re.fullmatch(r"(\d+)\s*([a-zà]*)", t)
    if not m or int(m.group(1)) <= 0:
        return None
    n, unita = int(m.group(1)), m.group(2)
    if unita in ("", "g", "gg", "giorno", "giorni"):
        return n, "giorni"
    if unita in ("s", "sett", "settimana", "settimane"):
        return n * 7, "giorni"
    if unita in ("m", "mese", "mesi"):
        return n, "mesi"
    if unita in ("a", "anno", "anni"):
        return n * 12, "mesi"
    return None


def n_giorni(n):
    """'1 giorno' / 'N giorni'."""
    return "1 giorno" if n == 1 else f"{n} giorni"


def testo_durata(n, unita):
    if unita == "mesi":
        return "1 mese" if n == 1 else f"{n} mesi"
    return "1 giorno" if n == 1 else f"{n} giorni"


def fine_dopo_apertura(apertura, n, unita):
    """Ultimo giorno di uso dopo l'apertura (a fine mese se il giorno non esiste, es. 31/01 + 1 mese = 28/02)."""
    if unita == "giorni":
        return apertura + timedelta(days=n)
    mese_totale = apertura.month - 1 + n
    anno, mese = apertura.year + mese_totale // 12, mese_totale % 12 + 1
    return date(anno, mese, min(apertura.day, calendar.monthrange(anno, mese)[1]))


class ScadenzeApp:
    def __init__(self, root):
        self.root = root
        self._prepara_finestra()

        self.dati_completi = carica_dati()
        
        # Migrazione vecchio formato se necessario
        if "veicoli" not in self.dati_completi:
            self.migra_vecchio_formato()
        
        # Aggiungi scadenze_personali se non esistono
        if "scadenze_personali" not in self.dati_completi:
            self.dati_completi["scadenze_personali"] = {}
            salva_dati(self.dati_completi)

        # Elenco dei medicinali (scheda 💊 Medicinali): nessuna notifica, solo promemoria
        self.dati_completi.setdefault("medicinali", [])
        
        self.veicolo_corrente = self.dati_completi.get("veicolo_selezionato", list(self.dati_completi["veicoli"].keys())[0])
        
        self.crea_interfaccia()
        self.aggiorna_visualizzazione()
    
    def _prepara_finestra(self):
        """Titolo, dimensioni, colori e caratteri della finestra principale."""
        self.root.title("Gestione Scadenze - Veicoli e Personali")
        self.root.geometry("1300x800")  # dimensione quando si "ripristina" la finestra
        # Apre la finestra ingrandita (come il pulsante quadrato di Windows).
        # Va fatto dopo che la finestra è comparsa, altrimenti Windows lo ignora.
        self.root.after(50, self._ingrandisci_finestra)
        self.root.configure(bg=COLORE_SFONDO)
        stile = ttk.Style(self.root)
        stile.configure("TNotebook", background=COLORE_SFONDO)

        self.title_font = tkfont.Font(family="Helvetica", size=14, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=10)

    # Piccoli aiuti per aggiornare i widget: la versione moderna (main_moderno.py)
    # li ridefinisce, perché i suoi widget usano nomi di opzioni diversi.
    def _imposta_stato(self, etichetta, testo, colore):
        # Toni un po' più scuri dei colori base, leggibili anche su sfondi non bianchi
        colori = {"red": "#C62828", "orange": "#E65100", "green": "#2E7D32", "gray": "#616161"}
        etichetta.config(text=testo, fg=colori.get(colore, colore))

    def _abilita_campo(self, campo, abilitato):
        campo.config(state=tk.NORMAL if abilitato else tk.DISABLED)

    def _ingrandisci_finestra(self):
        """Porta la finestra a schermo intero (ingrandita), mantenendo la barra di Windows."""
        try:
            self.root.state("zoomed")          # Windows
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                pass  # se non supportato resta 1300x800

    def migra_vecchio_formato(self):
        """Converte il vecchio formato dati al nuovo formato multi-veicolo"""
        nome = self.dati_completi.get("nome_veicolo", "Veicolo")
        targa = self.dati_completi.get("targa", "XX000XX")
        chiave = f"{nome} ({targa})"
        
        self.dati_completi = {
            "veicoli": {
                chiave: {
                    "nome_veicolo": nome,
                    "targa": targa,
                    "km_attuali": self.dati_completi.get("km_attuali", 0),
                    "scadenze_fisse": self.dati_completi.get("scadenze_fisse", {}),
                    "scadenze_chilometriche": self.dati_completi.get("scadenze_chilometriche", {}),
                }
            },
            "veicolo_selezionato": chiave
        }
        salva_dati(self.dati_completi)
    
    def get_dati_veicolo(self):
        """Ottiene i dati del veicolo corrente"""
        return self.dati_completi["veicoli"][self.veicolo_corrente]
    
    def cambia_veicolo(self, event=None):
        """Cambia il veicolo selezionato"""
        self.veicolo_corrente = self.veicolo_combo.get()
        self.dati_completi["veicolo_selezionato"] = self.veicolo_corrente
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia(tab_da_aprire="veicoli")
    
    def aggiungi_veicolo(self):
        """Aggiunge un nuovo veicolo"""
        nome = simpledialog.askstring("Nuovo Veicolo", "Nome del veicolo:")
        if not nome:
            return
        
        targa = simpledialog.askstring("Nuovo Veicolo", "Targa del veicolo:")
        if not targa:
            return
        
        targa = targa.upper()
        chiave = f"{nome} ({targa})"
        
        if chiave in self.dati_completi["veicoli"]:
            messagebox.showerror("Errore", "Veicolo già esistente!")
            return
        
        self.dati_completi["veicoli"][chiave] = {
            "nome_veicolo": nome,
            "targa": targa,
            "km_attuali": 0,
            "scadenze_fisse": {},
            "scadenze_chilometriche": {},
        }
        
        self.veicolo_corrente = chiave
        self.dati_completi["veicolo_selezionato"] = chiave
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Veicolo '{nome}' aggiunto!")
    
    def rimuovi_veicolo(self):
        """Rimuove il veicolo corrente dopo conferma"""
        # Controlla che ci sia più di un veicolo
        if len(self.dati_completi["veicoli"]) <= 1:
            messagebox.showerror("Errore", "Non puoi eliminare l'ultimo veicolo!")
            return
        
        # Chiedi conferma
        dati = self.get_dati_veicolo()
        nome = dati["nome_veicolo"]
        targa = dati["targa"]
        
        conferma = messagebox.askyesno(
            "Conferma Eliminazione", 
            f"Vuoi veramente cancellare il veicolo '{nome} ({targa})'?\n\nQuesta operazione non può essere annullata!",
            icon='warning'
        )
        
        if not conferma:
            return
        
        # Rimuovi il veicolo
        del self.dati_completi["veicoli"][self.veicolo_corrente]
        
        # Seleziona il primo veicolo rimasto
        self.veicolo_corrente = list(self.dati_completi["veicoli"].keys())[0]
        self.dati_completi["veicolo_selezionato"] = self.veicolo_corrente
        
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia()
        
        messagebox.showinfo("Successo", f"Veicolo '{nome}' eliminato!")
    
    def controlla_scadenze_notifiche(self):
        """Controlla le scadenze e mostra notifiche desktop"""
        if not NOTIFICHE_DISPONIBILI:
            messagebox.showerror("Errore", "Modulo notifiche non disponibile.\nInstalla plyer: pip install plyer")
            return
        
        # Controlla tutti i veicoli
        riepilogo = notifiche.controlla_tutti_veicoli(self.dati_completi)
        
        if riepilogo:
            # Mostra riepilogo
            messaggio = "Notifiche inviate per:\n\n"
            for veicolo, avvisi in riepilogo.items():
                messaggio += f"🚗 {veicolo}:\n"
                for avviso in avvisi:
                    messaggio += f"  • {avviso}\n"
                messaggio += "\n"
            messagebox.showinfo("Controllo Scadenze", messaggio)
        else:
            messagebox.showinfo("Controllo Scadenze", "✅ Nessuna scadenza critica o in avvicinamento!")
    
    def esporta_veicolo_su_calendar(self):
        """Esporta le scadenze del veicolo corrente su Google Calendar"""
        if not GOOGLE_CALENDAR_DISPONIBILE:
            messagebox.showerror(
                "Errore", 
                "Modulo Google Calendar non disponibile.\n\n"
                "Per installare:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return
        
        dati = self.get_dati_veicolo()
        successo, risultato = google_calendar.esporta_scadenze_veicolo(dati, self.veicolo_corrente)
        
        if successo:
            messaggio = f"📅 Scadenze esportate su Google Calendar:\n\n"
            for evento in risultato:
                messaggio += f"  ✅ {evento}\n"
            messagebox.showinfo("Esportazione Completata", messaggio)
        else:
            messagebox.showerror("Errore Esportazione", risultato)
    
    def esporta_personali_su_calendar(self):
        """Esporta le scadenze personali su Google Calendar"""
        if not GOOGLE_CALENDAR_DISPONIBILE:
            messagebox.showerror(
                "Errore", 
                "Modulo Google Calendar non disponibile.\n\n"
                "Per installare:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return
        
        successo, risultato = google_calendar.esporta_scadenze_personali(
            self.dati_completi.get("scadenze_personali", {})
        )
        
        if successo:
            messaggio = f"📅 Scadenze personali esportate su Google Calendar:\n\n"
            for evento in risultato:
                messaggio += f"  ✅ {evento}\n"
            messagebox.showinfo("Esportazione Completata", messaggio)
        else:
            messagebox.showerror("Errore Esportazione", risultato)

    def _nome_personale_univoco(self, nome_base):
        """Genera un nome univoco per scadenze personali evitando sovrascritture."""
        nome = nome_base.strip() or "Senza titolo"
        if nome not in self.dati_completi["scadenze_personali"]:
            return nome

        idx = 2
        while True:
            candidato = f"{nome} ({idx})"
            if candidato not in self.dati_completi["scadenze_personali"]:
                return candidato
            idx += 1

    def _chiave_duplicato_personale(self, nome, data_obj):
        """Crea una chiave stabile per confrontare duplicati personali."""
        if isinstance(data_obj, str):
            data = data_obj
            ora_inizio = None
            con_orario = False
        else:
            data = data_obj.get("data")
            ora_inizio = data_obj.get("ora_inizio")
            con_orario = data_obj.get("con_orario", False)

        return (nome.strip().lower(), data, con_orario, ora_inizio)

    def importa_personali_da_calendar(self):
        """Importa eventi da Google Calendar in scadenze personali con filtro data/giorni."""
        if not GOOGLE_CALENDAR_DISPONIBILE:
            messagebox.showerror(
                "Errore", 
                "Modulo Google Calendar non disponibile.\n\n"
                "Per installare:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return

        oggi_ita = datetime.now().strftime("%d-%m-%Y")
        data_inizio_ita = simpledialog.askstring(
            "Importa da Google Calendar",
            "Data inizio ricerca (GG-MM-AAAA):",
            initialvalue=oggi_ita,
        )
        if not data_inizio_ita:
            return

        try:
            data_inizio_iso = data_italiana_a_iso(data_inizio_ita)
            datetime.strptime(data_inizio_iso, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Errore", "Data non valida! Usa il formato GG-MM-AAAA")
            return

        giorni = simpledialog.askinteger(
            "Importa da Google Calendar",
            "Numero giorni da cercare (es. 15):",
            initialvalue=15,
            minvalue=1,
            maxvalue=3650,
        )
        if giorni is None:
            return

        successo, risultato = google_calendar.leggi_eventi_calendar(
            data_inizio=data_inizio_iso,
            giorni=giorni,
            nome_calendario='Famiglia',
        )

        if not successo:
            messagebox.showerror("Errore Importazione", risultato)
            return

        eventi = risultato
        if not eventi:
            messagebox.showinfo(
                "Importazione",
                "Nessun evento trovato nel periodo selezionato.",
            )
            return

        esistenti = set(
            self._chiave_duplicato_personale(nome, data_obj)
            for nome, data_obj in self.dati_completi.get("scadenze_personali", {}).items()
        )

        importati = 0
        duplicati = 0
        saltati = 0

        for evento in eventi:
            nome_import = evento.get("nome_import", "Senza titolo")
            data_evento = evento.get("data")
            con_orario = evento.get("con_orario", False)
            ora_inizio = evento.get("ora_inizio") if con_orario else None
            ora_fine = evento.get("ora_fine") if con_orario else None

            chiave = (nome_import.strip().lower(), data_evento, con_orario, ora_inizio)
            if chiave in esistenti:
                duplicati += 1
                continue

            testo = (
                f"Titolo: {evento.get('titolo', nome_import)}\n"
                f"Data: {data_iso_a_italiana(data_evento)}"
            )
            if con_orario and ora_inizio:
                testo += f"\nOrario: {ora_inizio}"
                if ora_fine:
                    testo += f" - {ora_fine}"

            testo += "\n\nImportare questa voce nelle scadenze personali?"

            conferma = messagebox.askyesnocancel("Importazione Evento", testo)
            if conferma is None:
                break
            if not conferma:
                saltati += 1
                continue

            nome_finale = self._nome_personale_univoco(nome_import)
            tipo_import = evento.get("tipo_import")
            self.dati_completi["scadenze_personali"][nome_finale] = {
                "data": data_evento,
                "con_orario": con_orario,
                "ora_inizio": ora_inizio,
                "ora_fine": ora_fine,
                "categoria": "visita_prenotata" if tipo_import == "Visita" else "scadenza",
            }
            esistenti.add(chiave)
            importati += 1

        if importati > 0:
            salva_dati(self.dati_completi)
            self.ricarica_interfaccia()

        messagebox.showinfo(
            "Importazione completata",
            (
                f"Eventi trovati: {len(eventi)}\n"
                f"Importati: {importati}\n"
                f"Duplicati ignorati: {duplicati}\n"
                f"Saltati manualmente: {saltati}"
            ),
        )
    
    def esporta_singola_scad_temp(self, nome_scadenza):
        """Esporta una singola scadenza temporale del veicolo su Google Calendar"""
        if not GOOGLE_CALENDAR_DISPONIBILE:
            messagebox.showerror(
                "Errore", 
                "Modulo Google Calendar non disponibile.\n\n"
                "Per installare:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return
        
        dati = self.get_dati_veicolo()
        data_scadenza = dati["scadenze_fisse"][nome_scadenza]
        
        successo, risultato = google_calendar.esporta_singola_scadenza(
            nome_scadenza=nome_scadenza,
            data_scadenza=data_scadenza,
            tipo_scadenza="Scadenza temporale",
            veicolo=self.veicolo_corrente
        )
        
        if successo:
            messagebox.showinfo("Esportazione Completata", risultato)
        else:
            messagebox.showerror("Errore Esportazione", risultato)
    
    def esporta_singola_scad_personale(self, nome_scadenza):
        """Esporta una singola scadenza personale su Google Calendar"""
        if not GOOGLE_CALENDAR_DISPONIBILE:
            messagebox.showerror(
                "Errore", 
                "Modulo Google Calendar non disponibile.\n\n"
                "Per installare:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return
        
        data_obj = self.dati_completi["scadenze_personali"][nome_scadenza]
        # Gestisci sia il vecchio formato (stringa) che il nuovo (dict)
        if isinstance(data_obj, str):
            data_scadenza = data_obj
            orario_inizio = None
            orario_fine = None
            ricorrenza = None
        else:
            data_scadenza = data_obj.get('data', '')
            orario_inizio = data_obj.get('ora_inizio') if data_obj.get('con_orario') else None
            orario_fine = data_obj.get('ora_fine') if data_obj.get('con_orario') else None
            ricorrenza = data_obj.get('ricorrenza')
        
        # Determina il tipo e il nome dell'evento (stessa regola delle sezioni della scheda)
        if self._sezione_personale(nome_scadenza, data_obj) in ("visite", "da_prenotare"):
            tipo_scadenza = "Visita"
            # Rimuovi "Visita " dal nome per l'export (il prefisso viene aggiunto da esporta_singola_scadenza)
            nome_evento = nome_scadenza.replace("Visita ", "", 1)
        else:
            tipo_scadenza = "Scadenza"
            nome_evento = nome_scadenza
        
        successo, risultato = google_calendar.esporta_singola_scadenza(
            nome_scadenza=nome_evento,
            data_scadenza=data_scadenza,
            tipo_scadenza="Visita" if tipo_scadenza == "Visita" else "Personale",
            veicolo="",
            ora_inizio=orario_inizio,
            ora_fine=orario_fine,
            ricorrenza=ricorrenza
        )
        
        if successo:
            messagebox.showinfo("Esportazione Completata", risultato)
        else:
            messagebox.showerror("Errore Esportazione", risultato)
    
    def ricarica_interfaccia(self, tab_da_aprire="personali"):
        """Ricarica l'interfaccia con i dati del veicolo corrente"""
        # Distruggi tutti i widget
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ricrea l'interfaccia
        self.crea_interfaccia(tab_da_aprire=tab_da_aprire)
        self.aggiorna_visualizzazione()
    
    def crea_interfaccia(self, tab_da_aprire="personali"):
        # Crea Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Veicoli
        tab_veicoli = tk.Frame(self.notebook, bg=COLORE_SFONDO)
        self.notebook.add(tab_veicoli, text="🚗 Veicoli")
        
        # Tab 2: Scadenze Personali
        tab_personali = tk.Frame(self.notebook, bg=COLORE_SFONDO)
        self.notebook.add(tab_personali, text="📋 Scadenze Personali")
        
        # Crea contenuto tab veicoli
        self.crea_tab_veicoli(tab_veicoli)
        
        # Crea contenuto tab scadenze personali
        self.crea_tab_personali(tab_personali)

        # Tab 3: Medicinali
        tab_medicinali = tk.Frame(self.notebook, bg=COLORE_SFONDO)
        self.notebook.add(tab_medicinali, text="💊 Medicinali")
        self.crea_tab_medicinali(tab_medicinali)

        # Se richiesto, resta sul tab Veicoli (es. cambio veicolo) o Medicinali
        if tab_da_aprire == "veicoli":
            self.notebook.select(tab_veicoli)
        elif tab_da_aprire == "medicinali":
            self.notebook.select(tab_medicinali)
        else:
            # Default: tab Scadenze Personali
            self.notebook.select(tab_personali)
    
    def crea_tab_veicoli(self, parent):
        """Crea il tab per la gestione veicoli"""
        main_frame = tk.Frame(parent, bg=COLORE_SFONDO)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # SELEZIONE VEICOLO
        sel_frame = tk.Frame(main_frame, bg=COLORE_SFONDO)
        sel_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(sel_frame, text="Seleziona Veicolo:", font=self.title_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=5)
        
        self.veicolo_combo = ttk.Combobox(sel_frame, values=list(self.dati_completi["veicoli"].keys()), 
                                          font=self.normal_font, state="readonly", width=30)
        self.veicolo_combo.set(self.veicolo_corrente)
        self.veicolo_combo.bind("<<ComboboxSelected>>", self.cambia_veicolo)
        self.veicolo_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Button(sel_frame, text="+ Nuovo Veicolo", command=self.aggiungi_veicolo, 
                 bg="#FF9800", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        tk.Button(sel_frame, text="- Rimuovi Veicolo", command=self.rimuovi_veicolo, 
                 bg="#F44336", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        if NOTIFICHE_DISPONIBILI:
            tk.Button(sel_frame, text="🔔 Controlla Scadenze", command=self.controlla_scadenze_notifiche, 
                     bg="#673AB7", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        if GOOGLE_CALENDAR_DISPONIBILE:
            tk.Button(sel_frame, text="📅 Esporta su Calendar", command=self.esporta_veicolo_su_calendar, 
                     bg="#4285F4", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        dati = self.get_dati_veicolo()
        
        # SEZIONE INFO VEICOLO
        info_frame = tk.LabelFrame(main_frame, text="Informazioni Veicolo", 
                                    font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(info_frame, text="Nome Veicolo:", font=self.normal_font, bg=COLORE_SFONDO).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.veicolo_entry = tk.Entry(info_frame, font=self.normal_font, width=20)
        self.veicolo_entry.grid(row=0, column=1, padx=5)
        self.veicolo_entry.insert(0, dati.get("nome_veicolo", "Veicolo"))
        
        tk.Label(info_frame, text="Targa:", font=self.normal_font, bg=COLORE_SFONDO).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.targa_entry = tk.Entry(info_frame, font=self.normal_font, width=15)
        self.targa_entry.grid(row=0, column=3, padx=5)
        self.targa_entry.insert(0, dati.get("targa", "XX000XX"))
        
        tk.Button(info_frame, text="Salva Info", command=self.salva_info_veicolo, 
                 bg="#9C27B0", fg="white", font=self.normal_font).grid(row=0, column=4, padx=5)
        
        # SEZIONE KM ATTUALI
        km_frame = tk.LabelFrame(main_frame, text="Chilometraggio Attuale", 
                                  font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        km_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(km_frame, text="Km Attuali:", font=self.normal_font, bg=COLORE_SFONDO).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.km_entry = tk.Entry(km_frame, font=self.normal_font, width=15)
        self.km_entry.grid(row=0, column=1, padx=5)
        self.km_entry.insert(0, str(dati["km_attuali"]))
        
        tk.Button(km_frame, text="Aggiorna Km", command=self.aggiorna_km, 
                 bg="#4CAF50", fg="white", font=self.normal_font).grid(row=0, column=2, padx=5)
        
        # LEGENDA TASTI
        legenda_frame = tk.Frame(main_frame, bg=COLORE_SFONDO)
        legenda_frame.pack(fill=tk.X, pady=(10, 5))
        
        legenda_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        tk.Label(legenda_frame, text="Legenda:", font=legenda_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=5)
        tk.Label(legenda_frame, text="✏️ Modifica", font=self.normal_font, bg="#FFF3E0", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="✕ Elimina", font=self.normal_font, bg="#FFEBEE", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="📅 Esporta", font=self.normal_font, bg="#E3F2FD", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        
        # SEZIONE SCADENZE TEMPORALI
        temp_frame = tk.LabelFrame(main_frame, text="Scadenze Temporali", 
                                    font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        temp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.temp_container = tk.Frame(temp_frame, bg=COLORE_SFONDO)
        self.temp_container.pack(fill=tk.BOTH, expand=True)
        
        self.scadenze_temp_widgets = {}
        row = 0
        for voce, data in sorted(dati["scadenze_fisse"].items(), key=lambda x: x[1]):
            tk.Label(self.temp_container, text=f"{voce}:", font=self.normal_font, bg=COLORE_SFONDO).grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            entry = tk.Entry(self.temp_container, font=self.normal_font, width=15)
            entry.grid(row=row, column=1, padx=5)
            entry.insert(0, data_iso_a_italiana(data))
            label_stato = tk.Label(self.temp_container, text="", font=self.normal_font, bg=COLORE_SFONDO, width=30)
            label_stato.grid(row=row, column=2, padx=5)
            
            # Pulsante modifica
            btn_modifica = tk.Button(self.temp_container, text="✏️", 
                                    command=lambda v=voce: self.modifica_scadenza_temp(v),
                                    bg="#FF9800", fg="white", width=2)
            btn_modifica.grid(row=row, column=3, padx=2)
            
            # Pulsante elimina
            btn_elimina = tk.Button(self.temp_container, text="✕", 
                                   command=lambda v=voce: self.elimina_scadenza_temp(v),
                                   bg="#F44336", fg="white", width=2)
            btn_elimina.grid(row=row, column=4, padx=2)
            
            # Pulsante esporta su Google Calendar
            btn_calendar = tk.Button(self.temp_container, text="📅", 
                                    command=lambda v=voce: self.esporta_singola_scad_temp(v),
                                    bg="#4285F4", fg="white", width=2)
            btn_calendar.grid(row=row, column=5, padx=2)
            
            self.scadenze_temp_widgets[voce] = {"entry": entry, "label": label_stato, "btn_modifica": btn_modifica, "btn_elimina": btn_elimina, "btn_calendar": btn_calendar}
            row += 1
        
        btn_frame_temp = tk.Frame(temp_frame, bg=COLORE_SFONDO)
        btn_frame_temp.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame_temp, text="+ Nuova Scadenza", command=self.aggiungi_scadenza_temp,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_temp, text="Salva Scadenze Temporali", command=self.salva_scadenze_temp,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        # SEZIONE SCADENZE CHILOMETRICHE
        km_manu_frame = tk.LabelFrame(main_frame, text="Manutenzione Chilometrica", 
                                       font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        km_manu_frame.pack(fill=tk.BOTH, expand=True)
        
        self.km_container = tk.Frame(km_manu_frame, bg=COLORE_SFONDO)
        self.km_container.pack(fill=tk.BOTH, expand=True)
        
        self.scadenze_km_widgets = {}
        row = 0
        tk.Label(self.km_container, text="Componente", font=self.title_font, bg=COLORE_SFONDO).grid(row=row, column=0, pady=5)
        tk.Label(self.km_container, text="Ultimo Km", font=self.title_font, bg=COLORE_SFONDO).grid(row=row, column=1, pady=5)
        tk.Label(self.km_container, text="Prossimo Km", font=self.title_font, bg=COLORE_SFONDO).grid(row=row, column=2, pady=5)
        tk.Label(self.km_container, text="Km Residui", font=self.title_font, bg=COLORE_SFONDO).grid(row=row, column=3, pady=5)
        tk.Label(self.km_container, text="Azioni", font=self.title_font, bg=COLORE_SFONDO).grid(row=row, column=4, pady=5)
        row += 1
        
        for voce, info in sorted(dati["scadenze_chilometriche"].items(), key=lambda x: x[1]["prossimo_km"] - dati["km_attuali"]):
            tk.Label(self.km_container, text=f"{voce}:", font=self.normal_font, bg=COLORE_SFONDO).grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            
            ultimo_entry = tk.Entry(self.km_container, font=self.normal_font, width=12)
            ultimo_entry.grid(row=row, column=1, padx=5)
            ultimo_entry.insert(0, str(info["ultimo_km"]))
            
            prossimo_entry = tk.Entry(self.km_container, font=self.normal_font, width=12)
            prossimo_entry.grid(row=row, column=2, padx=5)
            prossimo_entry.insert(0, str(info["prossimo_km"]))
            
            label_residui = tk.Label(self.km_container, text="", font=self.normal_font, bg=COLORE_SFONDO, width=25)
            label_residui.grid(row=row, column=3, padx=5)
            
            # Frame per pulsanti modifica/elimina/esporta
            btn_frame_azioni = tk.Frame(self.km_container, bg=COLORE_SFONDO)
            btn_frame_azioni.grid(row=row, column=4, padx=5)
            
            # Pulsante modifica
            btn_modifica = tk.Button(btn_frame_azioni, text="✏️", 
                                    command=lambda v=voce: self.modifica_scadenza_km(v),
                                    bg="#FF9800", fg="white", width=2)
            btn_modifica.pack(side=tk.LEFT, padx=2)
            
            # Pulsante elimina
            btn_elimina = tk.Button(btn_frame_azioni, text="✕", 
                                   command=lambda v=voce: self.elimina_scadenza_km(v),
                                   bg="#F44336", fg="white", width=2)
            btn_elimina.pack(side=tk.LEFT, padx=2)
            
            # Pulsante esporta (nota: non applicabile per scadenze chilometriche senza data)
            btn_esporta = tk.Button(btn_frame_azioni, text="📅", 
                                   command=lambda v=voce: messagebox.showinfo("Info", 
                                       "Le scadenze chilometriche non hanno date specifiche e non possono essere esportate su Google Calendar."),
                                   bg="#4285F4", fg="white", width=2)
            btn_esporta.pack(side=tk.LEFT, padx=2)
            
            self.scadenze_km_widgets[voce] = {
                "ultimo": ultimo_entry,
                "prossimo": prossimo_entry,
                "label": label_residui,
                "btn_modifica": btn_modifica,
                "btn_elimina": btn_elimina,
                "btn_esporta": btn_esporta
            }
            row += 1
        
        btn_frame_km = tk.Frame(km_manu_frame, bg=COLORE_SFONDO)
        btn_frame_km.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame_km, text="+ Nuova Scadenza Km", command=self.aggiungi_scadenza_km,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_km, text="Salva Scadenze Chilometriche", command=self.salva_scadenze_km,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
    
    def toggle_orario_personale(self, voce):
        """Abilita/disabilita i campi orario quando cambia il checkbox"""
        if voce in self.scadenze_personali_widgets:
            widgets = self.scadenze_personali_widgets[voce]
            abilitato = not widgets["var_tutto_giorno"].get()
            self._abilita_campo(widgets["entry_inizio"], abilitato)
            self._abilita_campo(widgets["entry_fine"], abilitato)

    def _is_visita_personale(self, voce, data_obj=None):
        """Determina se una voce personale appartiene alle visite mediche."""
        if isinstance(data_obj, dict) and data_obj.get("categoria") == "visita_prenotata":
            return True
        voce_lower = voce.lower()
        return "visita" in voce_lower or "medic" in voce_lower

    def _is_visita_da_prenotare(self, voce):
        """Riconosce le visite ancora da prenotare in base al nome della voce."""
        voce_lower = voce.lower()
        return "prenotare" in voce_lower or "da prenotare" in voce_lower

    def _is_festa_compleanno(self, voce):
        """Determina se una voce personale appartiene a feste o compleanni."""
        voce_lower = voce.lower()
        return "compleanno" in voce_lower or "festa" in voce_lower

    def _sezione_personale(self, voce, data_obj=None):
        """Sezione di una scadenza personale: 'visite', 'da_prenotare', 'feste' o 'scadenze'.

        Conta prima la categoria salvata (visita / festa), poi le parole nel nome.
        Tra visite prenotate e da prenotare decide il nome ("... da prenotare").
        """
        categoria = data_obj.get("categoria") if isinstance(data_obj, dict) else None
        if categoria in ("visita_prenotata", "visita_da_prenotare") or self._is_visita_personale(voce):
            return "da_prenotare" if self._is_visita_da_prenotare(voce) else "visite"
        if categoria == "festa_compleanno" or self._is_festa_compleanno(voce):
            return "feste"
        return "scadenze"
    
    def _impegni_nel_periodo(self, inizio, fine):
        """Raccoglie tutti gli impegni tra inizio e fine (inclusi).

        Comprende le scadenze personali (con tutte le ripetizioni delle ricorrenti)
        e le scadenze a data dei veicoli.
        Restituisce {data: [(ora_ordinamento, riga, sezione, ora_testo, nome), ...]}
        dove sezione è una chiave di SEZIONI_RIEPILOGO.
        """
        impegni = {}

        for nome, data_obj in self.dati_completi.get("scadenze_personali", {}).items():
            if isinstance(data_obj, str):
                data_obj = {"data": data_obj}
            try:
                data_iniziale = datetime.strptime(data_obj.get("data", ""), "%Y-%m-%d").date()
            except ValueError:
                continue

            ora_inizio = data_obj.get("ora_inizio") if data_obj.get("con_orario") else None
            ora_fine = data_obj.get("ora_fine") if data_obj.get("con_orario") else None
            if ora_inizio and ora_fine:
                ora_testo = f"{ora_inizio}-{ora_fine}"
            else:
                ora_testo = ora_inizio or ""
            riga = f"{ora_testo} {nome}" if ora_testo else nome

            # Stessa suddivisione della scheda Scadenze Personali
            sezione = self._sezione_personale(nome, data_obj)

            for giorno in occorrenze_nel_periodo(data_iniziale, data_obj.get("ricorrenza"), inizio, fine):
                # Le voci senza orario vanno in cima alla giornata
                impegni.setdefault(giorno, []).append((ora_inizio or "00:00", riga, sezione, ora_testo, nome))

        for dati_veicolo in self.dati_completi.get("veicoli", {}).values():
            nome_veicolo = dati_veicolo.get("nome_veicolo", "Veicolo")
            for voce, data_str in dati_veicolo.get("scadenze_fisse", {}).items():
                try:
                    giorno = datetime.strptime(data_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if inizio <= giorno <= fine:
                    nome = f"{voce} ({nome_veicolo})"
                    impegni.setdefault(giorno, []).append(("00:00", nome, "veicoli", "", nome))

        return impegni

    def _testo_settimana(self, inizio=None, giorni=GIORNI_RIEPILOGO):
        """Crea il testo del riepilogo, già formattato per WhatsApp (*grassetto*)."""
        oggi = datetime.now().date()
        inizio = inizio or oggi
        fine = inizio + timedelta(days=giorni - 1)
        impegni = self._impegni_nel_periodo(inizio, fine)

        righe = [f"*Impegni dal {inizio.strftime('%d/%m')} al {fine.strftime('%d/%m')}*"]
        if not impegni:
            righe += ["", "Nessun impegno in programma."]
            return "\n".join(righe)

        for giorno in sorted(impegni):
            etichetta = f"{NOMI_GIORNI[giorno.weekday()]} {giorno.strftime('%d/%m')}"
            if giorno == oggi:
                etichetta += " (oggi)"
            elif giorno == oggi + timedelta(days=1):
                etichetta += " (domani)"
            righe += ["", f"*{etichetta}*"]
            for voce in sorted(impegni[giorno]):
                righe.append(f"• {voce[1]}")

        return "\n".join(righe)

    def _immagine_settimana(self, vista, inizio=None, impegni=None):
        """Crea l'immagine degli impegni dei prossimi giorni: vista 'calendario' o 'elenco'.

        Se `impegni` è dato (impegni modificati a mano) usa quelli invece dei dati dell'app.
        """
        inizio = inizio or datetime.now().date()
        fine = inizio + timedelta(days=GIORNI_RIEPILOGO - 1)
        if impegni is None:
            impegni = self._impegni_nel_periodo(inizio, fine)

        if vista == "calendario":
            colori = {chiave: colore for chiave, _, colore in SEZIONI_RIEPILOGO}
            eventi, usate = [], set()
            for giorno, voci in impegni.items():
                for _, _, sezione, ora_testo, nome in voci:
                    eventi.append({"giorno": giorno, "ora": ora_testo, "nome": nome, "colore": colori[sezione]})
                    usate.add(sezione)
            legenda = [(LEGENDA_BREVE[chiave], colore) for chiave, _, colore in SEZIONI_RIEPILOGO if chiave in usate]
            return immagine_settimana.crea_immagine_calendario(
                eventi, inizio, giorni=GIORNI_RIEPILOGO, legenda=legenda)

        # Vista elenco: raggruppa per sezione, ordinando per giorno e orario
        per_sezione = {chiave: [] for chiave, _, _ in SEZIONI_RIEPILOGO}
        for giorno, voci in impegni.items():
            for ora_ord, _, sezione, ora_testo, nome in voci:
                per_sezione[sezione].append((giorno, ora_ord, {"giorno": giorno, "ora": ora_testo, "nome": nome}))
        sezioni = [
            (titolo, colore, [r for _, _, r in sorted(per_sezione[chiave], key=lambda x: (x[0], x[1], x[2]["nome"]))])
            for chiave, titolo, colore in SEZIONI_RIEPILOGO
        ]
        return immagine_settimana.crea_immagine(sezioni, inizio, fine)

    # ------------------------------------------------ impegni modificabili come testo

    # Riga impegno: [giorno settimana] GG/MM[/AAAA]  [HH:MM[-HH:MM]]  Nome
    _RIGA_IMPEGNO = re.compile(
        r"^\s*(?:[A-Za-zÀ-ÿ]{2,10}\.?\s+)?"              # giorno della settimana (facoltativo, ignorato)
        r"(\d{1,2}[/.\-]\d{1,2}(?:[/.\-]\d{2,4})?)\s+"   # data
        r"(?:(\d{1,2}[:.]\d{2})(?:\s*-\s*(\d{1,2}[:.]\d{2}))?\s+)?"  # orario (facoltativo)
        r"(.+?)\s*$"                                       # nome
    )

    def _testo_da_impegni(self, impegni):
        """Trasforma gli impegni in testo modificabile, una riga per impegno, diviso per sezioni."""
        per_sezione = {chiave: [] for chiave, _, _ in SEZIONI_RIEPILOGO}
        for giorno, voci in impegni.items():
            for ora_ord, _, sezione, ora_testo, nome in voci:
                per_sezione[sezione].append((giorno, ora_ord, nome, ora_testo))
        blocchi = []
        for chiave, _, _ in SEZIONI_RIEPILOGO:
            if not per_sezione[chiave]:
                continue
            righe = [f"# {LEGENDA_BREVE[chiave]}"]
            for giorno, _, nome, ora_testo in sorted(per_sezione[chiave]):
                data_txt = f"{NOMI_GIORNI[giorno.weekday()][:3]} {giorno.strftime('%d/%m')}"
                righe.append(f"{data_txt}  {ora_testo}  {nome}" if ora_testo else f"{data_txt}  {nome}")
            blocchi.append("\n".join(righe))
        return "\n\n".join(blocchi) + "\n" if blocchi else "# Scadenze\n"

    @staticmethod
    def _sezione_da_titolo(titolo):
        """'# Visite da prenotare' → 'da_prenotare'; None se non riconosciuta."""
        t = titolo.strip().lstrip("#").strip().lower()
        if t.startswith("visite da") or t.startswith("da prenotare"):
            return "da_prenotare"
        if t.startswith("visit"):
            return "visite"
        if t.startswith("scad"):
            return "scadenze"
        if t.startswith("fest") or t.startswith("compl"):
            return "feste"
        if t.startswith("veic") or t.startswith("auto"):
            return "veicoli"
        return None

    def _impegni_da_testo(self, testo, inizio, fine):
        """Legge il testo modificato. Restituisce (impegni, errori).

        impegni ha lo stesso formato di _impegni_nel_periodo; errori è una lista di stringhe.
        """
        impegni, errori = {}, []
        sezione = "scadenze"  # righe prima di qualsiasi titolo
        for n, riga in enumerate(testo.splitlines(), start=1):
            if not riga.strip():
                continue
            if riga.strip().startswith("#"):
                trovata = self._sezione_da_titolo(riga)
                if trovata is None:
                    errori.append(f"Riga {n}: sezione '{riga.strip()}' non riconosciuta "
                                  f"(usa {', '.join('# ' + v for v in LEGENDA_BREVE.values())})")
                else:
                    sezione = trovata
                continue

            m = self._RIGA_IMPEGNO.match(riga)
            if not m:
                errori.append(f"Riga {n}: formato non valido → {riga.strip()}")
                continue
            data_txt, ora_da, ora_a, nome = m.groups()
            giorno = interpreta_data(data_txt, inizio)
            if giorno is None:
                errori.append(f"Riga {n}: data non valida → {data_txt}")
                continue
            if not inizio <= giorno <= fine:
                errori.append(f"Riga {n}: {giorno.strftime('%d/%m/%Y')} è fuori dal periodo "
                              f"({inizio.strftime('%d/%m')} - {fine.strftime('%d/%m')})")
                continue

            orari = []
            for valore in (ora_da, ora_a):
                if valore is None:
                    continue
                try:
                    orari.append(datetime.strptime(valore.replace(".", ":"), "%H:%M").strftime("%H:%M"))
                except ValueError:
                    orari.append(None)
            if None in orari:
                errori.append(f"Riga {n}: orario non valido → {riga.strip()}")
                continue
            if len(orari) == 2 and orari[1] <= orari[0]:
                errori.append(f"Riga {n}: l'orario di fine è prima dell'inizio → {riga.strip()}")
                continue

            ora_testo = "-".join(orari)
            voce = f"{ora_testo} {nome}" if ora_testo else nome
            impegni.setdefault(giorno, []).append(
                (orari[0] if orari else "00:00", voce, sezione, ora_testo, nome))
        return impegni, errori

    def _barra_data_inizio(self, parent, stato, al_cambio):
        """Aggiunge a parent i controlli per scegliere il giorno di inizio (stato["inizio"])."""
        tk.Label(parent, text="Dal:", font=self.normal_font, bg=COLORE_SFONDO).pack(side=tk.LEFT)
        var_data = tk.StringVar(value=stato["inizio"].strftime("%d/%m/%Y"))

        def imposta(nuova):
            stato["inizio"] = nuova
            var_data.set(nuova.strftime("%d/%m/%Y"))
            al_cambio()

        def da_campo(*_):
            nuova = interpreta_data(var_data.get(), datetime.now().date())
            if nuova is None:
                messagebox.showerror("Errore", "Data non valida. Usa il formato GG/MM/AAAA",
                                     parent=parent.winfo_toplevel())
                return
            imposta(nuova)

        def sposta(giorni):
            return lambda: imposta(stato["inizio"] + timedelta(days=giorni))

        tk.Button(parent, text="<<", font=self.normal_font, width=3,
                  command=sposta(-GIORNI_RIEPILOGO)).pack(side=tk.LEFT, padx=2)
        tk.Button(parent, text="<", font=self.normal_font, width=3,
                  command=sposta(-1)).pack(side=tk.LEFT, padx=2)
        campo = tk.Entry(parent, textvariable=var_data, font=self.normal_font, width=11, justify=tk.CENTER)
        campo.pack(side=tk.LEFT, padx=2)
        campo.bind("<Return>", da_campo)
        tk.Button(parent, text=">", font=self.normal_font, width=3,
                  command=sposta(1)).pack(side=tk.LEFT, padx=2)
        tk.Button(parent, text=">>", font=self.normal_font, width=3,
                  command=sposta(GIORNI_RIEPILOGO)).pack(side=tk.LEFT, padx=2)
        tk.Button(parent, text="Vai", font=self.normal_font, command=da_campo).pack(side=tk.LEFT, padx=2)
        tk.Button(parent, text="Oggi", font=self.normal_font,
                  command=lambda: imposta(datetime.now().date())).pack(side=tk.LEFT, padx=(2, 12))

    def copia_settimana_immagine(self):
        """Crea un'immagine a colori degli impegni (calendario o elenco) e la copia negli appunti."""
        if not IMMAGINE_DISPONIBILE:
            messagebox.showerror(
                "Errore",
                "Per creare l'immagine serve la libreria Pillow.\n\n"
                "Installa con: pip install Pillow\n"
                "(oppure riavvia con avvia_scadenze.bat, che la installa da solo)"
            )
            return

        win = tk.Toplevel(self.root)
        win.title("Impegni della settimana - immagine")
        win.configure(bg=COLORE_SFONDO)
        win.transient(self.root)

        var_vista = tk.StringVar(value=VISTA_IMMAGINE_PREDEFINITA)
        stato = {"img": None, "inizio": datetime.now().date(),
                 "impegni_modificati": None, "testo_modificato": None, "editor": None}

        def periodo():
            return stato["inizio"], stato["inizio"] + timedelta(days=GIORNI_RIEPILOGO - 1)

        def data_cambiata():
            # Le modifiche a mano valgono per un periodo: cambiando data si riparte dai dati
            stato["impegni_modificati"] = stato["testo_modificato"] = None
            if stato["editor"] is not None and stato["editor"]["win"].winfo_exists():
                stato["editor"]["carica"]("Periodo cambiato: impegni ricaricati dai dati dell'app.")
            genera()

        # Barra in alto: scelta della vista e pulsanti (sempre visibili)
        barra = tk.Frame(win, bg=COLORE_SFONDO)
        barra.pack(fill=tk.X, padx=10, pady=(10, 0))
        self._barra_data_inizio(barra, stato, data_cambiata)
        tk.Label(barra, text="Vista:", font=self.normal_font, bg=COLORE_SFONDO).pack(side=tk.LEFT)
        lbl_msg = tk.Label(win, text="", font=self.normal_font, bg=COLORE_SFONDO, justify=tk.LEFT)
        lbl_msg.pack(anchor=tk.W, padx=10, pady=(6, 4))
        area = tk.Label(win, bg=COLORE_SFONDO)
        area.pack(padx=10, pady=(0, 10))

        def copia_e_mostra():
            img = stato["img"]
            copiato, errore = immagine_settimana.copia_immagine_negli_appunti(img)
            if copiato:
                msg, col = "✅ Immagine copiata negli appunti: incollala su WhatsApp con Ctrl+V", "#1B5E20"
            else:
                msg, col = f"⚠️ {errore}", "#B71C1C"
            if stato.get("percorso"):
                msg += f"\nSalvata anche in: {stato['percorso']}"
            if stato["impegni_modificati"] is not None:
                msg += "\n✏️ Immagine creata con le tue modifiche (i dati dell'app non cambiano)"
            lbl_msg.config(text=msg, fg=col)

        def genera(*_):
            img = self._immagine_settimana(var_vista.get(), stato["inizio"], stato["impegni_modificati"])
            stato["img"] = img
            # Salva anche un file, utile se si vuole trascinarlo o inviarlo in altro modo
            percorso = os.path.abspath(FILE_IMMAGINE_RIEPILOGO)
            try:
                img.save(percorso)
                stato["percorso"] = percorso
            except OSError:
                stato["percorso"] = None
            copia_e_mostra()
            # Anteprima ridotta per stare nello schermo, rimpicciolita in modo morbido
            # (l'immagine copiata resta a piena risoluzione)
            altezza_max = int(self.root.winfo_screenheight() * 0.75)
            larghezza_max = int(self.root.winfo_screenwidth() * 0.85)
            rapporto = min(altezza_max / img.height, larghezza_max / img.width, 1.0)
            try:
                from PIL import ImageTk
                ridotta = img.resize((int(img.width * rapporto), int(img.height * rapporto)),
                                     immagine_settimana.Image.LANCZOS)
                foto = ImageTk.PhotoImage(ridotta, master=win)
            except Exception:
                foto = None
                if stato["percorso"]:
                    try:
                        fattore = max(1, round(1 / rapporto))
                        foto = tk.PhotoImage(file=stato["percorso"]).subsample(fattore)
                    except tk.TclError:
                        foto = None
            if foto is not None:
                area.config(image=foto)
                area.image = foto  # mantiene il riferimento

        for valore, testo in (("calendario", "📅 Calendario"), ("elenco", "📋 Elenco")):
            tk.Radiobutton(barra, text=testo, variable=var_vista, value=valore, command=genera,
                           font=self.normal_font, bg=COLORE_SFONDO, indicatoron=False,
                           selectcolor="#C8E6C9", padx=8, pady=2).pack(side=tk.LEFT, padx=4)
        def apri_editor():
            ed = stato["editor"]
            if ed is not None and ed["win"].winfo_exists():
                ed["win"].lift()
                ed["win"].focus_force()
                return
            stato["editor"] = self._finestra_modifica_impegni(win, stato, periodo, genera)

        tk.Button(barra, text="✏️ Modifica impegni", command=apri_editor, bg="#FF9800", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=(16, 4))
        tk.Button(barra, text="🖼️ Copia di nuovo", command=copia_e_mostra, bg="#25D366", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=4)
        tk.Button(barra, text="Chiudi", command=win.destroy, bg="#9E9E9E", fg="white",
                  font=self.normal_font, width=10).pack(side=tk.LEFT, padx=4)

        genera()

    def _finestra_modifica_impegni(self, padre, stato, periodo, genera):
        """Finestra per modificare a mano, come un file di testo, gli impegni dell'immagine.

        Le modifiche finiscono in stato["impegni_modificati"] e servono solo per l'immagine
        da mandare su WhatsApp: i dati salvati dell'app non vengono toccati.
        """
        ed = tk.Toplevel(padre)
        ed.title("Modifica impegni (solo per l'immagine WhatsApp)")
        ed.geometry("680x640")
        ed.configure(bg=COLORE_SFONDO)
        ed.transient(padre)

        istruzioni = (
            "Una riga per impegno:   GG/MM   ORA-ORA   Nome        (senza orario = tutto il giorno)\n"
            "Le righe con # scelgono la sezione e il colore: "
            + ", ".join("# " + v for v in LEGENDA_BREVE.values()) + "\n"
            "Puoi correggere, cancellare o aggiungere righe. I dati dell'app NON vengono modificati."
        )
        tk.Label(ed, text=istruzioni, font=self.normal_font, bg=COLORE_SFONDO, fg="#555555",
                 justify=tk.LEFT, wraplength=640).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Pulsanti ed esito vanno in basso PRIMA dell'area di testo, così restano sempre visibili
        btn = tk.Frame(ed, bg=COLORE_SFONDO)
        btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        lbl_esito = tk.Label(ed, text="", font=self.normal_font, bg=COLORE_SFONDO, justify=tk.LEFT,
                             wraplength=640)
        lbl_esito.pack(side=tk.BOTTOM, anchor=tk.W, padx=10, pady=(4, 0))

        cornice = tk.Frame(ed, bg=COLORE_SFONDO)
        cornice.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        barra_scroll = ttk.Scrollbar(cornice, orient=tk.VERTICAL)
        area = tk.Text(cornice, font=tkfont.Font(family="Consolas", size=11), wrap=tk.NONE,
                       undo=True, height=14, yscrollcommand=barra_scroll.set)
        barra_scroll.config(command=area.yview)
        barra_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def carica(messaggio=""):
            """Mette nell'area il testo modificato, se c'è, altrimenti gli impegni dai dati."""
            if stato["testo_modificato"] is not None:
                testo = stato["testo_modificato"]
            else:
                inizio, fine = periodo()
                testo = self._testo_da_impegni(self._impegni_nel_periodo(inizio, fine))
            area.delete("1.0", tk.END)
            area.insert("1.0", testo)
            area.edit_reset()
            lbl_esito.config(text=messaggio, fg="#555555")

        def aggiorna(*_):
            inizio, fine = periodo()
            testo = area.get("1.0", "end-1c")
            impegni, errori = self._impegni_da_testo(testo, inizio, fine)
            stato["impegni_modificati"] = impegni
            stato["testo_modificato"] = testo
            genera()
            if errori:
                lbl_esito.config(fg="#B71C1C", text="⚠️ Immagine aggiornata, ma queste righe sono state ignorate:\n"
                                 + "\n".join(errori[:8]) + ("\n…" if len(errori) > 8 else ""))
            else:
                lbl_esito.config(fg="#1B5E20", text="✅ Immagine aggiornata e copiata negli appunti.")
            return "break"

        def ripristina():
            stato["impegni_modificati"] = stato["testo_modificato"] = None
            carica("↩️ Ripristinati gli impegni dai dati dell'app.")
            genera()

        tk.Button(btn, text="🔄 Aggiorna immagine  (Ctrl+Invio)", command=aggiorna, bg="#25D366", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=4)
        tk.Button(btn, text="↩️ Ripristina dai dati", command=ripristina, bg="#607D8B", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=4)
        tk.Button(btn, text="Chiudi", command=ed.destroy, bg="#9E9E9E", fg="white",
                  font=self.normal_font, width=10).pack(side=tk.LEFT, padx=4)
        area.bind("<Control-Return>", aggiorna)

        carica()
        area.focus_set()
        return {"win": ed, "carica": carica}

    def _copia_negli_appunti(self, testo):
        self.root.clipboard_clear()
        self.root.clipboard_append(testo)
        self.root.update()  # rende disponibile subito il testo alle altre applicazioni

    def copia_settimana(self):
        """Copia negli appunti gli impegni dei prossimi giorni e mostra un'anteprima modificabile."""
        testo = self._testo_settimana()
        self._copia_negli_appunti(testo)

        win = tk.Toplevel(self.root)
        win.title("Impegni della settimana")
        win.geometry("560x600")
        win.configure(bg=COLORE_SFONDO)
        win.transient(self.root)

        periodo = {"inizio": datetime.now().date()}

        def rigenera():
            nuovo = self._testo_settimana(periodo["inizio"])
            area.delete("1.0", tk.END)
            area.insert("1.0", nuovo)
            self._copia_negli_appunti(nuovo)
            stato.config(text="✅ Copiato negli appunti: incollalo su WhatsApp con Ctrl+V")

        barra_data = tk.Frame(win, bg=COLORE_SFONDO)
        barra_data.pack(fill=tk.X, padx=10, pady=(10, 0))
        self._barra_data_inizio(barra_data, periodo, rigenera)

        stato = tk.Label(win, text="✅ Copiato negli appunti: incollalo su WhatsApp con Ctrl+V",
                         font=self.normal_font, bg=COLORE_SFONDO, fg="#1B5E20")
        stato.pack(anchor=tk.W, padx=10, pady=(10, 5))

        area = tk.Text(win, font=self.normal_font, wrap=tk.WORD, height=20)
        area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        area.insert("1.0", testo)

        def ricopia():
            self._copia_negli_appunti(area.get("1.0", "end-1c"))
            stato.config(text="✅ Testo modificato copiato negli appunti")

        btn_frame = tk.Frame(win, bg=COLORE_SFONDO)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(btn_frame, text="📋 Copia di nuovo", command=ricopia, bg="#25D366", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Chiudi", command=win.destroy, bg="#9E9E9E", fg="white",
                  font=self.normal_font, width=10).pack(side=tk.LEFT, padx=5)

    def _scroll_rotellina(self, event):
        """Scorre con la rotellina la scheda aperta (Scadenze Personali o Medicinali)."""
        try:
            # Ignora la rotellina nelle finestre di dialogo (es. Ricorrenza)
            if event.widget.winfo_toplevel() is not self.root:
                return
            # Scorre solo nelle schede con l'area scorrevole
            scheda = self.notebook.index(self.notebook.select())
            canvas = {1: getattr(self, "canvas_personali", None),
                      2: getattr(self, "canvas_medicinali", None)}.get(scheda)
            if canvas is None or not canvas.winfo_exists():
                return
            # Su Windows ogni "scatto" della rotellina vale delta = 120
            passi = -event.delta / 120 * SCROLL_UNITA_PER_SCATTO
            passi = int(passi) if abs(passi) >= 1 else (1 if passi > 0 else -1)
            canvas.yview_scroll(passi, "units")
        except (tk.TclError, AttributeError):
            pass

    # ------------------------------------------------ scheda Medicinali

    @staticmethod
    def _testo_scadenza_medicinale(voce):
        """Scadenza come l'ha scritta l'utente: '03-2027' (solo mese) oppure '15-03-2027'."""
        scadenza = date.fromisoformat(voce["scadenza"])
        return scadenza.strftime("%m-%Y") if voce.get("solo_mese") else scadenza.strftime("%d-%m-%Y")

    def crea_tab_medicinali(self, parent):
        """Scheda con i medicinali in ordine di scadenza (solo promemoria, nessuna notifica)."""
        scroll_frame = tk.Frame(parent, bg=COLORE_SFONDO)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(scroll_frame, bg=COLORE_SFONDO, highlightthickness=0,
                           yscrollincrement=SCROLL_PIXEL_PER_UNITA)
        self.canvas_medicinali = canvas
        scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        main_frame = tk.Frame(canvas, bg=COLORE_SFONDO)
        finestra = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(finestra, width=e.width))

        testata = tk.Frame(main_frame, bg=COLORE_SFONDO)
        testata.pack(fill=tk.X, pady=(0, 10))
        tk.Label(testata, text="Scadenza Medicinali", font=self.title_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=5)
        tk.Label(testata, text="Solo promemoria: niente notifiche, non va su Google Calendar",
                 font=self.normal_font, bg=COLORE_SFONDO, fg="gray").pack(side=tk.LEFT, padx=15)
        tk.Button(testata, text="🖨️ Report (stampa / WhatsApp)", command=self.report_medicinali,
                  bg="#455A64", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)

        riquadro = tk.LabelFrame(main_frame, text="Medicinali", font=self.title_font,
                                 bg=COLORE_SFONDO, padx=10, pady=10)
        riquadro.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tk.Label(riquadro, text="Scadenza: GG-MM-AAAA oppure solo MM-AAAA come sulla confezione  ·  "
                                "Aperto il: lascia vuoto se la confezione è ancora chiusa  ·  "
                                "Dopo apertura: es. 28 giorni, 6 mesi (dal foglietto)\n"
                                "La posizione si salva appena la scegli dal menu  ·  "
                                "Clic su un titolo (Medicinale, Scadenza, Aperto il, Posizione) per cambiare l'ordine, "
                                "un secondo clic lo inverte",
                 font=self.normal_font, bg=COLORE_SFONDO, fg="gray", justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 6))
        self._griglia_medicinali = tk.Frame(riquadro, bg=COLORE_SFONDO)
        self._griglia_medicinali.pack(fill=tk.BOTH, expand=True)
        self.medicinali_widgets = {}
        self._riempi_griglia_medicinali()

        pulsanti = tk.Frame(riquadro, bg=COLORE_SFONDO)
        pulsanti.pack(fill=tk.X, pady=(10, 0))
        tk.Button(pulsanti, text="+ Nuovo Medicinale", command=self.aggiungi_medicinale,
                  bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(pulsanti, text="Salva Medicinali", command=self.salva_medicinali,
                  bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)

    # Ordinamento: chiave "scadenza", "apertura" o "nome"; ricordato nel file dati
    COLONNE_MEDICINALI = (("Medicinale", "nome"), ("Scadenza", "scadenza"), ("Aperto il", "apertura"),
                          ("Dopo apertura", None), ("Posizione", "posizione"), ("Stato", None))
    GIORNI_PREAVVISO_APERTO = 7  # arancione quando mancano al massimo 7 giorni al limite dopo l'apertura
    # Dove si trova il medicinale (valore salvato, testo mostrato), nell'ordine usato per ordinare
    POSIZIONI_MEDICINALI = (("sotto", "Piano sotto"), ("intermedio", "Piano intermedio"), ("sopra", "Piano sopra"))
    SENZA_POSIZIONE = "—"

    def _ordine_medicinali(self):
        chiave, inverso = self.dati_completi.get("impostazioni", {}).get("ordine_medicinali", ["scadenza", False])
        if chiave not in ("scadenza", "apertura", "nome", "posizione"):
            chiave, inverso = "scadenza", False
        return chiave, bool(inverso)

    @staticmethod
    def _scadenza_effettiva(voce):
        """(data, limite_apertura): la data che arriva prima tra la scadenza della confezione
        e apertura + durata dopo l'apertura. limite_apertura è True se decide l'apertura."""
        scadenza = date.fromisoformat(voce["scadenza"])
        durata = interpreta_durata(voce.get("durata_apertura") or "")
        if voce.get("apertura") and durata:
            limite = fine_dopo_apertura(date.fromisoformat(voce["apertura"]), *durata)
            if limite < scadenza:
                return limite, True
        return scadenza, False

    def _medicinali_ordinati(self, chiave, inverso):
        lista = list(self.dati_completi.get("medicinali", []))
        effettiva = lambda v: self._scadenza_effettiva(v)[0].isoformat()
        if chiave == "nome":
            return sorted(lista, key=lambda v: (v["nome"].casefold(), effettiva(v)), reverse=inverso)
        if chiave == "posizione":
            # Piano sotto, intermedio, sopra; quelli senza posizione restano sempre in fondo
            ordine = {k: i for i, (k, _) in enumerate(self.POSIZIONI_MEDICINALI)}
            con_posizione = sorted((v for v in lista if v.get("posizione") in ordine),
                                   key=lambda v: (ordine[v["posizione"]], effettiva(v)), reverse=inverso)
            senza = sorted((v for v in lista if v.get("posizione") not in ordine),
                           key=lambda v: (effettiva(v), v["nome"].casefold()))
            return con_posizione + senza
        if chiave == "apertura":
            # Le confezioni ancora chiuse restano sempre in fondo, in ordine di scadenza
            aperti = sorted((v for v in lista if v.get("apertura")),
                            key=lambda v: (v["apertura"], effettiva(v)), reverse=inverso)
            chiusi = sorted((v for v in lista if not v.get("apertura")),
                            key=lambda v: (effettiva(v), v["nome"].casefold()))
            return aperti + chiusi
        return sorted(lista, key=lambda v: (effettiva(v), v["nome"].casefold()), reverse=inverso)

    def ordina_medicinali(self, chiave):
        """Clic su un titolo di colonna: ordina per quella colonna, un secondo clic inverte l'ordine."""
        attuale, inverso = self._ordine_medicinali()
        inverso = (not inverso) if chiave == attuale else False
        self.dati_completi.setdefault("impostazioni", {})["ordine_medicinali"] = [chiave, inverso]
        salva_dati(self.dati_completi)
        self._riempi_griglia_medicinali(conserva_testi=True)

    def _riempi_griglia_medicinali(self, conserva_testi=False):
        """(Ri)disegna le righe dei medicinali nell'ordine scelto.

        Con conserva_testi=True le date scritte nei campi e non ancora salvate restano al loro posto.
        """
        griglia = self._griglia_medicinali
        testi = {}
        if conserva_testi:
            for w in self.medicinali_widgets.values():
                testi[id(w["voce"])] = (w["entry_scadenza"].get(), w["entry_apertura"].get(),
                                        w["entry_durata"].get())
        for figlio in griglia.winfo_children():
            figlio.destroy()
        self.medicinali_widgets = {}

        chiave, inverso = self._ordine_medicinali()
        medicinali = self._medicinali_ordinati(chiave, inverso)
        if not medicinali:
            tk.Label(griglia, text="Nessun medicinale inserito", font=self.normal_font,
                     bg=COLORE_SFONDO, fg="gray").grid(row=0, column=0, sticky=tk.W, pady=10)
            return

        for c, (titolo, chiave_col) in enumerate(self.COLONNE_MEDICINALI):
            attiva = chiave_col == chiave
            testo = f"{titolo} {'▼' if inverso else '▲'}" if attiva else titolo
            etichetta = tk.Label(griglia, text=testo, font=self.title_font, bg=COLORE_SFONDO,
                                 fg="#1565C0" if attiva else "black")
            etichetta.grid(row=0, column=c, sticky=tk.W, padx=5, pady=(0, 5))
            if chiave_col:
                etichetta.configure(cursor="hand2")
                etichetta.bind("<Button-1>", lambda e, k=chiave_col: self.ordina_medicinali(k))

        for r, voce in enumerate(medicinali, start=1):
            testo_scadenza, testo_apertura, testo_durata_campo = testi.get(id(voce), (
                self._testo_scadenza_medicinale(voce),
                data_iso_a_italiana(voce["apertura"]) if voce.get("apertura") else "",
                voce.get("durata_apertura") or ""))
            # I nomi molto lunghi vanno a capo invece di allargare tutta la tabella
            tk.Label(griglia, text=voce["nome"], font=self.normal_font, bg=COLORE_SFONDO, width=30,
                     anchor=tk.W, justify=tk.LEFT, wraplength=250).grid(row=r, column=0, sticky=tk.W, padx=5, pady=4)
            entry_scadenza = tk.Entry(griglia, font=self.normal_font, width=12)
            entry_scadenza.grid(row=r, column=1, padx=5)
            entry_scadenza.insert(0, testo_scadenza)
            entry_apertura = tk.Entry(griglia, font=self.normal_font, width=12)
            entry_apertura.grid(row=r, column=2, padx=5)
            entry_apertura.insert(0, testo_apertura)
            entry_durata = tk.Entry(griglia, font=self.normal_font, width=11)
            entry_durata.grid(row=r, column=3, padx=5)
            entry_durata.insert(0, testo_durata_campo)
            testi_posizione = [t for _, t in self.POSIZIONI_MEDICINALI] + [self.SENZA_POSIZIONE]
            combo_posizione = ttk.Combobox(griglia, values=testi_posizione, state="readonly",
                                           width=16, font=self.normal_font)
            combo_posizione.set(dict(self.POSIZIONI_MEDICINALI).get(voce.get("posizione"), self.SENZA_POSIZIONE))
            combo_posizione.grid(row=r, column=4, padx=5)
            combo_posizione.bind("<<ComboboxSelected>>",
                                 lambda e, v=voce, c=combo_posizione: self._cambia_posizione_medicinale(v, c.get()))
            # La rotellina sopra il menu scorre la pagina invece di cambiare piano per sbaglio
            combo_posizione.bind("<MouseWheel>", lambda e: (self._scroll_rotellina(e), "break")[1])
            label_stato = tk.Label(griglia, text="", font=self.normal_font, bg=COLORE_SFONDO, width=40,
                                   anchor=tk.W, justify=tk.LEFT)
            label_stato.grid(row=r, column=5, sticky=tk.W, padx=10)
            tk.Button(griglia, text="✏️", command=lambda v=voce: self.rinomina_medicinale(v),
                      bg="#FF9800", fg="white", width=2).grid(row=r, column=6, padx=2)
            tk.Button(griglia, text="✕", command=lambda v=voce: self.elimina_medicinale(v),
                      bg="#F44336", fg="white", width=2).grid(row=r, column=7, padx=2)
            self.medicinali_widgets[r] = {"voce": voce, "entry_scadenza": entry_scadenza,
                                          "entry_apertura": entry_apertura, "entry_durata": entry_durata,
                                          "combo_posizione": combo_posizione, "label": label_stato}
        self._aggiorna_stato_medicinali()

    def _cambia_posizione_medicinale(self, voce, testo):
        """Scelta dal menu: la posizione si salva subito (non serve 'Salva Medicinali')."""
        voce["posizione"] = {t: k for k, t in self.POSIZIONI_MEDICINALI}.get(testo)
        salva_dati(self.dati_completi)
        if self._ordine_medicinali()[0] == "posizione":
            self._riempi_griglia_medicinali(conserva_testi=True)

    def _scegli_posizione_medicinale(self, nome):
        """Finestrella con un pulsante per piano. Restituisce 'sotto'/'intermedio'/'sopra' oppure None."""
        scelta = {}
        win = tk.Toplevel(self.root)
        win.title("Posizione")
        win.configure(bg=COLORE_SFONDO)
        win.transient(self.root)
        win.resizable(False, False)
        tk.Label(win, text=f"Dove si trova '{nome}'?", font=self.normal_font, bg=COLORE_SFONDO).pack(
            padx=20, pady=(15, 10))
        pulsanti = tk.Frame(win, bg=COLORE_SFONDO)
        pulsanti.pack(padx=20, pady=(0, 15))

        def scegli(valore):
            scelta["valore"] = valore
            win.destroy()

        for valore, testo in self.POSIZIONI_MEDICINALI:
            tk.Button(pulsanti, text=testo, width=16, font=self.normal_font, bg="#2196F3", fg="white",
                      command=lambda v=valore: scegli(v)).pack(side=tk.LEFT, padx=4)
        tk.Button(pulsanti, text="Non indicare", width=12, font=self.normal_font,
                  command=lambda: scegli(None)).pack(side=tk.LEFT, padx=(12, 4))
        # Al centro della finestra principale
        win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_height()) // 3
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        win.grab_set()
        win.wait_window()
        return scelta.get("valore")

    def _stato_medicinale(self, voce, oggi=None):
        """(colore, testo) dello stato di un medicinale: giorni alla scadenza effettiva,
        apertura, durata. Usato dalla scheda e dal report."""
        oggi = oggi or datetime.now().date()
        effettiva, limite_apertura = self._scadenza_effettiva(voce)
        giorni = (effettiva - oggi).days
        aperto_da = (oggi - date.fromisoformat(voce["apertura"])).days if voce.get("apertura") else None
        durata = voce.get("durata_apertura")

        if limite_apertura:
            # Decide la durata dopo l'apertura (es. collirio: 28 giorni)
            fino_al = effettiva.strftime("%d-%m-%Y")
            if giorni < 0:
                colore, stato = "red", f"⚠️ DA BUTTARE\naperto da {n_giorni(aperto_da)} (dura {durata})"
            elif giorni == 0:
                colore, stato = "red", f"⚠️ Ultimo giorno di uso\ndura {durata} dopo l'apertura"
            else:
                colore = "orange" if giorni <= self.GIORNI_PREAVVISO_APERTO else "green"
                stato = f"Da usare entro {n_giorni(giorni)} (fino al {fino_al})"
                stato += f"\naperto da {n_giorni(aperto_da)}" if aperto_da else "\naperto oggi"
        else:
            if giorni < 0:
                colore, stato = "red", f"⚠️ SCADUTO da {n_giorni(abs(giorni))}"
            elif giorni == 0:
                colore, stato = "red", "⚠️ Scade oggi"
            elif giorni <= SOGLIA_GIORNI_PREAVVISO:
                colore, stato = "orange", f"⚠️ Scade tra {n_giorni(giorni)}"
            else:
                colore, stato = "green", n_giorni(giorni)
            if aperto_da is not None:
                stato += f"\naperto da {n_giorni(aperto_da)}" if aperto_da > 0 else "\naperto oggi"
            elif durata:
                stato += f"\ndopo l'apertura dura {durata}"
        return colore, stato

    def _aggiorna_stato_medicinali(self):
        """Giorni alla scadenza (tenendo conto della durata dopo l'apertura). Solo a video, nessuna notifica."""
        oggi = datetime.now().date()
        for widgets in getattr(self, "medicinali_widgets", {}).values():
            colore, stato = self._stato_medicinale(widgets["voce"], oggi)
            self._imposta_stato(widgets["label"], stato, colore)

    FILE_REPORT_MEDICINALI = "report_medicinali"  # .png e .pdf nella cartella del programma
    INGRANDIMENTO_STAMPA = 1.15  # nel PDF da stampare i caratteri sono più grandi del 15%
    # ...ma se così servirebbe un secondo foglio e con caratteri un po' più piccoli sta in uno solo,
    # si stampa su un foglio solo
    INGRANDIMENTI_PER_UN_FOGLIO = (1.1, 1.05, 1.0)

    def _righe_report_medicinali(self):
        """Righe del report nell'ordine scelto nella scheda, più il riepilogo in alto."""
        oggi = datetime.now().date()
        chiave, inverso = self._ordine_medicinali()
        posizioni = dict(self.POSIZIONI_MEDICINALI)
        righe, conteggio = [], {"red": 0, "orange": 0}
        for voce in self._medicinali_ordinati(chiave, inverso):
            colore, stato = self._stato_medicinale(voce, oggi)
            if colore in conteggio:
                conteggio[colore] += 1
            righe.append({
                "nome": voce["nome"],
                "scadenza": self._testo_scadenza_medicinale(voce),
                "apertura": data_iso_a_italiana(voce["apertura"]) if voce.get("apertura") else "",
                "durata": voce.get("durata_apertura") or "",
                "posizione": posizioni.get(voce.get("posizione"), ""),
                # "156 giorni" da solo nel report si capisce poco: "Scade tra 156 giorni"
                "stato": re.sub(r"^(\d+ giorn[oi])", r"Scade tra \1", stato.replace("⚠️ ", "")),
                "colore": colore,
            })
        n = len(righe)
        riepilogo = [(f"{n} medicinal{'e' if n == 1 else 'i'}", "gray")]
        if conteggio["red"]:
            riepilogo.append((f"{conteggio['red']} scadut{'o' if conteggio['red'] == 1 else 'i'} o da buttare", "red"))
        if conteggio["orange"]:
            riepilogo.append((f"{conteggio['orange']} in scadenza", "orange"))
        if not conteggio["red"] and not conteggio["orange"] and n:
            riepilogo.append(("tutto in regola", "green"))
        nomi_ordine = {"scadenza": "scadenza", "apertura": "data di apertura", "nome": "nome", "posizione": "posizione"}
        sottotitolo = (f"Situazione al {oggi.strftime('%d/%m/%Y')}  ·  "
                       f"in ordine di {nomi_ordine[chiave]} {'▼' if inverso else '▲'}")
        return righe, riepilogo, sottotitolo

    def report_medicinali(self):
        """Anteprima del report con i pulsanti per WhatsApp (immagine negli appunti) e per la stampa (PDF A4).

        Le spunte "Mostra lo stato", "Mostra 'Dopo apertura'" e "Mostra 'Aperto il'" tolgono o
        rimettono quelle colonne (scelte ricordate nel file dati). Se c'è spazio la tabella si
        divide in più colonne affiancate (es. solo Medicinale, Scadenza e Posizione: 2 colonne sul
        foglio verticale, 3 su quello orizzontale). "Foglio: Verticale / Orizzontale" vale per il PDF.
        """
        if not IMMAGINE_DISPONIBILE:
            messagebox.showerror("Errore", "Per creare il report serve la libreria Pillow.\n\n"
                                 "Riavvia con avvia_scadenze.bat, che la installa da sola.")
            return
        righe, riepilogo, sottotitolo = self._righe_report_medicinali()
        oggi = datetime.now().date()
        base = os.path.join(CARTELLA_PROGRAMMA, self.FILE_REPORT_MEDICINALI)
        impostazioni = self.dati_completi.setdefault("impostazioni", {})
        var_stato = tk.BooleanVar(master=self.root, value=impostazioni.get("report_mostra_stato", True))
        var_durata = tk.BooleanVar(master=self.root, value=impostazioni.get("report_mostra_durata", True))
        var_apertura = tk.BooleanVar(master=self.root, value=impostazioni.get("report_mostra_apertura", True))
        var_orizzontale = tk.BooleanVar(master=self.root, value=impostazioni.get("report_orizzontale", False))
        stato = {"immagine": None}

        def parametri():
            mostra = var_stato.get()
            # Senza stato, in alto resta solo il numero di medicinali
            return dict(oggi=oggi, sottotitolo=sottotitolo, mostra_stato=mostra,
                        mostra_durata=var_durata.get(), mostra_apertura=var_apertura.get(),
                        riepilogo=riepilogo if mostra else riepilogo[:1])

        win = tk.Toplevel(self.root)
        win.title("Report medicinali")
        win.configure(bg=COLORE_SFONDO)
        win.transient(self.root)
        barra = tk.Frame(win, bg=COLORE_SFONDO)
        barra.pack(fill=tk.X, padx=10, pady=(10, 0))
        barra_colonne = tk.Frame(win, bg=COLORE_SFONDO)
        barra_colonne.pack(fill=tk.X, padx=10, pady=(6, 0))
        lbl_msg = tk.Label(win, text="", font=self.normal_font, bg=COLORE_SFONDO, justify=tk.LEFT)
        lbl_msg.pack(anchor=tk.W, padx=10, pady=(6, 4))
        area = tk.Label(win, bg=COLORE_SFONDO)
        area.pack(padx=10, pady=(0, 10))

        def copia():
            fatto, errore = immagine_settimana.copia_immagine_negli_appunti(stato["immagine"])
            if fatto:
                lbl_msg.config(text="✅ Report copiato negli appunti: incollalo su WhatsApp con Ctrl+V", fg="#1B5E20")
            else:
                lbl_msg.config(text=f"⚠️ {errore}\nL'immagine è salvata in: {base}.png", fg="#B71C1C")

        def genera():
            immagine = immagine_settimana.crea_report_medicinali(righe, **parametri())[0]
            stato["immagine"] = immagine
            try:
                immagine.save(base + ".png")
            except OSError:
                pass
            # Anteprima rimpicciolita in modo morbido
            rapporto = min(self.root.winfo_screenheight() * 0.75 / immagine.height,
                           self.root.winfo_screenwidth() * 0.85 / immagine.width, 1.0)
            try:
                from PIL import ImageTk
                ridotta = immagine.resize((int(immagine.width * rapporto), int(immagine.height * rapporto)),
                                          immagine_settimana.Image.LANCZOS)
                foto = ImageTk.PhotoImage(ridotta, master=win)
                area.config(image=foto)
                area.image = foto
            except Exception:
                pass
            copia()  # come per gli impegni: il report è subito negli appunti

        def cambia_colonne():
            impostazioni["report_mostra_stato"] = var_stato.get()
            impostazioni["report_mostra_durata"] = var_durata.get()
            impostazioni["report_mostra_apertura"] = var_apertura.get()
            salva_dati(self.dati_completi)
            genera()

        def cambia_foglio():
            impostazioni["report_orizzontale"] = var_orizzontale.get()
            salva_dati(self.dati_completi)
            verso = "orizzontale" if var_orizzontale.get() else "verticale"
            lbl_msg.config(text=f"📄 Il PDF sarà su foglio A4 {verso}: premi «🖨️ Stampa (PDF)»", fg="#37474F")

        def stampa():
            orizzontale = var_orizzontale.get()
            pagina = immagine_settimana.pagina_report_a4(orizzontale)

            def pagine_pdf(ingrandimento):
                return immagine_settimana.crea_report_medicinali(
                    righe, larghezza=pagina["larghezza"], altezza_pagina=pagina["altezza_pagina"],
                    ingrandimento=ingrandimento, **parametri())

            pagine = pagine_pdf(self.INGRANDIMENTO_STAMPA)
            # Se per poco non sta in un foglio, caratteri un filo più piccoli (mai sotto la grandezza normale)
            if len(pagine) > 1:
                for ingrandimento in self.INGRANDIMENTI_PER_UN_FOGLIO:
                    if ingrandimento < self.INGRANDIMENTO_STAMPA:
                        prova = pagine_pdf(ingrandimento)
                        if len(prova) == 1:
                            pagine = prova
                            break
            try:
                pdf = immagine_settimana.salva_pdf_a4(pagine, base + ".pdf", orizzontale=orizzontale)
            except OSError as e:
                lbl_msg.config(text=f"⚠️ PDF non creato: {e}\n(forse è aperto in un altro programma: chiudilo e riprova)",
                               fg="#B71C1C")
                return
            try:
                os.startfile(pdf)  # apre il PDF con il programma predefinito (Windows)
                lbl_msg.config(text=f"🖨️ Si è aperto il PDF ({len(pagine)} pagin{'a' if len(pagine) == 1 else 'e'}"
                                    f" A4 {'orizzontal' if orizzontale else 'vertical'}{'e' if len(pagine) == 1 else 'i'}):"
                                    f" premi Ctrl+P per stampare.\nSalvato in: {pdf}", fg="#1B5E20")
            except (AttributeError, OSError):
                lbl_msg.config(text=f"PDF salvato in: {pdf}\nAprilo e stampalo da lì.", fg="#1B5E20")

        tk.Button(barra, text="📋 Copia per WhatsApp", command=copia, bg="#25D366", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=4)
        tk.Button(barra, text="🖨️ Stampa (PDF)", command=stampa, bg="#455A64", fg="white",
                  font=self.normal_font).pack(side=tk.LEFT, padx=4)
        tk.Label(barra, text="Foglio:", font=self.normal_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=(16, 2))
        for testo, valore in (("Verticale", False), ("Orizzontale", True)):
            tk.Radiobutton(barra, text=testo, variable=var_orizzontale, value=valore, command=cambia_foglio,
                           font=self.normal_font, bg=COLORE_SFONDO,
                           activebackground=COLORE_SFONDO).pack(side=tk.LEFT, padx=2)
        tk.Button(barra, text="Chiudi", command=win.destroy, bg="#9E9E9E", fg="white",
                  font=self.normal_font, width=10).pack(side=tk.LEFT, padx=(16, 4))
        tk.Label(barra_colonne, text="Colonne:", font=self.normal_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=(4, 2))
        for testo, variabile in (("Mostra lo stato (giorni rimasti, scaduti...)", var_stato),
                                 ("Mostra 'Dopo apertura'", var_durata),
                                 ("Mostra 'Aperto il'", var_apertura)):
            tk.Checkbutton(barra_colonne, text=testo, variable=variabile, command=cambia_colonne,
                           font=self.normal_font, bg=COLORE_SFONDO,
                           activebackground=COLORE_SFONDO).pack(side=tk.LEFT, padx=4)
        genera()

    def aggiungi_medicinale(self):
        nome = simpledialog.askstring("Nuovo Medicinale", "Nome del medicinale:")
        if not nome or not nome.strip():
            return
        testo = simpledialog.askstring("Nuovo Medicinale",
                                       "Data di scadenza (GG-MM-AAAA oppure MM-AAAA come sulla confezione):")
        if not testo:
            return
        scadenza, solo_mese = interpreta_scadenza_medicinale(testo)
        if scadenza is None:
            messagebox.showerror("Errore", "Data di scadenza non valida!\nUsa GG-MM-AAAA oppure MM-AAAA (es. 03-2027)")
            return
        testo_apertura = simpledialog.askstring(
            "Nuovo Medicinale", "Data di apertura (GG-MM-AAAA)\nLascia vuoto se la confezione è ancora chiusa:")
        apertura = None
        if testo_apertura and testo_apertura.strip():
            apertura = interpreta_data(testo_apertura, date.today())
            if apertura is None:
                messagebox.showerror("Errore", "Data di apertura non valida! Usa il formato GG-MM-AAAA")
                return
        testo_durata_risposta = simpledialog.askstring(
            "Nuovo Medicinale", "Dopo l'apertura va usato entro... (es. 28 giorni, 6 mesi, 1 anno)\n"
                                "Lascia vuoto se non è indicato sul foglietto:")
        durata = None
        if testo_durata_risposta and testo_durata_risposta.strip():
            durata = interpreta_durata(testo_durata_risposta)
            if durata is None:
                messagebox.showerror("Errore", "Durata non valida! Scrivi per esempio 28 giorni, 6 mesi o 1 anno")
                return
        posizione = self._scegli_posizione_medicinale(nome.strip())
        self.dati_completi.setdefault("medicinali", []).append({
            "nome": nome.strip(),
            "scadenza": scadenza.isoformat(),
            "solo_mese": solo_mese,
            "apertura": apertura.isoformat() if apertura else None,
            "durata_apertura": testo_durata(*durata) if durata else None,
            "posizione": posizione,
        })
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia(tab_da_aprire="medicinali")
        messagebox.showinfo("Successo", f"Medicinale '{nome.strip()}' aggiunto!")

    def salva_medicinali(self):
        """Salva le date modificate nei campi; se una è sbagliata non cambia nulla e dice quale."""
        nuove = []
        for widgets in self.medicinali_widgets.values():
            voce = widgets["voce"]
            scadenza, solo_mese = interpreta_scadenza_medicinale(widgets["entry_scadenza"].get())
            if scadenza is None:
                messagebox.showerror("Errore", f"Scadenza non valida per '{voce['nome']}'!\n\n"
                                     "Usa GG-MM-AAAA oppure MM-AAAA.\nNessuna modifica è stata salvata.")
                return
            testo_apertura = widgets["entry_apertura"].get().strip()
            apertura = None
            if testo_apertura:
                apertura = interpreta_data(testo_apertura, date.today())
                if apertura is None:
                    messagebox.showerror("Errore", f"Data di apertura non valida per '{voce['nome']}'!\n\n"
                                         "Usa GG-MM-AAAA oppure lascia vuoto.\nNessuna modifica è stata salvata.")
                    return
            testo_dur = widgets["entry_durata"].get().strip()
            durata = None
            if testo_dur:
                durata = interpreta_durata(testo_dur)
                if durata is None:
                    messagebox.showerror("Errore", f"Durata dopo l'apertura non valida per '{voce['nome']}'!\n\n"
                                         "Scrivi per esempio 28 giorni, 6 mesi, 1 anno oppure lascia vuoto.\n"
                                         "Nessuna modifica è stata salvata.")
                    return
            nuove.append((voce, scadenza, solo_mese, apertura, durata))
        for voce, scadenza, solo_mese, apertura, durata in nuove:
            voce["scadenza"] = scadenza.isoformat()
            voce["solo_mese"] = solo_mese
            voce["apertura"] = apertura.isoformat() if apertura else None
            voce["durata_apertura"] = testo_durata(*durata) if durata else None
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia(tab_da_aprire="medicinali")  # per rimettere in ordine di scadenza
        messagebox.showinfo("Successo", "Medicinali salvati!")

    def rinomina_medicinale(self, voce):
        nuovo = simpledialog.askstring("Modifica Medicinale", f"Nuovo nome per '{voce['nome']}':",
                                       initialvalue=voce["nome"])
        if not nuovo or not nuovo.strip() or nuovo.strip() == voce["nome"]:
            return
        voce["nome"] = nuovo.strip()
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia(tab_da_aprire="medicinali")

    def elimina_medicinale(self, voce):
        if not messagebox.askyesno("Conferma Eliminazione", f"Vuoi eliminare il medicinale '{voce['nome']}'?",
                                   icon="warning"):
            return
        self.dati_completi["medicinali"] = [v for v in self.dati_completi.get("medicinali", []) if v is not voce]
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia(tab_da_aprire="medicinali")

    def crea_tab_personali(self, parent):
        """Crea il tab per le scadenze personali, diviso in visite e altre scadenze."""
        scroll_frame = tk.Frame(parent, bg=COLORE_SFONDO)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        # yscrollincrement = pixel per "unità" di scroll (frecce della barra e rotellina)
        canvas = tk.Canvas(scroll_frame, bg=COLORE_SFONDO, highlightthickness=0,
                           yscrollincrement=SCROLL_PIXEL_PER_UNITA)
        self.canvas_personali = canvas
        scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(canvas, bg=COLORE_SFONDO)
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")

        def aggiorna_area_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def adatta_larghezza(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        main_frame.bind("<Configure>", aggiorna_area_scroll)
        canvas.bind("<Configure>", adatta_larghezza)

        # Scroll con la rotellina del mouse ovunque nella finestra principale
        self.root.bind_all("<MouseWheel>", self._scroll_rotellina)

        # Titolo e pulsante notifiche
        header_frame = tk.Frame(main_frame, bg=COLORE_SFONDO)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Gestione Scadenze Personali", 
                font=self.title_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=5)
        
        if GOOGLE_CALENDAR_DISPONIBILE:
            tk.Button(header_frame, text="📅 Esporta su Calendar", command=self.esporta_personali_su_calendar, 
                     bg="#4285F4", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)

            tk.Button(header_frame, text="📥 Importa da Calendar", command=self.importa_personali_da_calendar,
                     bg="#0F9D58", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)
        
        if NOTIFICHE_DISPONIBILI:
            tk.Button(header_frame, text="🔔 Controlla Scadenze", command=self.controlla_scadenze_notifiche,
                     bg="#673AB7", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)

        tk.Button(header_frame, text="🖼️ Copia immagine", command=self.copia_settimana_immagine,
                  bg="#128C7E", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)

        tk.Button(header_frame, text="📋 Copia settimana", command=self.copia_settimana,
                  bg="#25D366", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)
        
        self.scadenze_personali_widgets = {}
        
        # LEGENDA TASTI
        legenda_frame = tk.Frame(main_frame, bg=COLORE_SFONDO)
        legenda_frame.pack(fill=tk.X, pady=(0, 10))
        
        legenda_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        tk.Label(legenda_frame, text="Legenda:", font=legenda_font, bg=COLORE_SFONDO).pack(side=tk.LEFT, padx=5)
        tk.Label(legenda_frame, text="✏️ Modifica", font=self.normal_font, bg="#FFF3E0", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="✕ Cancella", font=self.normal_font, bg="#FFEBEE", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="📅 Esporta", font=self.normal_font, bg="#E3F2FD", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        
        # SEZIONE VISITE PRENOTATE
        visite_frame = tk.LabelFrame(main_frame, text="Visite Mediche prenotate", 
                                     font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        visite_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        visite_container = tk.Frame(visite_frame, bg=COLORE_SFONDO)
        visite_container.pack(fill=tk.BOTH, expand=True)

        # SEZIONE VISITE DA PRENOTARE
        visite_prenotare_frame = tk.LabelFrame(main_frame, text="Visite da prenotare entro il", 
                               font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        visite_prenotare_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        visite_prenotare_container = tk.Frame(visite_prenotare_frame, bg=COLORE_SFONDO)
        visite_prenotare_container.pack(fill=tk.BOTH, expand=True)
        
        # SEZIONE SCADENZE
        scad_frame = tk.LabelFrame(main_frame, text="Scadenze (Casa, ISEE, IMU, Documenti, Altro)", 
                                    font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        scad_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        scad_container = tk.Frame(scad_frame, bg=COLORE_SFONDO)
        scad_container.pack(fill=tk.BOTH, expand=True)

        # SEZIONE FESTE E COMPLEANNI
        feste_frame = tk.LabelFrame(main_frame, text="Feste e Compleanni",
                        font=self.title_font, bg=COLORE_SFONDO, padx=10, pady=10)
        feste_frame.pack(fill=tk.BOTH, expand=True)

        feste_container = tk.Frame(feste_frame, bg=COLORE_SFONDO)
        feste_container.pack(fill=tk.BOTH, expand=True)
        
        # Separazione visite prenotate, visite da prenotare e altre scadenze
        visite_dict = {}
        visite_da_prenotare_dict = {}
        scadenze_dict = {}
        feste_dict = {}
        
        per_sezione = {"visite": visite_dict, "da_prenotare": visite_da_prenotare_dict,
                       "feste": feste_dict, "scadenze": scadenze_dict}
        for voce, data_obj in self.dati_completi.get("scadenze_personali", {}).items():
            per_sezione[self._sezione_personale(voce, data_obj)][voce] = data_obj
        
        # Rendering VISITE
        row_visite = 0
        for voce, data_obj in sorted(visite_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(visite_container, voce, data_obj, row_visite)
            row_visite += 1
        
        # Se non ci sono visite, mostra messaggio
        if row_visite == 0:
            tk.Label(visite_container, text="Nessuna visita prenotata", 
                    font=self.normal_font, bg=COLORE_SFONDO, fg="gray").pack(pady=10)

        # Rendering VISITE DA PRENOTARE
        row_visite_prenotare = 0
        for voce, data_obj in sorted(visite_da_prenotare_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(visite_prenotare_container, voce, data_obj, row_visite_prenotare)
            row_visite_prenotare += 1

        if row_visite_prenotare == 0:
            tk.Label(visite_prenotare_container, text="Nessuna visita da prenotare", 
                    font=self.normal_font, bg=COLORE_SFONDO, fg="gray").pack(pady=10)
        
        # Rendering SCADENZE
        row_scad = 0
        for voce, data_obj in sorted(scadenze_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(scad_container, voce, data_obj, row_scad)
            row_scad += 1
        
        # Se non ci sono scadenze, mostra messaggio
        if row_scad == 0:
            tk.Label(scad_container, text="Nessuna scadenza programmata", 
                    font=self.normal_font, bg=COLORE_SFONDO, fg="gray").pack(pady=10)

        # Rendering FESTE E COMPLEANNI
        row_feste = 0
        for voce, data_obj in sorted(feste_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(feste_container, voce, data_obj, row_feste)
            row_feste += 1

        if row_feste == 0:
            tk.Label(feste_container, text="Nessuna festa o compleanno programmato",
                    font=self.normal_font, bg=COLORE_SFONDO, fg="gray").pack(pady=10)
        
        # Pulsanti di azione
        btn_frame = tk.Frame(main_frame, bg=COLORE_SFONDO)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="+ Nuova Scadenza",
             command=lambda: self.aggiungi_scadenza_personale("scadenza"),
             bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+ Nuova Visita Prenotata",
             command=lambda: self.aggiungi_scadenza_personale("visita_prenotata"),
             bg="#009688", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+ Nuova Visita da Prenotare",
             command=lambda: self.aggiungi_scadenza_personale("visita_da_prenotare"),
             bg="#FF9800", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="+ Festa o Compleanno",
             command=lambda: self.aggiungi_scadenza_personale("festa_compleanno"),
             bg="#E91E63", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Salva Scadenze Personali", command=self.salva_scadenze_personali,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
    
    def _descrizione_ricorrenza(self, ricorrenza):
        """Restituisce una breve descrizione testuale della ricorrenza, o stringa vuota."""
        if not ricorrenza or not ricorrenza.get("attiva"):
            return ""

        intervallo = ricorrenza.get("intervallo", 1)
        freq = ricorrenza.get("freq", "WEEKLY")

        if freq == "WEEKLY":
            giorni = ricorrenza.get("giorni") or []
            etichette = [lbl for lbl, cod in GIORNI_SETTIMANA if cod in giorni]
            giorni_txt = f" ({', '.join(etichette)})" if etichette else ""
            base = "ogni settimana" if intervallo == 1 else f"ogni {intervallo} settimane"
            testo = f"🔁 Si ripete {base}{giorni_txt}"
        else:
            base = "ogni mese" if intervallo == 1 else f"ogni {intervallo} mesi"
            testo = f"🔁 Si ripete {base}"

        if ricorrenza.get("fino_al"):
            testo += f" fino al {data_iso_a_italiana(ricorrenza['fino_al'])}"

        return testo

    def _dialog_ricorrenza(self, nome_scadenza, ricorrenza_attuale, data_riferimento_iso=None):
        """Apre una finestra modale per impostare la ricorrenza di una scadenza.

        Restituisce un dict {"attiva", "freq", "intervallo", "giorni", "fino_al"}
        oppure None se l'utente ha annullato.
        """
        ricorrenza_attuale = ricorrenza_attuale or {}
        risultato = {}

        win = tk.Toplevel(self.root)
        win.title(f"Ricorrenza - {nome_scadenza}")
        win.geometry("380x360")
        win.configure(bg=COLORE_SFONDO)
        win.transient(self.root)
        win.grab_set()

        var_attiva = tk.BooleanVar(value=ricorrenza_attuale.get("attiva", False))
        var_freq = tk.StringVar(value=ricorrenza_attuale.get("freq", "WEEKLY"))
        var_intervallo = tk.StringVar(value=str(ricorrenza_attuale.get("intervallo", 1)))

        giorni_default = ricorrenza_attuale.get("giorni")
        if not giorni_default and data_riferimento_iso:
            try:
                idx = datetime.strptime(data_riferimento_iso, "%Y-%m-%d").weekday()
                giorni_default = [GIORNI_SETTIMANA[idx][1]]
            except ValueError:
                giorni_default = []
        giorni_default = giorni_default or []

        vars_giorni = {cod: tk.BooleanVar(value=cod in giorni_default) for _, cod in GIORNI_SETTIMANA}

        fino_al_default = data_iso_a_italiana(ricorrenza_attuale.get("fino_al")) if ricorrenza_attuale.get("fino_al") else ""

        tk.Checkbutton(win, text="Si ripete", variable=var_attiva, font=self.normal_font,
                       bg=COLORE_SFONDO).pack(anchor=tk.W, padx=10, pady=(10, 5))

        freq_frame = tk.Frame(win, bg=COLORE_SFONDO)
        freq_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(freq_frame, text="Ripeti ogni:", bg=COLORE_SFONDO, font=self.normal_font).pack(side=tk.LEFT)
        spin_intervallo = tk.Spinbox(freq_frame, from_=1, to=30, width=4, textvariable=var_intervallo)
        spin_intervallo.pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(freq_frame, text="Settimana/e", variable=var_freq, value="WEEKLY",
                       bg=COLORE_SFONDO, font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(freq_frame, text="Mese/i", variable=var_freq, value="MONTHLY",
                       bg=COLORE_SFONDO, font=self.normal_font).pack(side=tk.LEFT, padx=5)

        giorni_frame = tk.LabelFrame(win, text="Giorni della settimana (solo per ricorrenza settimanale)",
                                     bg=COLORE_SFONDO, font=self.normal_font, padx=5, pady=5)
        giorni_frame.pack(fill=tk.X, padx=10, pady=10)
        for i, (etichetta, codice) in enumerate(GIORNI_SETTIMANA):
            tk.Checkbutton(giorni_frame, text=etichetta, variable=vars_giorni[codice],
                          bg=COLORE_SFONDO, font=self.normal_font).grid(row=0, column=i, padx=2)

        fino_frame = tk.Frame(win, bg=COLORE_SFONDO)
        fino_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(fino_frame, text="Fino al (GG-MM-AAAA, vuoto = senza fine):",
                bg=COLORE_SFONDO, font=self.normal_font).pack(anchor=tk.W)
        entry_fino_al = tk.Entry(fino_frame, font=self.normal_font, width=15)
        entry_fino_al.pack(anchor=tk.W, pady=3)
        entry_fino_al.insert(0, fino_al_default)

        def conferma():
            if not var_attiva.get():
                risultato["attiva"] = False
                win.destroy()
                return

            try:
                intervallo = int(var_intervallo.get())
                if intervallo < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Errore", "L'intervallo deve essere un numero intero positivo", parent=win)
                return

            freq = var_freq.get()
            giorni_sel = [cod for cod, var in vars_giorni.items() if var.get()]
            if freq == "WEEKLY" and not giorni_sel:
                messagebox.showerror("Errore", "Seleziona almeno un giorno della settimana", parent=win)
                return

            fino_al_txt = entry_fino_al.get().strip()
            fino_al_iso = None
            if fino_al_txt:
                try:
                    fino_al_iso = data_italiana_a_iso(fino_al_txt)
                    datetime.strptime(fino_al_iso, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Errore", "Data 'fino al' non valida! Usa GG-MM-AAAA", parent=win)
                    return

            risultato.update({
                "attiva": True,
                "freq": freq,
                "intervallo": intervallo,
                "giorni": giorni_sel if freq == "WEEKLY" else [],
                "fino_al": fino_al_iso,
            })
            win.destroy()

        def annulla():
            win.destroy()

        btn_frame = tk.Frame(win, bg=COLORE_SFONDO)
        btn_frame.pack(fill=tk.X, padx=10, pady=15)
        tk.Button(btn_frame, text="OK", command=conferma, bg="#4CAF50", fg="white",
                 font=self.normal_font, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Annulla", command=annulla, bg="#9E9E9E", fg="white",
                 font=self.normal_font, width=10).pack(side=tk.LEFT, padx=5)

        win.wait_window()
        return risultato if risultato else None

    def _crea_riga_personale(self, container, voce, data_obj, row):
        """Funzione helper per creare una riga di scadenza/visita"""
        # Gestisci sia il vecchio formato (stringa) che il nuovo (dict)
        if isinstance(data_obj, str):
            data_obj = {'data': data_obj, 'con_orario': False, 'ora_inizio': None, 'ora_fine': None}
        
        tk.Label(container, text=f"{voce}:", 
            font=self.normal_font, bg=COLORE_SFONDO, width=42, anchor=tk.W).grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
        
        entry = tk.Entry(container, font=self.normal_font, width=15)
        entry.grid(row=row, column=1, padx=5)
        entry.insert(0, data_iso_a_italiana(data_obj['data']))
        
        # Checkbox per indicare un evento senza orario
        var_tutto_giorno = tk.BooleanVar(value=not data_obj.get('con_orario', False))
        chk_orario = tk.Checkbutton(container, text="Tutto il giorno", variable=var_tutto_giorno,
                       bg=COLORE_SFONDO, font=self.normal_font,
                                   command=lambda v=voce: self.toggle_orario_personale(v))
        chk_orario.grid(row=row, column=2, padx=2)
        
        # Campi orario (inizialmente disabilitati)
        entry_inizio = tk.Entry(container, font=self.normal_font, width=8)
        entry_inizio.grid(row=row, column=3, padx=2)
        entry_inizio.insert(0, data_obj.get('ora_inizio') or "HH:MM")
        entry_inizio.config(state=tk.DISABLED if var_tutto_giorno.get() else tk.NORMAL)
        
        entry_fine = tk.Entry(container, font=self.normal_font, width=8)
        entry_fine.grid(row=row, column=4, padx=2)
        entry_fine.insert(0, data_obj.get('ora_fine') or "HH:MM")
        entry_fine.config(state=tk.DISABLED if var_tutto_giorno.get() else tk.NORMAL)
        
        label_stato = tk.Label(container, text="", 
                              font=self.normal_font, bg=COLORE_SFONDO, width=35)
        label_stato.grid(row=row, column=5, padx=10, sticky=tk.W)
        
        # Pulsante modifica nome
        btn_modifica = tk.Button(container, text="✏️", 
                                command=lambda v=voce: self.modifica_scadenza_personale(v),
                                bg="#FF9800", fg="white", width=2)
        btn_modifica.grid(row=row, column=6, padx=2)
        
        btn_elimina = tk.Button(container, text="✕", 
                               command=lambda v=voce: self.elimina_scadenza_personale(v),
                               bg="#F44336", fg="white", width=2)
        btn_elimina.grid(row=row, column=7, padx=2)
        
        # Pulsante esporta su Google Calendar
        btn_calendar = tk.Button(container, text="📅", 
                                command=lambda v=voce: self.esporta_singola_scad_personale(v),
                                bg="#4285F4", fg="white", width=2)
        btn_calendar.grid(row=row, column=8, padx=2)

        # Pulsante ricorrenza (imposta ripetizione settimanale/mensile)
        ricorrenza_attiva = bool((data_obj.get("ricorrenza") or {}).get("attiva"))
        btn_ricorrenza = tk.Button(container, text="🔁",
                                  command=lambda v=voce: self.gestisci_ricorrenza_personale(v),
                                  bg="#009688" if ricorrenza_attiva else "#B0BEC5", fg="white", width=2)
        btn_ricorrenza.grid(row=row, column=9, padx=2)
        
        self.scadenze_personali_widgets[voce] = {
            "entry": entry, 
            "label": label_stato,
            "btn_modifica": btn_modifica,
            "btn_elimina": btn_elimina,
            "btn_calendar": btn_calendar,
            "btn_ricorrenza": btn_ricorrenza,
            "chk_orario": chk_orario,
            "var_tutto_giorno": var_tutto_giorno,
            "entry_inizio": entry_inizio,
            "entry_fine": entry_fine
        }
    
    def aggiungi_scadenza_temp(self):
        """Aggiunge una nuova scadenza temporale"""
        nome = simpledialog.askstring("Nuova Scadenza", "Nome della scadenza:")
        if not nome:
            return
        
        data = simpledialog.askstring("Nuova Scadenza", "Data scadenza (GG-MM-AAAA):")
        if not data:
            return
        
        try:
            data_obj = datetime.strptime(data, "%d-%m-%Y")
            data = data_obj.strftime("%Y-%m-%d")  # Converti in formato interno
        except ValueError:
            messagebox.showerror("Errore", "Data non valida! Usa il formato GG-MM-AAAA")
            return
        
        dati = self.get_dati_veicolo()
        dati["scadenze_fisse"][nome] = data
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome}' aggiunta!")
    
    def aggiungi_scadenza_km(self):
        """Aggiunge una nuova scadenza chilometrica"""
        nome = simpledialog.askstring("Nuova Scadenza Km", "Nome del componente:")
        if not nome:
            return
        
        ultimo = simpledialog.askinteger("Nuova Scadenza Km", "Ultimo km:", minvalue=0)
        if ultimo is None:
            return
        
        prossimo = simpledialog.askinteger("Nuova Scadenza Km", "Prossimo km:", minvalue=0)
        if prossimo is None:
            return
        
        dati = self.get_dati_veicolo()
        dati["scadenze_chilometriche"][nome] = {
            "ultimo_km": ultimo,
            "prossimo_km": prossimo
        }
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome}' aggiunta!")
    
    def salva_info_veicolo(self):
        nome = self.veicolo_entry.get().strip()
        targa = self.targa_entry.get().strip().upper()
        if nome and targa:
            vecchia_chiave = self.veicolo_corrente
            nuova_chiave = f"{nome} ({targa})"
            
            dati = self.get_dati_veicolo()
            dati["nome_veicolo"] = nome
            dati["targa"] = targa
            
            if vecchia_chiave != nuova_chiave:
                self.dati_completi["veicoli"][nuova_chiave] = self.dati_completi["veicoli"].pop(vecchia_chiave)
                self.veicolo_corrente = nuova_chiave
                self.dati_completi["veicolo_selezionato"] = nuova_chiave
            
            salva_dati(self.dati_completi)
            self.ricarica_interfaccia()
            messagebox.showinfo("Successo", "Informazioni veicolo salvate!")
        else:
            messagebox.showerror("Errore", "Inserisci nome veicolo e targa")
    
    def aggiorna_km(self):
        try:
            nuovo_km = int(self.km_entry.get())
            dati = self.get_dati_veicolo()
            dati["km_attuali"] = nuovo_km
            salva_dati(self.dati_completi)
            self.aggiorna_visualizzazione()
            messagebox.showinfo("Successo", f"Chilometraggio aggiornato a {nuovo_km} km")
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido per i km")
    
    def salva_scadenze_temp(self):
        """Salva le date del veicolo; se una è sbagliata non cambia nulla e dice quale."""
        dati = self.get_dati_veicolo()
        nuove = {}
        for voce, widgets in self.scadenze_temp_widgets.items():
            # Converte da formato italiano (GG-MM-AAAA) a ISO (YYYY-MM-DD)
            data_iso = data_italiana_a_iso(widgets["entry"].get().strip())
            try:
                datetime.strptime(data_iso, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Errore", f"Data non valida in '{voce}'!\n\nUsa il formato GG-MM-AAAA.\n"
                                     "Nessuna modifica è stata salvata.")
                return
            nuove[voce] = data_iso  # Salva in formato ISO
        dati["scadenze_fisse"].update(nuove)
        salva_dati(self.dati_completi)
        self.aggiorna_visualizzazione()
        messagebox.showinfo("Successo", "Scadenze temporali salvate!")
    
    def salva_scadenze_km(self):
        try:
            dati = self.get_dati_veicolo()
            for voce, widgets in self.scadenze_km_widgets.items():
                ultimo = int(widgets["ultimo"].get())
                prossimo = int(widgets["prossimo"].get())
                dati["scadenze_chilometriche"][voce] = {
                    "ultimo_km": ultimo,
                    "prossimo_km": prossimo
                }
            salva_dati(self.dati_completi)
            self.aggiorna_visualizzazione()
            messagebox.showinfo("Successo", "Scadenze chilometriche salvate!")
        except ValueError:
            messagebox.showerror("Errore", "Inserisci numeri validi per i chilometri")
    
    def modifica_scadenza_temp(self, nome_scadenza):
        """Modifica il nome di una scadenza temporale"""
        nuovo_nome = simpledialog.askstring(
            "Modifica Scadenza Temporale",
            f"Nuovo nome per '{nome_scadenza}':",
            initialvalue=nome_scadenza
        )
        
        if not nuovo_nome or nuovo_nome == nome_scadenza:
            return
        
        dati = self.get_dati_veicolo()
        
        # Controlla se il nuovo nome esiste già
        if nuovo_nome in dati["scadenze_fisse"]:
            messagebox.showerror("Errore", f"Una scadenza con il nome '{nuovo_nome}' esiste già!")
            return
        
        # Sposta la scadenza dal vecchio nome al nuovo
        dati["scadenze_fisse"][nuovo_nome] = dati["scadenze_fisse"].pop(nome_scadenza)
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza rinominata da '{nome_scadenza}' a '{nuovo_nome}'!")
    
    def elimina_scadenza_temp(self, nome_scadenza):
        """Elimina una scadenza temporale"""
        conferma = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Vuoi eliminare la scadenza '{nome_scadenza}'?",
            icon='warning'
        )
        
        if not conferma:
            return
        
        dati = self.get_dati_veicolo()
        del dati["scadenze_fisse"][nome_scadenza]
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome_scadenza}' eliminata!")
    
    def modifica_scadenza_km(self, nome_scadenza):
        """Modifica il nome di una scadenza chilometrica"""
        nuovo_nome = simpledialog.askstring(
            "Modifica Scadenza Chilometrica",
            f"Nuovo nome per '{nome_scadenza}':",
            initialvalue=nome_scadenza
        )
        
        if not nuovo_nome or nuovo_nome == nome_scadenza:
            return
        
        dati = self.get_dati_veicolo()
        
        # Controlla se il nuovo nome esiste già
        if nuovo_nome in dati["scadenze_chilometriche"]:
            messagebox.showerror("Errore", f"Una scadenza con il nome '{nuovo_nome}' esiste già!")
            return
        
        # Sposta la scadenza dal vecchio nome al nuovo
        dati["scadenze_chilometriche"][nuovo_nome] = dati["scadenze_chilometriche"].pop(nome_scadenza)
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza rinominata da '{nome_scadenza}' a '{nuovo_nome}'!")
    
    def elimina_scadenza_km(self, nome_scadenza):
        """Elimina una scadenza chilometrica"""
        conferma = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Vuoi eliminare la scadenza '{nome_scadenza}'?",
            icon='warning'
        )
        
        if not conferma:
            return
        
        dati = self.get_dati_veicolo()
        del dati["scadenze_chilometriche"][nome_scadenza]
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome_scadenza}' eliminata!")
    
    def aggiungi_scadenza_personale(self, tipo="scadenza"):
        """Aggiunge una nuova scadenza personale, visita, festa o compleanno."""
        if tipo == "visita_prenotata":
            titolo = "Nuova Visita Prenotata"
            nome_base = simpledialog.askstring(
                titolo,
                "Nome visita (es: Visita cardiologica, Controllo oculistico):"
            )
            if not nome_base:
                return
            nome_finale = nome_base.strip()
            prompt_data = "Data visita (GG-MM-AAAA):"
        elif tipo == "visita_da_prenotare":
            titolo = "Nuova Visita da Prenotare"
            nome_base = simpledialog.askstring(
                titolo,
                "Nome visita da prenotare (es: Visita cardiologica, Controllo oculistico):"
            )
            if not nome_base:
                return
            nome_finale = f"{nome_base.strip()} da prenotare"
            prompt_data = "Da prenotare entro il (GG-MM-AAAA):"
        elif tipo == "festa_compleanno":
            titolo = "Nuova Festa o Compleanno"
            nome_finale = simpledialog.askstring(
                titolo,
                "Nome della festa o del compleanno (es: Compleanno Marco, Festa Ludovica):"
            )
            if not nome_finale:
                return
            nome_finale = nome_finale.strip()
            prompt_data = "Data della festa o del compleanno (GG-MM-AAAA):"
        else:
            titolo = "Nuova Scadenza"
            nome_finale = simpledialog.askstring(
                titolo,
                "Nome della scadenza (es: IMU, ISEE, Passaporto):"
            )
            if not nome_finale:
                return
            nome_finale = nome_finale.strip()
            prompt_data = "Data scadenza (GG-MM-AAAA):"

        data = simpledialog.askstring(titolo, prompt_data)
        if not data:
            return

        try:
            data_obj = datetime.strptime(data, "%d-%m-%Y")
            data = data_obj.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Errore", "Data non valida! Usa il formato GG-MM-AAAA")
            return

        nome_finale = self._nome_personale_univoco(nome_finale)
        self.dati_completi["scadenze_personali"][nome_finale] = {
            "data": data,
            "con_orario": False,
            "ora_inizio": None,
            "ora_fine": None
        }
        # La categoria tiene la voce nella sua sezione anche se il nome non contiene "visita"/"compleanno"
        categoria = {"visita_prenotata": "visita_prenotata", "visita_da_prenotare": "visita_da_prenotare",
                     "festa_compleanno": "festa_compleanno"}.get(tipo)
        if categoria:
            self.dati_completi["scadenze_personali"][nome_finale]["categoria"] = categoria
        salva_dati(self.dati_completi)

        if messagebox.askyesno("Ricorrenza", f"'{nome_finale}' si ripete nel tempo (es. ogni settimana)?"):
            ricorrenza = self._dialog_ricorrenza(nome_finale, None, data)
            if ricorrenza is not None:
                self.dati_completi["scadenze_personali"][nome_finale]["ricorrenza"] = ricorrenza
                salva_dati(self.dati_completi)

        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome_finale}' aggiunta!")
    
    def modifica_scadenza_personale(self, nome_scadenza):
        """Modifica il nome di una scadenza personale"""
        nuovo_nome = simpledialog.askstring(
            "Modifica Scadenza",
            f"Nuovo nome per '{nome_scadenza}':",
            initialvalue=nome_scadenza
        )
        
        if not nuovo_nome or nuovo_nome == nome_scadenza:
            return
        
        # Controlla se il nuovo nome esiste già
        if nuovo_nome in self.dati_completi["scadenze_personali"]:
            messagebox.showerror("Errore", f"Una scadenza con il nome '{nuovo_nome}' esiste già!")
            return
        
        # Sposta la scadenza dal vecchio nome al nuovo
        self.dati_completi["scadenze_personali"][nuovo_nome] = self.dati_completi["scadenze_personali"].pop(nome_scadenza)
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza rinominata da '{nome_scadenza}' a '{nuovo_nome}'!")
    
    def gestisci_ricorrenza_personale(self, nome_scadenza):
        """Apre il dialogo di ricorrenza e salva la nuova configurazione per la scadenza."""
        voce = self.dati_completi["scadenze_personali"].get(nome_scadenza)
        if isinstance(voce, str):
            voce = {'data': voce, 'con_orario': False, 'ora_inizio': None, 'ora_fine': None}
            self.dati_completi["scadenze_personali"][nome_scadenza] = voce

        ricorrenza_attuale = voce.get("ricorrenza")
        nuova_ricorrenza = self._dialog_ricorrenza(nome_scadenza, ricorrenza_attuale, voce.get("data"))

        if nuova_ricorrenza is None:
            return

        voce["ricorrenza"] = nuova_ricorrenza
        salva_dati(self.dati_completi)
        self.ricarica_interfaccia()

    def elimina_scadenza_personale(self, nome_scadenza):
        """Elimina una scadenza personale"""
        conferma = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Vuoi eliminare la scadenza '{nome_scadenza}'?",
            icon='warning'
        )
        
        if not conferma:
            return
        
        del self.dati_completi["scadenze_personali"][nome_scadenza]
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome_scadenza}' eliminata!")
    
    def salva_scadenze_personali(self):
        """Salva le modifiche alle scadenze personali con orari opzionali.

        Controlla prima tutte le righe: se una è sbagliata non cambia nulla e dice quale.
        Mantiene gli altri campi della voce (ricorrenza, categoria, ...).
        """
        nuove = {}
        for voce, widgets in self.scadenze_personali_widgets.items():
            try:
                # Converte da formato italiano (GG-MM-AAAA) a ISO (YYYY-MM-DD)
                data_iso = data_italiana_a_iso(widgets["entry"].get().strip())
                datetime.strptime(data_iso, "%Y-%m-%d")

                con_orario = not widgets["var_tutto_giorno"].get()
                ora_inizio = ora_fine = None
                if con_orario:
                    ora_inizio = widgets["entry_inizio"].get().strip()
                    ora_fine = widgets["entry_fine"].get().strip()
                    if ora_inizio in ("", "HH:MM"):
                        ora_inizio = None
                    if ora_fine in ("", "HH:MM"):
                        ora_fine = None
                    # Valida il formato HH:MM
                    if ora_inizio:
                        datetime.strptime(ora_inizio, "%H:%M")
                    if ora_fine:
                        datetime.strptime(ora_fine, "%H:%M")
            except ValueError:
                messagebox.showerror("Errore", f"Formato non valido in '{voce}'!\n\n"
                                     "Date: GG-MM-AAAA\nOrari: HH:MM\n\nNessuna modifica è stata salvata.")
                return

            precedente = self.dati_completi["scadenze_personali"].get(voce)
            voce_nuova = dict(precedente) if isinstance(precedente, dict) else {}
            voce_nuova.update({
                "data": data_iso,  # Salva in formato ISO
                "con_orario": con_orario,
                "ora_inizio": ora_inizio,
                "ora_fine": ora_fine,
            })
            voce_nuova.setdefault("ricorrenza", None)
            nuove[voce] = voce_nuova

        self.dati_completi["scadenze_personali"].update(nuove)
        salva_dati(self.dati_completi)
        self.aggiorna_visualizzazione()
        messagebox.showinfo("Successo", "Scadenze personali salvate!")

    def aggiorna_visualizzazione(self):
        oggi = datetime.now().date()
        dati = self.get_dati_veicolo()
        km_auto = dati["km_attuali"]
        
        for voce, widgets in self.scadenze_temp_widgets.items():
            data_str = dati["scadenze_fisse"][voce]
            data_scadenza = datetime.strptime(data_str, "%Y-%m-%d").date()
            giorni_rimasti = (data_scadenza - oggi).days
            
            if giorni_rimasti < 0:
                colore = "red"
                stato = f"⚠️ ERRORE: SCADUTO da {abs(giorni_rimasti)} giorni!"
            elif giorni_rimasti <= SOGLIA_GIORNI_PREAVVISO:
                colore = "orange"
                stato = f"⚠️ {giorni_rimasti} giorni (In scadenza)"
            else:
                colore = "green"
                stato = f"{giorni_rimasti} giorni"
            
            self._imposta_stato(widgets["label"], stato, colore)
        
        for voce, widgets in self.scadenze_km_widgets.items():
            info = dati["scadenze_chilometriche"][voce]
            km_residui = info["prossimo_km"] - km_auto
            
            if km_residui <= 0:
                colore = "red"
                stato = f"⚠️ ERRORE: SUPERATO di {abs(km_residui)} km!"
            elif km_residui <= SOGLIA_KM_PREAVVISO:
                colore = "orange"
                stato = f"⚠️ {km_residui} km (Attenzione!)"
            else:
                colore = "green"
                stato = f"{km_residui} km"
            
            self._imposta_stato(widgets["label"], stato, colore)
        
        # Aggiorna scadenze personali
        for voce, widgets in self.scadenze_personali_widgets.items():
            data_obj = self.dati_completi["scadenze_personali"].get(voce, {})
            if isinstance(data_obj, str):
                data_obj = {'data': data_obj, 'con_orario': False, 'ora_inizio': None, 'ora_fine': None}
            
            data_str = data_obj.get('data', '')
            data_iniziale = datetime.strptime(data_str, "%Y-%m-%d").date()
            data_scadenza = prossima_occorrenza(
                data_iniziale, data_obj.get("ricorrenza"), oggi
            )
            if data_scadenza is None:
                self._imposta_stato(widgets["label"], "Ricorrenza terminata", "gray")
                continue
            giorni_rimasti = (data_scadenza - oggi).days
            
            if giorni_rimasti < 0:
                colore = "red"
                stato = f"⚠️ ERRORE: SCADUTO da {abs(giorni_rimasti)} giorni!"
            elif giorni_rimasti <= SOGLIA_GIORNI_PREAVVISO:
                colore = "orange"
                stato = f"⚠️ {giorni_rimasti} giorni (In scadenza)"
            else:
                colore = "green"
                stato = f"{giorni_rimasti} giorni"
            
            # Aggiungi orario se presente
            if data_obj.get('con_orario') and data_obj.get('ora_inizio'):
                stato += f" - {data_obj['ora_inizio']}"
                if data_obj.get('ora_fine'):
                    stato += f" a {data_obj['ora_fine']}"

            # Aggiungi indicazione di ricorrenza se presente
            descrizione_ricorrenza = self._descrizione_ricorrenza(data_obj.get("ricorrenza"))
            if descrizione_ricorrenza:
                stato += f"\n{descrizione_ricorrenza}"

            self._imposta_stato(widgets["label"], stato, colore)


        # Medicinali: giorni alla scadenza ed eventuale apertura (solo a video, nessuna notifica)
        self._aggiorna_stato_medicinali()

if __name__ == "__main__":
    inizializza_db()
    root = tk.Tk()
    app = ScadenzeApp(root)
    root.mainloop()
