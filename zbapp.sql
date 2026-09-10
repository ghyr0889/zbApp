/*
 Navicat Premium Dump SQL

 Source Server         : test
 Source Server Type    : MySQL
 Source Server Version : 80046 (8.0.46)
 Source Host           : localhost:3306
 Source Schema         : zbapp

 Target Server Type    : MySQL
 Target Server Version : 80046 (8.0.46)
 File Encoding         : 65001

 Date: 09/09/2026 11:33:43
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for monthly_extra_score
-- ----------------------------
DROP TABLE IF EXISTS `monthly_extra_score`;
CREATE TABLE `monthly_extra_score`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `patent_score` float NULL DEFAULT NULL,
  `knowledge_score` float NULL DEFAULT NULL,
  `train_score` float NULL DEFAULT NULL,
  `deduct_score` float NULL DEFAULT NULL,
  `quality_event_score` float NULL DEFAULT NULL,
  `carrier_inspection_score` float NULL DEFAULT NULL,
  `updated_by_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `month` varchar(7) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_user_month`(`user_id` ASC, `month` ASC) USING BTREE,
  INDEX `updated_by_id`(`updated_by_id` ASC) USING BTREE,
  INDEX `ix_monthly_extra_score_id`(`id` ASC) USING BTREE,
  INDEX `ix_monthly_extra_score_month`(`month` ASC) USING BTREE,
  CONSTRAINT `monthly_extra_score_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `monthly_extra_score_ibfk_2` FOREIGN KEY (`updated_by_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for projects
-- ----------------------------
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `level` varchar(10) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `complete_status` tinyint(1) NULL DEFAULT NULL,
  `category` varchar(100) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `tech_owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `isclosed` tinyint(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `owner_id`(`owner_id` ASC) USING BTREE,
  INDEX `tech_owner_id`(`tech_owner_id` ASC) USING BTREE,
  INDEX `ix_projects_name`(`name` ASC) USING BTREE,
  INDEX `ix_projects_id`(`id` ASC) USING BTREE,
  CONSTRAINT `projects_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `projects_ibfk_2` FOREIGN KEY (`tech_owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 18 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for score_dimension_levels
-- ----------------------------
DROP TABLE IF EXISTS `score_dimension_levels`;
CREATE TABLE `score_dimension_levels`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `variable` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `level` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `factor` float NULL DEFAULT NULL,
  `job_grade` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_score_dimension_levels_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 396 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for score_level_defs
-- ----------------------------
DROP TABLE IF EXISTS `score_level_defs`;
CREATE TABLE `score_level_defs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `sort_order` int NULL DEFAULT NULL,
  `is_active` int NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_def_category_name`(`category` ASC, `name` ASC) USING BTREE,
  INDEX `ix_score_level_defs_category`(`category` ASC) USING BTREE,
  INDEX `ix_score_level_defs_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 120 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for task_transfers
-- ----------------------------
DROP TABLE IF EXISTS `task_transfers`;
CREATE TABLE `task_transfers`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_assignment_id` varchar(50) CHARACTER SET utf8mb4 COLLATE  NOT NULL COMMENT '任务分配记录 ID',
  `work_package_id` int NOT NULL,
  `from_user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL COMMENT '发起人(原负责人)',
  `to_user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL COMMENT '接收人(新负责人)',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL COMMENT '状态: PENDING/ACCEPTED/REJECTED',
  `created_at` datetime NULL DEFAULT NULL,
  `transfer_type` varchar(20) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT 'work_item',
  `work_item_id` int NULL DEFAULT NULL,
  `transfer_score` float NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `work_package_id`(`work_package_id` ASC) USING BTREE,
  INDEX `ix_task_transfers_id`(`id` ASC) USING BTREE,
  CONSTRAINT `task_transfers_ibfk_1` FOREIGN KEY (`work_package_id`) REFERENCES `work_packages` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `job_grade` varchar(20) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `is_deleted` tinyint NULL DEFAULT 0,
  `deleted_at` datetime NULL DEFAULT NULL,
  `deleted_by` varchar(10) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_users_username`(`username` ASC) USING BTREE,
  INDEX `ix_users_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for work_item_monthly_scores
-- ----------------------------
DROP TABLE IF EXISTS `work_item_monthly_scores`;
CREATE TABLE `work_item_monthly_scores`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `work_item_id` int NOT NULL,
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `month` varchar(7) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `score` float NULL DEFAULT NULL,
  `calculate_score` float NULL DEFAULT NULL,
  `quality_score` float NULL DEFAULT NULL,
  `quality_score_updated_at` datetime NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_work_item_month`(`work_item_id` ASC, `month` ASC) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  INDEX `ix_work_item_monthly_scores_month`(`month` ASC) USING BTREE,
  INDEX `ix_work_item_monthly_scores_id`(`id` ASC) USING BTREE,
  INDEX `idx_ms_work_item_id`(`work_item_id` ASC) USING BTREE,
  INDEX `idx_ms_month`(`month` ASC) USING BTREE,
  CONSTRAINT `work_item_monthly_scores_ibfk_1` FOREIGN KEY (`work_item_id`) REFERENCES `work_items` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_item_monthly_scores_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 28 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for work_items
-- ----------------------------
DROP TABLE IF EXISTS `work_items`;
CREATE TABLE `work_items`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `standard` text CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL,
  `difficulty` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `importance` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `innovation` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `deadline` datetime NOT NULL,
  `completed_at` datetime NULL DEFAULT NULL,
  `score` float NULL DEFAULT NULL,
  `complete_status` tinyint(1) NULL DEFAULT NULL,
  `work_package_id` int NOT NULL,
  `owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `notes` text CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL,
  `isclosed` tinyint(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_work_items_id`(`id` ASC) USING BTREE,
  INDEX `idx_work_items_work_package_id`(`work_package_id` ASC) USING BTREE,
  CONSTRAINT `work_items_ibfk_1` FOREIGN KEY (`work_package_id`) REFERENCES `work_packages` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 56 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for work_package_categories
-- ----------------------------
DROP TABLE IF EXISTS `work_package_categories`;
CREATE TABLE `work_package_categories`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_work_package_categories_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for work_package_split_requests
-- ----------------------------
DROP TABLE IF EXISTS `work_package_split_requests`;
CREATE TABLE `work_package_split_requests`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `work_package_id` int NOT NULL,
  `applicant_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `reason` text CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `split_items` text CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `reviewer_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `review_comment` text CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `reviewed_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `work_package_id`(`work_package_id` ASC) USING BTREE,
  INDEX `applicant_id`(`applicant_id` ASC) USING BTREE,
  INDEX `reviewer_id`(`reviewer_id` ASC) USING BTREE,
  INDEX `ix_work_package_split_requests_id`(`id` ASC) USING BTREE,
  CONSTRAINT `work_package_split_requests_ibfk_1` FOREIGN KEY (`work_package_id`) REFERENCES `work_packages` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_package_split_requests_ibfk_2` FOREIGN KEY (`applicant_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_package_split_requests_ibfk_3` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for work_packages
-- ----------------------------
DROP TABLE IF EXISTS `work_packages`;
CREATE TABLE `work_packages`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NOT NULL,
  `owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `name` text CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL,
  `complete_status` tinyint(1) NULL DEFAULT NULL,
  `tech_owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `project_id` int NOT NULL,
  `category_name` varchar(100) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `objective` varchar(100) CHARACTER SET utf8mb4 COLLATE uft8mb4_unicode_ci NULL DEFAULT NULL,
  `isclosed` tinyint(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `owner_id`(`owner_id` ASC) USING BTREE,
  INDEX `category_name`(`category_name` ASC) USING BTREE,
  INDEX `ix_work_packages_id`(`id` ASC) USING BTREE,
  INDEX `idx_work_packages_project_id`(`project_id` ASC) USING BTREE,
  CONSTRAINT `work_packages_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_packages_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 28 CHARACTER SET = utf8mb4 COLLATE = uft8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
