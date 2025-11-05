SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS UNISYNCDB;
CREATE DATABASE UNISYNCDB CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE UNISYNCDB;
SET FOREIGN_KEY_CHECKS = 1;

-- TABLES

CREATE TABLE Student (
  SRN VARCHAR(13) PRIMARY KEY,
  FirstName VARCHAR(30),
  MiddleName VARCHAR(30),
  LastName VARCHAR(30),
  Email VARCHAR(50) UNIQUE,
  Phone VARCHAR(15),
  Department VARCHAR(30),
  JoinDate DATE,
  Password VARCHAR(256)
) ENGINE=InnoDB;

CREATE TABLE Category (
  Cat_ID INT PRIMARY KEY,
  MainType VARCHAR(50) NOT NULL,
  SubType VARCHAR(50)
) ENGINE=InnoDB;

CREATE TABLE Resource (
  ResourceID INT AUTO_INCREMENT PRIMARY KEY,
  Title VARCHAR(50),
  Description TEXT,
  itemCondition VARCHAR(20),
  Status VARCHAR(20),
  ListingType ENUM('Sell','Lend','Barter') NOT NULL,
  OwnerID VARCHAR(13),
  CategoryID INT,
  ImagePath VARCHAR(255),
  CONSTRAINT fk_res_owner FOREIGN KEY (OwnerID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT fk_res_cat FOREIGN KEY (CategoryID) REFERENCES Category(Cat_ID)
) ENGINE=InnoDB;

CREATE TABLE LendBorrow (
  LendBorrowID INT AUTO_INCREMENT PRIMARY KEY,
  itemID INT NOT NULL,
  LenderID VARCHAR(13) NOT NULL,
  BorrowerID VARCHAR(13) NOT NULL,
  StartDate DATE NOT NULL,
  EndDate DATE,
  Status VARCHAR(20) NOT NULL,
  TransactionID INT NULL,
  PenaltyAmount DECIMAL(10,2) DEFAULT 0.00,
  CONSTRAINT fk_lb_resource FOREIGN KEY (itemID) REFERENCES Resource(ResourceID) ON DELETE CASCADE,
  CONSTRAINT fk_lb_lender FOREIGN KEY (LenderID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT fk_lb_borrower FOREIGN KEY (BorrowerID) REFERENCES Student(SRN) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE BuySell (
  BuySellID INT AUTO_INCREMENT PRIMARY KEY,
  ItemID INT NOT NULL,
  SellerID VARCHAR(13) NOT NULL,
  BuyerID VARCHAR(13),
  Price DECIMAL(10,2) NOT NULL,
  Status VARCHAR(20) NOT NULL,
  TransactionDate DATE NOT NULL,
  BuyerTransID VARCHAR(100),
  SellerConfirm BOOLEAN DEFAULT FALSE,
  TransactionID INT NULL,
  CONSTRAINT fk_bs_resource FOREIGN KEY (ItemID) REFERENCES Resource(ResourceID) ON DELETE CASCADE,
  CONSTRAINT fk_bs_seller FOREIGN KEY (SellerID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT fk_bs_buyer FOREIGN KEY (BuyerID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT chk_price_positive CHECK (Price > 0)
) ENGINE=InnoDB;

CREATE TABLE Barter (
  BarterID INT AUTO_INCREMENT PRIMARY KEY,
  Item1ID INT NOT NULL,
  Item2ID INT NOT NULL,
  ProposerID VARCHAR(13) NOT NULL,
  AccepterID VARCHAR(13) NOT NULL,
  Status VARCHAR(20) NOT NULL,
  BarterDate DATE NOT NULL,
  TransactionID INT NULL,
  CONSTRAINT fk_barter_res1 FOREIGN KEY (Item1ID) REFERENCES Resource(ResourceID) ON DELETE CASCADE,
  CONSTRAINT fk_barter_res2 FOREIGN KEY (Item2ID) REFERENCES Resource(ResourceID) ON DELETE CASCADE,
  CONSTRAINT fk_barter_prop FOREIGN KEY (ProposerID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT fk_barter_acc FOREIGN KEY (AccepterID) REFERENCES Student(SRN) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE Transactions (
  TransactionID INT AUTO_INCREMENT PRIMARY KEY,
  Type ENUM('BuySell','LendBorrow','Barter') NOT NULL
) ENGINE=InnoDB;

ALTER TABLE LendBorrow
  ADD CONSTRAINT fk_lb_trans FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID) ON DELETE SET NULL;
ALTER TABLE BuySell
  ADD CONSTRAINT fk_bs_trans FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID) ON DELETE SET NULL;
ALTER TABLE Barter
  ADD CONSTRAINT fk_bt_trans FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID) ON DELETE SET NULL;

CREATE TABLE Reminder (
  ReminderID INT AUTO_INCREMENT PRIMARY KEY,
  STD_ID VARCHAR(13) NOT NULL,
  TransID INT NOT NULL,
  Msg VARCHAR(100) NOT NULL,
  Status VARCHAR(20) NOT NULL,
  RDate DATE NOT NULL,
  CONSTRAINT fk_rem_stud FOREIGN KEY (STD_ID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT fk_rem_trans FOREIGN KEY (TransID) REFERENCES Transactions(TransactionID) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE Review (
  ReviewID INT AUTO_INCREMENT PRIMARY KEY,
  Rating INT CHECK (Rating BETWEEN 1 AND 5),
  Comments VARCHAR(255),
  STD_ID VARCHAR(13) NOT NULL,
  ItemID INT NOT NULL,
  CONSTRAINT fk_review_student FOREIGN KEY (STD_ID) REFERENCES Student(SRN) ON DELETE CASCADE,
  CONSTRAINT fk_review_resource FOREIGN KEY (ItemID) REFERENCES Resource(ResourceID) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX idx_student_email ON Student(Email);
CREATE INDEX idx_student_phone ON Student(Phone);
CREATE INDEX idx_resource_status ON Resource(Status);
CREATE INDEX idx_resource_owner ON Resource(OwnerID);
CREATE INDEX idx_resource_category ON Resource(CategoryID);
CREATE INDEX idx_lb_status ON LendBorrow(Status);
CREATE INDEX idx_lb_borrower ON LendBorrow(BorrowerID);
CREATE INDEX idx_lb_lender ON LendBorrow(LenderID);
CREATE INDEX idx_barter_status ON Barter(Status);
CREATE INDEX idx_barter_proposer ON Barter(ProposerID);
CREATE INDEX idx_barter_accepter ON Barter(AccepterID);
CREATE INDEX idx_reminder_student ON Reminder(STD_ID);
CREATE INDEX idx_reminder_status ON Reminder(Status);
CREATE INDEX idx_review_student ON Review(STD_ID);
CREATE INDEX idx_review_item ON Review(ItemID);

ALTER TABLE Student ADD CONSTRAINT uq_phone UNIQUE (Phone);

-- =========================================================
-- SEED DATA
-- =========================================================

INSERT INTO Student (SRN, FirstName, MiddleName, LastName, Email, Phone, Department, JoinDate, Password) VALUES
('PES2UG23CS001','John','','Doe','john.doe@unisync.edu','9000000001','Computer Science','2023-08-01','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'),
('PES2UG23CS002','Jane','','Doe','jane.doe@unisync.edu','9000000002','Electronics','2023-08-01','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'),
('PES2UG23CS003','Alice','','Smith','alice.smith@unisync.edu','9000000003','Mechanical','2023-08-01','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'),
('PES2UG23CS004','Bob','','Johnson','bob.johnson@unisync.edu','9000000004','Civil','2023-08-01','a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3');

INSERT INTO Category (Cat_ID, MainType, SubType) VALUES
(1,'Books','Textbook'),
(2,'Electronics','Laptop'),
(3,'Furniture','Chair'),
(4,'Miscellaneous','General');

INSERT INTO Resource (Title, Description, itemCondition, Status, ListingType, OwnerID, CategoryID) VALUES
('DBMS Book','Database Systems Concepts, 7th Edition','Good','Available','Lend','PES2UG23CS001',1),
('Dell Laptop','i5, 8GB RAM, 512GB SSD','Excellent','Available','Sell','PES2UG23CS002',2),
('Study Chair','Ergonomic chair for study use','Fair','Available','Barter','PES2UG23CS003',3);

INSERT INTO Transactions (Type) VALUES ('LendBorrow'),('BuySell'),('Barter');

INSERT INTO LendBorrow (itemID, LenderID, BorrowerID, StartDate, EndDate, Status, TransactionID)
VALUES (1,'PES2UG23CS001','PES2UG23CS002','2025-09-01','2025-09-10','Active',1);

INSERT INTO BuySell (ItemID, SellerID, BuyerID, Price, Status, TransactionDate, TransactionID)
VALUES (2,'PES2UG23CS002','PES2UG23CS003',45000.00,'Completed','2025-09-05',2);

INSERT INTO Barter (Item1ID, Item2ID, ProposerID, AccepterID, Status, BarterDate, TransactionID)
VALUES (3,1,'PES2UG23CS003','PES2UG23CS001','Pending','2025-09-07',3);

INSERT INTO Reminder (STD_ID, TransID, Msg, Status, RDate)
VALUES ('PES2UG23CS002',1,'Return DBMS Book by 10th Sept','Unread','2025-09-08');

INSERT INTO Review (Rating, Comments, STD_ID, ItemID)
VALUES (5,'Great quality book, very helpful!','PES2UG23CS002',1),
       (4,'Laptop is in excellent condition','PES2UG23CS003',2);

-- =========================================================
-- TRIGGERS
-- =========================================================

DELIMITER $$

CREATE TRIGGER tg_lend_insert
AFTER INSERT ON LendBorrow
FOR EACH ROW
BEGIN
  IF NEW.Status IS NOT NULL THEN
    UPDATE Resource SET Status = 'Unavailable' WHERE ResourceID = NEW.itemID;
    IF NEW.EndDate IS NOT NULL THEN
      INSERT INTO Reminder (STD_ID, TransID, Msg, Status, RDate)
      VALUES (NEW.BorrowerID, NEW.TransactionID,
              CONCAT('Reminder: return item ', NEW.itemID, ' by ', DATE_FORMAT(NEW.EndDate,'%Y-%m-%d')),
              'Unread', DATE_SUB(NEW.EndDate, INTERVAL 2 DAY));
    END IF;
  END IF;
END$$

CREATE TRIGGER tg_lend_update_complete
AFTER UPDATE ON LendBorrow
FOR EACH ROW
BEGIN
  IF (OLD.Status <> NEW.Status) AND (NEW.Status = 'Completed') THEN
    UPDATE Resource SET Status = 'Available' WHERE ResourceID = NEW.itemID;
    UPDATE Reminder SET Status = 'Expired' WHERE TransID = NEW.TransactionID;
  END IF;
END$$

CREATE TRIGGER tg_buysell_update_complete
AFTER UPDATE ON BuySell
FOR EACH ROW
BEGIN
  IF (OLD.Status <> NEW.Status) AND (NEW.Status = 'Completed') THEN
    UPDATE Resource SET Status = 'Sold' WHERE ResourceID = NEW.ItemID;
  END IF;
END$$

CREATE TRIGGER tg_barter_update_accepted
AFTER UPDATE ON Barter
FOR EACH ROW
BEGIN
  IF (OLD.Status <> NEW.Status) AND (LOWER(NEW.Status) = 'accepted') THEN
    UPDATE Resource SET Status = 'Unavailable' WHERE ResourceID IN (NEW.Item1ID, NEW.Item2ID);
  END IF;
END$$

DELIMITER ;

-- =========================================================
-- FUNCTIONS & PROCEDURES
-- =========================================================

DELIMITER $$

CREATE FUNCTION calculate_penalty(p_LendBorrowID INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_EndDate DATE;
  DECLARE v_DaysLate INT;
  DECLARE v_Penalty DECIMAL(10,2) DEFAULT 0.00;
  DECLARE v_RatePerDay DECIMAL(10,2) DEFAULT 10.00;
  SELECT EndDate INTO v_EndDate FROM LendBorrow WHERE LendBorrowID = p_LendBorrowID;
  SET v_DaysLate = DATEDIFF(CURDATE(), v_EndDate);
  IF v_DaysLate > 0 THEN
    SET v_Penalty = v_DaysLate * v_RatePerDay;
  END IF;
  RETURN v_Penalty;
END$$

CREATE PROCEDURE complete_lend_with_penalty(IN p_LendBorrowID INT)
BEGIN
  DECLARE v_exists INT;
  DECLARE v_penalty DECIMAL(10,2);
  SELECT COUNT(*) INTO v_exists FROM LendBorrow WHERE LendBorrowID = p_LendBorrowID AND Status = 'Ongoing';
  IF v_exists = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'complete_lend: Active LendBorrowID not found';
  ELSE
    SET v_penalty = calculate_penalty(p_LendBorrowID);
    UPDATE LendBorrow
    SET Status = 'Completed',
        PenaltyAmount = v_penalty,
        EndDate = CASE WHEN v_penalty > 0 THEN CURDATE() ELSE EndDate END
    WHERE LendBorrowID = p_LendBorrowID;
  END IF;
END$$

CREATE PROCEDURE initiate_lend(
  IN p_ItemID INT,
  IN p_LenderID VARCHAR(13),
  IN p_BorrowerID VARCHAR(13),
  IN p_StartDate DATE,
  IN p_EndDate DATE,
  OUT p_LendBorrowID INT
)
BEGIN
  DECLARE v_status VARCHAR(20);
  DECLARE v_transID INT;
  SELECT Status INTO v_status FROM Resource WHERE ResourceID = p_ItemID FOR UPDATE;
  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'initiate_lend: Resource not found';
  ELSEIF v_status <> 'Available' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'initiate_lend: Resource not available';
  ELSE
    INSERT INTO Transactions (Type) VALUES ('LendBorrow');
    SET v_transID = LAST_INSERT_ID();
    INSERT INTO LendBorrow(itemID, LenderID, BorrowerID, StartDate, EndDate, Status, TransactionID)
    VALUES (p_ItemID, p_LenderID, p_BorrowerID, p_StartDate, p_EndDate, 'Ongoing', v_transID);
    SET p_LendBorrowID = LAST_INSERT_ID();
  END IF;
END$$

CREATE PROCEDURE complete_lend(IN p_LendBorrowID INT)
BEGIN
  DECLARE v_exists INT;
  SELECT COUNT(*) INTO v_exists FROM LendBorrow WHERE LendBorrowID = p_LendBorrowID;
  IF v_exists = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'complete_lend: LendBorrowID not found';
  ELSE
    UPDATE LendBorrow
    SET Status = 'Completed',
        EndDate = CASE WHEN EndDate IS NULL THEN CURDATE() ELSE EndDate END
    WHERE LendBorrowID = p_LendBorrowID;
  END IF;
END$$

CREATE FUNCTION get_avg_rating(p_ItemID INT)
RETURNS DECIMAL(3,2)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_avg DECIMAL(5,2);
  SELECT AVG(Rating) INTO v_avg FROM Review WHERE ItemID = p_ItemID;
  IF v_avg IS NULL THEN
    RETURN 0.00;
  ELSE
    RETURN ROUND(v_avg,2);
  END IF;
END$$

DELIMITER ;
