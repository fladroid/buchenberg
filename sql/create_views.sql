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
