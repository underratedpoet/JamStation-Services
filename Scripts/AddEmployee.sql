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