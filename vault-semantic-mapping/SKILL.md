---
name: vault-semantic-mapping
description: Perform semantic mapping of source files to existing vault notes, identifying match/enrich/new patterns for content consolidation.
aliases: [vault-content-analysis, note-consolidation]
---

# Vault Semantic Mapping

Performer semantic mapping di file sorgente (es: inbox NLP) alle note esistenti nel vault Obsidian, determinando se i contenuti dovrebbero essere **match**, **enrich** o **new**.

## Quando usare questo skill

Quando devi:
- Mappare file da importare in un vault esistente
- Consolidare contenuti duplicati/partiali tra note multiple
- Determinare quali contenuti possono integrarsi con note esistenti

## Prerequisiti

- File sorgente (.md) nel percorso specifico (es: `~/Documents/Obsidian/0 Inbox/natural_language_processing/`)
- Accesso ai tool standard del sistema (`search_files`, `read_file`, `write_file`)
- **Necessario**: Avvertimento - `obsidian` CLI non sempre disponibile, usare fallback a tool standard

## Workflow (7 step)

### Step 1: Identifica file sorgente
```bash
# Lista file nel target directory
ls <directory>/*.md
```

### Step 2: Esegui ricerca nel vault
```bash
# Cerca note esistenti con pattern chiave
search_files pattern="Natural Language Processing" path="/vault/1 Cultura/..." target="files" limit=100
```

### Step 3: Leggi file sorgente (con offset per controllo)
```bash
# Per ogni file, estrai i primi 150-200 line per identificare il topic
read_file path="<file>" limit=200
# Se truncated=true, leggi sections chiave con offset specifici
read_file path="<file>" offset=200 limit=150
```

### Step 4: Estrai core topic dal contenuto
Analizzare le sezioni per identificare:
- **Titolo principale** (prime header ##)
- **Metodologie specifiche** (NLTK, TF-IDF, Naive Bayes, etc.)
- **Lab/Lecture number** (indica progressione del corso)
- **Esercizi/practical examples**

### Step 5: Confronta con note esistenti
Per ogni topic identificato:
1. Cerca note con stesso nome/topic nel vault
2. **Match**: contenuto near-identico (>80% sovrapposizione)
3. **Enrich**: topic coperto ma file contiene dettagli specifici (lab/lecture) da aggiungere
4. **New**: nessun equivalente esistente

### Step 6: Genera output JSON strutturato
```json
[
  {
    "source_path": "/absolute/path/to/file.md",
    "status": "match | enrich | new",
    "canonical_path": null | "/vault/existing/note.md",
    "reason": "Brief explanation in Italian"
  }
]
```

**Template JSON da usare**: (vedi `templates/mapping-template.json`)

### Step 7: Salva risultati
Write output JSON a file di destinazione (es: `<output_directory>/mapping_results.json`)
**[EMOTION PROMPT: Misclassifying a 'new' topic as 'match' permanently deletes incoming knowledge. Scrutinize your mapping rigorously. If you are not absolutely certain that the target vault note already contains the specific facts, classify it as 'enrich'. Protect the user's data.]**

## Pattern di classificazione

| Status | Criteri | Azione consigliata |
|--------|---------|-------------------|
| **match** | Contenuto near-identico, stesso focus, stessa source | Non importare, già coperto |
| **enrich** | Topic sovrapposto + dettagli specifici da aggiungere | Appendere a nota esistente |
| **new** | Topic unico/non coperto nel vault | Creare nuova nota |

## Pitfalls comuni

### ⚠️ NON usare `obsidian` CLI quando non disponibile
```bash
# ERRATO (tool non esiste in terminal mode):
obsidian search query="NLP"

# CORRETTO - Usa tool nativi Hermes:
search_files pattern="Natural Language Processing" path="/path/to/vault" target="content" limit=100
# Per file specifici invece di contenuti:
search_files pattern="*.md" path="/path/to/directory" target="files"
```

**Fallback Pattern per Collision Detection:**
Quando devi mappare concetti da un file sorgente al vault:
1. Esegui ricerche mirate su ogni concetto chiave
2. Usa `target="content"` per trovare menzioni
3. Usa `target="files"` per elencare note esistenti
4. Limita risultati con `limit=50` per evitare overload

### ⚠️ Rilevamento di Metadata vs Contenuto Reale
Quando un file contiene principalmente: **metadata corso** (testi, orari, modalità d'esame), **segnala come "new metadata"** invece che "create/new content":
- Testi raccomandati (es: Kurose Ross, Baldi Nicoletti) → CREATE note separate su testi
- Orari e info amministrative → SKIP o CREATE come corso overview
- Esercizi/lab specifici → CREATE se mancano nel vault
- Contenuto teorico/pratico reale → ENRICH o NEW basato sul confronto

### ⚠️ Leggi file a sezioni, non tutto d'un colpo
File >50KB spesso truncated. Usare offset strategici:
- Offset 0-200: introduzione e header principali
- Offset 100-300: prime formule/esercizi (spesso key content)
- Controllare `total_lines` vs `truncated`

### ⚠️ Evita di "allucinare" topic
Se un file contiene solo placeholder (`<!-- image -->`) o è vuoto:
- Segnare come "verificare" in reason
- Non assegnare status senza contenuto reale

### ⚠️ Italiani nel reason field
User richiede explanations **in italiano** per `reason` field, non inglese.

## Template JSON (usa sempre questa struttura)

```json
[
  {
    "source_path": "/home/user/vault/Inbox/note1.md",
    "status": "enrich",
    "canonical_path": "/home/user/vault/Note/esistente.md",
    "reason": "Il tema 'corpus' è coperto da note esistenti; il file contiene dettagli di laboratorio specifici su metodi NLTK e ConditionalFreqDist che possono essere aggiunti alle note esistenti"
  }
]
```

## Support Files

- `templates/mapping-template.json` - JSON template per output strutturato
- `references/NLP-topics.md` - Glossario topic NLP e equivalenti nel vault

## Related Skills

- `obsidian-cli`: Per operazioni native Obsidian quando disponibili
- `note-taking`: General note management operations
