-- create_jobs_table_mysql.sql
-- 针对 MySQL (InnoDB, utf8mb4) 的 jobs 表建表语句
CREATE TABLE IF NOT EXISTS `jobs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `job_id` VARCHAR(64) NOT NULL,
  `eval_set_id` INT NULL,
  `status` VARCHAR(32) NOT NULL DEFAULT 'pending',
  `processed` INT NOT NULL DEFAULT 0,
  `total` INT NOT NULL DEFAULT 0,
  `file_path` VARCHAR(1000) NULL,
  `error` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `started_at` DATETIME NULL,
  `finished_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_jobs_job_id` (`job_id`),
  KEY `idx_jobs_eval_set_id` (`eval_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
