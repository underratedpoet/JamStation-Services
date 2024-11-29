use JamStation


-- Таблица с локациями
CREATE TABLE Locations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,  -- Название локации
    address NVARCHAR(255) NOT NULL,       -- Адрес
    phone_number NVARCHAR(50) NOT NULL,    -- Телефонный номер
    email NVARCHAR(100)           -- Электронная почта
);

-- Индекс для поиска по имени локации
CREATE INDEX IX_Locations_Name ON Locations(name);

-- Таблица с залами
CREATE TABLE Rooms (
    id INT IDENTITY(1,1) PRIMARY KEY,
    location_id INT NOT NULL FOREIGN KEY REFERENCES Locations(id),  -- Локация, к которой относится зал
    name NVARCHAR(100) NOT NULL,  -- Название зала
    capacity INT NOT NULL,       -- Вместимость зала
    hourly_rate DECIMAL(10, 2) NOT NULL  -- Стоимость аренды за час
);

-- Индекс для поиска по локации
CREATE INDEX IX_Rooms_Location ON Rooms(location_id);

-- Таблица с персоналом
CREATE TABLE Employees (
    id INT IDENTITY(1,1) PRIMARY KEY,
    location_id INT NOT NULL FOREIGN KEY REFERENCES Locations(id),  -- Локация, к которой относится сотрудник
    first_name NVARCHAR(20) NOT NULL,  -- Имя сотрудника
	second_name NVARCHAR(20),  -- Отчество сотрудника
	last_name NVARCHAR(20) NOT NULL,  -- Фамилия сотрудника
    role NVARCHAR(50) NOT NULL,            -- Должность (например, администратор, менеджер, техник)
    phone_number NVARCHAR(50) NOT NULL,    -- Телефонный номер
    email NVARCHAR(100),           -- Электронная почта
	login NVARCHAR(255) NOT NULL,
    password_hash NVARCHAR(255) NOT NULL
);

-- Индекс для поиска по локации и роли
CREATE INDEX IX_Employees_Location_Role ON Employees(location_id, role);

-- Таблица с товарами (расходниками)
CREATE TABLE Consumables (
    id INT IDENTITY(1,1) PRIMARY KEY,
    location_id INT NOT NULL FOREIGN KEY REFERENCES Locations(id),  -- Локация, к которой привязан товар
    name NVARCHAR(100) NOT NULL,  -- Название товара
    price DECIMAL(10, 2) NOT NULL,  -- Цена товара
    quantity INT, -- Количество

	CONSTRAINT chk_cons_quantity CHECK (quantity >= 0)
);

-- Индекс для поиска по локации и названию товара
CREATE INDEX IX_Consumables_Location_Name ON Consumables(location_id, name);

CREATE TABLE Equipment (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    type NVARCHAR(50) NOT NULL,
    room_id INT NOT NULL FOREIGN KEY REFERENCES Rooms(id),
    status NVARCHAR(20)
);

-- Таблица с клиентами
CREATE TABLE Clients (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,  -- Имя клиента
    phone_number NVARCHAR(50) NOT NULL,    -- Телефонный номер
    email NVARCHAR(100)          -- Электронная почта
);

-- Индекс для поиска по имени клиента
CREATE INDEX IX_Clients_Name ON Clients(name);

-- Таблица с расписанием посещений
CREATE TABLE Schedules ( 
    id INT IDENTITY(1,1) PRIMARY KEY, 
    room_id INT NOT NULL FOREIGN KEY REFERENCES Rooms(id),  -- Зал, который забронирован 
    client_id INT NOT NULL FOREIGN KEY REFERENCES Clients(id),  -- Клиент, который забронировал 
    start_time DATETIME NOT NULL,  -- Время начала 
    duration_hours INT NOT NULL,   -- Продолжительность в часах 
	is_paid BIT NOT NULL DEFAULT 0,
    status NVARCHAR(50) NOT NULL DEFAULT 'Активно',  -- Статус бронирования (Активно, Завершено, Отменено)
    
    -- Ограничение на start_time: не позднее чем через две недели от настоящего дня
    CONSTRAINT chk_start_time CHECK (start_time <= DATEADD(day, 14, GETDATE())),
    
    -- Ограничение на duration_hours: от 1 до 6 часов
    CONSTRAINT chk_duration_hours CHECK (duration_hours BETWEEN 1 AND 6)
);

-- Индекс для поиска по комнате и времени
CREATE INDEX IX_Schedules_Room_StartTime ON Schedules(room_id, start_time);

-- Таблица с чеками
CREATE TABLE Receipts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    employee_id INT NOT NULL FOREIGN KEY REFERENCES Employees(id),  -- Сотрудник, который выписал чек
    total_amount DECIMAL(10, 2) NOT NULL,  -- Общая сумма чека
    created_at DATETIME NOT NULL DEFAULT GETDATE()  -- Дата и время создания чека
);

-- Индекс для поиска по расписанию
CREATE INDEX IX_Receipts_Schedule ON Receipts(employee_id);

-- Таблица с позициями чека
CREATE TABLE Receipt_Items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    receipt_id INT NOT NULL FOREIGN KEY REFERENCES Receipts(id),  -- Ссылка на чек
    item_table NVARCHAR(50) NOT NULL,  -- Тип товара
    item_id INT NOT NULL,  -- ID товара (зал или товар)
    quantity INT, -- Количество
    total DECIMAL(10, 2) NOT NULL -- Общая сумма
);

-- Индекс для поиска по чеку и типу позиции
CREATE INDEX IX_Receipt_Items_ReceiptType ON Receipt_Items(receipt_id, item_table);

-- Таблица с применением штрафов к клиентам
CREATE TABLE Penalties (
    id INT IDENTITY(1,1) PRIMARY KEY,
    client_id INT NOT NULL FOREIGN KEY REFERENCES Clients(id),  -- Клиент, на которого наложен штраф
	description NVARCHAR(255),    -- Описание штрафа
    amount DECIMAL(10, 2) NOT NULL,  -- Сумма штрафа
    applied_at DATETIME NOT NULL DEFAULT GETDATE(),  -- Дата и время применения штрафа
	written_off DATETIME -- Дата и время списания
);

-- Индекс для поиска по клиенту и штрафу
CREATE INDEX IX_Client_Penalties_Client_Penalty ON Penalties(client_id);

-- Таблица с музыкальными инструментами
CREATE TABLE Instruments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    location_id INT NOT NULL FOREIGN KEY REFERENCES Locations(id),  -- Локация, к которой привязан инструмент
    name NVARCHAR(100) NOT NULL,  -- Название инструмента
    hourly_rate DECIMAL(10, 2) NOT NULL  -- Стоимость аренды за репетицию
);

-- Индекс для поиска по локации и названию инструмента
CREATE INDEX IX_Instruments_Location_Name ON Instruments(location_id, name);

-- Таблица с инструментами в аренде
CREATE TABLE Rentals (
    id INT IDENTITY(1,1) PRIMARY KEY,
	employee_id INT NOT NULL FOREIGN KEY REFERENCES Employees(id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES Instruments(id),  -- Инструмент, который был арендован
    schedule_id INT NOT NULL FOREIGN KEY REFERENCES Schedules(id),  -- Клиент, который арендовал
    rental_start_time DATETIME NOT NULL DEFAULT GETDATE(),  -- Время начала аренды
    rental_end_time DATETIME,    -- Время окончания аренды
);

-- Индекс для поиска по инструменту и клиенту
CREATE INDEX IX_Rentals_Instrument_Schedule ON Rentals(instrument_id, schedule_id);

-- Таблица с проверками оборудования и инструментов
CREATE TABLE Checks (
    id INT IDENTITY(1,1) PRIMARY KEY,
	employee_id INT NOT NULL FOREIGN KEY REFERENCES Employees(id),
    item_id INT NOT NULL,  -- ID оборудования или инструмента
    item_table NVARCHAR(50) NOT NULL, -- Тип объекта
    inspection_date DATETIME NOT NULL DEFAULT GETDATE(), -- Дата проверки
    description NVARCHAR(255),  -- Описание поломки
    status NVARCHAR(50) NOT NULL DEFAULT 'OK'  -- Статус ('ok' или 'broken')
);

-- Индекс для поиска по типу объекта и дате
CREATE INDEX IX_Checks_ItemType_Date ON Checks(item_table, inspection_date);

CREATE TABLE Keys_Transfers(
	id INT IDENTITY(1,1) PRIMARY KEY,
	employee_id INT NOT NULL FOREIGN KEY REFERENCES Employees(id),
	room_id INT NOT NULL FOREIGN KEY REFERENCES Rooms(id), -- От какой комнаты ключ
	schedule_id INT NOT NULL FOREIGN KEY REFERENCES Schedules(id), -- Кто забрал
    rental_start_time DATETIME NOT NULL DEFAULT GETDATE(),  -- Время начала аренды
    rental_end_time DATETIME,    -- Время окончания аренды
);

-- Таблица сдачи оборудования и инструментов в ремонт
CREATE TABLE Repairs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    check_id INT NOT NULL FOREIGN KEY REFERENCES Checks(id),  -- Ссылка на проверку оборудования или инструмента
    repair_start_date DATETIME DEFAULT GETDATE(),   -- Дата начала ремонта (NULL, если не в ремонте)
    repair_end_date DATETIME,    -- Дата завершения ремонта (NULL, если ещё не завершён)
    repair_status NVARCHAR(50) NOT NULL DEFAULT 'В процессе', -- Статус ремонта (in_progress, completed)
    legal_entity NVARCHAR(255) NOT NULL,  -- Юридическое лицо, куда сдается
    repair_cost DECIMAL(10, 2) NOT NULL  -- Цена ремонта
);

-- Индекс для поиска по статусу ремонта и юридическому лицу
CREATE INDEX IX_Repairs_Status_LegalEntity ON Repairs(repair_status, legal_entity);


