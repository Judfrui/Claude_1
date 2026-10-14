# Voix off

Voix générée avec Magnific (Google Gemini 2.5 Pro TTS), voix « Charon »,
avec la consigne : « Lis comme le narrateur d'un film de présentation
d'entreprise. Français standard, accent neutre, sans accent parisien ni accent
régional marqué. Ton posé, assuré et chaleureux, débit modéré. »
Une réplique par scène, placée au temps indiqué dans la colonne « Départ » pour
que les mots clés tombent sur les images (par exemple « noir sur blanc » au
moment où l'écran bascule en blanc).

Chaque réplique est légèrement compressée, ramenée à -16 LUFS et limitée à
-1,5 dB. La réplique 03 est accélérée de 5 % pour tenir dans sa scène.

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
| 01 | 1,2 s | 4,7 s | Du premier trait à la dernière pierre... construire demande de la rigueur. | https://www.magnific.com/app/creation/LwcyxtPswO |
| 02 | 10,4 s | 3,6 s | Starc. Studio d'architecture, à Gembloux. | https://www.magnific.com/app/creation/fHPKvoQCDY |
| 03 | 14,05 s | 9,95 s | Architectes, ingénieurs, responsable PEB, auditeurs énergétiques, hydrologues, architectes d'intérieur : toutes les compétences, sous un même toit. | https://www.magnific.com/app/creation/LwcyjVjswO |
| 04 | 24,4 s | 11,65 s | Notre bureau fonctionne comme une chaîne de montage. L'architecte « gentil » conçoit votre projet et décroche le permis. Le « méchant » prend le relais : exécution, appel d'offres et chantier. | https://www.magnific.com/app/creation/1lzwkDXr4r |
| 05 | 38,8 s | 5,98 s | Quatre équipes travaillent en parallèle : de quoi absorber une forte charge, et réagir vite en cas d'urgence. | https://www.magnific.com/app/creation/nVFezJDYQD |
| 06 | 46,7 s | 6,53 s | Scanner trois D, drones, rendus photoréalistes : nos outils sont à la pointe de la technologie. | https://www.magnific.com/app/creation/jUWOxHDLD0 |
| 07 | 56,56 s | 6,16 s | Nos honoraires sont fixés au forfait, dès la signature. Aucune surprise : tout est posé noir sur blanc. | https://www.magnific.com/app/creation/tCwFIX8mZJ |
| 08 | 65,0 s | 7,15 s | Votre projet s'adapte à vos besoins, à vos envies, à vos contraintes. Chaque projet est une création unique. | https://www.magnific.com/app/creation/SyMNS7AUb8 |
| 09 | 77,0 s | 2,84 s | Plus de cinq cents références construites en témoignent. | https://www.magnific.com/app/creation/s70Ps7Dl8e |
| 10 | 82,8 s | 5,19 s | Starc. Bâtir avec rigueur. Un projet ? Parlons-en ! | https://www.magnific.com/app/creation/ksGUkUt16B |
