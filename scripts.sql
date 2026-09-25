CREATE OR REPLACE FUNCTION add_new_messages_to_measures()
RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    new_message_count           integer;
    new_spam_message_count      integer;
    new_not_spam_message_count  integer;

    added_spam_word_total       integer;
    added_not_spam_word_total   integer;

    new_unique_spam_words       integer;
    new_unique_not_spam_words   integer;
BEGIN
    SELECT
        count(*),
        count(*) FILTER (WHERE is_spam),
        count(*) FILTER (WHERE NOT is_spam)
    INTO new_message_count, new_spam_message_count, new_not_spam_message_count
    FROM inserted_messages;

    IF new_message_count = 0 THEN
        RETURN NULL;
    END IF;


    CREATE TEMP TABLE new_word_counts ON COMMIT DROP AS
    SELECT
        message.is_spam                        AS is_from_spam,
        split.word                             AS word,
        count(*)::integer                      AS occurrences
    FROM inserted_messages AS message
    CROSS JOIN LATERAL
        regexp_split_to_table(lower(message.message), '[^a-z0-9]+') AS split(word)
    WHERE split.word <> '' AND char_length(split.word) <= 45
    GROUP BY message.is_spam, split.word;


    WITH upserted AS (
        INSERT INTO labeled_words (word, occurrences, is_from_spam)
        SELECT word, occurrences, is_from_spam FROM new_word_counts
        ON CONFLICT (word, is_from_spam)
        DO UPDATE SET occurrences = labeled_words.occurrences + excluded.occurrences
        RETURNING is_from_spam, (xmax = 0) AS is_brand_new
    )
    SELECT
        count(*) FILTER (WHERE is_brand_new AND is_from_spam),
        count(*) FILTER (WHERE is_brand_new AND NOT is_from_spam)
    INTO new_unique_spam_words, new_unique_not_spam_words
    FROM upserted;

    SELECT
        coalesce(sum(occurrences) FILTER (WHERE is_from_spam), 0),
        coalesce(sum(occurrences) FILTER (WHERE NOT is_from_spam), 0)
    INTO added_spam_word_total, added_not_spam_word_total
    FROM new_word_counts;

    DROP TABLE new_word_counts;


    INSERT INTO measures (name, value, updated_at) VALUES
        ('total_messages',        new_message_count,           now()),
        ('spam_messages',         new_spam_message_count,      now()),
        ('not_spam_messages',     new_not_spam_message_count,  now()),
        ('total_spam_words',      added_spam_word_total,        now()),
        ('total_not_spam_words',  added_not_spam_word_total,    now()),
        ('unique_spam_words',     new_unique_spam_words,        now()),
        ('unique_not_spam_words', new_unique_not_spam_words,    now())
    ON CONFLICT (name) DO UPDATE
        SET value      = measures.value + excluded.value,
            updated_at = now();

    RETURN NULL;
END;
$$;


DROP TRIGGER IF EXISTS labeled_messages_after_insert ON labeled_messages;

CREATE TRIGGER labeled_messages_after_insert
    AFTER INSERT ON labeled_messages
    REFERENCING NEW TABLE AS inserted_messages
    FOR EACH STATEMENT
    EXECUTE FUNCTION add_new_messages_to_measures();
