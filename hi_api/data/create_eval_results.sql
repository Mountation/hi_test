-- 创建 eval_results 表 (评测结果表)
-- 说明：存储每条评测数据的实际结果、评分、执行时间、Agent版本等信息
CREATE TABLE IF NOT EXISTS `eval_results` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `eval_set_id` BIGINT NOT NULL COMMENT '所属评测集ID',
  `eval_data_id` BIGINT NOT NULL COMMENT '语料id',
  `actual_result` TEXT NULL COMMENT '实际模型返回结果',
  `actual_intent` VARCHAR(255) NULL COMMENT '实际意图',
  `score` DECIMAL(10,4) NULL COMMENT '评分（可为空）',
  `exec_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  `agent_version` VARCHAR(64) NULL COMMENT 'Agent版本',
  `kdb` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否命中知识库（0否 1是）',
  `deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否删除（软删除标记）',
  PRIMARY KEY (`id`),
  KEY `idx_eval_set` (`eval_set_id`),
  KEY `idx_eval_data` (`eval_data_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评测结果表';