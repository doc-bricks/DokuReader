# EXPORTFORMAT - DokuReader

Stand: 2026-11-18

## Zweck

`dokureader-library-v1.json` ist das stabile Austauschformat für die lokale Bibliothek von DokuReader. Der Export dient Web/PWA-Companions (`web_companion/`), Backups der Themenstruktur und dem bidirektionalen Lesestatus-Abgleich zwischen Desktop und Companion (`INV-SCHEMA-04`).

Der Standardexport enthält bewusst **keine Dokumentinhalte** und kopiert keine Dateien. Exportiert werden ausschließlich Themen, Dokumentpfade und Metadaten, die sich ohne Eingriff in die Originaldateien (`INV-INPLACE-03`) aus dem lokalen Zustand ableiten lassen.

## Stabilitätsregeln

- Dateiname des Formats: `dokureader-library-v1.json`
- `schema_version` ist für v1 immer exakt `dokureader-library-v1`
- Neue optionale Felder dürfen ergänzt werden
- Bestehende Felder dürfen in v1 nicht umbenannt oder in ihrem Typ geändert werden
- Ein späterer Bundle-Export mit echten Dateien ist **nicht** Teil dieses Formats und braucht ein eigenes Schema

## Top-Level-Schema

| Feld | Typ | Bedeutung |
|---|---|---|
| `schema_version` | String | Formatkennung, aktuell `dokureader-library-v1` |
| `exported_at` | String | UTC-Zeitstempel des Exports im ISO-8601-Format |
| `app_name` | String (optional beim Reimport) | Anzeigename der exportierenden App |
| `app_version` | String (optional beim Reimport) | App- oder Build-Stand der exportierenden Version |
| `current_topic` | String oder `null` | Zuletzt aktives Thema |
| `topics` | Array | Exportierte Themen |
| `totals` | Objekt | Summen über alle Themen |

## Themen

Jeder Eintrag in `topics` hat dieses Schema:

| Feld | Typ | Bedeutung |
|---|---|---|
| `name` | String | Themenname |
| `document_count` | Integer (optional beim Reimport) | Anzahl der exportierten Dokumenteinträge |
| `documents` | Array | Dokumente des Themas |

## Dokumente

Jeder Eintrag in `documents` hat dieses Schema:

| Feld | Typ | Bedeutung |
|---|---|---|
| `path` | String | Originalpfad der Datei auf dem Desktop-System |
| `filename` | String | Dateiname ohne Pfad |
| `extension` | String | Dateiendung inklusive Punkt, z. B. `.pdf` |
| `read` | Boolean | Gelesen-Status aus DokuReader bzw. Companion |
| `size_bytes` | Integer oder `null` | Dateigröße in Bytes, `null` wenn Datei fehlt |
| `mtime` | String oder `null` | Änderungszeit der Datei in UTC-ISO-8601, `null` wenn Datei fehlt |
| `missing` | Boolean | `true`, wenn der Pfad beim Export nicht auf eine lesbare Datei zeigte |

## Summen

`totals` enthält aktuell:

| Feld | Typ | Bedeutung |
|---|---|---|
| `topic_count` | Integer | Anzahl exportierter Themen |
| `document_count` | Integer | Anzahl exportierter Dokumente |
| `missing_documents` | Integer | Anzahl Dokumente mit `missing=true` |

## Beispiel

```json
{
  "schema_version": "dokureader-library-v1",
  "exported_at": "2026-05-26T09:18:11Z",
  "app_name": "Dokumentenbibliothek",
  "app_version": "1.0.1-dev",
  "current_topic": "Forschung",
  "topics": [
    {
      "name": "Forschung",
      "document_count": 2,
      "documents": [
        {
          "path": "C:/Users/User/Documents/Paper.pdf",
          "filename": "Paper.pdf",
          "extension": ".pdf",
          "read": true,
          "size_bytes": 182044,
          "mtime": "2026-05-25T18:42:01Z",
          "missing": false
        },
        {
          "path": "C:/Users/User/Documents/Notizen.txt",
          "filename": "Notizen.txt",
          "extension": ".txt",
          "read": false,
          "size_bytes": null,
          "mtime": null,
          "missing": true
        }
      ]
    }
  ],
  "totals": {
    "topic_count": 1,
    "document_count": 2,
    "missing_documents": 1
  }
}
```

## Desktop-Verhalten (Export & Lesestatus-Reimport)

### 1. Export (`JSON-Export…`)
- Die GUI exportiert immer die gesamte Bibliothek, nicht nur das aktuell sichtbare Thema.
- Das aktuell gewählte Thema wird zusätzlich als `current_topic` mitgegeben.
- Der Export schreibt atomar (`.tmp` + `fsync` + `os.replace`) in UTF-8 mit echten Umlauten und verweigert das Überschreiben geschützter Originaldokumente sowie der internen Bibliotheksdatei.
- Dokumentinhalte, Vorschaubilder, PDFs und Binärdateien werden nicht eingebettet.

### 2. Lesestatus-Reimport (`Status importieren…`)
- Über `Status importieren…` (`read_library_export` + `State.reconcile_from_export`) liest die Desktop-App eine im Web/PWA-Companion aktualisierte `dokureader-library-v1.json`-Datei (Größenwächter max. 16 MiB, strikte Schema- und Typprüfung).
- Abgeglichen wird ausschließlich das boolesche Feld `read` für bereits in der lokalen Desktop-Bibliothek vorhandene `(Thema, Pfad)`-Einträge (exakter Pfad oder kanonischer absoluter Pfad-Alias innerhalb desselben Themas).
- **Sicherheitsinvarianten beim Reimport:**
  - Fremde Themen oder unbekannte Dateipfade aus der Importdatei werden niemals automatisch in die lokale Bibliothek eingefügt (`unmatched` wird gezählt und übersprungen).
  - Lokale Themen oder Dokumente, die im älteren Companion-Export fehlen, bleiben vollständig erhalten.
  - Originaldateien im Dateisystem werden zu keinem Zeitpunkt verändert, verschoben oder gelöscht (`INV-INPLACE-03`).
  - Die aktualisierte Bibliothek wird atomar in `.dokubibliothek_state.json` gespeichert.
