# Gestione Scadenze — Documentazione tecnica

Questo documento spiega **come è fatto il codice**: struttura dei file, formato dei dati, flusso dell'applicazione, logica di calcolo, integrazione con Google Calendar e notifiche. In fondo c'è l'esito della **revisione del codice** con i problemi trovati.

Per l'uso quotidiano (pulsanti, colori) vedi [README.md](README.md); per configurare Google vedi [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md).

---

## 1. Panoramica

Applicazione desktop in **Python + tkinter**, a finestra singola con tre schede:

| Scheda | Contenuto |
|---|---|
| 🚗 **Veicoli** | Più veicoli; per ognuno km attuali, scadenze a data (Bollo, Assicurazione, Revisione…) e scadenze chilometriche (Tagliando, Freni, Gomme…) |
| 📋 **Scadenze Personali** | Quattro sezioni: *Visite prenotate*, *Visite da prenotare*, *Scadenze* (casa, ISEE, IMU, documenti…), *Feste e compleanni*. Supporta orari e ricorrenze settimanali/mensili |
| 💊 **Medicinali** | Medicinali con data di scadenza ed eventuale data di apertura, in ordine di scadenza. Solo promemoria: niente notifiche, Calendar o WhatsApp (§8b) |

Funzioni trasversali: semaforo verde/arancione/rosso, notifiche desktop (`plyer`), esportazione/importazione con Google Calendar (calendario **"Famiglia"**).

Nessun database: tutto vive in un unico file JSON, `stato_veicolo.json`.

---

## 2. Avvio

```
avvia_scadenze.bat
 ├─ verifica che "python" sia nel PATH        → altrimenti errore e pausa
 ├─ cd nella cartella dello script (%~dp0)    → importante: i file sono cercati con percorso relativo
 ├─ se esiste venv\ lo attiva, altrimenti usa il Python di sistema
 ├─ se "import plyer" fallisce → pip install -r requirements.txt
 ├─ python main.py
 └─ se l'app esce con errore → mostra messaggio e pausa (così si legge il traceback)
```

`run.bat` fa solo `cd` + `python main.py`, senza controlli.

All'interno di `main.py`:

```
inizializza_db()          crea stato_veicolo.json con dati di esempio se non esiste
tk.Tk() → ScadenzeApp     carica il JSON, eventuale migrazione, costruisce le schede
root.mainloop()
```

Tutti i file (`stato_veicolo.json`, `backup/`, `credentials.json`, `token.pickle`, `riepilogo_settimana.png`) sono cercati nella **cartella del programma** (`CARTELLA_PROGRAMMA` in `main.py` e `google_calendar.py`), da qualunque cartella lo si avvii.

Una versione con grafica moderna (customtkinter) è stata provata il 23/10/2026 e poi eliminata: si è preferita l'interfaccia classica (§13).

---

## 3. Struttura dei file

| File | Righe | Ruolo |
|---|---|---|
| `main.py` | ~2200 | Applicazione (classe `ScadenzeApp`): logica, lettura/scrittura JSON con copie di sicurezza, conversione date, semaforo, interfaccia classica tkinter |
| `ricorrenze.py` | ~70 | `prossima_occorrenza()`: calcola la prossima data di una scadenza ricorrente |
| `notifiche.py` | ~175 | Controllo scadenze e invio notifiche desktop con `plyer` |
| `google_calendar.py` | ~545 | OAuth Google, export eventi (singoli e in blocco, con RRULE), import eventi |
| `immagine_settimana.py` | ~720 | Immagini con Pillow: impegni della settimana (elenco/calendario), report medicinali e PDF A4; copia negli appunti (ctypes) |
| `stato_veicolo.json` | — | Tutti i dati |
| `backup/` | — | Una copia di `stato_veicolo.json` al giorno (`stato_veicolo_AAAA-MM-GG.json`), ultime 30 (esclusa da git) |
| `avvia_scadenze.bat` | — | Avvio con installazione automatica delle librerie mancanti |
| `requirements.txt` | — | `plyer`, `Pillow` + librerie Google |
| `credentials.json` / `client_secret_*.json` | — | Credenziali OAuth (escluse da git) |
| `token.pickle` | — | Token Google salvato dopo il primo login (escluso da git) |

Dipendenze tra moduli:

```
main.py ──► ricorrenze.py
   │  ├──► notifiche.py ──► ricorrenze.py, plyer
   │  └──► google_calendar.py ──► google-auth, googleapiclient
```

`notifiche` e `google_calendar` sono **opzionali**: se l'import fallisce, `main.py` imposta `NOTIFICHE_DISPONIBILI` / `GOOGLE_CALENDAR_DISPONIBILE = False` e semplicemente non mostra i relativi pulsanti.

---

## 4. Formato dei dati (`stato_veicolo.json`)

```jsonc
{
  "veicoli": {
    "Corolla (GD028MR)": {                 // chiave = "Nome (TARGA)"
      "nome_veicolo": "Corolla",
      "targa": "GD028MR",
      "km_attuali": 88375,
      "scadenze_fisse": {                  // nome → data ISO
        "Bollo": "2026-08-31"
      },
      "scadenze_chilometriche": {          // nome → km
        "Tagliando": { "ultimo_km": 0, "prossimo_km": 91400 }
      }
    }
  },
  "veicolo_selezionato": "Corolla (GD028MR)",

  "scadenze_personali": {
    "Visita Fazi": {                       // chiave = nome visualizzato (univoco)
      "data": "2026-10-16",                // ISO, per le ricorrenti è la data di partenza
      "con_orario": true,
      "ora_inizio": "16:00",               // "HH:MM" oppure null
      "ora_fine": "17:00",
      "ricorrenza": null,                  // oppure oggetto (sotto)
      "categoria": "visita_prenotata"      // facoltativo: visita_prenotata | visita_da_prenotare | festa_compleanno
    },
    "Basket": {
      "data": "2026-09-22", "con_orario": true, "ora_inizio": "17:30", "ora_fine": "18:30",
      "ricorrenza": {
        "attiva": true,
        "freq": "WEEKLY",                  // "WEEKLY" | "MONTHLY"
        "intervallo": 1,                   // ogni N settimane/mesi
        "giorni": ["MO", "TH"],            // solo WEEKLY, codici RRULE
        "fino_al": "2027-06-29"            // ISO oppure null = senza fine
      }
    }
  },

  "medicinali": [                          // scheda 💊 Medicinali (§8b)
    {
      "nome": "Sciroppo tosse",
      "scadenza": "2026-12-31",            // ISO; con solo_mese è l'ultimo giorno del mese
      "solo_mese": true,                   // scritta come "12-2026" (come sulla confezione)
      "apertura": "2026-10-20",            // ISO oppure null = confezione chiusa
      "durata_apertura": "6 mesi",         // "N giorni" | "N mesi" oppure null
      "posizione": "sotto"                 // "sotto" | "intermedio" | "sopra" | null
    }
  ],

  "impostazioni": {
    "ordine_medicinali": ["scadenza", false],  // colonna ("nome", "scadenza", "apertura", "posizione"), invertito
    "report_mostra_stato": true                // report medicinali con o senza colonna Stato
  }
}
```

Note:
- **Date sempre in ISO** (`AAAA-MM-GG`) nel file; nell'interfaccia sono mostrate e digitate in italiano (`GG-MM-AAAA`). Le conversioni sono `data_iso_a_italiana()` / `data_italiana_a_iso()`.
- **Vecchio formato** ancora supportato ovunque: una scadenza personale può essere una semplice stringa `"2027-01-15"` invece di un oggetto.
- Il codice migra anche un formato ancora più vecchio a veicolo singolo (`migra_vecchio_formato()`).

---

## 5. Come vengono classificate le scadenze personali

Un'unica funzione, `_sezione_personale(nome, voce)`, decide la sezione per la scheda, per Copia settimana/immagine e per l'export su Google:

| Ordine | Condizione | Sezione |
|---|---|---|
| 1 | `categoria` è `visita_prenotata` / `visita_da_prenotare` **oppure** il nome contiene `visita` o `medic` | Visite: **da prenotare** se il nome contiene `prenotare`, altrimenti **prenotate** |
| 2 | `categoria == "festa_compleanno"` **oppure** il nome contiene `compleanno` o `festa` | Feste e compleanni |
| 3 | tutto il resto | Scadenze |

La `categoria` viene salvata dai pulsanti "+ Nuova Visita Prenotata", "+ Nuova Visita da Prenotare", "+ Festa o Compleanno" (e dall'import di Google per le visite), quindi una visita chiamata "Controllo oculistico" resta tra le visite anche senza la parola "visita". La categoria non si perde salvando né rinominando.

Il pulsante "+ Nuova Visita da Prenotare" aggiunge automaticamente il suffisso ` da prenotare` al nome. Rinominare una voce può quindi **spostarla di sezione**.

Se un nome esiste già, `_nome_personale_univoco()` aggiunge ` (2)`, ` (3)`, …

---

## 6. Semaforo e soglie

Costanti (duplicate in `main.py` e `notifiche.py`):

```python
SOGLIA_GIORNI_PREAVVISO = 30
SOGLIA_KM_PREAVVISO     = 3500
```

| Stato | Scadenza a data | Scadenza a km |
|---|---|---|
| 🟢 verde | > 30 giorni | > 3500 km residui |
| 🟠 arancione | 0–30 giorni | 1–3500 km |
| 🔴 rosso | data passata | km residui ≤ 0 |

Il calcolo avviene in `ScadenzeApp.aggiorna_visualizzazione()`, chiamata a ogni ricostruzione dell'interfaccia e dopo ogni salvataggio. Le voci di ogni sezione sono ordinate per data (o per km residui).

---

## 7. Ricorrenze (`ricorrenze.py`)

`prossima_occorrenza(data_iniziale, ricorrenza, oggi)` restituisce:
- `data_iniziale` se la voce non è ricorrente;
- la **prima occorrenza da oggi in poi** se è ricorrente;
- `None` se la ricorrenza è finita (`fino_al` superato) → l'interfaccia mostra "Ricorrenza terminata" in grigio.

**Settimanale**: scorre i giorni da `max(data_iniziale, oggi)` e prende il primo che cade in uno dei `giorni` scelti e in una settimana valida per l'`intervallo` (contando le settimane dal lunedì della data iniziale).

**Mensile**: stesso giorno del mese della data iniziale, ogni `intervallo` mesi; se il mese è più corto usa l'ultimo giorno (es. 31 → 30 o 28/29).

Effetto pratico: una voce ricorrente non diventa mai rossa, mostra sempre i giorni alla prossima occorrenza.

La ricorrenza si imposta con il pulsante 🔁 su ogni riga (finestra `_dialog_ricorrenza`) o rispondendo "Sì" quando si crea una nuova voce. Le ricorrenze esistono **solo per le scadenze personali**.

---

## 8. Salvataggio

- `salva_dati()` riscrive **tutto** il JSON ad ogni modifica, in modo sicuro: scrive `stato_veicolo.json.tmp` e poi lo sostituisce all'originale (`os.replace`), così un'interruzione a metà non lascia il file vuoto o rovinato.
- Prima del primo salvataggio di ogni giorno, `_backup_giornaliero()` copia il file in `backup/stato_veicolo_AAAA-MM-GG.json` e tiene solo le ultime `GIORNI_BACKUP = 30` copie. Per tornare indietro basta copiare una di queste sopra `stato_veicolo.json` (ad app chiusa).
- "Salva Scadenze Personali" / "Salva Scadenze Temporali" controllano **prima tutte le righe**: se una data o un orario è sbagliato non cambia nulla e il messaggio dice in quale voce è l'errore.
- Aggiunta, eliminazione, rinomina, cambio veicolo, km e ricorrenza **salvano subito**.
- Le modifiche fatte **a mano nei campi** (date, orari, km di tagliando…) vengono salvate **solo** premendo il relativo pulsante blu "Salva …". Se si cambia veicolo o si aggiunge una voce prima di aver salvato, l'interfaccia viene ricostruita dal file e quelle modifiche si perdono.
- Dopo quasi ogni operazione l'interfaccia viene distrutta e ricostruita da zero (`ricarica_interfaccia()`), riaprendo di default la scheda *Scadenze Personali* (o *Veicoli* se si è cambiato veicolo).

---

## 8b. Scheda Medicinali

Terza scheda, **💊 Medicinali** (`crea_tab_medicinali()` in `main.py`). I medicinali stanno nell'elenco `"medicinali"` del file dati, separato dalle scadenze personali: per questo notifiche, Google Calendar, Copia settimana/immagine li ignorano senza bisogno di altro codice.

- **Campi:** nome, scadenza, data di apertura (facoltativa), durata dopo l'apertura (facoltativa), posizione (facoltativa: Piano sotto / intermedio / sopra, `POSIZIONI_MEDICINALI`).
- **Scadenza:** `GG-MM-AAAA` oppure solo `MM-AAAA` / `MM-AA` come sulle confezioni (`interpreta_scadenza_medicinale()`): con solo mese e anno vale l'ultimo giorno del mese e viene mostrata di nuovo come `MM-AAAA` (campo `solo_mese`).
- **Apertura:** `GG-MM-AAAA` (anche senza anno, come la barra "Dal:"); vuota = confezione chiusa.
- **Durata dopo l'apertura:** colonna "Dopo apertura", come sul foglietto: `28`, `28 giorni`, `28gg`, `4 settimane` (→ 28 giorni), `6 mesi`, `6m`, `1 anno` (→ 12 mesi) — `interpreta_durata()`, salvata normalizzata (`testo_durata()`). Con confezione aperta il limite è `fine_dopo_apertura()` = apertura + durata (i mesi sono mesi di calendario: 31/01 + 1 mese = 28/02).
- **Scadenza effettiva** (`_scadenza_effettiva()`): la data che arriva prima tra scadenza stampata e limite dopo l'apertura. È quella usata per lo stato e per l'ordinamento "Scadenza", così in cima c'è ciò che va usato o buttato per primo.
- **Ordine:** clic sul titolo di una colonna (`ordina_medicinali()`): per nome (maiuscole/minuscole ignorate), scadenza, apertura o posizione (sotto → intermedio → sopra); un secondo clic inverte (▲/▼). Con apertura e posizione, le voci senza valore restano sempre in fondo, in ordine di scadenza. La scelta è salvata in `impostazioni.ordine_medicinali` e ricordata alla riapertura; predefinito: scadenza ▲. Il riordino ridisegna solo le righe (`_riempi_griglia_medicinali(conserva_testi=True)`) e lascia nei campi le date scritte e non ancora salvate (l'ordine però usa le date salvate).
- **Posizione:** menu a tendina (`ttk.Combobox` in sola lettura) che **salva subito** alla scelta (`_cambia_posizione_medicinale()`); la rotellina del mouse sopra il menu scorre la pagina invece di cambiare piano. All'aggiunta la chiede una finestrella con un pulsante per piano (`_scegli_posizione_medicinale()`).
- **Stato** (due righe):
  - se decide la scadenza stampata: giorni alla scadenza (rosso scaduto/oggi, arancione entro `SOGLIA_GIORNI_PREAVVISO` = 30 giorni, verde oltre) e sotto "aperto da N giorni" oppure, se chiuso, "dopo l'apertura dura …";
  - se decide l'apertura: "Da usare entro N giorni (fino al GG-MM-AAAA)" (arancione entro `GIORNI_PREAVVISO_APERTO` = 7 giorni, verde oltre), poi "⚠️ Ultimo giorno di uso" e "⚠️ DA BUTTARE" in rosso.
- I nomi molto lunghi vanno a capo per tenere la tabella stretta.
- Lo stato è calcolato da `_stato_medicinale(voce)`, usato sia dalla scheda sia dal report.

### 🖨️ Report medicinali (stampa / WhatsApp)

Pulsante in alto nella scheda (`report_medicinali()`):

1. `_righe_report_medicinali()` prepara le righe **nell'ordine scelto nella scheda** (dati salvati) e il riepilogo: numero di medicinali, quanti scaduti o da buttare (rosso), quanti in scadenza (arancione), oppure "tutto in regola". Nel report "156 giorni" diventa "Scade tra 156 giorni" e il simbolo ⚠️ viene tolto.
2. `immagine_settimana.crea_report_medicinali()` disegna con Pillow una tabella (Medicinale, Scadenza, Aperto il, Dopo apertura, Posizione, Stato) con barretta colorata a sinistra di ogni riga, righe alternate, nomi e stato a capo se lunghi. Viene salvata in `report_medicinali.png` e **copiata subito negli appunti**.
3. Finestra di anteprima con:
   - **📋 Copia per WhatsApp**: ricopia l'immagine negli appunti (stessa funzione dell'immagine settimanale);
   - spunta **Mostra lo stato**: se tolta, `crea_report_medicinali(..., mostra_stato=False)` disegna la tabella senza colonna Stato (colonne `COLONNE_REPORT_SENZA_STATO`, più larghe), con barrette grigie e nel riepilogo solo il numero di medicinali. Vale per anteprima, immagine per WhatsApp e PDF; la scelta è salvata in `impostazioni.report_mostra_stato` (predefinito: con stato);
   - **🖨️ Stampa (PDF)**: rigenera il report diviso in pagine (`altezza_pagina_report_a4()`), lo mette su fogli A4 verticali a 200 dpi con margini (`salva_pdf_a4()`), salva `report_medicinali.pdf` e lo apre con il programma predefinito (`os.startfile`): da lì Ctrl+P. Se il PDF è aperto in un altro programma e non si può sovrascrivere, compare un avviso.
- **Pulsanti:** "+ Nuovo Medicinale" (chiede nome, scadenza, apertura, posizione), "Salva Medicinali" (salva le date modificate nei campi e riordina; con una data sbagliata non salva nulla e dice quale), ✏️ rinomina, ✕ elimina. Dopo ogni operazione resta aperta la scheda Medicinali; la rotellina del mouse scorre anche questa scheda.

---

## 9. Notifiche desktop (`notifiche.py`)

Il pulsante 🔔 chiama `controlla_tutti_veicoli(dati)` che:
1. per ogni veicolo controlla scadenze a data e a km (`controlla_e_notifica`);
2. controlla le scadenze personali (`controlla_scadenze_personali`, tenendo conto delle ricorrenze);
3. per ogni voce rossa o arancione invia una notifica Windows (timeout 15 s critiche, 10 s avvisi);
4. restituisce un riepilogo mostrato poi in una finestra.

Le notifiche partono **solo premendo il pulsante**: non c'è un controllo automatico all'avvio o periodico.

Test rapido: `python notifiche.py` invia una notifica di prova.

---

## 10. Google Calendar (`google_calendar.py`)

**Autenticazione** (`autentica_google_calendar`): se c'è `token.pickle` lo usa, se è scaduto lo rinnova, se il rinnovo fallisce lo cancella e apre il browser per un nuovo login con `credentials.json`. Scope: accesso completo al calendario.

**Calendario di destinazione**: cerca un calendario chiamato **"Famiglia"** (senza distinzione maiuscole); se non lo trova usa quello principale.

**Export** — cosa produce:

| Funzione | Titolo evento | Note |
|---|---|---|
| `esporta_singola_scadenza` (📅 su una riga) | `🏥 Visita: …`, `⚠️ …`, `⚠️ … - Veicolo` | Con orari e ricorrenza (RRULE) |
| `esporta_scadenze_veicolo` (📅 in alto, tab Veicoli) | `Bollo - Corolla` | Le scadenze a km diventano eventi con **data stimata a 50 km/giorno** |
| `esporta_scadenze_personali` (📅 in alto, tab Personali) | nome della voce | Con orari e ricorrenza |

Ogni evento: tutto il giorno oppure con orario (fuso `Europe/Rome`); colore del calendario; promemoria popup:

| Evento | Promemoria |
|---|---|
| Ricorrente (🔁 attivo) | 10 minuti prima |
| Tutti gli altri | 1 giorno prima e 10 minuti prima |

Si cambiano nelle costanti `PROMEMORIA_RICORRENTI` e `PROMEMORIA_SINGOLI` in cima a `google_calendar.py` (valori in minuti). Per gli eventi *tutto il giorno* Google conta i minuti dalla mezzanotte del giorno stesso: "10 minuti prima" = 23:50 della sera prima, "1 giorno prima" = mezzanotte del giorno precedente. Valgono solo per gli eventi esportati da quel momento in poi.

> ⚠️ L'export **non controlla i duplicati**: premere due volte "Esporta" crea due copie di ogni evento su Google.

**Import** (📥 "Importa da Calendar", solo tab Personali):
1. chiede data di inizio e numero di giorni;
2. legge gli eventi del calendario "Famiglia" (ricorrenze espanse in singoli eventi);
3. ripulisce i titoli dai prefissi messi dall'export (`🏥 Visita:`, `⚠️ Scadenza:`…);
4. salta i duplicati (stesso nome, data e orario);
5. chiede conferma evento per evento (Sì / No / Annulla per fermarsi);
6. gli eventi con `Tipo: Visita` nella descrizione vengono marcati `categoria: visita_prenotata`.

---

## 10b. Copia settimana (per WhatsApp)

Pulsante **📋 Copia settimana** nella scheda Scadenze Personali (`copia_settimana()` in `main.py`):

1. `_impegni_nel_periodo(oggi, oggi + 6)` raccoglie:
   - le scadenze personali, con **tutte** le ripetizioni delle ricorrenti nel periodo (`occorrenze_nel_periodo()` in `ricorrenze.py`);
   - le scadenze a data dei veicoli (es. "Bollo (Corolla)"). Le scadenze a km non sono incluse.
2. `_testo_settimana()` raggruppa per giorno (solo i giorni con impegni), ordina per orario (prima le voci senza orario) e usa `*testo*` per il grassetto di WhatsApp:

   ```
   *Impegni dal 18/10 al 24/10*

   *Lunedì 19/10 (domani)*
   • 15:30-16:00 Luzi Claudia per Andres
   • 16:30-18:30 Pallavolo Aurora
   ```
3. Il testo viene copiato subito negli appunti e mostrato in una finestra modificabile; "Copia di nuovo" ricopia il testo modificato.

Il numero di giorni è la costante `GIORNI_RIEPILOGO = 7` in `main.py`.

### Scelta del periodo (barra "Dal:")

Entrambe le finestre (testo e immagine) hanno in alto la barra creata da `_barra_data_inizio(parent, stato, al_cambio)`, che tiene il giorno di partenza in `stato["inizio"]` (di default oggi) e chiama `al_cambio()` a ogni modifica:

| Controllo | Effetto |
|---|---|
| `<<` / `>>` | indietro / avanti di `GIORNI_RIEPILOGO` giorni (una settimana) |
| `<` / `>` | indietro / avanti di un giorno |
| campo data + **Vai** o Invio | accetta `GG/MM/AAAA`, `GG/MM/AA` o `GG/MM` (anno corrente); `-` e `.` valgono come `/`. Data non valida → messaggio d'errore |
| **Oggi** | torna al giorno corrente |

Il campo data usa `interpreta_data(testo, riferimento)` (funzione in cima a `main.py`): accetta `GG/MM/AAAA`, `GG/MM/AA` e `GG/MM`; **senza anno sceglie l'anno che rende la data più vicina a oggi** (a ottobre `5/1` = 5 gennaio dell'anno dopo; `29/02` = il 29 febbraio più vicino). Non usa `strptime` senza anno, che in Python 3.13 dà un avviso.

`_testo_settimana(inizio)` e `_immagine_settimana(vista, inizio)` ricevono la data scelta. Le etichette "(oggi)" / "(domani)" del testo, il cerchio blu del calendario e "OGGI / domani / tra N giorni" dell'elenco restano riferiti alla **data reale di oggi**: se il periodo è tutto nel futuro o nel passato non compaiono, e per i giorni passati l'elenco mostra "ieri" / "N giorni fa" in grigio.

### Variante a immagine: 🖼️ Copia immagine

`copia_settimana_immagine()` in `main.py` usa gli stessi impegni, ma li raggruppa per **sezione** (stessa regola della scheda, §5, più "Veicoli") e chiama il modulo `immagine_settimana.py`:

- `crea_immagine(sezioni, inizio, fine)` disegna con **Pillow** un riquadro bianco per ogni sezione che ha impegni, con barra e titolo del colore della sezione; ogni riga mostra giorno, orario in un'etichetta colorata ("tutto il giorno" se senza orario), nome e a destra *OGGI* (rosso), *domani* (arancione) o *tra N giorni* (verde). Disegnata a doppia risoluzione (`SCALA = 2`) per restare nitida su WhatsApp.
- `copia_immagine_negli_appunti(img)` mette l'immagine negli appunti di Windows tramite `ctypes`, in formato DIB e PNG (quello che usano i browser). Solo su Windows.
- L'immagine viene salvata anche in `riepilogo_settimana.png` nella cartella del programma e mostrata in anteprima.

**Due viste**, scelte con i pulsanti in alto nella finestra di anteprima (cambiando vista l'immagine viene rigenerata e ricopiata):

- **📅 Calendario** (predefinita, `VISTA_IMMAGINE_PREDEFINITA` in `main.py`): `crea_immagine_calendario()` disegna una settimana stile Google Calendar con 7 colonne a partire da oggi (oggi evidenziato con il cerchio blu) e le ore a sinistra, da quella del primo impegno a quella dell'ultimo (minimo 4 ore). Ogni impegno con orario è un blocco del colore della sua sezione, con nome e orario; quelli "tutto il giorno" (e le scadenze dei veicoli) stanno in una fascia in alto. Gli impegni sovrapposti vanno **a cascata** (chi inizia dopo sta sopra, spostato a destra) oppure **affiancati** se iniziano a meno di 30 minuti uno dall'altro; il testo resta nella parte visibile del blocco. In fondo una legenda con i colori usati (`LEGENDA_BREVE`).
- **📋 Elenco**: `crea_immagine()`, un riquadro per sezione (descritta sopra).

Sezioni, titoli e colori sono nella lista `SEZIONI_RIEPILOGO` in `main.py`.

### ✏️ Modifica impegni (solo per l'immagine)

Il pulsante **✏️ Modifica impegni** della finestra immagine apre `_finestra_modifica_impegni()`: gli impegni del periodo scritti come un file di testo (`_testo_da_impegni()`), una riga per impegno, divisi per sezione:

```
# Scadenze
Gio 22/10  12:15-12:45  Trionfetti Aurora
Ven 23/10  17:30-19:00  Catechismo

# Feste e compleanni
Sab 24/10  Compleanno nonna
```

- Formato riga: `[giorno settimana] GG/MM[/AAAA]  [HH:MM[-HH:MM]]  Nome`. Il giorno della settimana è facoltativo e ignorato; senza orario = tutto il giorno; `9.00` vale come `09:00`.
- `# Visite`, `# Visite da prenotare`, `# Scadenze`, `# Feste e compleanni`, `# Veicoli` scelgono sezione e colore delle righe che seguono (basta l'inizio della parola, es. `# fest`). Righe prima di qualsiasi titolo → Scadenze.
- **🔄 Aggiorna immagine** (o Ctrl+Invio): `_impegni_da_testo()` legge il testo e l'immagine viene rigenerata e ricopiata. Le righe non valide (formato, data, orario di fine prima dell'inizio, data fuori dal periodo, sezione sconosciuta) vengono ignorate e elencate con il numero di riga.
- Le modifiche stanno solo in memoria (`stato["impegni_modificati"]`): valgono anche cambiando vista Calendario/Elenco e riaprendo l'editor, ma **non toccano i dati salvati**. Cambiando periodo con la barra "Dal:" vengono scartate e l'editor si ricarica dai dati; **↩️ Ripristina dai dati** le annulla.
- La finestra del testo (📋 Copia settimana) era già modificabile direttamente. Se Pillow manca il pulsante mostra come installarla; `avvia_scadenze.bat` ora controlla `plyer` **e** `PIL` e, se manca uno dei due, installa `requirements.txt`.

---

## 11. Personalizzazioni frequenti

| Cosa | Dove |
|---|---|
| Soglie di preavviso | `SOGLIA_*` in `main.py` **e** in `notifiche.py` |
| Nome del calendario Google | stringa `'Famiglia'` in `google_calendar.py` (3 punti) e `main.py` (import) |
| Promemoria degli eventi | `PROMEMORIA_RICORRENTI` / `PROMEMORIA_SINGOLI` in `google_calendar.py` |
| Colore di sfondo (versione classica) | `COLORE_SFONDO` in `main.py` (es. `"#f0f0f0"` chiaro, `"#cfd8dc"` grigio-azzurro, `"#b0bec5"` più scuro). I colori del testo di stato sono scuriti in `_imposta_stato()` per restare leggibili |
| Soglia arancione dei medicinali | la stessa `SOGLIA_GIORNI_PREAVVISO` delle altre scadenze |
| Velocità scroll (rotellina) schede Personali e Medicinali | `SCROLL_PIXEL_PER_UNITA` / `SCROLL_UNITA_PER_SCATTO` in `main.py` |
| Stima km/giorno | `km_medi_al_giorno = 50` in `esporta_scadenze_veicolo()` |
| Parole chiave per le sezioni | `_is_visita_personale`, `_is_visita_da_prenotare`, `_is_festa_compleanno` in `main.py` |
| Dati iniziali di esempio | `inizializza_db()` in `main.py` |

---

## 12. Revisione del codice

Verificata il 17/10/2026. I punti 1 e 2 sono stati **riprodotti con un test**.

### 🔴 Bug

**1. ✅ CORRETTO il 23/10/2026 — Le notifiche delle scadenze a data dei veicoli non partono mai.**
`notifiche.py`, `controlla_e_notifica()`, riga 28: usa la variabile `data_obj`, che in quella funzione non esiste. Ne nasce un `NameError`, nascosto dal `except: pass`, quindi Bollo, Assicurazione e Revisione **non generano mai notifiche**, nemmeno se scadute. (Le scadenze a km e quelle personali funzionano.)
Correzione: passare `None` al posto di `data_obj.get("ricorrenza")`.

**2. ✅ CORRETTO il 18/10/2026 — Ricorrenza mensile con intervallo > 1 salta occorrenze.**
`ricorrenze.py`, riga 60: l'indice di partenza è il numero di mesi trascorsi, ma viene poi moltiplicato per l'intervallo. Esempio: "ogni 2 mesi dal 15/01", oggi 01/03 → restituisce 15/05 invece di 15/03.
Correzione: partire da `(mese - mese_iniziale) // intervallo`.

**3. ✅ CORRETTO il 23/10/2026 — Il campo `categoria` viene perso al salvataggio.**
`salva_scadenze_personali()` riscrive ogni voce con solo `data/con_orario/ora_inizio/ora_fine/ricorrenza`. Una visita importata da Google con `categoria: visita_prenotata`, ma senza "visita" nel nome, dopo il primo "Salva Scadenze Personali" finisce nella sezione *Scadenze*.

**4. ✅ CORRETTO il 23/10/2026 — "+ Nuova Visita Prenotata" non registra la categoria.**
La voce viene messa tra le visite solo se il nome contiene "visita" o "medic". Una visita chiamata, per esempio, "Controllo oculistico" finisce tra le *Scadenze*; "Controllo oculistico da prenotare" non va tra le *Visite da prenotare*. Stesso discorso per le feste.

### 🟠 Rischi

**5. ✅ CORRETTO il 23/10/2026 (scrittura sicura + copie giornaliere, §8) — Scrittura del JSON non sicura.** `salva_dati()` sovrascrive direttamente il file: se il PC si spegne o l'app va in crash durante la scrittura, `stato_veicolo.json` può restare vuoto o corrotto e l'app non riparte più. Meglio scrivere su un file temporaneo e poi sostituire (`os.replace`), tenendo una copia `.bak`.

**6. ✅ CORRETTO il 23/10/2026 — Percorsi relativi.** Lanciando `main.py` da un'altra cartella si crea un nuovo file dati vuoto e non si trovano le credenziali Google. Meglio basare i percorsi su `os.path.dirname(__file__)`.

**7. ✅ CORRETTO il 23/10/2026 — Salvataggio parziale in memoria.** In `salva_scadenze_personali()` / `salva_scadenze_temp()`, se una riga a metà lista ha una data sbagliata, le righe precedenti sono già state modificate in memoria; non vengono scritte subito, ma lo saranno al prossimo salvataggio di qualsiasi altra cosa.

**8. Export duplicati su Google** (vedi §10): nessun controllo sugli eventi già presenti.

**9. In parte corretto il 23/10/2026 (in `notifiche.py` gli errori ora vengono stampati) — `except:` generici** in `notifiche.py` e nelle conversioni di data nascondono gli errori (è così che il bug 1 è rimasto invisibile).

### 🟡 Manutenibilità

- Soglie duplicate in due file: se ne cambi una sola, semaforo e notifiche non coincidono.
- Il blocco "Modulo Google Calendar non disponibile…" è copiato 5 volte in `main.py`.
- ✅ Corretto il 23/10/2026: il riconoscimento "è una visita?" ora usa ovunque `_sezione_personale()` (§5).
- `avvia_scadenze.bat` controlla `plyer` e `PIL`: se mancano le librerie Google l'app parte ma senza i pulsanti Calendar, senza avvisare.
- `README.md` in parte non aggiornato: non cita feste, import da Calendar e ricorrenze (promemoria e colori corretti il 17/10/2026).
- Il nome del veicolo è anche la chiave del dizionario: rinominarlo ricrea la chiave (gestito correttamente, ma fragile).

---

## 13. Versione moderna (eliminata)

Il 23/10/2026 è stata provata una versione con grafica moderna (`main_moderno.py`, customtkinter: angoli arrotondati, tema scuro), che ereditava la logica da `ScadenzeApp` e ridisegnava solo la finestra principale. È stata eliminata: si è preferita l'interfaccia classica, che è anche molto più veloce (ridisegno 0,05 s contro circa 0,45 s).

In `main.py` restano i piccoli metodi `_prepara_finestra()`, `_imposta_stato()` e `_abilita_campo()` nati per quella prova: non danno fastidio e tengono in un punto solo il modo di aggiornare i widget (es. i colori del testo di stato).
