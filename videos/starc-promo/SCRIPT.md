# Voix off

Voix générée avec Magnific (ElevenLabs v3), voix « Julien Bouchard »
(masculine, française, posée). Une réplique par scène, placée au temps
indiqué dans la colonne « Départ » pour que les mots clés tombent sur les
images (par exemple « noir sur blanc » au moment où l'écran bascule en blanc).

Les répliques sont dans `assets/audio/voix/` (vo01.mp3 à vo10.mp3) et sont
placées dans `index.html` (pistes `el-vo01` à `el-vo10`, groupe `voiceover`).
La musique est creusée sous la voix par le « voiceover carve » de HyperFrames
(attributs `data-fx-carve`, `data-fx-chain` et `data-automation` de `el-bgm`).
Après avoir déplacé ou remplacé une réplique, relancer le carve :

```bash
node <skills>/hyperframes-audio/scripts/carve.mjs --comp index.html --strength 0.6
```

| Scène | Départ | Durée | Texte | Réplique Magnific |
|-------|--------|-------|-------|-------------------|
| 01 | 1,2 s | 3,8 s | Du premier trait à la dernière pierre... construire demande de la rigueur. | https://www.magnific.com/app/creation/mE7FOKihJQ |
| 02 | 10,8 s | 2,9 s | Starc. Studio d'architecture, à Gembloux. | https://www.magnific.com/app/creation/JNd3BTmOq4 |
| 03 | 14,6 s | 8,7 s | Architectes, ingénieurs, responsable PEB, auditeurs énergétiques, hydrologues, architectes d'intérieur : toutes les compétences, sous un même toit. | https://www.magnific.com/app/creation/WDqd5KDcXe |
| 04 | 24,6 s | 10,8 s | Notre bureau fonctionne comme une chaîne de montage. L'architecte « gentil » conçoit votre projet et décroche le permis. Le « méchant » prend le relais : exécution, appel d'offres et chantier. | https://www.magnific.com/app/creation/cpbXKlQ0eP |
| 05 | 38,8 s | 5,8 s | Quatre équipes travaillent en parallèle : de quoi absorber une forte charge, et réagir vite en cas d'urgence. | https://www.magnific.com/app/creation/0e5BkJHTfW |
| 06 | 46,7 s | 5,7 s | Scanner trois D, drones, rendus photoréalistes : nos outils sont à la pointe de la technologie. | https://www.magnific.com/app/creation/WDqd5GxcXe |
| 07 | 56,8 s | 5,9 s | Nos honoraires sont fixés au forfait, dès la signature. Aucune surprise : tout est posé noir sur blanc. | https://www.magnific.com/app/creation/gOV4pUISXO |
| 08 | 65,0 s | 6,1 s | Votre projet s'adapte à vos besoins, à vos envies, à vos contraintes. Chaque projet est une création unique. | https://www.magnific.com/app/creation/mE7FyFyhJQ |
| 09 | 77,0 s | 2,2 s | Plus de cinq cents références construites en témoignent. | https://www.magnific.com/app/creation/SyM9e27Ub8 |
| 10 | 82,6 s | 5,2 s | Starc. Bâtir avec rigueur. Un projet ? Parlons-en ! | https://www.magnific.com/app/creation/rgnwc3Axtc |
