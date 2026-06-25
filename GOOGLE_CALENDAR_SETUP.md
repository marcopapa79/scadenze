# Setup Google Calendar - Guida Passo-Passo

Questa guida ti aiuta a configurare l'esportazione delle scadenze su Google Calendar.

## 📋 Prerequisiti

1. **Account Google** attivo
2. **Accesso a Google Cloud Console**

## 🔧 Setup (da fare una sola volta)

### Passo 1: Crea un Progetto su Google Cloud

1. Vai su [Google Cloud Console](https://console.cloud.google.com)
2. Clicca su **"Nuovo Progetto"** (in alto a sinistra)
3. Dai un nome al progetto (es: "Gestione Scadenze")
4. Clicca **"Crea"**

### Passo 2: Abilita Google Calendar API

1. Nel menu laterale, vai su **"API e servizi" → "Libreria"**
2. Cerca **"Google Calendar API"**
3. Clicca sul risultato
4. Clicca **"Abilita"**

### Passo 3: Crea Credenziali OAuth 2.0

1. Nel menu laterale, vai su **"API e servizi" → "Credenziali"**
2. Clicca **"+ Crea credenziali"** → **"ID client OAuth"**
3. Se richiesto, configura la schermata consenso:
   - Tipo: **"Esterno"**
   - Nome app: **"Gestione Scadenze"**
   - Email assistenza: la tua email
   - Clicca **"Salva e continua"** fino alla fine
4. Torna a "Credenziali" e clicca **"+ Crea credenziali" → "ID client OAuth"**
5. Tipo di applicazione: **"Applicazione desktop"**
6. Nome: **"Gestione Scadenze Desktop"**
7. Clicca **"Crea"**

### Passo 4: Scarica il File Credenziali

1. Nella lista delle credenziali, trova quella appena creata
2. Clicca sull'icona **download** (⬇) a destra
3. **Rinomina** il file scaricato in **`credentials.json`**
4. **Sposta** il file nella cartella del progetto `scadenze`

```
C:\My_Designs\scadenze\
  ├── main.py
  ├── google_calendar.py
  ├── credentials.json  ← QUI
  └── ...
```

## ✅ Installazione Dipendenze

Apri il terminale nella cartella del progetto ed esegui:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Oppure:

```bash
pip install -r requirements.txt
```

## 🚀 Primo Utilizzo

1. **Avvia l'applicazione**: `python main.py`
2. Vai nel tab **"🚗 Veicoli"** o **"📋 Scadenze Personali"**
3. Clicca sul pulsante **"📅 Esporta su Calendar"**
4. **La prima volta**:
   - Si aprirà il browser
   - Scegli il tuo account Google
   - Clicca **"Consenti"** per dare i permessi
   - Il browser dirà "Authentication successful" → chiudi la pagina
5. Le scadenze verranno create su Google Calendar!

## 🔒 Sicurezza

**IMPORTANTE**: 
- Il file `credentials.json` contiene le tue credenziali private
- **NON condividerlo** con nessuno
- **NON caricarlo** su GitHub/repository pubblici
- È già incluso nel `.gitignore`

## ❓ Risoluzione Problemi

### "File credentials.json non trovato"
→ Assicurati che il file sia nella cartella del progetto e si chiami esattamente `credentials.json`

### "Modulo Google Calendar non disponibile"
→ Installa le dipendenze: `pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`

### "Permission denied" o errore 403
→ Verifica di aver abilitato Google Calendar API nel progetto Google Cloud

### Vuoi ricominciare l'autenticazione
→ Elimina il file `token.pickle` e riprova

## 🎯 Cosa Viene Esportato

### Scadenze Veicoli:
- ⚠️ Scadenze temporali (Bollo, Assicurazione, Revisione)
- 🔧 Scadenze chilometriche (con data stimata basata su 50 km/giorno)
- 🔴 Eventi colorati in rosso per maggiore visibilità
- 🔔 Promemoria automatici: 7 giorni, 3 giorni e 1 giorno prima

### Scadenze Personali:
- 📋 Tutte le scadenze (ISEE, Casa, Documenti, ecc.)
- 🔴 Eventi colorati in rosso
- 🔔 Promemoria automatici

## 📚 Link Utili

- [Google Cloud Console](https://console.cloud.google.com)
- [Documentazione Google Calendar API](https://developers.google.com/calendar/api/v3/reference)
- [Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
