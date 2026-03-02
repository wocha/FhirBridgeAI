# Setup Guide: Continue.dev mit lokaler Ollama Instanz (ROCm / RDNA3)

Diese Dokumentation führt dich durch das Setup von **Continue.dev** (VSCodium) in Kombination mit unserer neuen lokalen **Ollama-Instanz (ROCm)**, die via Docker betrieben wird. Ziel ist ein Architektur-Setup mit vollständiger Datenkontrolle (Zero-Cloud).

## Architektur-Überblick

Wir kombinieren das VRAM deiner AMD Radeon RX 7900 XT intelligent, um sowohl Background-Processing (`fhirbridge_llm_worker`) als auch deine Entwickler-Experience in VSCodium mit Continue.dev lokal und blitzschnell zu gewährleisten.

Dafür nutzen wir **drei spezialisierte Modelle**:

1. **Mistral-NeMo (12b)**: Für Autocomplete und primären Chat. (Sehr schnell, starker Kontext).
2. **Nomic-Embed-Text**: Der lokale Embedder (Voraussetzung für RAG / `@codebase` ohne externe APIs).
3. **DeepSeek-R1 (14b)**: Für Architektur-Fragen und tiefgründiges Reasoning.

## 1. Modelle in Ollama bereitstellen

Starte den Ollama-Container in deinem Terminal (bzw. setze einfach das gesamte Environment auf):

```bash
docker-compose up -d ollama
```

Anschließend müssen wir die drei Modelle initial in die Docker-Instanz pullen. Führe dazu nacheinander folgende Befehle aus:

```bash
docker exec -it fhirbridge_ollama ollama pull mistral-nemo
docker exec -it fhirbridge_ollama ollama pull deepseek-r1:14b
docker exec -it fhirbridge_ollama ollama pull nomic-embed-text
```

> [!TIP]
> Die Modelle werden nun dauerhaft in deinem Docker-Volume (`ollama_data`) gecacht!

## 2. Anpassung der `config.json` von Continue.dev

Öffne deine Continue.dev Config (Meistens unter `~/.continue/config.json` oder `%USERPROFILE%\.continue\config.json` unter Windows).
Passe die Datei folgendermaßen an:

```json
{
  "models": [
    {
      "title": "Mistral NeMo (Local)",
      "provider": "ollama",
      "model": "mistral-nemo",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "DeepSeek R1 14b (Reasoning)",
      "provider": "ollama",
      "model": "deepseek-r1:14b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Mistral NeMo Autocomplete",
    "provider": "ollama",
    "model": "mistral-nemo",
    "apiBase": "http://localhost:11434"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "apiBase": "http://localhost:11434"
  },
  "allowAnonymousTelemetry": false
}
```

## 3. Local Indexing (`@codebase`) konfigurieren

Da wir im `embeddingsProvider` nun `nomic-embed-text` lokal via Ollama hinterlegt haben, bleibt dein Code auf deiner Maschine.

- Öffne VSCodium.
- Gib im Continue.dev Chat `@codebase` gefolgt von deiner Fragestellung ein (z. B. *"@codebase wo finde ich die DLX Logik für RabbitMQ?"*).
- **Das erste Mal**, wenn du dies ausführst, wird Continue.dev beginnen, deine lokale Codebasis zu indexieren. Dieser Vorgang nutzt nun ausschließlich die Power deines RX 7900 XT VRAMs und schickt nichts in die Cloud.

## 4. Wichtiger Hinweis zum VRAM Setup (Resource Protection)

Sollte dein LLM_Worker im Hintergrund exzessiv viele PDF-Dokumente zu verarbeiten haben, greift die Semaphore (siehe `.env.example`: `RABBITMQ_PREFETCH_COUNT=1` und `LLM_MAX_CONCURRENCY=1`).
Dies schützt den Ollama-Server vor einem Thundering Herd-Problem und erlaubt es dir somit flüssig in Continue.dev weiter zu coden, ohne dass die Pipeline blockiert.
