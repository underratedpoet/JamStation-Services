-- Создание пользователей

-- 1. Пользователь, который может только выполнять процедуру
CREATE USER ProcedureExecutor WITHOUT LOGIN;
GRANT EXECUTE ON dbo.YourProcedure TO ProcedureExecutor;

-- 2. Администратор
CREATE USER AdminUser WITHOUT LOGIN;

-- Предоставляем права на чтение данных из таблиц
GRANT SELECT ON dbo.Locations TO AdminUser;
GRANT SELECT ON dbo.Rooms TO AdminUser;
GRANT SELECT ON dbo.Consumables TO AdminUser;
GRANT SELECT ON dbo.Clients TO AdminUser;
GRANT SELECT ON dbo.Schedules TO AdminUser;
GRANT SELECT ON dbo.Receipts TO AdminUser;
GRANT SELECT ON dbo.Receipt_Items TO AdminUser;
GRANT SELECT ON dbo.Penalties TO AdminUser;
GRANT SELECT ON dbo.Instruments TO AdminUser;
GRANT SELECT ON dbo.Rentals TO AdminUser;
GRANT SELECT ON dbo.Checks TO AdminUser;
GRANT SELECT ON dbo.Keys_Transfers TO AdminUser;
GRANT SELECT ON dbo.Repairs TO AdminUser;

-- Предоставляем права на добавление и изменение данных в таблицах
GRANT INSERT, UPDATE ON dbo.Consumables TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Schedules TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Receipts TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Receipt_Items TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Penalties TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Instruments TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Rentals TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Checks TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Keys_Transfers TO AdminUser;
GRANT INSERT, UPDATE ON dbo.Repairs TO AdminUser;

-- Предоставляем права на выполнение конкретной процедуры
--GRANT EXECUTE ON dbo.YourProcedure TO AdminUser;

-- 3. Менеджер
CREATE USER ManagerUser WITHOUT LOGIN;

-- Предоставляем все права на таблицы для менеджера
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Locations TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Rooms TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Consumables TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Clients TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Schedules TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Receipts TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Receipt_Items TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Penalties TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Instruments TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Rentals TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Checks TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Keys_Transfers TO ManagerUser;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Repairs TO ManagerUser;

-- Предоставляем права на выполнение процедуры для менеджера
GRANT EXECUTE ON dbo.YourProcedure TO ManagerUser;

-- Назначение ролей для пользователей

-- Роль для администратора
CREATE ROLE AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Locations TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Rooms TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Consumables TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Clients TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Schedules TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Receipts TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Receipt_Items TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Penalties TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Instruments TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Rentals TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Checks TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Keys_Transfers TO AdminRole;
GRANT SELECT, INSERT, UPDATE ON dbo.Repairs TO AdminRole;
GRANT EXECUTE ON dbo.YourProcedure TO AdminRole;

-- Роль для менеджера
CREATE ROLE ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Locations TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Rooms TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Consumables TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Clients TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Schedules TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Receipts TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Receipt_Items TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Penalties TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Instruments TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Rentals TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Checks TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Keys_Transfers TO ManagerRole;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Repairs TO ManagerRole;
GRANT EXECUTE ON dbo.YourProcedure TO ManagerRole;

-- Назначаем роли пользователям
EXEC sp_addrolemember 'AdminRole', 'AdminUser';
EXEC sp_addrolemember 'ManagerRole', 'ManagerUser';

-- Присваиваем роль только для выполнения процедуры пользователю ProcedureExecutor
CREATE ROLE ProcedureExecutorRole;
GRANT EXECUTE ON dbo.YourProcedure TO ProcedureExecutorRole;
EXEC sp_addrolemember 'ProcedureExecutorRole', 'ProcedureExecutor';

-- Конец скрипта