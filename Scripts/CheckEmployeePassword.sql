CREATE PROCEDURE CheckEmployeePassword  
    @EmployeeLogin NVARCHAR(255),  -- Логин сотрудника 
    @Password NVARCHAR(255)        -- Пароль, введённый пользователем 
AS 
BEGIN 
    DECLARE @StoredPasswordHash NVARCHAR(255) 

    -- Получаем хэш пароля сотрудника по логину 
    SELECT @StoredPasswordHash = password_hash  
    FROM Employees  
    WHERE login = @EmployeeLogin 

    -- Проверка, что сотрудник с таким логином существует
    IF @StoredPasswordHash IS NULL 
    BEGIN 
        -- Если сотрудник не найден, возвращаем 0
        SELECT 0 AS IsPasswordCorrect 
        RETURN
    END 

    -- Сравнение хэшей паролей (с использованием подходящей функции хэширования)
    IF @StoredPasswordHash = HASHBYTES('SHA2_256', @Password) 
    BEGIN
        -- Если пароль правильный, возвращаем 1
        SELECT 1 AS IsPasswordCorrect
    END 
    ELSE 
    BEGIN
        -- Если пароль неправильный, возвращаем 0
        SELECT 0 AS IsPasswordCorrect
    END
END 
GO


