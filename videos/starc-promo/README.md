# STARC, film de présentation (HyperFrames)

Film promotionnel de 90 secondes pour STARC, Studio d'architecture (Gembloux),
réalisé avec [HyperFrames](https://hyperframes.heygen.com) : chaque scène est une
page HTML animée avec GSAP, rendue en MP4 par un navigateur sans interface.

Vidéo finale : `renders/starc-promo.mp4` (1920 x 1080, 30 i/s, 90 s).

## Contenu

| Temps | Scène | Message |
|-------|-------|---------|
| 0 à 8 s | 01-hook | Du premier trait à la dernière pierre. Concevoir, calculer, construire. |
| 8 à 12 s | 02-logo | Logo STARC, « Bâtir avec rigueur. » |
| 12 à 24 s | 03-equipe | Multidisciplinarité : 9 métiers sous un même toit, 25 collaborateurs, 0 sous-traitance, 1 interlocuteur. |
| 24 à 38 s | 04-chaine | Efficacité : la chaîne de montage, l'architecte « gentil » et l'architecte « méchant ». |
| 38 à 46 s | 05-equipes | 4 équipes en parallèle, épaulées par dessinateurs, ingénieurs et architectes d'intérieur. |
| 46 à 54 s | 06-outils | Scanner 3D, drones, rendus 3D. |
| 54 à 64 s | 07-forfait | Honoraires au forfait (10/20/20/20/30 %), « Tout est posé noir sur blanc. » |
| 64 à 74 s | 08-sur-mesure | Vos besoins, vos envies, vos contraintes : un projet unique. |
| 74 à 82 s | 09-references | Mur de réalisations, 500+ références construites. |
| 82 à 90 s | 10-contact | Un projet ? Parlons-en. www.starc.be |

Les textes, chiffres et photos proviennent de www.starc.be. La charte STARC est
respectée : noir et blanc uniquement pour le graphisme, Bebas Neue et Montserrat,
logo officiel inséré tel quel.

## Structure

```
index.html              composition principale (enchaîne les 10 scènes + musique)
compositions/           une sous-composition HTML par scène
assets/projects/        photos de réalisations (starc.be)
assets/mosaic/          157 vignettes pour le mur de références
assets/logos/           logos STARC blanc et noir
assets/fonts/           Bebas Neue et Montserrat
assets/audio/bgm.mp3    bande-son originale (générée par tools/make_bgm.py)
assets/vendor/          GSAP 3.14.2
STORYBOARD.md           découpage détaillé
SCRIPT.md               texte de voix off prêt à enregistrer
```

## Commandes

```bash
npx hyperframes preview          # prévisualiser et modifier dans le navigateur
npx hyperframes lint             # vérifier la composition
npx hyperframes render --quality delivery -o renders/starc-promo.mp4
python3 tools/make_bgm.py bgm_raw.wav   # régénérer la musique (puis loudnorm ffmpeg)
```

## Ajouter la voix off

1. Enregistrer ou générer le texte de `SCRIPT.md` (une piste continue de 90 s,
   calée sur les temps indiqués).
2. Déposer le fichier dans `assets/audio/voiceover.wav`.
3. Décommenter la ligne `el-voiceover` dans `index.html` et baisser
   `data-volume` de `el-bgm` vers 0.35.
4. Relancer le rendu.
