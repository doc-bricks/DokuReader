# EXPORTFORMAT - DokuReader

Stand: 2026-05-30

## Zweck

`dokureader-library-v1.json` ist das stabile Austauschformat für die lokale Bibliothek von DokuReader. Der Export ist für Web/PWA-Companions, Backups der Themenstruktur und spätere Status-Synchronisation gedacht.

Der Standardexport enthält bewusst **keine Dokumentinhalte** und kopiert keine Dateien. Exportiert werden nur Themen, Dokumentpfade und Metadaten, die sich ohne Eingriff in die Originaldateien aus dem lokalen Zustand ableiten lassen.

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
| `app_name` | String | Anzeigename der Desktop-App |
| `app_version` | String | App- oder Build-Stand der exportierenden Version |
| `current_topic` | String oder `null` | Im Desktop zuletzt aktives Thema |
| `topics` | Array | Exportierte Themen |
| `totals` | Objekt | Summen über alle Themen |

## Themen

Jeder Eintrag in `topics` hat dieses Schema:

| Feld | Typ | Bedeutung |
|---|---|---|
| `name` | String | Themenname |
| `document_count` | Integer | Anzahl der exportierten Dokumenteinträge |
| `documents` | Array | Dokumente des Themas |

## Dokumente

Jeder Eintrag in `documents` hat dieses Schema:

| Feld | Typ | Bedeutung |
|---|---|---|
| `path` | String | Originalpfad der Datei auf dem Desktop-System |
| `filename` | String | Dateiname ohne Pfad |
| `extension` | String | Dateiendung inklusive Punkt, z. B. `.pdf` |
| `read` | Boolean | Gelesen-Status aus DokuReader |
| `size_bytes` | Integer oder `null` | Dateigröße in Bytes, `null` wenn Datei fehlt |
| `mtime` | String oder `null` | Änderungszeit der Datei in UTC-ISO-8601, `null` wenn Datei fehlt |
| `missing` | Boolean | `true`, wenn der Pfad aktuell nicht mehr auf eine lesbare Datei zeigt |

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

## Desktop-Verhalten

- Die GUI exportiert immer die gesamte Bibliothek, nicht nur das aktuell sichtbare Thema
- Das aktuell gewählte Thema wird zusätzlich als `current_topic` mitgegeben
- Der Export nutzt UTF-8 und schreibt echte Umlaute
- Dokumentinhalte, Vorschaubilder, PDFs und Binärdateien werden nicht eingebettet

## Folgearbeit

- Rückexport für Lesestatus aus einem Companion-Format definieren
- Optionales Bundle-Format separat planen, falls mobile Offline-Pakete wirklich gebraucht werden
