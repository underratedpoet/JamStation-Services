use JamStation

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

CREATE PROCEDURE AddEmployee  
    @LocationId INT,            -- Локация сотрудника 
    @FirstName NVARCHAR(20),    -- Имя сотрудника
    @SecondName NVARCHAR(20),   -- Отчество сотрудника 
    @LastName NVARCHAR(20),     -- Фамилия сотрудника 
    @Role NVARCHAR(50),         -- Должность сотрудника 
    @PhoneNumber NVARCHAR(50),  -- Телефонный номер сотрудника 
    @Email NVARCHAR(100),       -- Электронная почта сотрудника 
    @Login NVARCHAR(255),       -- Логин сотрудника 
    @Password NVARCHAR(255)     -- Пароль сотрудника 
AS 
BEGIN 
    DECLARE @PasswordHash NVARCHAR(255) 

    -- Хэшируем пароль с использованием SHA2_256
    SET @PasswordHash = HASHBYTES('SHA2_256', @Password) 

    -- Вставляем нового сотрудника в таблицу
    INSERT INTO Employees (location_id, first_name, second_name, last_name, role, phone_number, email, login, password_hash) 
    VALUES (@LocationId, @FirstName, @SecondName, @LastName, @Role, @PhoneNumber, @Email, @Login, @PasswordHash) 

    -- Возвращаем таблицу с единственным значением 0, что подтверждает успешное выполнение
    SELECT 0 AS Status
END 
GO
