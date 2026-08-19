from pathlib import Path

path = Path("src/Localization.cs")
text = path.read_text(encoding="utf-8")

old = '''    public static string T(string? source)
    {
        if (string.IsNullOrEmpty(source) || string.Equals(CurrentLanguage, "ru", StringComparison.OrdinalIgnoreCase)) return source ?? "";
        var lang = Phrases.TryGetValue(CurrentLanguage, out var requested) ? requested : Phrases["en"];
        if (lang.TryGetValue(source, out var exact)) return exact;
        if (!ReferenceEquals(lang, Phrases["en"]) && Phrases["en"].TryGetValue(source, out var englishExact)) return englishExact;
        return ReplaceKnown(source, lang);
    }
'''

new = '''    public static string T(string? source)
    {
        if (string.IsNullOrEmpty(source) || string.Equals(CurrentLanguage, "ru", StringComparison.OrdinalIgnoreCase)) return source ?? "";

        var lang = Phrases.TryGetValue(CurrentLanguage, out var requested) ? requested : Phrases["en"];

        // Normal path: the UI text is the canonical Russian key.
        if (lang.TryGetValue(source, out var exact)) return exact;

        // Some controls already contain English text (for example INTRO/Text).
        // Resolve that English value back to the canonical Russian key, then
        // translate it into the selected language instead of leaving a mixed UI.
        if (!ReferenceEquals(lang, Phrases["en"]))
        {
            foreach (var pair in Phrases["en"])
            {
                if (!string.Equals(pair.Value, source, StringComparison.Ordinal)) continue;
                if (lang.TryGetValue(pair.Key, out var localizedFromEnglish)) return localizedFromEnglish;
                return pair.Value;
            }
        }

        if (!ReferenceEquals(lang, Phrases["en"]) && Phrases["en"].TryGetValue(source, out var englishExact)) return englishExact;
        return ReplaceKnown(source, lang);
    }
'''

if old not in text:
    raise SystemExit("Localization hotfix target was not found")

path.write_text(text.replace(old, new), encoding="utf-8")
print("Applied 5.20 localization hotfix")
