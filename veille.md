# Veille juridique — ChocoBot

## 1. Ce qui s'applique maintenant

| Risque                           | Statut                               | Pour ChocoBot                                                                                                                                                     |
| -------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RGPD**                         | Depuis 25/05/2018                    | **Critique** : allergies = donnée de santé (Art.9), âge enfants = personnes vulnérables                                                                           |
| **AI Act Art.50 (transparence)** | **Depuis 02/08/2026, sanctionnable** | **Critique** : dire dès le 1er message qu'on parle à une IA. Jusqu'à 15 M€ ou 3% CA                                                                               |
| AI Act haut risque (Annexe III)  | Reporté au 02/12/2027                | Non concerné (pas de RH/score/crédit/biométrie)                                                                                                                   |
| **AIPD (Art.35)**                | Applicable                           | **Requise en principe** (≥ 2 critères CEPD : santé, personnes vulnérables, IA). Grande échelle non démontrée : à confirmer, réalisation recommandée par prudence. |

---

## 2. RGPD — Les 5 points qui visent ChocoBot

1. **Allergies = donnée de santé (Art.9)** → consentement explicite et distinct dans `/profile`, sinon avertissement + purge des révélations spontanées dans le chat libre. *Réf. : CNIL IQVIA 26/05/2026 — 5 M€.*
2. **Conservation sans limite** (`db.py`) → fixer des durées et purger. *Réf. : Free 13/01/2026 — 42 M€.*
3. **Sécurité** → `/admin` et `/admin/data` sans auth, `chocobot.db` en clair = violation Art.32. Prévoir chiffrement, MFA, journalisation, et notification CNIL sous **72h** en cas de fuite.
4. **Information & droits** → pas de notice RGPD, pas de procédure d'effacement par `session_id`. Délai de réponse : 1 mois. *Réf. : EXTIA 21/07/2026 — 300 k€.*
5. **Bases légales distinctes par finalité** : répondre ≠ conserver l'historique ≠ entraîner un modèle ≠ cibler une offre.

**AIPD obligatoire** : allergies + enfants + LLM = 3 critères (2 suffisent). À réaliser avant mise en service, + registre Art.30, + DPO recommandé.

---

## 3. AI Act — Art.50 transparence (la date ratée par beaucoup)

L'Omnibus 2026/1744 a reporté le haut risque, **mais pas l'Art.50** : applicable depuis le **02/08/2026**.

- **Art.50(1)** : notice visible en langage clair **au 1er message** ("Vous parlez à Clémence, assistante IA de la Maison Delcourt"). Une mention en CGU ne suffit pas. Exception "évident" quasi jamais applicable,.
  → `chatbot.py:8` se présente comme "conseillère" sans mention IA = **non conforme**.
- **Art.5** : pas d'inférence d'émotions, de scoring, de manipulation.
- ChocoBot n'est **pas haut risque** : pas de marquage CE ni de base EU.

**Sanctions** : 15 M€ ou 3% CA mondial  (S'adapte en fonction de la taille de l'entreprise) (Art.99).

**Articulation** : RGPD et AI Act s'appliquent cumulativement — l'AI Act ne crée aucun régime dérogatoire (CNIL/CIANum 20/07/2026).

---

## 4. Autres textes

| Texte | Application |
|---|---|
| Cookies (Art.82 LIL) | Cookie à l'activation explicite + strictement nécessaire → exempté. Avant activation ou usage pub → consentement. Bouton "Refuser" aussi simple qu'accepter |
| Code conso. L121-1 | Pratique trompeuse si le chat invente un coffret/prix hors `catalog.json` (température 0.7 → risque d'hallucination) |
| Transferts hors UE | `llm.py` en local = bon point. Toute bascule API externe exige DPA + CCT |

---

## 5. Plan d'action

**Immédiat**
1. Bandeau IA au 1er message dans `static/index.html`.
2. Authentifier `/admin` et restreindre `/admin/data`, chiffrer ou migrer la base.
3. Durées de conservation + purge (`DELETE WHERE created_at < ...`).
4. Page `/confidentialite` (finalités, bases, destinataires, durées, droits).

**1–2 mois**
5. Case de consentement distincte pour les allergies + avertissement dans le chat.
6. Procédure d'effacement (vous + sous-traitant LLM), testée.
7. AIPD (modèle CNIL) + registre Art.30 + DPA.

**Q4 2026 – Q1 2027**
8. Formation Art.4 (traces conservées).
9. Température `0.7 → 0.2`, garde-fou catalogue, bouton "Parler à un humain".
10. Audit du cookie `session_id`.
11. Veille CNIL/EDPB/AI Office. Échéances : **02/12/2026** (marquage, deepfakes), **02/12/2027** (haut risque).

---

## 6. Sources principales

- RGPD : `eur-lex.europa.eu/eli/reg/2016/679` — Loi 78-17 (CNIL)
- AI Act : `eur-lex.europa.eu/eli/reg/2024/1689` — Omnibus `eur-lex.europa.eu/eli/reg/2026/1744`
- Calendrier : `ai-act-service-desk.ec.europa.eu` — FAQ Art.50 (24/07/2026)

- Sanctions : EXTIA 300 k€ (2026), EU AI Act Art.99 (2026)
- Doctrine : `donneespersonnelles.fr` — `cnil.fr`

---

## 7. Annexes — cartographie des données (Registre Art.30)

| Donnée          | Catégorie                           | Base                       | Durée                                          | Risque                |
| --------------- | ----------------------------------- | -------------------------- | ---------------------------------------------- | --------------------- |
| `session_id`    | Identifiant technique               | Intérêt légitime / service | Session + 6 mois                               | Faible                |
| `name`, `email` | Donnée perso                        | Consentement / contrat     | 1 an, puis anonymisation                       | Moyen                 |
| `allergies`     | **Santé (Art.9)**                   | **Consentement explicite** | Fin de conversation, max 6 mois si réclamation | **Élevé**             |
| `children_ages` | Donnée perso                        | Consentement/ contrat      | Fin de conversation                            | **Élevé**             |
| `messages`      | Donnée perso (sensibles spontanées) | Contrat                    | 6 mois, purge auto                             | **Élevé**             |
| Logs `/admin`   | Agrégés                             | Intérêt légitime           | 6 mois                                         | **Élevé** (sans auth) |
