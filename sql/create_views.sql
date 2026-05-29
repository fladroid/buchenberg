-- VIEW: translation_scores
-- Cosinus sličnost (EN original vs prevod) direktno iz pgvector
CREATE VIEW translation_scores AS
SELECT
    t.id              AS translation_id,
    t.sentence_id,
    s.text            AS source_text,
    t.target_lang,
    t.model,
    t.temperature,
    t.translation,
    te.embedder,
    ROUND((1 - (se.vec <=> te.vec))::numeric, 4) AS cosine_score
FROM translations t
JOIN sentences s               ON s.id = t.sentence_id
JOIN translation_embeddings te ON te.translation_id = t.id
JOIN sentence_embeddings se    ON se.sentence_id = t.sentence_id
                               AND se.embedder = te.embedder;

-- VIEW: best_translation
-- Za svaku rečenicu — jedan red s globalnim best scoreom (svi jezici, svi modeli)
CREATE VIEW best_translation AS
SELECT DISTINCT ON (sentence_id)
    translation_id, sentence_id, source_text,
    target_lang, model, temperature, translation,
    embedder, cosine_score
FROM translation_scores
ORDER BY sentence_id, cosine_score DESC;

-- VIEW: color_summary
-- Broj zelenih/žutih/crvenih po jeziku i embedderu (best score per sentence)
CREATE VIEW color_summary AS
WITH best_per_sentence AS (
    SELECT target_lang, embedder, sentence_id,
           MAX(cosine_score) AS best_score
    FROM translation_scores
    GROUP BY target_lang, embedder, sentence_id
)
SELECT target_lang, embedder,
       COUNT(*) FILTER (WHERE best_score >= 0.90)                       AS zelene,
       COUNT(*) FILTER (WHERE best_score >= 0.80 AND best_score < 0.90) AS zute,
       COUNT(*) FILTER (WHERE best_score <  0.80)                       AS crvene,
       COUNT(*)                                                         AS ukupno
FROM best_per_sentence
GROUP BY target_lang, embedder
ORDER BY embedder, target_lang;
