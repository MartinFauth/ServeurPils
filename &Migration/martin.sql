-- --------------------------------------------------------
-- Hôte:                         127.0.0.1
-- Version du serveur:           9.1.0 - MySQL Community Server - GPL
-- SE du serveur:                Win64
-- HeidiSQL Version:             12.1.0.6537
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Listage de la structure de la base pour alerts_list
CREATE DATABASE IF NOT EXISTS `alerts_list` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `alerts_list`;

-- Listage de la structure de table alerts_list. alerts_list
CREATE TABLE IF NOT EXISTS `alerts_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `heure` time DEFAULT NULL,
  `date` date DEFAULT NULL,
  `camera_id` int DEFAULT NULL,
  `statut` varchar(20) DEFAULT NULL,
  `video` varchar(255) DEFAULT NULL,
  `websocket` varchar(3) DEFAULT NULL,
  `lastUpdate` datetime DEFAULT NULL,
  `updatedBy` varchar(50) DEFAULT NULL,
  `fauxPositif` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Listage des données de la table alerts_list.alerts_list : ~7 rows (environ)
INSERT INTO `alerts_list` (`id`, `heure`, `date`, `camera_id`, `statut`, `video`, `websocket`, `lastUpdate`, `updatedBy`, `fauxPositif`) VALUES
	(41, '17:06:17', '2025-01-17', 2, 'en cours', 'alert_1.mp4', '0', '2025-01-17 17:06:19', 'system', 0),
	(42, '17:06:32', '2025-01-17', 2, 'en cours', 'alert_2.mp4', '0', '2025-01-17 17:06:34', 'system', 0),
	(43, '17:06:40', '2025-01-17', 2, 'en cours', 'alert_3.mp4', '0', '2025-01-17 17:06:43', 'system', 0),
	(44, '17:06:46', '2025-01-17', 2, 'Classee', 'alert_4.mp4', '0', '2025-01-17 17:07:54', 'system', 0),
	(45, '17:06:55', '2025-01-17', 2, 'en cours', 'alert_5.mp4', '0', '2025-01-17 17:06:58', 'system', 0),
	(46, '17:33:54', '2025-01-17', 2, 'en cours', 'alert_1.mp4', '0', '2025-01-17 17:33:56', 'system', 0),
	(47, '17:34:10', '2025-01-17', 2, 'en cours', 'alert_2.mp4', '0', '2025-01-17 17:34:12', 'system', 0),
	(48, '17:34:20', '2025-01-17', 2, 'en cours', 'alert_3.mp4', '0', '2025-01-17 17:34:22', 'system', 0);


-- Listage de la structure de la base pour pils_users_db
CREATE DATABASE IF NOT EXISTS `pils_users_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `pils_users_db`;

-- Listage de la structure de table pils_users_db. users
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `is_admin` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Listage des données de la table pils_users_db.users : ~3 rows (environ)
INSERT INTO `users` (`id`, `username`, `email`, `password`, `is_admin`, `created_at`) VALUES
	(1, 'john_doe', 'john@example.com', 'securepassword', 0, '2025-01-04 15:08:42'),
	(2, 'admin', 'admin@example.com', 'admin', 1, '2025-01-04 15:12:26'),
	(13, 'a', 'a', 'a', 1, '2025-01-08 11:14:43');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
