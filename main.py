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


class ScadenzeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestione Scadenze - Veicoli e Personali")
        self.root.geometry("950x800")
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
        
        # SEZIONE SCADENZE TEMPORALI
        temp_frame = tk.LabelFrame(main_frame, text="Scadenze Temporali", 
                                    font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        temp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.temp_container = tk.Frame(temp_frame, bg="#f0f0f0")
        self.temp_container.pack(fill=tk.BOTH, expand=True)
        
        self.scadenze_temp_widgets = {}
        row = 0
        for voce, data in dati["scadenze_fisse"].items():
            tk.Label(self.temp_container, text=f"{voce}:", font=self.normal_font, bg="#f0f0f0").grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            entry = tk.Entry(self.temp_container, font=self.normal_font, width=15)
            entry.grid(row=row, column=1, padx=5)
            entry.insert(0, data)
            label_stato = tk.Label(self.temp_container, text="", font=self.normal_font, bg="#f0f0f0", width=30)
            label_stato.grid(row=row, column=2, padx=5)
            self.scadenze_temp_widgets[voce] = {"entry": entry, "label": label_stato}
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
        row += 1
        
        for voce, info in dati["scadenze_chilometriche"].items():
            tk.Label(self.km_container, text=f"{voce}:", font=self.normal_font, bg="#f0f0f0").grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            
            ultimo_entry = tk.Entry(self.km_container, font=self.normal_font, width=12)
            ultimo_entry.grid(row=row, column=1, padx=5)
            ultimo_entry.insert(0, str(info["ultimo_km"]))
            
            prossimo_entry = tk.Entry(self.km_container, font=self.normal_font, width=12)
            prossimo_entry.grid(row=row, column=2, padx=5)
            prossimo_entry.insert(0, str(info["prossimo_km"]))
            
            label_residui = tk.Label(self.km_container, text="", font=self.normal_font, bg="#f0f0f0", width=25)
            label_residui.grid(row=row, column=3, padx=5)
            
            self.scadenze_km_widgets[voce] = {
                "ultimo": ultimo_entry,
                "prossimo": prossimo_entry,
                "label": label_residui
            }
            row += 1
        
        btn_frame_km = tk.Frame(km_manu_frame, bg="#f0f0f0")
        btn_frame_km.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame_km, text="+ Nuova Scadenza Km", command=self.aggiungi_scadenza_km,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_km, text="Salva Scadenze Chilometriche", command=self.salva_scadenze_km,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
    
    def crea_tab_personali(self, parent):
        """Crea il tab per le scadenze personali (casa, ISEE, ecc.)"""
        main_frame = tk.Frame(parent, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titolo e pulsante notifiche
        header_frame = tk.Frame(main_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Gestione Scadenze Personali", 
                font=self.title_font, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        if NOTIFICHE_DISPONIBILI:
            tk.Button(header_frame, text="🔔 Controlla Scadenze", command=self.controlla_scadenze_notifiche, 
                     bg="#673AB7", fg="white", font=self.normal_font).pack(side=tk.RIGHT, padx=5)
        
        # SEZIONE SCADENZE PERSONALI
        scad_frame = tk.LabelFrame(main_frame, text="Scadenze (Casa, ISEE, Documenti, Altro)", 
                                    font=self.title_font, bg="#f0f0f0", padx=10, pady=10)
        scad_frame.pack(fill=tk.BOTH, expand=True)
        
        self.personali_container = tk.Frame(scad_frame, bg="#f0f0f0")
        self.personali_container.pack(fill=tk.BOTH, expand=True)
        
        self.scadenze_personali_widgets = {}
        row = 0
        for voce, data in self.dati_completi.get("scadenze_personali", {}).items():
            tk.Label(self.personali_container, text=f"{voce}:", 
                    font=self.normal_font, bg="#f0f0f0").grid(row=row, column=0, sticky=tk.W, pady=5, padx=2)
            
            entry = tk.Entry(self.personali_container, font=self.normal_font, width=15)
            entry.grid(row=row, column=1, padx=5)
            entry.insert(0, data)
            
            label_stato = tk.Label(self.personali_container, text="", 
                                  font=self.normal_font, bg="#f0f0f0", width=35)
            label_stato.grid(row=row, column=2, padx=5)
            
            btn_elimina = tk.Button(self.personali_container, text="✕", 
                                   command=lambda v=voce: self.elimina_scadenza_personale(v),
                                   bg="#F44336", fg="white", width=2)
            btn_elimina.grid(row=row, column=3, padx=2)
            
            self.scadenze_personali_widgets[voce] = {
                "entry": entry, 
                "label": label_stato,
                "btn_elimina": btn_elimina
            }
            row += 1
        
        btn_frame = tk.Frame(scad_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="+ Nuova Scadenza Personale", command=self.aggiungi_scadenza_personale,
                 bg="#4CAF50", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Salva Scadenze Personali", command=self.salva_scadenze_personali,
                 bg="#2196F3", fg="white", font=self.normal_font).pack(side=tk.LEFT, padx=5)
    
    def aggiungi_scadenza_temp(self):
        """Aggiunge una nuova scadenza temporale"""
        nome = simpledialog.askstring("Nuova Scadenza", "Nome della scadenza:")
        if not nome:
            return
        
        data = simpledialog.askstring("Nuova Scadenza", "Data scadenza (AAAA-MM-GG):")
        if not data:
            return
        
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Errore", "Data non valida! Usa il formato AAAA-MM-GG")
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
                datetime.strptime(data_str, "%Y-%m-%d")
                dati["scadenze_fisse"][voce] = data_str
            salva_dati(self.dati_completi)
            self.aggiorna_visualizzazione()
            messagebox.showinfo("Successo", "Scadenze temporali salvate!")
        except ValueError:
            messagebox.showerror("Errore", "Usa il formato AAAA-MM-GG per le date")
    
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
    
    def aggiungi_scadenza_personale(self):
        """Aggiunge una nuova scadenza personale"""
        nome = simpledialog.askstring("Nuova Scadenza Personale", 
                                      "Nome della scadenza (es: IMU, ISEE, Passaporto):")
        if not nome:
            return
        
        data = simpledialog.askstring("Nuova Scadenza Personale", 
                                      "Data scadenza (AAAA-MM-GG):")
        if not data:
            return
        
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Errore", "Data non valida! Usa il formato AAAA-MM-GG")
            return
        
        self.dati_completi["scadenze_personali"][nome] = data
        salva_dati(self.dati_completi)
        
        self.ricarica_interfaccia()
        messagebox.showinfo("Successo", f"Scadenza '{nome}' aggiunta!")
    
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
        """Salva le modifiche alle scadenze personali"""
        try:
            for voce, widgets in self.scadenze_personali_widgets.items():
                data_str = widgets["entry"].get()
                datetime.strptime(data_str, "%Y-%m-%d")
                self.dati_completi["scadenze_personali"][voce] = data_str
            
            salva_dati(self.dati_completi)
            self.aggiorna_visualizzazione()
            messagebox.showinfo("Successo", "Scadenze personali salvate!")
        except ValueError:
            messagebox.showerror("Errore", "Usa il formato AAAA-MM-GG per le date")
    
    def aggiorna_visualizzazione(self):
        oggi = datetime.now()
        dati = self.get_dati_veicolo()
        km_auto = dati["km_attuali"]
        
        for voce, widgets in self.scadenze_temp_widgets.items():
            data_str = dati["scadenze_fisse"][voce]
            data_scadenza = datetime.strptime(data_str, "%Y-%m-%d")
            giorni_rimasti = (data_scadenza - oggi).days
            
            if giorni_rimasti <= 0:
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
            data_str = self.dati_completi["scadenze_personali"][voce]
            data_scadenza = datetime.strptime(data_str, "%Y-%m-%d")
            giorni_rimasti = (data_scadenza - oggi).days
            
            if giorni_rimasti <= 0:
                colore = "red"
                stato = f"⚠️ ERRORE: SCADUTO da {abs(giorni_rimasti)} giorni!"
            elif giorni_rimasti <= SOGLIA_GIORNI_PREAVVISO:
                colore = "orange"
                stato = f"⚠️ {giorni_rimasti} giorni (In scadenza)"
            else:
                colore = "green"
                stato = f"{giorni_rimasti} giorni"
            
            widgets["label"].config(text=stato, fg=colore)


if __name__ == "__main__":
    inizializza_db()
    root = tk.Tk()
    app = ScadenzeApp(root)
    root.mainloop()
