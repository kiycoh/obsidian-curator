# Glossario Topic NLP - Vault Mapping Reference

## Mappatura Topic → Note Esistenti nel Vault

| Topic | Nota Canonica (Canonical Path) | Key Content |
|-------|-------------------------------|-------------|
| **Corpus** | `1.1.2 Intelligenza artificiale/Natural Language Processing/Corpus paralleli.md` |棕色, reuters, brown corpus, NLTK corpus methods |
| **POS Tagging / Part-of-Speech** | `Analisi lessicale (NLP).md` | Token tagging, universal tagset, DT/NN/VBZ tags |
| **Regular Expressions** | `NLP Pre-processing.md` | re module pattern matching, search/replace operations |
| **Edit Distance / Levenshtein** | `Edit distance (NLP).md` | Minimum edit distance algorithm, string similarity |
| **Logistic Regression** | `Applicazioni NLP.md` | Discriminative classifier, cross-entropy loss |
| **TF-IDF** | `Applicazioni NLP.md` | Term frequency, inverse document frequency formula |
| **N-gram / Language Modeling** | `Applicazioni NLP.md` | Bigram/trigram, Markov assumption, perplexity |
| **Naive Bayes Classifier** | `Applicazioni NLP.md` | Multinomial Naive Bayes, Laplace smoothing |
| **Tokenization** | `Tokenization/Tokenization (NLP).md` | Word token types, stemming, wordform/lemma |
| **Text Normalization** | `NLP Pre-processing.md` | Text cleaning, normalization pipeline steps |
| **NLTK Library** | `NLTK.md` | nltk.download(), Text class, FreqDist() |
| **Natural Language Processing (Intro)** | `Natural Language Processing (NLP).md` | NLP definition, Turing test, ELIZA chatbot |

## File Speciali nel Vault

| Nome File | Status | Contenuto |
|-----------|--------|-----------|
| `lezione-2025-12-25.md` | placeholder | Solo immagine, da verificare |
| `LEZIONE-2025-12-17.md` | placeholder | Solo immagine, da verificare |
| `NoteTraining.md` | placeholder | Solo immagine, da verificare |

## Topics Non Coperti (Richiedono Nuove Note)

1. **Neural Networks** - Simple NN, activation functions (sigmoid/tanh), weighted sum
2. **Word Embeddings** - Word meaning, synonymy/antonymy, semantic fields, vector semantics  
3. **Project Guidelines** - Struttura relazione progetto NLP, indicazioni esame
4. **Eliza Chatbot** - Conversational agent basics, ELIZA examples
5. **Universal Dependencies Tagset** - Complete 17 POS categories (UD standard)

## Best Practices per Mapping

### Quando usare `enrich`:
- Topic coperto da nota esistente MA il file contiene:
  - Dettagli specifici di laboratorio/lezioni
  - Esempi pratici NLTK non presenti nella nota originale
  - Formule matematiche aggiuntive
  - Esercizi o attività pratiche

### Quando usare `new`:
- Topic completamente nuovo/non menzionato nel vault
- File placeholder vuoto (solo immagini)
- Guide amministrative/procedurali (es: Extra_Progetti.md)

### Evita di duplicare:
- Contenuto near-identico (>80% sovrapposizione testuale)
- Stee same esercizi ripetuti
- Esempi già esistenti nella nota canonica
