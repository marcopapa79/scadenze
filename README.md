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

### Tab Medicinali
- **Scadenza Medicinali**: nome, data di scadenza ed eventuale data di apertura
- **Durata dopo l'apertura** (dal foglietto, es. `28 giorni`, `6 mesi`, `1 anno`): se la confezione è aperta, conta la data che arriva prima tra scadenza stampata e apertura + durata ("Da usare entro N giorni", poi "DA BUTTARE")
- **Posizione nell'armadietto**: Piano sotto, Piano intermedio o Piano sopra (menu a tendina, si salva subito)
- **Ordinabile**: clic sul titolo di una colonna (Medicinale, Scadenza, Aperto il, Posizione) per ordinare, un secondo clic inverte; l'ordine scelto viene ricordato
- **Giorni rimanenti colorati** (rosso scaduto, arancione entro 30 giorni, verde) e "aperto da N giorni"
- **Scadenza come sulla confezione**: si può scrivere `GG-MM-AAAA` oppure solo `MM-AAAA` (vale fino a fine mese)
- **Solo promemoria**: niente notifiche, non va su Google Calendar né nei riepiloghi settimanali
- **🖨️ Report (stampa / WhatsApp)**: tabella pulita di tutti i medicinali con riepilogo in alto (quanti scaduti / in scadenza), nell'ordine scelto. "📋 Copia per WhatsApp" copia l'immagine (Ctrl+V nella chat); "🖨️ Stampa (PDF)" crea un PDF A4, verticale o orizzontale, con i caratteri un po' più grandi (più pagine se servono) e lo apre: Ctrl+P per stampare. Salvati anche come `report_medicinali.png` / `.pdf`

### Funzionalità Comuni
- **Notifiche Desktop**: Avvisi automatici per scadenze critiche
- **Esportazione Google Calendar**: Esporta scadenze direttamente su Google Calendar
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

## 📅 Esportazione Google Calendar

Esporta tutte le tue scadenze su Google Calendar con un click!

**Caratteristiche:**
- Eventi nel calendario "Famiglia", con il colore del calendario
- Promemoria automatici: **1 giorno prima e 10 minuti prima**; per gli eventi che si ripetono solo **10 minuti prima**
- Scadenze chilometriche con data stimata
- Esportazione separata per veicoli e scadenze personali

**Setup:** Vedi [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) per istruzioni dettagliate

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

### Metodo 1: Doppio Click (Windows)
Fai doppio click su uno di questi file:
- **`avvia_scadenze.bat`** - Avvio completo con controlli e installazione automatica dipendenze
- **`run.bat`** - Avvio rapido (se le dipendenze sono già installate)

### Metodo 2: Da Terminale
```bash
python main.py
```

### Pulsanti Principali

**Tab Veicoli:**
- **+ Nuovo Veicolo**: Aggiunge un nuovo veicolo
- **- Rimuovi Veicolo**: Elimina il veicolo corrente (con conferma)
- **🔔 Controlla Scadenze**: Verifica tutte le scadenze e mostra notifiche desktop
- **📅 Esporta su Calendar**: Esporta scadenze del veicolo su Google Calendar
- **+ Nuova Scadenza**: Aggiunge scadenze temporali al veicolo
- **+ Nuova Scadenza Km**: Aggiunge scadenze chilometriche

**Tab Scadenze Personali:**
- **+ Nuova Scadenza** / **+ Nuova Visita Prenotata** / **+ Nuova Visita da Prenotare** / **+ Festa o Compleanno**: aprono lo stesso modulo, con già scelta la sezione del pulsante. Nel modulo si sceglie:
  - **Dove va**: Visite prenotate, Visite da prenotare, Scadenze o Feste e compleanni. Conta la sezione scelta, non il nome: non serve che inizi con "Visita"
  - **Nome** e **Data** (`GG-MM-AAAA`, va bene anche `5/11` o `5-11-26`)
  - **Orario**: *Tutto il giorno* oppure *A un orario* dalle … alle … (la fine è facoltativa; si può scrivere `9`, `9:30`, `9.30`, `930`). Scrivendo un orario si sceglie da solo "A un orario"; per le visite prenotate è proposto già "A un orario"
  - **Si ripete**: con *🔁 Imposta…* (ogni settimana / mese)
  - Invio = Salva, Esc = Annulla
- **✏️** (pulsante arancione): apre lo stesso modulo per cambiare nome, data, orario, ripetizione e **spostare la voce in un'altra sezione**. Spostando una "… da prenotare" tra le visite prenotate, il "da prenotare" viene tolto dal nome
- **✕** (pulsante rosso): Elimina la scadenza specifica
- **🔔 Controlla Scadenze**: Verifica tutte le scadenze (veicoli + personali)
- **📅 Esporta su Calendar**: Esporta scadenze personali su Google Calendar
- **📋 Copia settimana**: Copia negli appunti gli impegni da oggi ai prossimi 7 giorni (scadenze personali, ripetizioni settimanali e scadenze a data dei veicoli), già formattati per WhatsApp: basta incollare con Ctrl+V. Si apre anche un'anteprima modificabile con il pulsante "Copia di nuovo"
- **🖼️ Copia immagine**: Come "Copia settimana", ma copia un'**immagine a colori**. Nell'anteprima si sceglie la vista: **📅 Calendario** (settimana con le ore, stile Google Calendar, blocchi colorati per sezione) oppure **📋 Elenco**, divisa nelle stesse sezioni dell'app (Visite prenotate, Visite da prenotare, Scadenze, Feste e compleanni, Veicoli). Su WhatsApp Web si incolla con Ctrl+V come una foto. L'immagine viene salvata anche in `riepilogo_settimana.png` (richiede Pillow, installato da `avvia_scadenze.bat`)
- **Scegliere i giorni** (in tutte e due le finestre, barra **Dal:**): di default il periodo parte da oggi; con **<<** / **>>** si va indietro / avanti di una settimana, con **<** / **>** di un giorno, oppure si scrive una data (es. `20/11`, `1-12-26`, `01.12.2026`) e si preme **Vai** o Invio. **Oggi** torna al giorno corrente. A ogni cambio il testo o l'immagine vengono rigenerati e ricopiati negli appunti; per i giorni passati l'elenco mostra "ieri" / "N giorni fa". Senza anno (es. `5/1`) viene scelto l'anno più vicino a oggi
- **✏️ Modifica impegni** (finestra immagine): apre gli impegni del periodo come un file di testo, una riga per impegno (`Gio 22/10  17:30-18:30  Basket Andrés`, senza orario = tutto il giorno) divisi per sezione con righe `# Visite`, `# Scadenze`, `# Feste e compleanni`, ecc. Si possono correggere, cancellare o aggiungere righe e poi premere **Aggiorna immagine** (o Ctrl+Invio). Le modifiche valgono **solo per l'immagine da mandare su WhatsApp**: i dati dell'app non cambiano. "Ripristina dai dati" annulla le modifiche

**Tab Medicinali:**
- **+ Nuovo Medicinale**: chiede nome, scadenza (`GG-MM-AAAA` o `MM-AAAA`), data di apertura (vuota se la confezione è chiusa), durata dopo l'apertura (vuota se non indicata) e posizione (Piano sotto / intermedio / sopra / non indicare)
- **Salva Medicinali**: salva date e durate cambiate nei campi e rimette in ordine
- **Titoli delle colonne**: clic per ordinare per nome, scadenza, apertura o posizione (▲/▼)
- **Menu Posizione**: cambia il piano, salvato subito
- **✏️** cambia il nome, **✕** elimina il medicinale
- **🖨️ Report (stampa / WhatsApp)**: anteprima del report con i pulsanti **📋 Copia per WhatsApp** e **🖨️ Stampa (PDF)**, la scelta **Foglio: Verticale / Orizzontale** (vale per il PDF) e tre spunte: **Mostra lo stato** (togliendola il report diventa un semplice elenco, senza colonna Stato, colori e conteggi: utile da stampare e attaccare all'armadietto), **Mostra 'Dopo apertura'** e **Mostra 'Aperto il'** (tolgono quelle colonne). Se c'è spazio la tabella si divide in **più colonne affiancate**: togliendo tutte e tre restano Medicinale, Scadenza e Piano e vanno 2 colonne sul foglio verticale, 3 su quello orizzontale; in orizzontale ci stanno 2 colonne anche con 'Aperto il' o con lo stato. Con una quarantina di medicinali sta tutto in **un foglio A4**. Le colonne si adattano da sole ai testi (i nomi lunghi vanno a capo, mai tagliati); le scelte vengono ricordate. Nel PDF i caratteri sono più grandi del 15% (si cambia con `INGRANDIMENTO_STAMPA` in `main.py`, es. `1.25`); se però per poco non starebbe in un foglio, li rimpicciolisce quel tanto che basta (mai sotto la grandezza normale)

### Test Notifiche

Per testare le notifiche desktop:
```bash
python notifiche.py
```

## 📁 Struttura File

- `main.py`: Applicazione principale con GUI (versione classica)
- `ricorrenze.py`: Calcolo delle date delle scadenze che si ripetono
- `immagine_settimana.py`: Immagine a colori per WhatsApp (calendario / elenco)
- `notifiche.py`: Sistema di notifiche desktop
- `google_calendar.py`: Modulo esportazione Google Calendar
- `stato_veicolo.json`: tutti i dati (nella cartella del programma oppure nella cartella dati scelta, vedi sotto)
- `impostazioni_locali.json`: impostazioni solo di questo PC, es. la cartella dei dati (non va su git)
- `requirements.txt`: Dipendenze Python
- `avvia_scadenze.bat`: Avvio con controlli automatici (Windows)
- `backup/`: Copie di sicurezza giornaliere dei dati (create automaticamente, accanto al file dati); se i dati sono su Drive/NAS, nella cartella del programma una copia ogni 7 giorni
- `ISTRUZIONI_VSCODE.md`: passi per togliere i dati da git (anche da far eseguire a Copilot in VS Code)
- `run.bat`: Avvio rapido (Windows)
- `GOOGLE_CALENDAR_SETUP.md`: Guida setup Google Calendar
- `credentials.json`: **Credenziali Google (NON committare!)**
- `token.pickle`: **Token autenticazione (generato automaticamente)**

## 🔧 Personalizzazione

Puoi modificare le soglie di avviso in `main.py` e `notifiche.py`:
```python
SOGLIA_KM_PREAVVISO = 3500  # Avviso a 3500 km dalla scadenza
SOGLIA_GIORNI_PREAVVISO = 30  # Avviso 30 giorni prima
```

Colore di sfondo della versione classica, in cima a `main.py`:
```python
COLORE_SFONDO = "#f0f0f0"   # grigio chiaro (predefinito)
                            # altri esempi: "#dcdfe3" grigio un po' più scuro, "#cfd8dc" grigio-azzurro, "#b0bec5" grigio-azzurro scuro
```

## 📁 Dove salvare i dati (Google Drive, Dropbox, OneDrive, NAS)

Il file dei dati `stato_veicolo.json` può stare in qualunque cartella, così non serve più aggiornare git a ogni modifica e i dati sono anche al sicuro fuori dal PC.

1. In fondo alla finestra c'è **💾 Dati: …** con il percorso del file e il pulsante **📁 Cambia cartella dati…**
2. Scegli la cartella, per esempio:
   - **Google Drive** (con "Google Drive per desktop" installato): `G:\Il mio Drive\Scadenze`
   - **Dropbox**: `C:\Users\<nome>\Dropbox\Scadenze`
   - **OneDrive**: `C:\Users\<nome>\OneDrive\Scadenze`
   - **NAS**: una cartella di rete (`\\NAS\condivisa\Scadenze`) o un'unità collegata come `Z:\`
3. Il programma ci copia i dati e da quel momento legge e salva lì (anche le copie di sicurezza giornaliere, nella cartella `backup` accanto). La scelta viene ricordata solo su questo PC (`impostazioni_locali.json`).
4. In più, **ogni 7 giorni** una copia dei dati va anche nella cartella `backup` del programma, su questo PC: se succede qualcosa a Drive o al NAS i dati non sono persi (si tengono le ultime 30 copie, circa 7 mesi; si cambia con `GIORNI_BACKUP_LOCALE` / `COPIE_BACKUP_LOCALE` in `main.py`).

**Su un altro PC**: apri il programma, premi **📁 Cambia cartella dati…**, scegli la stessa cartella e rispondi **Sì** ("usa i dati che sono già nella cartella").

**Se la cartella non si trova** all'avvio (NAS spento, Drive non ancora partito) il programma non crea un file vuoto: propone *Riprova*, un'altra cartella oppure di uscire. Se non riesce a salvare durante l'uso, chiede *Riprova*; con *Annulla* le modifiche restano nella finestra e vengono salvate al prossimo salvataggio riuscito.

**Più PC**: meglio usare il programma su un PC alla volta. Se il file viene cambiato da un altro PC mentre il programma è aperto, tornando sulla finestra ti chiede se ricaricarlo; se salvi comunque, la versione dell'altro PC viene messa da parte in `backup/stato_veicolo_altro_pc_….json`, quindi non si perde nulla.

**Togliere i dati da git** (una volta sola, dopo aver spostato la cartella dati): i passi completi, anche da far eseguire a Copilot in VS Code, sono in [ISTRUZIONI_VSCODE.md](ISTRUZIONI_VSCODE.md). In breve, nel terminale dentro la cartella del programma:
```bash
git rm --cached stato_veicolo.json
git commit -m "Dati spostati fuori da git"
```
Il file resta sul disco (non viene più aggiornato) e `.gitignore` lo esclude d'ora in poi.

## 💾 Backup

I dati sono salvati in `stato_veicolo.json`, in modo sicuro (se il PC si spegne durante un salvataggio il file resta integro).

Ogni giorno, al primo salvataggio, l'app ne fa una copia nella cartella `backup/` accanto al file dati (`stato_veicolo_AAAA-MM-GG.json`) e tiene le ultime 30. Per recuperare i dati di un giorno: chiudi l'app e copia quel file sopra `stato_veicolo.json`. Google Drive e Dropbox tengono in più anche le versioni precedenti del file.

## 📝 Licenza

Progetto personale per la gestione delle scadenze dei veicoli.
