CLEANUP_PROMPT_TEMPLATES = {
'en': """
    You are an expert data pre-processor. Your task is to clean, reformat, and chunk raw markdown text from a website for a Retrieval-Augmented Generation (RAG) system's vector database.
    The content's primary language is **English**. Use this to inform your cleaning process, especially when identifying and removing boilerplate text like legal notices.

    Follow these rules precisely:

    **Part 1: Cleaning and Formatting**
    1.  **Preserve Core Content:** Keep all meaningful paragraphs, headings, lists, and factual information.
    2.  **Keep Important Links:** Preserve important inline markdown links `[like this](...)` that are part of a sentence's context.
    3.  **Remove Noise:** Delete all of the following:
        *   Repetitive navigation bars, headers, and footers.
        *   Advertisements and promotional banners.
        *   Cookie consent notices and language-specific legal disclaimers.
        *   Image tags `![...](...)` and social media links.
        *   Boilerplate text that doesn't add unique value.
    4.  **Format Cleanly:** Ensure the output is clean, well-structured markdown with proper spacing.

    **Part 2: Chunking**
    1.  **Split by Topic:** After cleaning, split the text into logical, self-contained chunks. Each chunk should focus on a single, specific topic (e.g., a person's profile, a specific project, a single feature).
    2.  **Keep Related Information Together:** Ensure that related information, like a person's name, role, and bio, are all in the same chunk. Do not split them.
    3.  **Use a Separator:** Separate each chunk with `---CHUNK_SEPARATOR---`. This is critical.
    4.  **Do Not Alter Content:** Do not rephrase or summarize the original text. Output the chunks exactly as they appear in the source.
    5.  **Handle Short Texts:** If the entire text is short and covers a single topic, output it as a single chunk without a separator.

    **Final Output:**
    *   Do not add any commentary or explanation.
    *   Only output the cleaned and chunked markdown, with the separator between chunks.

    Here is the raw markdown text:
    ---
    {raw_markdown}
    ---
""",

'de': """
    Sie sind ein Experte für die Vorverarbeitung von Daten. Ihre Aufgabe ist es, rohen Markdown-Text von einer Website zu bereinigen, neu zu formatieren und in Chunks aufzuteilen für die Vektordatenbank eines Retrieval-Augmented Generation (RAG) Systems.
    Die Hauptsprache des Inhalts ist **Deutsch**. Nutzen Sie dies, um Ihren Bereinigungsprozess zu steuern, insbesondere bei der Identifizierung und Entfernung von Standardtexten wie rechtlichen Hinweisen (z.B. Impressum, Datenschutz, AGB).

    Befolgen Sie diese Regeln genau:

    **Teil 1: Bereinigung und Formatierung**
    1.  **Kerninhalte erhalten:** Behalten Sie alle aussagekräftigen Absätze, Überschriften, Listen und sachlichen Informationen bei.
    2.  **Wichtige Links erhalten:** Behalten Sie wichtige Inline-Markdown-Links `[wie dieser](...)`, die Teil des Satzkontextes sind, bei.
    3.  **Störungen entfernen:** Löschen Sie Folgendes:
        *   Wiederholende Navigationsleisten, Kopf- und Fußzeilen.
        *   Werbeanzeigen und Werbebanner.
        *   Cookie-Einwilligungshinweise und sprachspezifische rechtliche Hinweise.
        *   Bild-Tags `![...](...)` und Social-Media-Links.
        *   Standardtexte, die keinen einzigartigen Wert hinzufügen.
    4.  **Sauber formatieren:** Stellen Sie sicher, dass die Ausgabe sauberer, gut strukturierter Markdown mit korrektem Abstand ist.

    **Teil 2: Chunking**
    1.  **Nach Thema aufteilen:** Teilen Sie den Text nach der Bereinigung in logische, in sich geschlossene Chunks auf. Jeder Chunk sollte sich auf ein einziges, spezifisches Thema konzentrieren (z. B. das Profil einer Person, ein bestimmtes Projekt, ein einzelnes Merkmal).
    2.  **Zusammengehörige Informationen zusammenhalten:** Stellen Sie sicher, dass zusammengehörige Informationen wie der Name, die Rolle und die Biografie einer Person im selben Chunk sind. Trennen Sie sie nicht.
    3.  **Trennzeichen verwenden:** Trennen Sie jeden Chunk mit `---CHUNK_SEPARATOR---`. Das ist entscheidend.
    4.  **Inhalt nicht verändern:** Formulieren Sie den Originaltext nicht um oder fassen Sie ihn nicht zusammen. Geben Sie die Chunks genau so aus, wie sie in der Quelle erscheinen.
    5.  **Kurze Texte behandeln:** Wenn der gesamte Text kurz ist und ein einziges Thema abdeckt, geben Sie ihn als einen einzigen Chunk ohne Trennzeichen aus.

    **Endgültige Ausgabe:**
    *   Fügen Sie keine Kommentare oder Erklärungen hinzu.
    *   Geben Sie nur den bereinigten und in Chunks aufgeteilten Markdown aus, mit dem Trennzeichen zwischen den Chunks.

    Hier ist der rohe Markdown-Text:
    ---
    {raw_markdown}
    ---
""",


'fr': """
    Vous êtes un expert en pré-traitement de données. Votre tâche est de nettoyer, reformater et segmenter du texte Markdown brut d'un site web pour la base de données vectorielle d'un système de génération augmentée par récupération (RAG).
    La langue principale du contenu est le **français**. Utilisez cette information pour guider votre processus de nettoyage, notamment pour identifier et supprimer les textes standards comme les mentions légales (par exemple, mentions légales, politique de confidentialité, CGV).

    Suivez ces règles précisément :

    **Partie 1 : Nettoyage et formatage**
    1.  **Conserver le contenu de base :** Gardez tous les paragraphes, titres, listes et informations factuelles significatifs.
    2.  **Conserver les liens importants :** Préservez les liens Markdown en ligne importants `[comme celui-ci](...)` qui font partie du contexte d'une phrase.
    3.  **Supprimer le bruit :** Supprimez tout ce qui suit :
        *   Barres de navigation, en-têtes et pieds de page répétitifs.
        *   Publicités et bannières promotionnelles.
        *   Avis de consentement aux cookies et mentions légales spécifiques à la langue.
        *   Balises d'image `![...](...)` et liens vers les réseaux sociaux.
        *   Texte standard qui n'ajoute pas de valeur unique.
    4.  **Mettre en forme proprement :** Assurez-vous que la sortie est un Markdown propre, bien structuré avec un espacement correct.

    **Partie 2 : Segmentation**
    1.  **Diviser par sujet :** Après le nettoyage, divisez le texte en segments logiques et autonomes. Chaque segment doit se concentrer sur un seul sujet spécifique (par exemple, le profil d'une personne, un projet spécifique, une seule fonctionnalité).
    2.  **Garder les informations connexes ensemble :** Assurez-vous que les informations connexes, comme le nom, le rôle et la biographie d'une personne, se trouvent dans le même segment. Ne les séparez pas.
    3.  **Utiliser un séparateur :** Séparez chaque segment avec `---CHUNK_SEPARATOR---`. C'est crucial.
    4.  **Ne pas modifier le contenu :** Ne reformulez pas et ne résumez pas le texte original. Sortez les segments exactement tels qu'ils apparaissent dans la source.
    5.  **Gérer les textes courts :** Si l'ensemble du texte est court et couvre un seul sujet, sortez-le en un seul segment sans séparateur.

    **Sortie finale :**
    *   N'ajoutez aucun commentaire ou explication.
    *   Sortez uniquement le Markdown nettoyé et segmenté, avec le séparateur entre les segments.

    Voici le texte Markdown brut :
    ---
    """
}

PDF_CLEANUP_PROMPT_TEMPLATES = {
    'en': """
    You are an expert document cleaner. Your task is to take raw text extracted from a PDF and reconstruct it into clean, readable Markdown.

    The content's primary language is **English**.

    **Instructions:**
    1.  **Remove Artifacts:** Delete headers, footers, page numbers (e.g., "Page 1 of 5"), and repetitive legal disclaimers that appear on every page.
    2.  **Fix Broken Text:** Join sentences that were split across page breaks. Fix hyphenated words that were split at the end of a line (e.g., "infor- mation" -> "information").
    3.  **Structure:** Use Markdown headers (#, ##, ###) to structure the document based on the text's hierarchy. Use bullet points for lists.
    4.  **Preserve Content:** Do not summarize. Keep all factual information, numbers, and names exactly as they are.
    5.  **Output:** Return ONLY the cleaned Markdown text. Do not add any conversational filler.

    **Raw Text:**
    ---
    {raw_text}
    ---
    """,

    'de': """
    Sie sind ein Experte für Dokumentenbereinigung. Ihre Aufgabe ist es, rohen Text, der aus einem PDF extrahiert wurde, in sauberes, lesbares Markdown umzuwandeln.

    Die Hauptsprache des Inhalts ist **Deutsch**.

    **Anweisungen:**
    1.  **Artefakte entfernen:** Löschen Sie Kopfzeilen, Fußzeilen, Seitenzahlen (z. B. "Seite 1 von 5") und wiederkehrende rechtliche Hinweise.
    2.  **Gebrochenen Text reparieren:** Fügen Sie Sätze zusammen, die durch Seitenumbrüche getrennt wurden. Korrigieren Sie Wörter, die am Zeilenende getrennt wurden (z. B. "Infor- mation" -> "Information").
    3.  **Struktur:** Verwenden Sie Markdown-Überschriften (#, ##, ###), um das Dokument basierend auf der Hierarchie des Textes zu strukturieren. Verwenden Sie Aufzählungszeichen für Listen.
    4.  **Inhalt bewahren:** Fassen Sie nicht zusammen. Behalten Sie alle sachlichen Informationen, Zahlen und Namen genau so bei, wie sie sind.
    5.  **Ausgabe:** Geben Sie NUR den bereinigten Markdown-Text zurück. Fügen Sie keine konversationellen Füllwörter hinzu.

    **Roher Text:**
    ---
    {raw_text}
    ---
    """,

    'fr': """
    Vous êtes un expert en nettoyage de documents. Votre tâche est de prendre du texte brut extrait d'un PDF et de le reconstruire en Markdown propre et lisible.

    La langue principale du contenu est le **Français**.

    **Instructions :**
    1.  **Supprimer les artefacts :** Supprimez les en-têtes, les pieds de page, les numéros de page (par exemple, "Page 1 sur 5") et les mentions légales répétitives.
    2.  **Réparer le texte cassé :** Joignez les phrases qui ont été coupées par des sauts de page. Corrigez les mots coupés en fin de ligne (par exemple, "infor- mation" -> "information").
    3.  **Structure :** Utilisez des en-têtes Markdown (#, ##, ###) pour structurer le document en fonction de la hiérarchie du texte. Utilisez des puces pour les listes.
    4.  **Préserver le contenu :** Ne résumez pas. Gardez toutes les informations factuelles, les chiffres et les noms exactement tels qu'ils sont.
    5.  **Sortie :** Retournez UNIQUEMENT le texte Markdown nettoyé. N'ajoutez pas de remplissage conversationnel.

    **Texte brut :**
    ---
    {raw_text}
    ---
    """
}

REPHRASE_PROMPTS = {
    'en': ("human", "Given a chat history and a follow up question, rephrase the follow up question to be a standalone question. Preserve important user information (e.g their Hometown, their Job-Title etc.)"),
    'de': ("human", "Formulieren Sie anhand eines Chat-Verlaufs und einer Folgefrage die Folgefrage so um, dass sie als eigenständige Frage stehen kann. Bewahre wichtige Benutzerinformationen (z. B. Heimatort, Berufsbezeichnung usw.) auf."),
    'fr': ("human", "Étant donné un historique de discussion et une question de suivi, reformulez la question de suivi pour qu'elle soit une question autonome. Conservez les informations importantes concernant les utilisateurs (par exemple, leur ville natale, leur fonction, etc.).")
}

FINE_TUNE_RULE_PROMPTS = {
    'en': "If the user's question is in some way related to '{trigger}', use the following guideline for your response: '{instruction}'",
    'de': "Wenn die Frage des Benutzers sich in irgend einer Weise auf '{trigger}' bezieht, verwende die folgende Richtlinie für deine Antwort: '{instruction}'",
    'fr': "Si la question de l'utilisateur se rapporte d'une manière ou d'une autre à '{trigger}', utilisez la ligne directrice suivante pour votre réponse: '{instruction}'"
}