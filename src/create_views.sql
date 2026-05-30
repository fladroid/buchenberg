-- v_sentence_features — glavni analitički view
-- Spaja sentences + named_entities + entity_aliases + books
-- Jedan red po rečenici, sve NLP karakteristike

CREATE OR REPLACE VIEW v_sentence_features AS
SELECT
  s.id                                          AS sentence_id,
  s.book_id,
  b.title                                       AS book_title,
  b.author                                      AS book_author,
  s.block_no,
  s.sentence_no,
  s.text,
  s.word_count,
  s.sentence_type,
  s.sentiment_label,
  s.sentiment_score,

  ARRAY_REMOVE(ARRAY_AGG(DISTINCT
    CASE WHEN ea.correct_label = 'PERSON' AND ea.role NOT IN ('noise','place_key','place_minor','organization')
    THEN ea.canonical_name END
  ), NULL)                                      AS persons,

  ARRAY_REMOVE(ARRAY_AGG(DISTINCT
    CASE WHEN ea.correct_label = 'PLACE'
    THEN ea.canonical_name END
  ), NULL)                                      AS places,

  BOOL_OR(ea.canonical_name = 'Holmes'          AND ea.correct_label = 'PERSON') AS has_holmes,
  BOOL_OR(ea.canonical_name = 'Watson'          AND ea.correct_label = 'PERSON') AS has_watson,
  BOOL_OR(ea.canonical_name = 'Mortimer'        AND ea.correct_label = 'PERSON') AS has_mortimer,
  BOOL_OR(ea.canonical_name = 'Stapleton'       AND ea.correct_label = 'PERSON') AS has_stapleton,
  BOOL_OR(ea.canonical_name = 'Henry Baskerville' AND ea.correct_label = 'PERSON') AS has_henry,
  BOOL_OR(ea.canonical_name = 'Charles Baskerville' AND ea.correct_label = 'PERSON') AS has_charles,
  BOOL_OR(ea.canonical_name = 'Barrymore'       AND ea.correct_label = 'PERSON') AS has_barrymore,
  BOOL_OR(ea.canonical_name = 'Selden'          AND ea.correct_label = 'PERSON') AS has_selden,
  BOOL_OR(ea.canonical_name = 'Laura Lyons'     AND ea.correct_label = 'PERSON') AS has_lyons,
  BOOL_OR(ea.canonical_name = 'Beryl Stapleton' AND ea.correct_label = 'PERSON') AS has_beryl,

  BOOL_OR(ea.canonical_name = 'Dartmoor'        AND ea.correct_label = 'PLACE') AS has_dartmoor,
  BOOL_OR(ea.canonical_name = 'Baskerville Hall' AND ea.correct_label = 'PLACE') AS has_baskerville_hall,
  BOOL_OR(ea.canonical_name = 'London'          AND ea.correct_label = 'PLACE') AS has_london,
  BOOL_OR(ea.canonical_name = 'Grimpen Mire'    AND ea.correct_label = 'PLACE') AS has_grimpen_mire,
  BOOL_OR(ea.canonical_name = 'Baker Street'    AND ea.correct_label = 'PLACE') AS has_baker_street,

  BOOL_OR(ea.role IN ('villain','villain_alias')) AS has_villain_ref,

  (SELECT ROUND((1 - (se1.vec <=> se2.vec))::numeric, 4)
   FROM sentence_embeddings se1
   JOIN sentence_embeddings se2
     ON se2.sentence_id = s.id - 1
     AND se1.embedder = 'e5'
     AND se2.embedder = 'e5'
   WHERE se1.sentence_id = s.id
   LIMIT 1)                                     AS cos_prev_e5

FROM sentences s
JOIN books b ON b.id = s.book_id
LEFT JOIN named_entities ne ON ne.sentence_id = s.id
LEFT JOIN entity_aliases ea
  ON ea.raw_text = ne.text
  AND ea.book_id = s.book_id
GROUP BY s.id, s.book_id, b.title, b.author,
         s.block_no, s.sentence_no, s.text,
         s.word_count, s.sentence_type,
         s.sentiment_label, s.sentiment_score
ORDER BY s.book_id, s.id;
