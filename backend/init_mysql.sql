-- ============================================================
-- 初始化 MySQL 数据库（本系统默认使用 MySQL，SQLite 已废弃）
-- 用法（PowerShell 不支持 < 重定向，请用管道）：
--   Get-Content init_mysql.sql | mysql -u root -p
-- 或直接执行：
--   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS work_stat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
-- ============================================================

CREATE DATABASE IF NOT EXISTS `work_stat`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
