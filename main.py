import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont

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

# Configurazione soglie di avviso
SOGLIA_KM_PREAVVISO = 3500
SOGLIA_GIORNI_PREAVVISO = 30

DB_FILE = "stato_veicolo.json"


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


def salva_dati(dati):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4)


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


class ScadenzeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestione Scadenze - Veicoli e Personali")
        self.root.geometry("1300x800")
        self.root.configure(bg="#f0f0f0")
        
        self.title_font = tkfont.Font(family="Helvetica", size=14, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=10)
        
        self.dati_completi = carica_dati()
        
        # Migrazione vecchio formato se necessario
        if "veicoli" not in self.dati_completi:
            self.migra_vecchio_formato()
        
        # Aggiungi scadenze_personali se non esistono
        if "scadenze_personali" not in self.dati_completi:
            self.dati_completi["scadenze_personali"] = {}
            salva_dati(self.dati_completi)
        
        self.veicolo_corrente = self.dati_completi.get("veicolo_selezionato", list(self.dati_completi["veicoli"].keys())[0])
        
        self.crea_interfaccia()
        self.aggiorna_visualizzazione()
    
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
        self.ricarica_interfaccia()
    
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
            self.dati_completi["scadenze_personali"][nome_finale] = {
                "data": data_evento,
                "con_orario": con_orario,
                "ora_inizio": ora_inizio,
                "ora_fine": ora_fine,
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
        else:
            data_scadenza = data_obj.get('data', '')
            orario_inizio = data_obj.get('ora_inizio') if data_obj.get('con_orario') else None
            orario_fine = data_obj.get('ora_fine') if data_obj.get('con_orario') else None
        
        # Determina il tipo e il nome dell'evento
        if "Visita" in nome_scadenza:
            tipo_scadenza = "Visita"
            # Rimuovi "Visita " dal nome per l'export (il prefisso viene aggiunto da esporta_singola_scadenza)
            nome_evento = nome_scadenza.replace("Visita ", "", 1)
        else:
            tipo_scadenza = "Scadenza"
            nome_evento = nome_scadenza
        
        successo, risultato = google_calendar.esporta_singola_scadenza(
            nome_scadenza=nome_evento,
            data_scadenza=data_scadenza,
            tipo_scadenza=tipo_scadenza,
            veicolo="",
            ora_inizio=orario_inizio,
            ora_fine=orario_fine
        )
        
        if successo:
            messagebox.showinfo("Esportazione Completata", risultato)
        else:
            messagebox.showerror("Errore Esportazione", risultato)
    
    def ricarica_interfaccia(self):
        """Ricarica l'interfaccia con i dati del veicolo corrente"""
        # Distruggi tutti i widget
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ricrea l'interfaccia
        self.crea_interfaccia()
        self.aggiorna_visualizzazione()
    
    def crea_interfaccia(self):
        # Crea Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Veicoli
        tab_veicoli = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(tab_veicoli, text="🚗 Veicoli")
        
        # Tab 2: Scadenze Personali
        tab_personali = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(tab_personali, text="📋 Scadenze Personali")
        
        # Crea contenuto tab veicoli
        self.crea_tab_veicoli(tab_veicoli)
        
        # Crea contenuto tab scadenze personali
        self.crea_tab_personali(tab_personali)
    
    def crea_tab_veicoli(self, parent):
        """Crea il tab per la gestione veicoli"""
        main_frame = tk.Frame(parent, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # SELEZIONE VEICOLO
        sel_frame = tk.Frame(main_frame, bg="#f0f0f0")
        sel_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(sel_frame, text="Seleziona Veicolo:", font=self.title_font, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
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
                                    font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(info_frame, text="Nome Veicolo:", font=self.normal_font, bg="#f0f0f0").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.veicolo_entry = tk.Entry(info_frame, font=self.normal_font, width=20)
        self.veicolo_entry.grid(row=0, column=1, padx=5)
        self.veicolo_entry.insert(0, dati.get("nome_veicolo", "Veicolo"))
        
        tk.Label(info_frame, text="Targa:", font=self.normal_font, bg="#f0f0f0").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.targa_entry = tk.Entry(info_frame, font=self.normal_font, width=15)
        self.targa_entry.grid(row=0, column=3, padx=5)
        self.targa_entry.insert(0, dati.get("targa", "XX000XX"))
        
        tk.Button(info_frame, text="Salva Info", command=self.salva_info_veicolo, 
                 bg="#9C27B0", fg="white", font=self.normal_font).grid(row=0, column=4, padx=5)
        
        # SEZIONE KM ATTUALI
        km_frame = tk.LabelFrame(main_frame, text="Chilometraggio Attuale", 
                                  font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        km_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(km_frame, text="Km Attuali:", font=self.normal_font, bg="#f0f0f0").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.km_entry = tk.Entry(km_frame, font=self.normal_font, width=15)
        self.km_entry.grid(row=0, column=1, padx=5)
        self.km_entry.insert(0, str(dati["km_attuali"]))
        
        tk.Button(km_frame, text="Aggiorna Km", command=self.aggiorna_km, 
                 bg="#4CAF50", fg="white", font=self.normal_font).grid(row=0, column=2, padx=5)
        
        # LEGENDA TASTI
        legenda_frame = tk.Frame(main_frame, bg="#f0f0f0")
        legenda_frame.pack(fill=tk.X, pady=(10, 5))
        
        legenda_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        tk.Label(legenda_frame, text="Legenda:", font=legenda_font, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        tk.Label(legenda_frame, text="✏️ Modifica", font=self.normal_font, bg="#FFF3E0", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="✕ Elimina", font=self.normal_font, bg="#FFEBEE", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="📅 Esporta", font=self.normal_font, bg="#E3F2FD", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        
        # SEZIONE SCADENZE TEMPORALI
        temp_frame = tk.LabelFrame(main_frame, text="Scadenze Temporali", 
                                    font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        temp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.temp_container = tk.Frame(temp_frame, bg="#f0f0f0")
        self.temp_container.pack(fill=tk.BOTH, expand=True)
        
        self.scadenze_temp_widgets = {}
        row = 0
        for voce, data in sorted(dati["scadenze_fisse"].items(), key=lambda x: x[1]):
            tk.Label(self.temp_container, text=f"{voce}:", font=self.normal_font, bg="#f0f0f0").grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            entry = tk.Entry(self.temp_container, font=self.normal_font, width=15)
            entry.grid(row=row, column=1, padx=5)
            entry.insert(0, data_iso_a_italiana(data))
            label_stato = tk.Label(self.temp_container, text="", font=self.normal_font, bg="#f0f0f0", width=30)
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
        
        btn_frame_temp = tk.Frame(temp_frame, bg="#f0f0f0")
        btn_frame_temp.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame_temp, text="+ Nuova Scadenza", command=self.aggiungi_scadenza_temp,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_temp, text="Salva Scadenze Temporali", command=self.salva_scadenze_temp,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        # SEZIONE SCADENZE CHILOMETRICHE
        km_manu_frame = tk.LabelFrame(main_frame, text="Manutenzione Chilometrica", 
                                       font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        km_manu_frame.pack(fill=tk.BOTH, expand=True)
        
        self.km_container = tk.Frame(km_manu_frame, bg="#f0f0f0")
        self.km_container.pack(fill=tk.BOTH, expand=True)
        
        self.scadenze_km_widgets = {}
        row = 0
        tk.Label(self.km_container, text="Componente", font=self.title_font, bg="#f0f0f0").grid(row=row, column=0, pady=5)
        tk.Label(self.km_container, text="Ultimo Km", font=self.title_font, bg="#f0f0f0").grid(row=row, column=1, pady=5)
        tk.Label(self.km_container, text="Prossimo Km", font=self.title_font, bg="#f0f0f0").grid(row=row, column=2, pady=5)
        tk.Label(self.km_container, text="Km Residui", font=self.title_font, bg="#f0f0f0").grid(row=row, column=3, pady=5)
        tk.Label(self.km_container, text="Azioni", font=self.title_font, bg="#f0f0f0").grid(row=row, column=4, pady=5)
        row += 1
        
        for voce, info in sorted(dati["scadenze_chilometriche"].items(), key=lambda x: x[1]["prossimo_km"] - dati["km_attuali"]):
            tk.Label(self.km_container, text=f"{voce}:", font=self.normal_font, bg="#f0f0f0").grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            
            ultimo_entry = tk.Entry(self.km_container, font=self.normal_font, width=12)
            ultimo_entry.grid(row=row, column=1, padx=5)
            ultimo_entry.insert(0, str(info["ultimo_km"]))
            
            prossimo_entry = tk.Entry(self.km_container, font=self.normal_font, width=12)
            prossimo_entry.grid(row=row, column=2, padx=5)
            prossimo_entry.insert(0, str(info["prossimo_km"]))
            
            label_residui = tk.Label(self.km_container, text="", font=self.normal_font, bg="#f0f0f0", width=25)
            label_residui.grid(row=row, column=3, padx=5)
            
            # Frame per pulsanti modifica/elimina/esporta
            btn_frame_azioni = tk.Frame(self.km_container, bg="#f0f0f0")
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
        
        btn_frame_km = tk.Frame(km_manu_frame, bg="#f0f0f0")
        btn_frame_km.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame_km, text="+ Nuova Scadenza Km", command=self.aggiungi_scadenza_km,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_km, text="Salva Scadenze Chilometriche", command=self.salva_scadenze_km,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
    
    def toggle_orario_personale(self, voce):
        """Abilita/disabilita i campi orario quando il checkbox viene cliccato"""
        if voce in self.scadenze_personali_widgets:
            widgets = self.scadenze_personali_widgets[voce]
            stato = tk.NORMAL if widgets["var_orario"].get() else tk.DISABLED
            widgets["entry_inizio"].config(state=stato)
            widgets["entry_fine"].config(state=stato)

    def _is_visita_personale(self, voce):
        """Determina se una voce personale appartiene alle visite mediche."""
        voce_lower = voce.lower()
        return "visita" in voce_lower or "medic" in voce_lower

    def _is_visita_da_prenotare(self, voce):
        """Riconosce le visite ancora da prenotare in base al nome della voce."""
        voce_lower = voce.lower()
        return "prenotare" in voce_lower or "da prenotare" in voce_lower
    
    def crea_tab_personali(self, parent):
        """Crea il tab per le scadenze personali, diviso in visite e altre scadenze."""
        main_frame = tk.Frame(parent, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titolo e pulsante notifiche
        header_frame = tk.Frame(main_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Gestione Scadenze Personali", 
                font=self.title_font, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        if GOOGLE_CALENDAR_DISPONIBILE:
            tk.Button(header_frame, text="📅 Esporta su Calendar", command=self.esporta_personali_su_calendar, 
                     bg="#4285F4", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)

            tk.Button(header_frame, text="📥 Importa da Calendar", command=self.importa_personali_da_calendar,
                     bg="#0F9D58", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)
        
        if NOTIFICHE_DISPONIBILI:
            tk.Button(header_frame, text="🔔 Controlla Scadenze", command=self.controlla_scadenze_notifiche, 
                     bg="#673AB7", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)
        
        self.scadenze_personali_widgets = {}
        
        # LEGENDA TASTI
        legenda_frame = tk.Frame(main_frame, bg="#f0f0f0")
        legenda_frame.pack(fill=tk.X, pady=(0, 10))
        
        legenda_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        tk.Label(legenda_frame, text="Legenda:", font=legenda_font, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        tk.Label(legenda_frame, text="✏️ Modifica", font=self.normal_font, bg="#FFF3E0", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="✕ Cancella", font=self.normal_font, bg="#FFEBEE", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        tk.Label(legenda_frame, text="📅 Esporta", font=self.normal_font, bg="#E3F2FD", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        
        # SEZIONE VISITE PRENOTATE
        visite_frame = tk.LabelFrame(main_frame, text="Visite Mediche prenotate", 
                                     font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        visite_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        visite_container = tk.Frame(visite_frame, bg="#f0f0f0")
        visite_container.pack(fill=tk.BOTH, expand=True)

        # SEZIONE VISITE DA PRENOTARE
        visite_prenotare_frame = tk.LabelFrame(main_frame, text="Visite da prenotare entro il", 
                               font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        visite_prenotare_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        visite_prenotare_container = tk.Frame(visite_prenotare_frame, bg="#f0f0f0")
        visite_prenotare_container.pack(fill=tk.BOTH, expand=True)
        
        # SEZIONE SCADENZE
        scad_frame = tk.LabelFrame(main_frame, text="Scadenze (Casa, ISEE, Documenti, Altro)", 
                                    font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        scad_frame.pack(fill=tk.BOTH, expand=True)
        
        scad_container = tk.Frame(scad_frame, bg="#f0f0f0")
        scad_container.pack(fill=tk.BOTH, expand=True)
        
        # Separazione visite prenotate, visite da prenotare e altre scadenze
        visite_dict = {}
        visite_da_prenotare_dict = {}
        scadenze_dict = {}
        
        for voce, data_obj in self.dati_completi.get("scadenze_personali", {}).items():
            if self._is_visita_personale(voce) and self._is_visita_da_prenotare(voce):
                visite_da_prenotare_dict[voce] = data_obj
            elif self._is_visita_personale(voce):
                visite_dict[voce] = data_obj
            else:
                scadenze_dict[voce] = data_obj
        
        # Rendering VISITE
        row_visite = 0
        for voce, data_obj in sorted(visite_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(visite_container, voce, data_obj, row_visite)
            row_visite += 1
        
        # Se non ci sono visite, mostra messaggio
        if row_visite == 0:
            tk.Label(visite_container, text="Nessuna visita prenotata", 
                    font=self.normal_font, bg="#f0f0f0", fg="gray").pack(pady=10)

        # Rendering VISITE DA PRENOTARE
        row_visite_prenotare = 0
        for voce, data_obj in sorted(visite_da_prenotare_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(visite_prenotare_container, voce, data_obj, row_visite_prenotare)
            row_visite_prenotare += 1

        if row_visite_prenotare == 0:
            tk.Label(visite_prenotare_container, text="Nessuna visita da prenotare", 
                    font=self.normal_font, bg="#f0f0f0", fg="gray").pack(pady=10)
        
        # Rendering SCADENZE
        row_scad = 0
        for voce, data_obj in sorted(scadenze_dict.items(), key=lambda x: x[1]['data'] if isinstance(x[1], dict) else x[1]):
            self._crea_riga_personale(scad_container, voce, data_obj, row_scad)
            row_scad += 1
        
        # Se non ci sono scadenze, mostra messaggio
        if row_scad == 0:
            tk.Label(scad_container, text="Nessuna scadenza programmata", 
                    font=self.normal_font, bg="#f0f0f0", fg="gray").pack(pady=10)
        
        # Pulsanti di azione
        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="+ Nuova Scadenza Personale", command=self.aggiungi_scadenza_personale,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Salva Scadenze Personali", command=self.salva_scadenze_personali,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
    
    def _crea_riga_personale(self, container, voce, data_obj, row):
        """Funzione helper per creare una riga di scadenza/visita"""
        # Gestisci sia il vecchio formato (stringa) che il nuovo (dict)
        if isinstance(data_obj, str):
            data_obj = {'data': data_obj, 'con_orario': False, 'ora_inizio': None, 'ora_fine': None}
        
        tk.Label(container, text=f"{voce}:", 
                font=self.normal_font, bg="#f0f0f0", width=28, anchor=tk.W).grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
        
        entry = tk.Entry(container, font=self.normal_font, width=15)
        entry.grid(row=row, column=1, padx=5)
        entry.insert(0, data_iso_a_italiana(data_obj['data']))
        
        # Checkbox per abilitare orario
        var_orario = tk.BooleanVar(value=data_obj.get('con_orario', False))
        chk_orario = tk.Checkbutton(container, text="⏰", variable=var_orario, 
                                   bg="#f0f0f0", font=self.normal_font, width=2,
                                   command=lambda v=voce: self.toggle_orario_personale(v))
        chk_orario.grid(row=row, column=2, padx=2)
        
        # Campi orario (inizialmente disabilitati)
        entry_inizio = tk.Entry(container, font=self.normal_font, width=8)
        entry_inizio.grid(row=row, column=3, padx=2)
        entry_inizio.insert(0, data_obj.get('ora_inizio') or "HH:MM")
        entry_inizio.config(state=tk.NORMAL if data_obj.get('con_orario') else tk.DISABLED)
        
        entry_fine = tk.Entry(container, font=self.normal_font, width=8)
        entry_fine.grid(row=row, column=4, padx=2)
        entry_fine.insert(0, data_obj.get('ora_fine') or "HH:MM")
        entry_fine.config(state=tk.NORMAL if data_obj.get('con_orario') else tk.DISABLED)
        
        label_stato = tk.Label(container, text="", 
                              font=self.normal_font, bg="#f0f0f0", width=35)
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
        
        self.scadenze_personali_widgets[voce] = {
            "entry": entry, 
            "label": label_stato,
            "btn_modifica": btn_modifica,
            "btn_elimina": btn_elimina,
            "btn_calendar": btn_calendar,
            "chk_orario": chk_orario,
            "var_orario": var_orario,
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
        try:
            dati = self.get_dati_veicolo()
            for voce, widgets in self.scadenze_temp_widgets.items():
                data_str = widgets["entry"].get()
                # Converte da formato italiano (GG-MM-AAAA) a ISO (YYYY-MM-DD)
                data_iso = data_italiana_a_iso(data_str)
                datetime.strptime(data_iso, "%Y-%m-%d")
                dati["scadenze_fisse"][voce] = data_iso  # Salva in formato ISO
            salva_dati(self.dati_completi)
            self.aggiorna_visualizzazione()
            messagebox.showinfo("Successo", "Scadenze temporali salvate!")
        except ValueError:
            messagebox.showerror("Errore", "Usa il formato GG-MM-AAAA per le date")
    
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
    
    def aggiungi_scadenza_personale(self):
        """Aggiunge una nuova scadenza personale"""
        nome = simpledialog.askstring("Nuova Scadenza Personale", 
                                      "Nome della scadenza (es: IMU, ISEE, Passaporto, Visita da prenotare):")
        if not nome:
            return
        
        data = simpledialog.askstring("Nuova Scadenza Personale", 
                                      "Data scadenza (GG-MM-AAAA):")
        if not data:
            return
        
        try:
            data_obj = datetime.strptime(data, "%d-%m-%Y")
            data = data_obj.strftime("%Y-%m-%d")  # Converti in formato interno
        except ValueError:
            messagebox.showerror("Errore", "Data non valida! Usa il formato AAAA-MM-GG")
            return
        
        self.dati_completi["scadenze_personali"][nome] = {
            "data": data,
            "con_orario": False,
            "ora_inizio": None,
            "ora_fine": None
        }
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome}' aggiunta!")
    
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
        """Salva le modifiche alle scadenze personali con orari opzionali"""
        try:
            for voce, widgets in self.scadenze_personali_widgets.items():
                data_str = widgets["entry"].get()
                # Converte da formato italiano (GG-MM-AAAA) a ISO (YYYY-MM-DD)
                data_iso = data_italiana_a_iso(data_str)
                datetime.strptime(data_iso, "%Y-%m-%d")
                
                con_orario = widgets["var_orario"].get()
                ora_inizio = None
                ora_fine = None
                
                if con_orario:
                    ora_inizio = widgets["entry_inizio"].get().strip()
                    ora_fine = widgets["entry_fine"].get().strip()
                    if ora_inizio == "HH:MM":
                        ora_inizio = None
                    if ora_fine == "HH:MM":
                        ora_fine = None
                    # Valida il formato HH:MM
                    if ora_inizio:
                        datetime.strptime(ora_inizio, "%H:%M")
                    if ora_fine:
                        datetime.strptime(ora_fine, "%H:%M")
                
                self.dati_completi["scadenze_personali"][voce] = {
                    "data": data_iso,  # Salva in formato ISO
                    "con_orario": con_orario,
                    "ora_inizio": ora_inizio,
                    "ora_fine": ora_fine
                }
            
            salva_dati(self.dati_completi)
            self.aggiorna_visualizzazione()
            messagebox.showinfo("Successo", "Scadenze personali salvate!")
        except ValueError as e:
            messagebox.showerror("Errore", f"Formato non valido!\nDate: GG-MM-AAAA\nOrari: HH:MM")
    
    
    
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
            
            widgets["label"].config(text=stato, fg=colore)
        
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
            
            widgets["label"].config(text=stato, fg=colore)
        
        # Aggiorna scadenze personali
        for voce, widgets in self.scadenze_personali_widgets.items():
            data_obj = self.dati_completi["scadenze_personali"].get(voce, {})
            if isinstance(data_obj, str):
                data_obj = {'data': data_obj, 'con_orario': False, 'ora_inizio': None, 'ora_fine': None}
            
            data_str = data_obj.get('data', '')
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
            
            # Aggiungi orario se presente
            if data_obj.get('con_orario') and data_obj.get('ora_inizio'):
                stato += f" - {data_obj['ora_inizio']}"
                if data_obj.get('ora_fine'):
                    stato += f" a {data_obj['ora_fine']}"
            
            widgets["label"].config(text=stato, fg=colore)


if __name__ == "__main__":
    inizializza_db()
    root = tk.Tk()
    app = ScadenzeApp(root)
    root.mainloop()
