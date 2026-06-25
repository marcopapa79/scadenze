# Gestione Scadenze Veicoli e Personali

Applicazione Python con interfaccia grafica per la gestione delle scadenze di veicoli e personali.

## 🚗 Funzionalità

### Tab Veicoli
- **Gestione Multi-Veicolo**: Gestisci scadenze per più veicoli (auto, moto, ecc.)
- **Scadenze Temporali**: Bollo, Assicurazione, Revisione, ecc.
- **Scadenze Chilometriche**: Tagliando, Freni, Gomme, ecc.
- **Aggiunta/Rimozione Veicoli**: Con conferma di sicurezza

### Tab Scadenze Personali
- **Gestione Scadenze Personali**: Casa, ISEE, Documenti, Altro
- **Solo Scadenze Temporali**: Basate su date (ISEE, IMU, Passaporto, ecc.)
- **Aggiunta/Rimozione Facile**: Con pulsante ✕ per ogni scadenza
- **Notifiche Desktop**: Incluse nelle notifiche automatiche

### Funzionalità Comuni
- **Notifiche Desktop**: Avvisi automatici per scadenze critiche
- **Interfaccia Grafica Intuitiva**: Con tab separati e codici colore
- **Salvataggio Automatico**: Tutti i dati salvati in JSON

## 📊 Sistema di Avvisi

- 🟢 **Verde**: Tutto OK (oltre 30 giorni o 3500 km)
- 🟠 **Arancione**: Attenzione (meno di 30 giorni o 3500 km)
- 🔴 **Rosso**: ERRORE - Scadenza superata!

## 🔔 Notifiche Desktop

Il sistema invia notifiche desktop automatiche quando:
- Una scadenza è superata (rosso)
- Una scadenza è in avvicinamento (giallo/arancione)

## Setup

1. Crea un ambiente virtuale:
   ```bash
   python -m venv venv
   ```

2. Attiva l'ambiente virtuale:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Utilizzo

```bash
python main.py
```

### Pulsanti Principali

**Tab Veicoli:**
- **+ Nuovo Veicolo**: Aggiunge un nuovo veicolo
- **- Rimuovi Veicolo**: Elimina il veicolo corrente (con conferma)
- **🔔 Controlla Scadenze**: Verifica tutte le scadenze e mostra notifiche desktop
- **+ Nuova Scadenza**: Aggiunge scadenze temporali al veicolo
- **+ Nuova Scadenza Km**: Aggiunge scadenze chilometriche

**Tab Scadenze Personali:**
- **+ Nuova Scadenza Personale**: Aggiunge una nuova scadenza (ISEE, Casa, ecc.)
- **✕** (pulsante rosso): Elimina la scadenza specifica
- **🔔 Controlla Scadenze**: Verifica tutte le scadenze (veicoli + personali)

### Test Notifiche

Per testare le notifiche desktop:
```bash
python notifiche.py
```

## 📁 Struttura File

- `main.py`: Applicazione principale con GUI
- `notifiche.py`: Sistema di notifiche desktop
- `stato_veicolo.json`: Database locale con i dati dei veicoli
- `requirements.txt`: Dipendenze Python

## 🔧 Personalizzazione

Puoi modificare le soglie di avviso in `main.py` e `notifiche.py`:
```python
SOGLIA_KM_PREAVVISO = 3500  # Avviso a 3500 km dalla scadenza
SOGLIA_GIORNI_PREAVVISO = 30  # Avviso 30 giorni prima
```

## 💾 Backup

I dati sono salvati in `stato_veicolo.json`. Si consiglia di fare backup regolari di questo file.

## 📝 Licenza

Progetto personale per la gestione delle scadenze dei veicoli.
