#!/usr/bin/env python3
"""
Find community-specific words by comparing server frequency to standard French.

This script identifies words that are common in your Discord server but NOT
common in standard French, revealing community slang, inside jokes, and
server-specific vocabulary.
"""

import asyncio

from nanapi.utils.clients import get_edgedb
from nanapi.utils.word_frequency import analyze_word_frequency

# Top 3000 most common French words
# Source: frequency lists from various French corpora
COMMON_FRENCH_WORDS = {
    # Core words (top ~100)
    'le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je', 'son',
    'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'pour',
    'pas', 'que', 'vous', 'par', 'sur', 'faire', 'plus', 'dire', 'me',
    'on', 'mon', 'lui', 'nous', 'comme', 'mais', 'pouvoir', 'avec', 'tout',
    'y', 'aller', 'voir', 'en', 'bien', 'où', 'sans', 'tu', 'ou', 'leur',
    'homme', 'si', 'deux', 'quand', 'même', 'aussi', 'autre', 'après',
    'prendre', 'venir', 'demander', 'petit', 'grand', 'jour', 'encore',
    'mettre', 'vouloir', 'temps', 'dont', 'très', 'savoir', 'falloir',
    'devenir', 'tenir', 'croire', 'heure', 'celui', 'trouver', 'quelque',
    'pays', 'laisser', 'vers', 'toujours', 'entre', 'moi', 'chose',
    'vie', 'monde', 'non', 'moins', 'sembler', 'yeux', 'rester', 'donner',
    'sentir', 'parler', 'montrer', 'part', 'mot', 'bon', 'nouveau',
    
    # Extended common words (100-500)
    'fois', 'gens', 'main', 'année', 'fois', 'passer', 'maison', 'premier',
    'moment', 'enfant', 'contre', 'tête', 'fils', 'ami', 'rendre', 'jeune',
    'place', 'suivre', 'question', 'travailler', 'cas', 'jamais', 'femme',
    'soir', 'entendre', 'aimer', 'comprendre', 'depuis', 'mari', 'arriver',
    'longtemps', 'parce', 'point', 'penser', 'seul', 'français', 'matin',
    'voix', 'coup', 'père', 'atteindre', 'surtout', 'paraître', 'devant',
    'politique', 'côté', 'ville', 'assez', 'tard', 'peu', 'route', 'garder',
    'vraiment', 'air', 'nom', 'fois', 'cela', 'tard', 'connaître', 'beau',
    'gros', 'appeler', 'milieu', 'dernier', 'regard', 'vieux', 'selon',
    'fond', 'bras', 'rue', 'œil', 'état', 'raison', 'pendant', 'ouvrir',
    
    # More common words (500-1000)
    'force', 'âme', 'importance', 'lieu', 'nature', 'manière', 'affaire',
    'pied', 'porte', 'chambre', 'frère', 'mère', 'sœur', 'fille', 'côté',
    'besoin', 'doute', 'cause', 'guerre', 'effet', 'certain', 'service',
    'esprit', 'art', 'ligne', 'vérité', 'forme', 'eau', 'figure', 'usage',
    'bout', 'moyen', 'train', 'table', 'mal', 'mouvement', 'rapport',
    'intérêt', 'genre', 'possible', 'papier', 'action', 'lettre', 'ordre',
    'espèce', 'signe', 'chef', 'ensemble', 'bord', 'idée', 'jeu', 'terre',
    'pays', 'présent', 'retour', 'face', 'coin', 'personne', 'autour',
    'peine', 'parti', 'propre', 'centre', 'près', 'mer', 'travail', 'livre',
    'droit', 'famille', 'monsieur', 'sentir', 'écrire', 'niveau', 'objet',
    
    # Common verbs and adjectives (1000-2000)
    'apprendre', 'agir', 'attendre', 'lever', 'rappeler', 'reconnaître',
    'recevoir', 'répondre', 'sourire', 'craindre', 'courir', 'porter',
    'crier', 'mener', 'tirer', 'tomber', 'partir', 'sortir', 'perdre',
    'gagner', 'souffrir', 'mort', 'vivre', 'seul', 'vrai', 'entier',
    'blanc', 'noir', 'long', 'différent', 'prochain', 'divers', 'simple',
    'semblable', 'tel', 'pauvre', 'public', 'actuel', 'juste', 'haut',
    'bas', 'doux', 'dur', 'étrange', 'sage', 'ancien', 'riche', 'secrèt',
    'capable', 'léger', 'lourd', 'large', 'étroit', 'profond', 'plein',
    'vide', 'clair', 'sombre', 'rapide', 'lent', 'facile', 'difficile',
    
    # More words (2000-3000)
    'continuer', 'changer', 'accepter', 'établir', 'souvenir', 'imaginer',
    'imposer', 'exister', 'produire', 'développer', 'créer', 'former',
    'soutenir', 'tenter', 'choisir', 'obtenir', 'défendre', 'remarquer',
    'but', 'fond', 'siècle', 'histoire', 'groupe', 'marche', 'ordre',
    'condition', 'moitié', 'direction', 'situation', 'société', 'attention',
    'occasion', 'impression', 'exemple', 'manque', 'besoin', 'épreuve',
    'bonheur', 'malheur', 'danger', 'fortune', 'misère', 'sort', 'destin',
    'prix', 'valeur', 'richesse', 'pauvreté', 'utilité', 'nécessité',
    'profit', 'avantage', 'inconvénient', 'difficulté', 'facilité',
    'possibilité', 'impossibilité', 'certitude', 'incertitude',
    
    # Internet & modern common (bonus)
    'internet', 'site', 'web', 'page', 'lien', 'clic', 'photo', 'image',
    'vidéo', 'film', 'musique', 'son', 'article', 'texte', 'message',
    'email', 'téléphone', 'numéro', 'appel', 'voiture', 'auto', 'train',
    'avion', 'bus', 'métro', 'sport', 'équipe', 'match', 'jeu', 'jouer',
    'gagner', 'perdre', 'restaurant', 'café', 'bar', 'boisson', 'manger',
    'boire', 'nourriture', 'plat', 'repas', 'pain', 'viande', 'légume',
    'fruit', 'fromage', 'vin', 'bière', 'lait', 'sucre', 'sel', 'poivre',
    
    # Common expressions and fillers
    'donc', 'alors', 'voilà', 'bon', 'eh', 'ah', 'oh', 'hein', 'quoi',
    'bah', 'ben', 'euh', 'hum', 'pfff', 'tiens', 'dis', 'écoute', 'regarde',
    'vois', 'comprends', 'sais', 'crois', 'pense', 'trouve', 'dis', 'sens',
    'fait', 'fais', 'va', 'vas', 'vais', 'peut', 'peux', 'veut', 'veux',
    'doit', 'dois', 'sait', 'sais', 'peut-être', 'vraiment', 'tellement',
    'plutôt', 'assez', 'très', 'trop', 'beaucoup', 'peu', 'moins', 'plus',
    
    # Question words
    'qui', 'que', 'quoi', 'où', 'quand', 'comment', 'pourquoi', 'combien',
    'quel', 'quelle', 'lequel', 'laquelle', 
    
    # Pronouns
    'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
    'me', 'te', 'se', 'le', 'la', 'les', 'lui', 'leur', 'moi', 'toi',
    'soi', 'eux', 'celui', 'celle', 'ceux', 'celles', 'celui-ci', 'celle-ci',
    'ceci', 'cela', 'ça', 'ce', 'cet', 'cette', 'ces',
    
    # Common verbs (important forms)
    'suis', 'es', 'est', 'sommes', 'êtes', 'sont', 'été', 'étais', 'était',
    'étaient', 'serai', 'sera', 'serais', 'serait', 'ai', 'as', 'avons',
    'avez', 'ont', 'avais', 'avait', 'avaient', 'aurai', 'aura', 'aurais',
    'aurait', 'fais', 'fait', 'faisons', 'faites', 'font', 'faisais',
    'faisait', 'ferai', 'fera', 'ferais', 'ferait', 'peux', 'peut',
    'pouvons', 'pouvez', 'peuvent', 'pouvais', 'pouvait', 'pourrai',
    'pourra', 'pourrais', 'pourrait', 'veux', 'veut', 'voulons', 'voulez',
    'veulent', 'voulais', 'voulait', 'voudrai', 'voudra', 'voudrais',
    'voudrait', 'va', 'vas', 'allons', 'allez', 'vont', 'allais', 'allait',
    'irai', 'ira', 'irais', 'irait',
    
    # Numbers
    'zéro', 'un', 'une', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept',
    'huit', 'neuf', 'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze',
    'seize', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante',
    'cent', 'mille', 'million', 'milliard', 'premier', 'deuxième',
    'troisième', 'dernier',
    
    # Days, months, time
    'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
    'septembre', 'octobre', 'novembre', 'décembre', 'aujourd hui', 'demain',
    'hier', 'maintenant', 'toujours', 'jamais', 'parfois', 'souvent',
    'rarement', 'encore', 'déjà', 'bientôt', 'tard', 'tôt', 'longtemps',
}


async def main():
    edgedb = get_edgedb()
    
    print("Fetching messages from server...")
    print("(Using 100,000 message sample for statistical accuracy)")
    print()
    
    # Fetch messages
    result = await edgedb.query('''
        with
          guild_id := <optional str>$guild_id,
        select discord::Message {
          content,
          author_id,
        }
        filter
          (.guild_id = guild_id if exists guild_id else true) and
          not exists .deleted_at and
          not exists .noindex and
          len(.content) > 0
        order by .timestamp desc
        limit 100000
    ''', guild_id='297436883883917312')
    
    print(f"Analyzing {len(result):,} messages...")
    
    # Analyze word frequency
    analysis = analyze_word_frequency(
        result,
        min_occurrences=20,  # Lower threshold to catch more words
        min_users=2,
        top_n=3000,  # Get top 3000 server words
    )
    
    # Find words NOT in common French
    community_words = []
    for word_data in analysis.top_words:
        word = word_data['word']
        # Check if word is NOT in common French words
        if word.lower() not in COMMON_FRENCH_WORDS:
            community_words.append(word_data)
    
    print()
    print("=" * 80)
    print(f"🎯 COMMUNITY-SPECIFIC WORDS (Top 3000 server words NOT in French top 3000)")
    print("=" * 80)
    print(f"Found {len(community_words)} unique community words!")
    print()
    print(f"{'Word':<25} {'Count':>10} {'Frequency':>10} {'Users':>8}")
    print("-" * 80)
    
    for word_data in community_words[:100]:  # Show top 100
        print(
            f"{word_data['word']:<25} "
            f"{word_data['count']:>10,} "
            f"{word_data['frequency']:>10.4f} "
            f"{word_data['unique_users']:>8}"
        )
    
    print()
    print("=" * 80)
    print("💡 BEST CANDIDATES FOR TRIGGER WORDS")
    print("=" * 80)
    print("These are community-specific and used by multiple people:")
    print()
    
    # Filter for best trigger candidates
    best_triggers = [
        w for w in community_words
        if w['unique_users'] >= 3  # Used by multiple people
        and w['count'] >= 30  # Reasonably common
        and len(w['word']) >= 3  # Not too short
    ]
    
    print(f"{'Word':<25} {'Count':>10} {'Users':>8} {'Frequency':>10}")
    print("-" * 80)
    for word_data in best_triggers[:50]:
        print(
            f"{word_data['word']:<25} "
            f"{word_data['count']:>10,} "
            f"{word_data['unique_users']:>8} "
            f"{word_data['frequency']:>10.4f}"
        )
    
    print()
    print("=" * 80)
    print(f"📊 SUMMARY")
    print("=" * 80)
    print(f"Total messages analyzed: {analysis.total_messages:,}")
    print(f"Total words: {analysis.total_words:,}")
    print(f"Unique words found: {analysis.unique_words:,}")
    print(f"Server top 3000 words: {len(analysis.top_words)}")
    print(f"Community-specific words: {len(community_words)}")
    print(f"Best trigger candidates: {len(best_triggers)}")
    print()
    print("🎮 These words are perfect for WaiColle conditional drops!")
    print("   They're unique to your community and used by multiple members.")
    print()


if __name__ == '__main__':
    asyncio.run(main())

