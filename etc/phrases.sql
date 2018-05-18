SELECT CASE phrase.type
         WHEN 'word' THEN phrase.origin
         ELSE 'sentence'
       END origin,
       transcription.value translation,
       translation.value transcription
  FROM phrase,
       versioned_string as translation,
       versioned_string as transcription
 WHERE phrase.translation_id = translation.id
   AND phrase.transcription_id = transcription.id;
