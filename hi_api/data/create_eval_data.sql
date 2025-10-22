-- Create table eval_data for MySQL
CREATE TABLE IF NOT EXISTS `eval_data` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `eval_set_id` INT NOT NULL COMMENT '评测集id',
  `corpus_id` INT NULL COMMENT '语料在所属评测集内的序号（从1开始）',
  `content` VARCHAR(2000) NOT NULL COMMENT '语料',
  `expected` VARCHAR(2000) NULL COMMENT '预期结果',
  `intent` VARCHAR(255) NULL COMMENT '意图',
  `deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '软删除标记',
  PRIMARY KEY (`id`),
  INDEX (`eval_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
