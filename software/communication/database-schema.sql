CREATE OR REPLACE FUNCTION notify_insert()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        TG_TABLE_NAME || '_insert',
        row_to_json(NEW)::text
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
