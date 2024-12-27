use JamStation

CREATE TRIGGER trg_DeleteEquipment
ON Equipment
INSTEAD OF DELETE
AS
BEGIN
    DELETE FROM Repairs
    WHERE check_id IN (
        SELECT id FROM Checks 
        WHERE item_table = 'Equipment' 
          AND item_id IN (SELECT id FROM DELETED)
    );

    DELETE FROM Checks
    WHERE item_table = 'Equipment' 
      AND item_id IN (SELECT id FROM DELETED);

    DELETE FROM Equipment
    WHERE id IN (SELECT id FROM DELETED);
END;

CREATE TRIGGER trg_DeleteInstrument
ON Instruments
INSTEAD OF DELETE
AS
BEGIN
    DELETE FROM Rentals
    WHERE instrument_id IN (SELECT id FROM DELETED);

    DELETE FROM Repairs
    WHERE check_id IN (
        SELECT id FROM Checks 
        WHERE item_table = 'Instruments' 
          AND item_id IN (SELECT id FROM DELETED)
    );

    DELETE FROM Checks
    WHERE item_table = 'Instruments' 
      AND item_id IN (SELECT id FROM DELETED);

    DELETE FROM Instruments
    WHERE id IN (SELECT id FROM DELETED);
END;

CREATE TRIGGER trg_DeleteClient
ON Clients
INSTEAD OF DELETE
AS
BEGIN
    DELETE FROM Penalties
    WHERE client_id IN (SELECT id FROM DELETED);

    DELETE FROM Keys_Transfers
    WHERE schedule_id IN (
        SELECT id FROM Schedules 
        WHERE client_id IN (SELECT id FROM DELETED)
    );

    DELETE FROM Rentals
    WHERE schedule_id IN (
        SELECT id FROM Schedules 
        WHERE client_id IN (SELECT id FROM DELETED)
    );

    DELETE FROM Schedules
    WHERE client_id IN (SELECT id FROM DELETED);

    DELETE FROM Clients
    WHERE id IN (SELECT id FROM DELETED);
END;
