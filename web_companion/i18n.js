/**
 * i18n.js — Tier-2 6-language localization catalog & helpers for DokuReader Companion
 * Languages: de, en, es, zh, ja, ru (Policy P-006 Full Set)
 * Zero external dependencies; 4-step fallback: lang -> en -> de -> key.
 */

export const SUPPORTED_LANGUAGES = Object.freeze(["de", "en", "es", "zh", "ja", "ru"]);

export const LANGUAGE_LABELS = Object.freeze({
  de: "Deutsch",
  en: "English",
  es: "Español",
  zh: "简体中文",
  ja: "日本語",
  ru: "Русский"
});

export const DATE_LOCALES = Object.freeze({
  de: "de-DE",
  en: "en-US",
  es: "es-ES",
  zh: "zh-CN",
  ja: "ja-JP",
  ru: "ru-RU"
});

export const TRANSLATIONS = Object.freeze({
  de: Object.freeze({
    app_title: "DokuReader Companion",
    lang_label: "Sprache auswählen",
    import_btn: "JSON importieren",
    demo_btn: "Demo laden",
    export_btn: "Status exportieren",
    clear_btn: "Lokale Daten löschen",
    drop_zone_help: "dokureader-library-v1.json hierher ziehen oder zum Auswählen aktivieren",
    topics_heading: "Themen",
    all_topics: "Alle Themen",
    search_placeholder: "Dokument suchen…",
    search_aria: "Dokument suchen",
    show_missing: "Fehlende anzeigen",
    empty_no_library: "Noch keine Bibliothek geladen.",
    empty_no_results: "Keine Dokumente gefunden.",
    status_loaded: "{topicCount} Themen · {docCount} Dokumente geladen",
    status_restored: "Gespeicherte Bibliothek wiederhergestellt ({topicCount} Themen · {docCount} Dokumente).",
    status_exported: "Bibliothek mit aktuellem Lesestatus exportiert.",
    status_cleared: "Lokale Bibliotheksdaten gelöscht.",
    status_invalid_json: "Ungültige JSON-Datei.",
    status_read_error: "Datei konnte nicht gelesen werden.",
    status_corrupt_cleared: "Beschädigter lokaler Zwischenspeicher wurde zurückgesetzt.",
    status_storage_quota: "Bibliothek geladen (lokaler Offline-Speicher voll — nicht dauerhaft gesichert).",
    status_error_prefix: "Fehler: {message}",
    badge_read: "✓ Gelesen",
    badge_unread: "Ungelesen",
    state_read: "Gelesen",
    state_unread: "Ungelesen",
    card_aria_toggle: "{filename} — {state}, Klicken zum Umschalten",
    missing_flag: "⚠ Datei fehlt"
  }),
  en: Object.freeze({
    app_title: "DokuReader Companion",
    lang_label: "Select language",
    import_btn: "Import JSON",
    demo_btn: "Load demo",
    export_btn: "Export status",
    clear_btn: "Clear local data",
    drop_zone_help: "Drop dokureader-library-v1.json here or activate to browse",
    topics_heading: "Topics",
    all_topics: "All topics",
    search_placeholder: "Search document…",
    search_aria: "Search document",
    show_missing: "Show missing",
    empty_no_library: "No library loaded yet.",
    empty_no_results: "No documents found.",
    status_loaded: "{topicCount} topics · {docCount} documents loaded",
    status_restored: "Saved library restored ({topicCount} topics · {docCount} documents).",
    status_exported: "Library exported with current read status.",
    status_cleared: "Local library data cleared.",
    status_invalid_json: "Invalid JSON file.",
    status_read_error: "File could not be read.",
    status_corrupt_cleared: "Corrupted local cache was reset.",
    status_storage_quota: "Library loaded (local offline storage full — not persisted).",
    status_error_prefix: "Error: {message}",
    badge_read: "✓ Read",
    badge_unread: "Unread",
    state_read: "Read",
    state_unread: "Unread",
    card_aria_toggle: "{filename} — {state}, activate to toggle",
    missing_flag: "⚠ File missing"
  }),
  es: Object.freeze({
    app_title: "DokuReader Companion",
    lang_label: "Seleccionar idioma",
    import_btn: "Importar JSON",
    demo_btn: "Cargar demo",
    export_btn: "Exportar estado",
    clear_btn: "Borrar datos locales",
    drop_zone_help: "Arrastra dokureader-library-v1.json aquí o activa para seleccionar",
    topics_heading: "Temas",
    all_topics: "Todos los temas",
    search_placeholder: "Buscar documento…",
    search_aria: "Buscar documento",
    show_missing: "Mostrar faltantes",
    empty_no_library: "Aún no se ha cargado ninguna biblioteca.",
    empty_no_results: "No se encontraron documentos.",
    status_loaded: "{topicCount} temas · {docCount} documentos cargados",
    status_restored: "Biblioteca guardada restaurada ({topicCount} temas · {docCount} documentos).",
    status_exported: "Biblioteca exportada con el estado de lectura actual.",
    status_cleared: "Datos locales de la biblioteca borrados.",
    status_invalid_json: "Archivo JSON no válido.",
    status_read_error: "No se pudo leer el archivo.",
    status_corrupt_cleared: "Se restableció la caché local dañada.",
    status_storage_quota: "Biblioteca cargada (almacenamiento local sin conexión lleno).",
    status_error_prefix: "Error: {message}",
    badge_read: "✓ Leído",
    badge_unread: "No leído",
    state_read: "Leído",
    state_unread: "No leído",
    card_aria_toggle: "{filename} — {state}, activar para cambiar",
    missing_flag: "⚠ Falta el archivo"
  }),
  zh: Object.freeze({
    app_title: "DokuReader Companion",
    lang_label: "选择语言",
    import_btn: "导入 JSON",
    demo_btn: "加载演示",
    export_btn: "导出状态",
    clear_btn: "清除本地数据",
    drop_zone_help: "将 dokureader-library-v1.json 拖放到此处或点击选择文件",
    topics_heading: "主题",
    all_topics: "所有主题",
    search_placeholder: "搜索文档…",
    search_aria: "搜索文档",
    show_missing: "显示缺失文件",
    empty_no_library: "尚未加载任何文献库。",
    empty_no_results: "未找到匹配的文档。",
    status_loaded: "已加载 {topicCount} 个主题 · {docCount} 份文档",
    status_restored: "已恢复本地保存的文献库（{topicCount} 个主题 · {docCount} 份文档）。",
    status_exported: "已导出包含最新阅读状态的文献库。",
    status_cleared: "已清除本地文献库数据。",
    status_invalid_json: "无效的 JSON 文件。",
    status_read_error: "无法读取文件。",
    status_corrupt_cleared: "损坏的本地缓存已重置。",
    status_storage_quota: "文献库已加载（本地离线存储空间已满，未能持久化保存）。",
    status_error_prefix: "错误：{message}",
    badge_read: "✓ 已读",
    badge_unread: "未读",
    state_read: "已读",
    state_unread: "未读",
    card_aria_toggle: "{filename} — {state}，点击切换阅读状态",
    missing_flag: "⚠ 文件缺失"
  }),
  ja: Object.freeze({
    app_title: "DokuReader Companion",
    lang_label: "言語を選択",
    import_btn: "JSON をインポート",
    demo_btn: "デモを読み込む",
    export_btn: "状態をエクスポート",
    clear_btn: "ローカルデータを消去",
    drop_zone_help: "dokureader-library-v1.json をここにドロップするか選択してください",
    topics_heading: "トピック",
    all_topics: "すべてのトピック",
    search_placeholder: "ドキュメントを検索…",
    search_aria: "ドキュメントを検索",
    show_missing: "欠落ファイルを表示",
    empty_no_library: "ライブラリはまだ読み込まれていません。",
    empty_no_results: "ドキュメントが見つかりませんでした。",
    status_loaded: "{topicCount} 件のトピック・{docCount} 件のドキュメントを読み込みました",
    status_restored: "保存済みライブラリを復元しました（{topicCount} 件のトピック・{docCount} 件のドキュメント）。",
    status_exported: "現在の既読状態を含むライブラリをエクスポートしました。",
    status_cleared: "ローカルのライブラリデータを消去しました。",
    status_invalid_json: "無効な JSON ファイルです。",
    status_read_error: "ファイルを読み込めませんでした。",
    status_corrupt_cleared: "破損したローカルキャッシュをリセットしました。",
    status_storage_quota: "ライブラリを読み込みました（ローカル保存容量の上限に達しています）。",
    status_error_prefix: "エラー: {message}",
    badge_read: "✓ 既読",
    badge_unread: "未読",
    state_read: "既読",
    state_unread: "未読",
    card_aria_toggle: "{filename} — {state}、クリックして切り替え",
    missing_flag: "⚠ ファイル欠落"
  }),
  ru: Object.freeze({
    app_title: "DokuReader Companion",
    lang_label: "Выбрать язык",
    import_btn: "Импорт JSON",
    demo_btn: "Загрузить демо",
    export_btn: "Экспорт статуса",
    clear_btn: "Очистить локальные данные",
    drop_zone_help: "Перетащите dokureader-library-v1.json сюда или нажмите для выбора",
    topics_heading: "Темы",
    all_topics: "Все темы",
    search_placeholder: "Поиск документа…",
    search_aria: "Поиск документа",
    show_missing: "Показать отсутствующие",
    empty_no_library: "Библиотека ещё не загружена.",
    empty_no_results: "Документы не найдены.",
    status_loaded: "Загружено тем: {topicCount} · документов: {docCount}",
    status_restored: "Сохранённая библиотека восстановлена (тем: {topicCount} · документов: {docCount}).",
    status_exported: "Библиотека экспортирована с текущим статусом прочтения.",
    status_cleared: "Локальные данные библиотеки удалены.",
    status_invalid_json: "Некорректный JSON-файл.",
    status_read_error: "Не удалось прочитать файл.",
    status_corrupt_cleared: "Повреждённый локальный кэш был сброшен.",
    status_storage_quota: "Библиотека загружена (локальное хранилище заполнено).",
    status_error_prefix: "Ошибка: {message}",
    badge_read: "✓ Прочитано",
    badge_unread: "Не прочитано",
    state_read: "Прочитано",
    state_unread: "Не прочитано",
    card_aria_toggle: "{filename} — {state}, нажмите для переключения",
    missing_flag: "⚠ Файл отсутствует"
  })
});

export function normalizeLanguage(input, fallback = "de") {
  const safeFallback = SUPPORTED_LANGUAGES.includes(fallback) ? fallback : "de";
  if (typeof input !== "string" || !input.trim()) {
    return safeFallback;
  }
  const base = input.trim().toLowerCase().split(/[-_]/)[0];
  return SUPPORTED_LANGUAGES.includes(base) ? base : safeFallback;
}

export function getDateLocale(lang = "de") {
  return DATE_LOCALES[normalizeLanguage(lang)] || DATE_LOCALES.de;
}

export function t(key, lang = "de", params = {}) {
  const norm = normalizeLanguage(lang);
  const template =
    TRANSLATIONS[norm]?.[key] ??
    TRANSLATIONS.en[key] ??
    TRANSLATIONS.de[key] ??
    String(key);

  if (!params || typeof params !== "object") {
    return template;
  }
  return template.replace(/\{([a-zA-Z0-9_]+)\}/g, (match, token) =>
    Object.prototype.hasOwnProperty.call(params, token) ? String(params[token]) : match
  );
}
