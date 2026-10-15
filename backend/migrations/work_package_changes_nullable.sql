-- 在启动新版后端前执行：新增申请尚无正式工作包，删除后保留申请快照。
-- 不删除表或历史数据；已有外键保持不变。
ALTER TABLE work_package_change_requests MODIFY COLUMN work_package_id INT NULL;
