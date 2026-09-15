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

 Date: 15/09/2026 17:17:34
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for monthly_extra_score
-- ----------------------------
DROP TABLE IF EXISTS `monthly_extra_score`;
CREATE TABLE `monthly_extra_score`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `patent_score` float NULL DEFAULT NULL,
  `knowledge_score` float NULL DEFAULT NULL,
  `train_score` float NULL DEFAULT NULL,
  `deduct_score` float NULL DEFAULT NULL,
  `quality_event_score` float NULL DEFAULT NULL,
  `carrier_inspection_score` float NULL DEFAULT NULL,
  `updated_by_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_user_month`(`user_id` ASC, `month` ASC) USING BTREE,
  INDEX `updated_by_id`(`updated_by_id` ASC) USING BTREE,
  INDEX `ix_monthly_extra_score_id`(`id` ASC) USING BTREE,
  INDEX `ix_monthly_extra_score_month`(`month` ASC) USING BTREE,
  CONSTRAINT `monthly_extra_score_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `monthly_extra_score_ibfk_2` FOREIGN KEY (`updated_by_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of monthly_extra_score
-- ----------------------------

-- ----------------------------
-- Table structure for projects
-- ----------------------------
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `level` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `complete_status` tinyint(1) NULL DEFAULT NULL,
  `category` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `tech_owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isclosed` tinyint(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `owner_id`(`owner_id` ASC) USING BTREE,
  INDEX `tech_owner_id`(`tech_owner_id` ASC) USING BTREE,
  INDEX `ix_projects_name`(`name` ASC) USING BTREE,
  INDEX `ix_projects_id`(`id` ASC) USING BTREE,
  CONSTRAINT `projects_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `projects_ibfk_2` FOREIGN KEY (`tech_owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 218 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of projects
-- ----------------------------
INSERT INTO `projects` VALUES (118, 'QEIX', 'jherbert', '18', 'C', 1, '类型4', '18', 0);
INSERT INTO `projects` VALUES (119, 'JEWZ', 'lawrence86', '19', 'D', 1, '类型1', '19', 0);
INSERT INTO `projects` VALUES (120, 'KGJH', 'zli', '5', 'C', 1, '类型4', '5', 0);
INSERT INTO `projects` VALUES (121, 'VPWW', 'sakuy703', '19', 'A', 0, '类型4', '19', 0);
INSERT INTO `projects` VALUES (122, 'LUTI', 'hikaruic', '8', 'A', 0, '类型1', '8', 0);
INSERT INTO `projects` VALUES (123, 'NTAO', 'ba69', '1', 'B', 0, '类型3', '1', 0);
INSERT INTO `projects` VALUES (124, 'MNYI', 'cmildred', '12', 'D', 0, '类型3', '12', 0);
INSERT INTO `projects` VALUES (125, 'JZKO', 'takazuma1', '0123', 'A', 1, '类型3', '0123', 0);
INSERT INTO `projects` VALUES (126, 'JDTZ', 'cltam10', '17', 'C', 1, '类型3', '17', 0);
INSERT INTO `projects` VALUES (127, 'FOUE', 'takmiura209', '11', 'D', 1, '类型2', '11', 0);
INSERT INTO `projects` VALUES (128, 'ZUZW', 'fang6', '14', 'C', 0, '类型3', '14', 0);
INSERT INTO `projects` VALUES (129, 'ZBPA', 'fschiang', '30', 'B', 0, '类型4', '30', 0);
INSERT INTO `projects` VALUES (130, 'TPTQ', 'ok6', '20', 'B', 0, '类型3', '20', 0);
INSERT INTO `projects` VALUES (131, 'XMRW', 'eita415', '13', 'A', 1, '类型3', '13', 0);
INSERT INTO `projects` VALUES (132, 'VGBK', 'yunayamaguchi4', '2', 'A', 1, '类型4', '2', 0);
INSERT INTO `projects` VALUES (133, 'YEJQ', 'holmes4', '1', 'A', 1, '类型3', '1', 0);
INSERT INTO `projects` VALUES (134, 'RWWM', 'hikarui10', '2', 'C', 0, '类型4', '2', 0);
INSERT INTO `projects` VALUES (135, 'DUWF', 'sugawara41', '15', 'A', 1, '类型1', '15', 0);
INSERT INTO `projects` VALUES (136, 'WPAT', 'xzhennan', '13', 'A', 0, '类型4', '13', 0);
INSERT INTO `projects` VALUES (137, 'JAEY', 'yamato605', '19', 'B', 1, '类型1', '19', 0);
INSERT INTO `projects` VALUES (138, 'WGBR', 'lingling10', '30', 'D', 1, '类型2', '30', 0);
INSERT INTO `projects` VALUES (139, 'MAXR', 'rena5', '26', 'C', 0, '类型2', '26', 0);
INSERT INTO `projects` VALUES (140, 'EFRE', 'fujiwarama', '11', 'C', 0, '类型3', '11', 0);
INSERT INTO `projects` VALUES (141, 'FLMG', 'tujoa', '0000', 'C', 0, '类型3', '0000', 0);
INSERT INTO `projects` VALUES (142, 'ADUX', 'kasumnakagawa', '28', 'C', 0, '类型4', '28', 0);
INSERT INTO `projects` VALUES (143, 'NVML', 'allen1130', '5', 'B', 1, '类型4', '5', 0);
INSERT INTO `projects` VALUES (144, 'HSON', 'kyying', '3', 'D', 0, '类型1', '3', 0);
INSERT INTO `projects` VALUES (145, 'HMYX', 'changtingfung3', '28', 'D', 0, '类型3', '28', 0);
INSERT INTO `projects` VALUES (146, 'HOEB', 'ya81', '19', 'B', 0, '类型4', '19', 0);
INSERT INTO `projects` VALUES (147, 'LMRU', 'klyue3', '13', 'A', 1, '类型3', '13', 0);
INSERT INTO `projects` VALUES (148, 'VSWQ', 'narimura', '24', 'D', 1, '类型3', '24', 0);
INSERT INTO `projects` VALUES (149, 'QFHX', 'crawford84', '1', 'C', 1, '类型4', '1', 0);
INSERT INTO `projects` VALUES (150, 'KOSF', 'peternguy', '18', 'A', 0, '类型1', '18', 0);
INSERT INTO `projects` VALUES (151, 'PITL', 'ortiz10', '10', 'B', 1, '类型3', '10', 0);
INSERT INTO `projects` VALUES (152, 'OCLH', 'yunfatcheung708', '9', 'C', 1, '类型3', '9', 0);
INSERT INTO `projects` VALUES (153, 'UIBI', 'emily313', '26', 'D', 0, '类型3', '26', 0);
INSERT INTO `projects` VALUES (154, 'GAAK', 'louiseclark', '3', 'D', 0, '类型4', '3', 0);
INSERT INTO `projects` VALUES (155, 'NLNH', 'mchiyuen', '13', 'C', 1, '类型3', '13', 0);
INSERT INTO `projects` VALUES (156, 'ISYX', 'zgong327', '12', 'A', 0, '类型2', '12', 0);
INSERT INTO `projects` VALUES (157, 'RUZZ', 'wilson205', '11', 'B', 1, '类型4', '11', 0);
INSERT INTO `projects` VALUES (158, 'PRMG', 'sun1973', '4', 'C', 0, '类型4', '4', 0);
INSERT INTO `projects` VALUES (159, 'TOMF', 'wffung1972', '24', 'D', 1, '类型1', '24', 0);
INSERT INTO `projects` VALUES (160, 'SRBQ', 'wu7', '27', 'C', 0, '类型1', '27', 0);
INSERT INTO `projects` VALUES (161, 'JSRO', 'ghunte', '0123', 'D', 1, '类型3', '0123', 0);
INSERT INTO `projects` VALUES (162, 'RQZV', 'kwokwing55', '8', 'B', 0, '类型1', '8', 0);
INSERT INTO `projects` VALUES (163, 'WWCT', 'kylok', '4', 'D', 1, '类型4', '4', 0);
INSERT INTO `projects` VALUES (164, 'AIAB', 'clpang', '13', 'A', 0, '类型4', '13', 0);
INSERT INTO `projects` VALUES (165, 'ZUWN', 'jianyuning', '25', 'C', 1, '类型4', '25', 0);
INSERT INTO `projects` VALUES (166, 'ASFG', 'ereynolds', '8', 'B', 0, '类型1', '8', 0);
INSERT INTO `projects` VALUES (167, 'OQBO', 'akato', '9', 'B', 0, '类型1', '9', 0);
INSERT INTO `projects` VALUES (168, 'RJEO', 'zhengzit', '5', 'C', 0, '类型4', '5', 0);
INSERT INTO `projects` VALUES (169, 'OFCB', 'kwokyinmo1116', '21', 'D', 1, '类型3', '21', 0);
INSERT INTO `projects` VALUES (170, 'JIXN', 'kazuma203', '28', 'A', 0, '类型2', '28', 0);
INSERT INTO `projects` VALUES (171, 'CUON', 'fming', '5', 'C', 0, '类型3', '5', 0);
INSERT INTO `projects` VALUES (172, 'RVGA', 'lanma', '10', 'A', 0, '类型1', '10', 0);
INSERT INTO `projects` VALUES (173, 'ABBO', 'yaichikawa', '13', 'A', 1, '类型4', '13', 0);
INSERT INTO `projects` VALUES (174, 'WWAZ', 'chungyin6', '6', 'A', 0, '类型1', '6', 0);
INSERT INTO `projects` VALUES (175, 'JBNK', 'jiehong57', '0123', 'D', 1, '类型3', '0123', 0);
INSERT INTO `projects` VALUES (176, 'XRYO', 'crose', '18', 'A', 1, '类型3', '18', 0);
INSERT INTO `projects` VALUES (177, 'XXRV', 'kenito', '15', 'C', 0, '类型4', '15', 0);
INSERT INTO `projects` VALUES (178, 'PERT', 'kato10', '21', 'B', 0, '类型4', '21', 0);
INSERT INTO `projects` VALUES (179, 'HQFL', 'zitao2', '6', 'D', 0, '类型2', '6', 0);
INSERT INTO `projects` VALUES (180, 'MKOE', 'anqipeng', '12', 'B', 1, '类型4', '12', 0);
INSERT INTO `projects` VALUES (181, 'XAET', 'llpak', '24', 'C', 1, '类型2', '24', 0);
INSERT INTO `projects` VALUES (182, 'GMOC', 'danielfernandez', '30', 'B', 1, '类型4', '30', 0);
INSERT INTO `projects` VALUES (183, 'KENY', 'shinomi924', '3', 'A', 0, '类型3', '3', 0);
INSERT INTO `projects` VALUES (184, 'UDZG', 'daichis', '7', 'C', 0, '类型2', '7', 0);
INSERT INTO `projects` VALUES (185, 'EXFZ', 'xiak', '26', 'A', 1, '类型4', '26', 0);
INSERT INTO `projects` VALUES (186, 'WDZC', 'lziyi', '9', 'A', 0, '类型2', '9', 0);
INSERT INTO `projects` VALUES (187, 'RFHP', 'okaday', '27', 'C', 0, '类型2', '27', 0);
INSERT INTO `projects` VALUES (188, 'XUHV', 'tinwinghsua', '20', 'D', 1, '类型4', '20', 0);
INSERT INTO `projects` VALUES (189, 'OGSI', 'chomingsze', '7', 'D', 1, '类型3', '7', 0);
INSERT INTO `projects` VALUES (190, 'DXQL', 'maryale', '0123', 'D', 0, '类型2', '0123', 0);
INSERT INTO `projects` VALUES (191, 'EGNS', 'fushing02', '15', 'D', 1, '类型4', '15', 0);
INSERT INTO `projects` VALUES (192, 'NEUZ', 'szekwanman', '0000', 'C', 1, '类型2', '0000', 0);
INSERT INTO `projects` VALUES (193, 'IKLT', 'jbrown710', '13', 'D', 1, '类型4', '13', 0);
INSERT INTO `projects` VALUES (194, 'FJLP', 'xiuying10', '4', 'C', 1, '类型3', '4', 0);
INSERT INTO `projects` VALUES (195, 'RNRM', 'tsuisw5', '20', 'C', 1, '类型1', '20', 0);
INSERT INTO `projects` VALUES (196, 'ACTA', 'fernandez2', '14', 'A', 1, '类型2', '14', 0);
INSERT INTO `projects` VALUES (197, 'BPMN', 'leews', '12', 'A', 1, '类型2', '12', 0);
INSERT INTO `projects` VALUES (198, 'ZQGA', 'miryota', '17', 'C', 0, '类型2', '17', 0);
INSERT INTO `projects` VALUES (199, 'ZWOK', 'shenz1954', '30', 'B', 1, '类型1', '30', 0);
INSERT INTO `projects` VALUES (200, 'ILIH', 'heathercoleman', '0000', 'A', 1, '类型4', '0000', 0);
INSERT INTO `projects` VALUES (201, 'NAKU', 'tingfungcho', '28', 'B', 0, '类型4', '28', 0);
INSERT INTO `projects` VALUES (202, 'DVQA', 'wbonnie203', '24', 'A', 1, '类型2', '24', 0);
INSERT INTO `projects` VALUES (203, 'TQRQ', 'chiehlun4', '3', 'D', 1, '类型2', '3', 0);
INSERT INTO `projects` VALUES (204, 'RPWV', 'crasteph12', '18', 'D', 1, '类型1', '18', 0);
INSERT INTO `projects` VALUES (205, 'DMME', 'jialei', '0000', 'A', 0, '类型3', '0000', 0);
INSERT INTO `projects` VALUES (206, 'DZGU', 'xiong88', '30', 'B', 0, '类型2', '30', 0);
INSERT INTO `projects` VALUES (207, 'EIAQ', 'weizitao1974', '5', 'C', 1, '类型3', '5', 0);
INSERT INTO `projects` VALUES (208, 'SNTG', 'sklou', '2', 'D', 1, '类型3', '2', 0);
INSERT INTO `projects` VALUES (209, 'ZVWY', 'yanglu', '7', 'A', 1, '类型4', '7', 0);
INSERT INTO `projects` VALUES (210, 'YSPC', 'rkoyama6', '25', 'D', 1, '类型2', '25', 0);
INSERT INTO `projects` VALUES (211, 'ADBC', 'xiuyinglei', '20', 'A', 0, '类型2', '20', 0);
INSERT INTO `projects` VALUES (212, 'ADJX', 'dengxiuyi10', '29', 'A', 0, '类型4', '29', 0);
INSERT INTO `projects` VALUES (213, 'EVVD', 'zhengrui202', '27', 'D', 0, '类型1', '27', 0);
INSERT INTO `projects` VALUES (214, 'PZWV', 'choikaling10', '26', 'B', 1, '类型2', '26', 0);
INSERT INTO `projects` VALUES (215, 'BJSE', 'hokyauwong', '0012', 'D', 0, '类型2', '0012', 0);
INSERT INTO `projects` VALUES (216, 'OFRS', 'tokim75', '4', 'D', 1, '类型2', '4', 0);
INSERT INTO `projects` VALUES (217, 'CEIT', 'waihacheung314', '7', 'D', 0, '类型3', '7', 0);

-- ----------------------------
-- Table structure for score_dimension_levels
-- ----------------------------
DROP TABLE IF EXISTS `score_dimension_levels`;
CREATE TABLE `score_dimension_levels`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `variable` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `level` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `factor` float NULL DEFAULT NULL,
  `job_grade` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_score_dimension_levels_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 396 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of score_dimension_levels
-- ----------------------------
INSERT INTO `score_dimension_levels` VALUES (315, 'difficulty', 'P2', 1, 'P2');
INSERT INTO `score_dimension_levels` VALUES (316, 'difficulty', 'P3', 1.05, 'P2');
INSERT INTO `score_dimension_levels` VALUES (317, 'difficulty', 'P4', 1.1, 'P2');
INSERT INTO `score_dimension_levels` VALUES (318, 'difficulty', 'P5', 1.15, 'P2');
INSERT INTO `score_dimension_levels` VALUES (319, 'difficulty', 'P6', 1.2, 'P2');
INSERT INTO `score_dimension_levels` VALUES (320, 'difficulty', 'P7', 1.25, 'P2');
INSERT INTO `score_dimension_levels` VALUES (321, 'difficulty', 'P8', 1.3, 'P2');
INSERT INTO `score_dimension_levels` VALUES (322, 'importance', 'Ⅰ级', 0.175, 'P2');
INSERT INTO `score_dimension_levels` VALUES (323, 'importance', 'Ⅱ级', 0.125, 'P2');
INSERT INTO `score_dimension_levels` VALUES (324, 'importance', 'Ⅲ级', 0.075, 'P2');
INSERT INTO `score_dimension_levels` VALUES (325, 'importance', 'Ⅳ级', 0, 'P2');
INSERT INTO `score_dimension_levels` VALUES (326, 'difficulty', 'P2', 1, 'P3');
INSERT INTO `score_dimension_levels` VALUES (327, 'difficulty', 'P3', 1, 'P3');
INSERT INTO `score_dimension_levels` VALUES (328, 'difficulty', 'P4', 1.05, 'P3');
INSERT INTO `score_dimension_levels` VALUES (329, 'difficulty', 'P5', 1.1, 'P3');
INSERT INTO `score_dimension_levels` VALUES (330, 'difficulty', 'P6', 1.15, 'P3');
INSERT INTO `score_dimension_levels` VALUES (331, 'difficulty', 'P7', 1.2, 'P3');
INSERT INTO `score_dimension_levels` VALUES (332, 'difficulty', 'P8', 1.25, 'P3');
INSERT INTO `score_dimension_levels` VALUES (333, 'importance', 'Ⅰ级', 0.15, 'P3');
INSERT INTO `score_dimension_levels` VALUES (334, 'importance', 'Ⅱ级', 0.1, 'P3');
INSERT INTO `score_dimension_levels` VALUES (335, 'importance', 'Ⅲ级', 0.5, 'P3');
INSERT INTO `score_dimension_levels` VALUES (336, 'importance', 'Ⅳ级', 0, 'P3');
INSERT INTO `score_dimension_levels` VALUES (337, 'difficulty', 'P2', 1, 'P4');
INSERT INTO `score_dimension_levels` VALUES (338, 'difficulty', 'P3', 1, 'P4');
INSERT INTO `score_dimension_levels` VALUES (339, 'difficulty', 'P4', 1, 'P4');
INSERT INTO `score_dimension_levels` VALUES (340, 'difficulty', 'P5', 1.05, 'P4');
INSERT INTO `score_dimension_levels` VALUES (341, 'difficulty', 'P6', 1.1, 'P4');
INSERT INTO `score_dimension_levels` VALUES (342, 'difficulty', 'P7', 1.15, 'P4');
INSERT INTO `score_dimension_levels` VALUES (343, 'difficulty', 'P8', 1.2, 'P4');
INSERT INTO `score_dimension_levels` VALUES (344, 'importance', 'Ⅰ级', 0.125, 'P4');
INSERT INTO `score_dimension_levels` VALUES (345, 'importance', 'Ⅱ级', 0.075, 'P4');
INSERT INTO `score_dimension_levels` VALUES (346, 'importance', 'Ⅲ级', 0.025, 'P4');
INSERT INTO `score_dimension_levels` VALUES (347, 'importance', 'Ⅳ级', 0, 'P4');
INSERT INTO `score_dimension_levels` VALUES (348, 'difficulty', 'P2', 1, 'P5');
INSERT INTO `score_dimension_levels` VALUES (349, 'difficulty', 'P3', 1, 'P5');
INSERT INTO `score_dimension_levels` VALUES (350, 'difficulty', 'P4', 1, 'P5');
INSERT INTO `score_dimension_levels` VALUES (351, 'difficulty', 'P5', 1, 'P5');
INSERT INTO `score_dimension_levels` VALUES (352, 'difficulty', 'P6', 1.05, 'P5');
INSERT INTO `score_dimension_levels` VALUES (353, 'difficulty', 'P7', 1.1, 'P5');
INSERT INTO `score_dimension_levels` VALUES (354, 'difficulty', 'P8', 1.15, 'P5');
INSERT INTO `score_dimension_levels` VALUES (355, 'importance', 'Ⅰ级', 0.1, 'P5');
INSERT INTO `score_dimension_levels` VALUES (356, 'importance', 'Ⅱ级', 0.5, 'P5');
INSERT INTO `score_dimension_levels` VALUES (357, 'importance', 'Ⅲ级', 0, 'P5');
INSERT INTO `score_dimension_levels` VALUES (358, 'importance', 'Ⅳ级', 0, 'P5');
INSERT INTO `score_dimension_levels` VALUES (359, 'difficulty', 'P2', 1, 'P6');
INSERT INTO `score_dimension_levels` VALUES (360, 'difficulty', 'P3', 1, 'P6');
INSERT INTO `score_dimension_levels` VALUES (361, 'difficulty', 'P4', 1, 'P6');
INSERT INTO `score_dimension_levels` VALUES (362, 'difficulty', 'P5', 1, 'P6');
INSERT INTO `score_dimension_levels` VALUES (363, 'difficulty', 'P6', 1, 'P6');
INSERT INTO `score_dimension_levels` VALUES (364, 'difficulty', 'P7', 1.05, 'P6');
INSERT INTO `score_dimension_levels` VALUES (365, 'difficulty', 'P8', 1.1, 'P6');
INSERT INTO `score_dimension_levels` VALUES (366, 'importance', 'Ⅰ级', 0.75, 'P6');
INSERT INTO `score_dimension_levels` VALUES (367, 'importance', 'Ⅱ级', 0.25, 'P6');
INSERT INTO `score_dimension_levels` VALUES (368, 'importance', 'Ⅲ级', 0, 'P6');
INSERT INTO `score_dimension_levels` VALUES (369, 'importance', 'Ⅳ级', 0, 'P6');
INSERT INTO `score_dimension_levels` VALUES (370, 'difficulty', 'P2', 1, 'P7');
INSERT INTO `score_dimension_levels` VALUES (371, 'difficulty', 'P3', 1, 'P7');
INSERT INTO `score_dimension_levels` VALUES (372, 'difficulty', 'P4', 1, 'P7');
INSERT INTO `score_dimension_levels` VALUES (373, 'difficulty', 'P5', 1, 'P7');
INSERT INTO `score_dimension_levels` VALUES (374, 'difficulty', 'P6', 1, 'P7');
INSERT INTO `score_dimension_levels` VALUES (375, 'difficulty', 'P7', 1, 'P7');
INSERT INTO `score_dimension_levels` VALUES (376, 'difficulty', 'P8', 1.05, 'P7');
INSERT INTO `score_dimension_levels` VALUES (377, 'importance', 'Ⅰ级', 0.5, 'P7');
INSERT INTO `score_dimension_levels` VALUES (378, 'importance', 'Ⅱ级', 0, 'P7');
INSERT INTO `score_dimension_levels` VALUES (379, 'importance', 'Ⅲ级', 0, 'P7');
INSERT INTO `score_dimension_levels` VALUES (380, 'importance', 'Ⅳ级', 0, 'P7');
INSERT INTO `score_dimension_levels` VALUES (381, 'difficulty', 'P2', 1, 'P8');
INSERT INTO `score_dimension_levels` VALUES (382, 'difficulty', 'P3', 1, 'P8');
INSERT INTO `score_dimension_levels` VALUES (383, 'difficulty', 'P4', 1, 'P8');
INSERT INTO `score_dimension_levels` VALUES (384, 'difficulty', 'P5', 1, 'P8');
INSERT INTO `score_dimension_levels` VALUES (385, 'difficulty', 'P6', 1, 'P8');
INSERT INTO `score_dimension_levels` VALUES (386, 'difficulty', 'P7', 1, 'P8');
INSERT INTO `score_dimension_levels` VALUES (387, 'difficulty', 'P8', 1.05, 'P8');
INSERT INTO `score_dimension_levels` VALUES (388, 'importance', 'Ⅰ级', 0.25, 'P8');
INSERT INTO `score_dimension_levels` VALUES (389, 'importance', 'Ⅱ级', 0, 'P8');
INSERT INTO `score_dimension_levels` VALUES (390, 'importance', 'Ⅲ级', 0, 'P8');
INSERT INTO `score_dimension_levels` VALUES (391, 'importance', 'Ⅳ级', 0, 'P8');
INSERT INTO `score_dimension_levels` VALUES (392, 'innovation', '无', 0, '');
INSERT INTO `score_dimension_levels` VALUES (393, 'innovation', '低', 0.1, '');
INSERT INTO `score_dimension_levels` VALUES (394, 'innovation', '中', 0.2, '');
INSERT INTO `score_dimension_levels` VALUES (395, 'innovation', '高', 0.3, '');

-- ----------------------------
-- Table structure for score_level_defs
-- ----------------------------
DROP TABLE IF EXISTS `score_level_defs`;
CREATE TABLE `score_level_defs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `sort_order` int NULL DEFAULT NULL,
  `is_active` int NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_def_category_name`(`category` ASC, `name` ASC) USING BTREE,
  INDEX `ix_score_level_defs_category`(`category` ASC) USING BTREE,
  INDEX `ix_score_level_defs_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 120 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of score_level_defs
-- ----------------------------
INSERT INTO `score_level_defs` VALUES (98, 'job_grade', 'P2', 0, 1);
INSERT INTO `score_level_defs` VALUES (99, 'job_grade', 'P3', 1, 1);
INSERT INTO `score_level_defs` VALUES (100, 'job_grade', 'P4', 2, 1);
INSERT INTO `score_level_defs` VALUES (101, 'job_grade', 'P5', 3, 1);
INSERT INTO `score_level_defs` VALUES (102, 'job_grade', 'P6', 4, 1);
INSERT INTO `score_level_defs` VALUES (103, 'job_grade', 'P7', 5, 1);
INSERT INTO `score_level_defs` VALUES (104, 'job_grade', 'P8', 6, 1);
INSERT INTO `score_level_defs` VALUES (105, 'difficulty', 'P2', 0, 1);
INSERT INTO `score_level_defs` VALUES (106, 'difficulty', 'P3', 1, 1);
INSERT INTO `score_level_defs` VALUES (107, 'difficulty', 'P4', 2, 1);
INSERT INTO `score_level_defs` VALUES (108, 'difficulty', 'P5', 3, 1);
INSERT INTO `score_level_defs` VALUES (109, 'difficulty', 'P6', 4, 1);
INSERT INTO `score_level_defs` VALUES (110, 'difficulty', 'P7', 5, 1);
INSERT INTO `score_level_defs` VALUES (111, 'difficulty', 'P8', 6, 1);
INSERT INTO `score_level_defs` VALUES (112, 'importance', 'Ⅰ级', 0, 1);
INSERT INTO `score_level_defs` VALUES (113, 'importance', 'Ⅱ级', 1, 1);
INSERT INTO `score_level_defs` VALUES (114, 'importance', 'Ⅲ级', 2, 1);
INSERT INTO `score_level_defs` VALUES (115, 'importance', 'Ⅳ级', 3, 1);
INSERT INTO `score_level_defs` VALUES (116, 'innovation', '无', 0, 1);
INSERT INTO `score_level_defs` VALUES (117, 'innovation', '低', 1, 1);
INSERT INTO `score_level_defs` VALUES (118, 'innovation', '中', 2, 1);
INSERT INTO `score_level_defs` VALUES (119, 'innovation', '高', 3, 1);

-- ----------------------------
-- Table structure for task_transfers
-- ----------------------------
DROP TABLE IF EXISTS `task_transfers`;
CREATE TABLE `task_transfers`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `work_package_id` int NOT NULL,
  `from_user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '发起人(原负责人)',
  `to_user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '接收人(新负责人)',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '状态: PENDING/ACCEPTED/REJECTED',
  `created_at` datetime NULL DEFAULT NULL,
  `transfer_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'work_item',
  `work_item_id` int NULL DEFAULT NULL,
  `transfer_score` float NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `work_package_id`(`work_package_id` ASC) USING BTREE,
  INDEX `ix_task_transfers_id`(`id` ASC) USING BTREE,
  CONSTRAINT `task_transfers_ibfk_1` FOREIGN KEY (`work_package_id`) REFERENCES `work_packages` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of task_transfers
-- ----------------------------

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `job_grade` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `is_deleted` tinyint NULL DEFAULT 0,
  `deleted_at` datetime NULL DEFAULT NULL,
  `deleted_by` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_users_username`(`username` ASC) USING BTREE,
  INDEX `ix_users_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES ('0000', '小明', '123456', 'ADMIN', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('0001', '小苏', '123456', 'DEPARTMENT', 'P5', 1, '2026-09-07 16:54:22', '0000');
INSERT INTO `users` VALUES ('0012', '小李', '123456', 'DEPARTMENT', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('0123', '小王', '123456', 'LEADER', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('1', '姜璐', '693720', 'DEPARTMENT', 'P8', 0, NULL, NULL);
INSERT INTO `users` VALUES ('10', '贺詩涵', '848400', 'DEPARTMENT', 'P7', 0, NULL, NULL);
INSERT INTO `users` VALUES ('11', '谢嘉伦', '838922', 'LEADER', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('12', '卢嘉伦', '842648', 'DEPARTMENT', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('13', '汪嘉伦', '428408', 'LEADER', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('14', '钱云熙', '447536', 'ADMIN', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('15', '钱岚', '771599', 'LEADER', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('16', '傅宇宁', '818676', 'DEPARTMENT', 'P5', 0, NULL, NULL);
INSERT INTO `users` VALUES ('17', '郑杰宏', '619128', 'ADMIN', 'P6', 0, NULL, NULL);
INSERT INTO `users` VALUES ('18', '贾宇宁', '640747', 'ADMIN', 'P6', 0, NULL, NULL);
INSERT INTO `users` VALUES ('19', '任璐', '228225', 'LEADER', 'P5', 0, NULL, NULL);
INSERT INTO `users` VALUES ('2', '雷晓明', '713485', 'ADMIN', 'P8', 0, NULL, NULL);
INSERT INTO `users` VALUES ('20', '向子异', '446543', 'EMPLOYEE', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('21', '赵子韬', '336191', 'EMPLOYEE', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('22', '谢詩涵', '412411', 'EMPLOYEE', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('23', '姚晓明', '794492', 'DEPARTMENT', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('24', '李秀英', '080103', 'DEPARTMENT', 'P6', 0, NULL, NULL);
INSERT INTO `users` VALUES ('25', '何璐', '289818', 'LEADER', 'P7', 0, NULL, NULL);
INSERT INTO `users` VALUES ('26', '叶睿', '201068', 'LEADER', 'P3', 0, NULL, NULL);
INSERT INTO `users` VALUES ('27', '段震南', '112170', 'LEADER', 'P8', 0, NULL, NULL);
INSERT INTO `users` VALUES ('28', '严詩涵', '130053', 'DEPARTMENT', 'P8', 0, NULL, NULL);
INSERT INTO `users` VALUES ('29', '陆子韬', '485088', 'ADMIN', 'P2', 0, NULL, NULL);
INSERT INTO `users` VALUES ('3', '马子异', '396096', 'ADMIN', 'P8', 0, NULL, NULL);
INSERT INTO `users` VALUES ('30', '魏璐', '397076', 'LEADER', 'P8', 0, NULL, NULL);
INSERT INTO `users` VALUES ('4', '丁睿', '498009', 'EMPLOYEE', 'P5', 0, NULL, NULL);
INSERT INTO `users` VALUES ('5', '李璐', '708368', 'ADMIN', 'P7', 0, NULL, NULL);
INSERT INTO `users` VALUES ('6', '宋安琪', '178454', 'LEADER', 'P7', 0, NULL, NULL);
INSERT INTO `users` VALUES ('7', '程晓明', '769168', 'LEADER', 'P4', 0, NULL, NULL);
INSERT INTO `users` VALUES ('8', '林宇宁', '928497', 'DEPARTMENT', 'P4', 0, NULL, NULL);
INSERT INTO `users` VALUES ('9', '蔡睿', '958824', 'ADMIN', 'P7', 0, NULL, NULL);

-- ----------------------------
-- Table structure for work_item_completion_reviews
-- ----------------------------
DROP TABLE IF EXISTS `work_item_completion_reviews`;
CREATE TABLE `work_item_completion_reviews`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `work_item_id` int NOT NULL,
  `applicant_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `reviewer_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `review_comment` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `reviewed_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `work_item_id`(`work_item_id` ASC) USING BTREE,
  INDEX `applicant_id`(`applicant_id` ASC) USING BTREE,
  INDEX `reviewer_id`(`reviewer_id` ASC) USING BTREE,
  CONSTRAINT `work_item_completion_reviews_ibfk_1` FOREIGN KEY (`work_item_id`) REFERENCES `work_items` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_item_completion_reviews_ibfk_2` FOREIGN KEY (`applicant_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_item_completion_reviews_ibfk_3` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of work_item_completion_reviews
-- ----------------------------
INSERT INTO `work_item_completion_reviews` VALUES (2, 536, '0000', '0000', 'APPROVED', '负责人手动确认完成', '审核通过', '2026-09-15 15:11:17', '2026-09-15 15:11:40');
INSERT INTO `work_item_completion_reviews` VALUES (3, 166, '30', '0000', 'REJECTED', '进度已满，系统自动提交完成申请', '工作量不够', '2026-09-15 15:17:00', '2026-09-15 15:17:42');
INSERT INTO `work_item_completion_reviews` VALUES (4, 469, '22', NULL, 'PENDING', '进度已满，系统自动提交完成申请', NULL, '2026-09-15 15:25:24', NULL);

-- ----------------------------
-- Table structure for work_item_monthly_scores
-- ----------------------------
DROP TABLE IF EXISTS `work_item_monthly_scores`;
CREATE TABLE `work_item_monthly_scores`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `work_item_id` int NOT NULL,
  `user_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
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
) ENGINE = InnoDB AUTO_INCREMENT = 35 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of work_item_monthly_scores
-- ----------------------------
INSERT INTO `work_item_monthly_scores` VALUES (32, 536, '0123', '2026-09', 92.9, 116.125, 0, NULL, '2026-09-15 15:12:00', '2026-09-15 15:12:00');
INSERT INTO `work_item_monthly_scores` VALUES (33, 166, '30', '2026-09', 70.1, 91.13, 0, NULL, '2026-09-15 15:12:07', '2026-09-15 15:12:07');
INSERT INTO `work_item_monthly_scores` VALUES (34, 469, '22', '2026-09', 11.6, 11.6, 0, NULL, '2026-09-15 15:25:24', '2026-09-15 15:25:24');

-- ----------------------------
-- Table structure for work_items
-- ----------------------------
DROP TABLE IF EXISTS `work_items`;
CREATE TABLE `work_items`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `standard` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `difficulty` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `importance` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `innovation` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `deadline` datetime NOT NULL,
  `completed_at` datetime NULL DEFAULT NULL,
  `score` float NULL DEFAULT NULL,
  `complete_status` tinyint(1) NULL DEFAULT NULL,
  `work_package_id` int NOT NULL,
  `owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `isclosed` tinyint(1) NULL DEFAULT 0,
  `tech_owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_work_items_id`(`id` ASC) USING BTREE,
  INDEX `idx_work_items_work_package_id`(`work_package_id` ASC) USING BTREE,
  INDEX `work_items_ibfk_2`(`tech_owner_id` ASC) USING BTREE,
  CONSTRAINT `work_items_ibfk_1` FOREIGN KEY (`work_package_id`) REFERENCES `work_packages` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_items_ibfk_2` FOREIGN KEY (`tech_owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 558 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of work_items
-- ----------------------------
INSERT INTO `work_items` VALUES (58, 'Navicat allows you to transfer                    ', 'In other words, Navicat provides                  ', 'P7', 'Ⅰ', '低', '2027-10-30 05:33:49', NULL, 25.4, 0, 43, '8', 'Always keep your eyes open. Keep                  ', 0, '3');
INSERT INTO `work_items` VALUES (59, 'Navicat is a multi-connections                    ', 'Anyone who has ever made anything                 ', 'P7', 'Ⅰ', '中', '2027-05-29 06:59:08', NULL, 31.2, 0, 35, '6', 'There is no way to happiness. Happiness           ', 0, '0123');
INSERT INTO `work_items` VALUES (60, 'Navicat allows you to transfer                    ', 'Optimism is the one quality more                  ', 'P5', 'Ⅱ', '中', '2027-01-22 04:35:05', NULL, 83.4, 0, 68, '12', 'A query is used to extract data                   ', 1, '6');
INSERT INTO `work_items` VALUES (61, 'You must be the change you wish                   ', 'Secure SHell (SSH) is a program                   ', 'P3', 'Ⅰ', '低', '2026-11-08 02:30:41', NULL, 33.1, 0, 223, '23', 'The reason why a great man is great               ', 0, '23');
INSERT INTO `work_items` VALUES (62, 'Navicat Data Modeler enables you                  ', 'If your Internet Service Provider                 ', 'P3', 'Ⅱ', '无', '2027-12-01 15:03:29', NULL, 74.3, 0, 254, '5', 'It can also manage cloud databases                ', 0, '29');
INSERT INTO `work_items` VALUES (63, 'Instead of wondering when your                    ', 'The Synchronize to Database function              ', 'P4', 'Ⅳ', '中', '2027-04-21 16:21:26', NULL, 72, 0, 136, '18', 'A man’s best friends are his ten fingers.', 1, '25');
INSERT INTO `work_items` VALUES (64, 'If it scares you, it might be a good thing to try.', 'The Synchronize to Database function              ', 'P5', 'Ⅱ', '高', '2027-04-27 21:03:38', NULL, 20, 0, 262, '0000', 'I destroy my enemies when I make them my friends.', 1, '24');
INSERT INTO `work_items` VALUES (65, 'Champions keep playing until they get it right.', 'It is used while your ISPs do not                 ', 'P2', 'Ⅱ', '高', '2027-06-01 08:18:12', NULL, 69.5, 0, 71, '22', 'The Navigation pane employs tree                  ', 0, '15');
INSERT INTO `work_items` VALUES (66, 'If opportunity doesn’t knock, build a door.     ', 'With its well-designed Graphical                  ', 'P2', 'Ⅱ', '无', '2027-11-03 12:18:00', NULL, 26.3, 0, 171, '7', NULL, 0, '25');
INSERT INTO `work_items` VALUES (67, 'Navicat Monitor requires a repository             ', 'I destroy my enemies when I make them my friends.', 'P5', 'Ⅳ', '无', '2027-03-15 03:15:38', NULL, 24.3, 0, 87, '15', 'The past has no power over the present moment.', 1, '12');
INSERT INTO `work_items` VALUES (68, 'Secure Sockets Layer(SSL) is a                    ', 'SQL Editor allows you to create                   ', 'P2', 'Ⅲ', '无', '2027-07-04 05:00:38', NULL, 96.3, 0, 74, '12', 'You can select any connections,                   ', 1, '11');
INSERT INTO `work_items` VALUES (69, 'I destroy my enemies when I make them my friends.', 'Success consists of going from                    ', 'P7', 'Ⅰ', '无', '2027-05-14 02:02:08', NULL, 90.6, 0, 52, '17', 'With its well-designed Graphical                  ', 1, '8');
INSERT INTO `work_items` VALUES (70, 'Difficult circumstances serve as                  ', 'Optimism is the one quality more                  ', 'P6', 'Ⅲ', '高', '2027-07-17 14:21:32', NULL, 26.1, 0, 256, '3', 'You must be the change you wish                   ', 0, '15');
INSERT INTO `work_items` VALUES (71, 'You will succeed because most people are lazy.', 'Export Wizard allows you to export                ', 'P4', 'Ⅳ', '高', '2027-11-30 01:52:36', NULL, 56, 0, 117, '15', 'Actually it is just in an idea                    ', 1, '26');
INSERT INTO `work_items` VALUES (72, 'If your Internet Service Provider                 ', 'You must be the change you wish                   ', 'P8', 'Ⅱ', '无', '2027-12-11 14:07:43', NULL, 5.6, 0, 77, '0000', 'Export Wizard allows you to export                ', 0, '3');
INSERT INTO `work_items` VALUES (73, 'After comparing data, the window                  ', 'To clear or reload various internal               ', 'P4', 'Ⅱ', '中', '2027-09-19 21:47:06', NULL, 23, 0, 190, '8', 'If it scares you, it might be a good thing to try.', 1, '0012');
INSERT INTO `work_items` VALUES (74, 'Navicat Data Modeler enables you                  ', 'The Navigation pane employs tree                  ', 'P8', 'Ⅲ', '低', '2026-09-12 02:52:33', NULL, 80.9, 0, 123, '19', NULL, 1, '9');
INSERT INTO `work_items` VALUES (75, 'The first step is as good as half over.', 'With its well-designed Graphical                  ', 'P3', 'Ⅲ', '无', '2027-06-29 15:53:13', NULL, 61.4, 0, 61, '0000', NULL, 0, '8');
INSERT INTO `work_items` VALUES (76, 'The Main Window consists of several               ', 'The Information Pane shows the                    ', 'P5', 'Ⅲ', '无', '2027-07-15 21:32:35', NULL, 17.6, 0, 127, '4', 'To open a query using an external                 ', 1, '18');
INSERT INTO `work_items` VALUES (77, 'It is used while your ISPs do not                 ', 'If you wait, all that happens is you get older.', 'P8', 'Ⅱ', '无', '2027-01-12 23:09:00', NULL, 78.9, 0, 307, '30', 'If the plan doesn’t work, change                ', 1, '26');
INSERT INTO `work_items` VALUES (78, 'Optimism is the one quality more                  ', 'It collects process metrics such                  ', 'P6', 'Ⅲ', '高', '2027-07-16 11:16:38', NULL, 30.2, 0, 193, '7', 'Navicat provides powerful tools                   ', 1, '15');
INSERT INTO `work_items` VALUES (79, 'Navicat is a multi-connections                    ', 'Instead of wondering when your                    ', 'P2', 'Ⅰ', '低', '2027-05-01 14:18:08', NULL, 58.9, 0, 72, '14', NULL, 1, '16');
INSERT INTO `work_items` VALUES (80, 'There is no way to happiness. Happiness           ', 'Navicat Monitor is a safe, simple                 ', 'P4', 'Ⅳ', '低', '2026-12-08 17:30:23', NULL, 35, 0, 84, '13', 'All the Navicat Cloud objects are                 ', 1, '22');
INSERT INTO `work_items` VALUES (81, 'You can select any connections,                   ', 'The Synchronize to Database function              ', 'P4', 'Ⅲ', '无', '2027-06-22 03:25:17', NULL, 98.1, 0, 235, '21', NULL, 1, '26');
INSERT INTO `work_items` VALUES (82, 'A man is not old until regrets                    ', 'Optimism is the one quality more                  ', 'P6', 'Ⅳ', '中', '2027-10-08 14:54:35', NULL, 60.1, 0, 103, '11', NULL, 1, '0001');
INSERT INTO `work_items` VALUES (83, 'I destroy my enemies when I make them my friends.', 'Anyone who has never made a mistake               ', 'P8', 'Ⅳ', '低', '2027-01-17 14:22:37', NULL, 10.2, 0, 170, '30', 'Navicat provides a wide range advanced            ', 1, '29');
INSERT INTO `work_items` VALUES (84, 'The repository database can be                    ', 'If it scares you, it might be a good thing to try.', 'P5', 'Ⅲ', '高', '2026-10-28 08:32:04', NULL, 79.3, 0, 145, '12', 'To get a secure connection, the                   ', 1, '1');
INSERT INTO `work_items` VALUES (85, 'Flexible settings enable you to                   ', 'Navicat allows you to transfer                    ', 'P6', 'Ⅲ', '低', '2026-10-23 18:39:24', NULL, 64.8, 0, 123, '30', NULL, 1, '9');
INSERT INTO `work_items` VALUES (86, 'A man is not old until regrets                    ', 'There is no way to happiness. Happiness           ', 'P7', 'Ⅰ', '高', '2027-01-13 11:35:19', NULL, 53.8, 0, 224, '6', 'Navicat Monitor requires a repository             ', 1, '5');
INSERT INTO `work_items` VALUES (87, 'Monitored servers include MySQL,                  ', 'Import Wizard allows you to import                ', 'P6', 'Ⅲ', '无', '2027-03-07 18:01:08', NULL, 45.9, 0, 145, '15', 'It provides strong authentication                 ', 1, '1');
INSERT INTO `work_items` VALUES (88, 'Instead of wondering when your                    ', 'The past has no power over the present moment.', 'P6', 'Ⅱ', '低', '2026-12-28 11:54:08', NULL, 78, 0, 325, '0123', 'A comfort zone is a beautiful place,              ', 1, '30');
INSERT INTO `work_items` VALUES (89, 'Navicat Cloud could not connect                   ', 'To successfully establish a new                   ', 'P4', 'Ⅲ', '中', '2027-10-12 03:08:56', NULL, 96, 0, 107, '15', 'Optimism is the one quality more                  ', 0, '4');
INSERT INTO `work_items` VALUES (90, 'The Main Window consists of several               ', 'The Main Window consists of several               ', 'P8', 'Ⅰ', '低', '2027-06-27 06:55:31', NULL, 9.8, 0, 197, '22', NULL, 0, '4');
INSERT INTO `work_items` VALUES (91, 'Success consists of going from                    ', 'Anyone who has never made a mistake               ', 'P4', 'Ⅳ', '无', '2027-10-29 08:31:40', NULL, 15.6, 0, 138, '30', NULL, 1, '28');
INSERT INTO `work_items` VALUES (92, 'It is used while your ISPs do not                 ', 'Navicat Monitor requires a repository             ', 'P8', 'Ⅱ', '中', '2026-11-29 08:50:53', NULL, 7.7, 0, 264, '19', 'Navicat is a multi-connections                    ', 1, '12');
INSERT INTO `work_items` VALUES (93, 'It collects process metrics such                  ', 'You can select any connections,                   ', 'P7', 'Ⅳ', '中', '2027-06-28 02:51:01', NULL, 52.4, 0, 176, '24', 'If your Internet Service Provider                 ', 1, '20');
INSERT INTO `work_items` VALUES (94, 'I may not have gone where I intended              ', 'After comparing data, the window                  ', 'P3', 'Ⅰ', '中', '2027-09-26 07:45:10', NULL, 23.4, 0, 113, '14', 'If the plan doesn’t work, change                ', 1, '19');
INSERT INTO `work_items` VALUES (95, 'Secure Sockets Layer(SSL) is a                    ', 'Success consists of going from                    ', 'P2', 'Ⅳ', '无', '2026-10-25 10:04:23', NULL, 99.1, 0, 102, '6', 'The Information Pane shows the                    ', 0, '11');
INSERT INTO `work_items` VALUES (96, 'To start working with your server                 ', 'You will succeed because most people are lazy.', 'P5', 'Ⅰ', '低', '2027-12-14 05:34:00', NULL, 20.4, 0, 187, '21', 'Navicat authorizes you to make                    ', 0, '0000');
INSERT INTO `work_items` VALUES (97, 'If you wait, all that happens is you get older.', 'Creativity is intelligence having fun.', 'P8', 'Ⅰ', '中', '2027-03-25 03:26:59', NULL, 51.7, 0, 271, '11', NULL, 0, '30');
INSERT INTO `work_items` VALUES (98, 'To open a query using an external                 ', 'I destroy my enemies when I make them my friends.', 'P4', 'Ⅱ', '无', '2027-10-27 06:03:06', NULL, 95.6, 0, 276, '0000', NULL, 0, '26');
INSERT INTO `work_items` VALUES (99, 'The reason why a great man is great               ', 'All the Navicat Cloud objects are                 ', 'P3', 'Ⅱ', '中', '2027-08-07 10:41:22', NULL, 6.4, 0, 264, '9', 'A query is used to extract data                   ', 0, '12');
INSERT INTO `work_items` VALUES (100, 'HTTP Tunneling is a method for                    ', 'Secure SHell (SSH) is a program                   ', 'P2', 'Ⅳ', '高', '2027-09-19 14:07:10', NULL, 35.3, 0, 245, '1', NULL, 1, '6');
INSERT INTO `work_items` VALUES (101, 'Navicat allows you to transfer                    ', 'HTTP Tunneling is a method for                    ', 'P7', 'Ⅳ', '低', '2027-06-21 06:25:18', NULL, 62.9, 0, 62, '4', 'Navicat Cloud provides a cloud                    ', 0, '0123');
INSERT INTO `work_items` VALUES (102, 'Navicat Cloud could not connect                   ', 'Such sessions are also susceptible                ', 'P5', 'Ⅱ', '无', '2027-06-23 03:24:38', NULL, 55.8, 0, 216, '8', 'A man is not old until regrets                    ', 1, '30');
INSERT INTO `work_items` VALUES (103, 'A man’s best friends are his ten fingers.', 'If you wait, all that happens is you get older.', 'P2', 'Ⅱ', '高', '2027-10-18 13:33:11', NULL, 9.1, 0, 256, '25', NULL, 1, '15');
INSERT INTO `work_items` VALUES (104, 'You can select any connections,                   ', 'If the plan doesn’t work, change                ', 'P7', 'Ⅱ', '无', '2027-07-14 01:41:27', NULL, 85.5, 0, 65, '3', 'A comfort zone is a beautiful place,              ', 1, '26');
INSERT INTO `work_items` VALUES (105, 'If your Internet Service Provider                 ', 'How we spend our days is, of course,              ', 'P7', 'Ⅱ', '高', '2027-07-15 04:20:38', NULL, 15.3, 0, 241, '17', 'If your Internet Service Provider                 ', 0, '10');
INSERT INTO `work_items` VALUES (106, 'In a Telnet session, all communications,          ', 'A man’s best friends are his ten fingers.', 'P3', 'Ⅲ', '低', '2027-02-20 13:52:51', NULL, 72.5, 0, 220, '8', 'Monitored servers include MySQL,                  ', 1, '1');
INSERT INTO `work_items` VALUES (107, 'HTTP Tunneling is a method for                    ', 'Navicat 15 has added support for                  ', 'P3', 'Ⅲ', '无', '2027-11-14 09:58:29', NULL, 43.4, 0, 161, '0001', 'To successfully establish a new                   ', 1, '0000');
INSERT INTO `work_items` VALUES (108, 'Anyone who has never made a mistake               ', 'You must be the change you wish                   ', 'P3', 'Ⅲ', '高', '2027-06-30 15:18:03', NULL, 68.6, 0, 124, '12', 'Monitored servers include MySQL,                  ', 0, '29');
INSERT INTO `work_items` VALUES (109, 'The Main Window consists of several               ', 'The past has no power over the present moment.', 'P7', 'Ⅲ', '高', '2026-09-14 17:48:19', NULL, 50.8, 0, 276, '1', 'To get a secure connection, the                   ', 0, '26');
INSERT INTO `work_items` VALUES (110, 'SQL Editor allows you to create                   ', 'Navicat Data Modeler is a powerful                ', 'P7', 'Ⅳ', '低', '2026-10-09 12:56:53', NULL, 28.8, 0, 209, '22', 'To start working with your server                 ', 0, '20');
INSERT INTO `work_items` VALUES (111, 'It is used while your ISPs do not                 ', 'Typically, it is employed as an                   ', 'P6', 'Ⅳ', '无', '2026-12-22 03:05:53', NULL, 43.9, 0, 280, '24', 'The Synchronize to Database function              ', 1, '11');
INSERT INTO `work_items` VALUES (112, 'In a Telnet session, all communications,          ', 'Actually it is just in an idea                    ', 'P6', 'Ⅰ', '高', '2027-07-27 11:36:46', NULL, 45.8, 0, 94, '17', NULL, 1, '25');
INSERT INTO `work_items` VALUES (113, 'Optimism is the one quality more                  ', 'A query is used to extract data                   ', 'P2', 'Ⅱ', '中', '2027-02-04 17:14:03', NULL, 98.4, 0, 41, '27', NULL, 1, '21');
INSERT INTO `work_items` VALUES (114, 'In the middle of winter I at last                 ', 'Optimism is the one quality more                  ', 'P6', 'Ⅱ', '中', '2027-08-21 04:57:50', NULL, 65, 0, 219, '15', 'To successfully establish a new                   ', 1, '5');
INSERT INTO `work_items` VALUES (115, 'Champions keep playing until they get it right.', 'If you wait, all that happens is you get older.', 'P3', 'Ⅳ', '高', '2027-01-11 04:59:48', NULL, 21.7, 0, 171, '16', 'Navicat 15 has added support for                  ', 0, '25');
INSERT INTO `work_items` VALUES (116, 'Navicat Cloud could not connect                   ', 'The repository database can be                    ', 'P3', 'Ⅲ', '低', '2027-03-26 20:40:05', NULL, 54.2, 0, 296, '18', 'After logged in the Navicat Cloud                 ', 0, '29');
INSERT INTO `work_items` VALUES (117, 'I may not have gone where I intended              ', 'It can also manage cloud databases                ', 'P4', 'Ⅱ', '无', '2026-12-06 08:10:23', NULL, 25.1, 0, 170, '0000', 'A comfort zone is a beautiful place,              ', 0, '29');
INSERT INTO `work_items` VALUES (118, 'HTTP Tunneling is a method for                    ', 'Navicat Data Modeler enables you                  ', 'P8', 'Ⅳ', '高', '2027-01-28 16:41:05', NULL, 77.4, 0, 91, '28', 'To start working with your server                 ', 0, '11');
INSERT INTO `work_items` VALUES (119, 'To open a query using an external                 ', 'The Information Pane shows the                    ', 'P8', 'Ⅲ', '无', '2027-07-01 21:25:47', NULL, 60.4, 0, 191, '0000', NULL, 1, '8');
INSERT INTO `work_items` VALUES (120, 'HTTP Tunneling is a method for                    ', 'To open a query using an external                 ', 'P5', 'Ⅳ', '中', '2027-10-25 03:15:54', NULL, 65.4, 0, 97, '26', NULL, 1, '16');
INSERT INTO `work_items` VALUES (121, 'It wasn’t raining when Noah built the ark.      ', 'If you wait, all that happens is you get older.', 'P8', 'Ⅱ', '中', '2027-07-22 16:26:11', NULL, 74.2, 0, 58, '24', 'Navicat allows you to transfer                    ', 1, '0012');
INSERT INTO `work_items` VALUES (122, 'Secure Sockets Layer(SSL) is a                    ', 'To successfully establish a new                   ', 'P8', 'Ⅱ', '低', '2026-11-18 20:00:59', NULL, 13.7, 0, 227, '0012', 'Anyone who has never made a mistake               ', 1, '16');
INSERT INTO `work_items` VALUES (123, 'Optimism is the one quality more                  ', 'To successfully establish a new                   ', 'P3', 'Ⅱ', '无', '2027-08-02 13:40:58', NULL, 44.4, 0, 162, '0012', 'The On Startup feature allows you                 ', 1, '27');
INSERT INTO `work_items` VALUES (124, 'It collects process metrics such                  ', 'In the middle of winter I at last                 ', 'P7', 'Ⅰ', '高', '2027-10-21 18:47:03', NULL, 31.8, 0, 47, '4', 'It can also manage cloud databases                ', 0, '0001');
INSERT INTO `work_items` VALUES (125, 'To start working with your server                 ', 'Creativity is intelligence having fun.            ', 'P6', 'Ⅰ', '无', '2027-10-12 03:33:16', NULL, 66.6, 0, 45, '9', 'Navicat Data Modeler enables you                  ', 0, '0000');
INSERT INTO `work_items` VALUES (126, 'Navicat Data Modeler enables you                  ', 'Always keep your eyes open. Keep                  ', 'P8', 'Ⅳ', '高', '2026-11-14 09:42:23', NULL, 77.7, 0, 319, '0123', 'The Synchronize to Database function              ', 1, '4');
INSERT INTO `work_items` VALUES (127, 'Navicat Data Modeler is a powerful                ', 'Instead of wondering when your                    ', 'P2', 'Ⅰ', '低', '2026-09-11 23:28:10', NULL, 72.3, 0, 169, '27', NULL, 0, '11');
INSERT INTO `work_items` VALUES (128, 'Instead of wondering when your                    ', 'I destroy my enemies when I make them my friends.', 'P4', 'Ⅳ', '无', '2027-11-10 00:48:39', NULL, 91.6, 0, 222, '2', NULL, 0, '28');
INSERT INTO `work_items` VALUES (129, 'Navicat allows you to transfer                    ', 'To successfully establish a new                   ', 'P6', 'Ⅱ', '高', '2026-12-03 07:14:26', NULL, 60.7, 0, 237, '10', 'The Synchronize to Database function              ', 0, '19');
INSERT INTO `work_items` VALUES (130, 'Navicat provides a wide range advanced            ', 'Difficult circumstances serve as                  ', 'P8', 'Ⅱ', '中', '2027-07-16 00:17:01', NULL, 20.1, 0, 39, '12', 'It wasn’t raining when Noah built the ark.      ', 1, '23');
INSERT INTO `work_items` VALUES (131, 'Flexible settings enable you to                   ', 'If the plan doesn’t work, change                ', 'P8', 'Ⅲ', '高', '2027-09-28 00:26:15', NULL, 67.5, 0, 289, '4', NULL, 1, '10');
INSERT INTO `work_items` VALUES (132, 'Navicat provides a wide range advanced            ', 'You will succeed because most people are lazy.    ', 'P3', 'Ⅰ', '中', '2026-10-11 21:13:57', NULL, 50.8, 0, 37, '4', 'Champions keep playing until they get it right.', 0, '11');
INSERT INTO `work_items` VALUES (133, 'If the Show objects under schema                  ', 'Navicat authorizes you to make                    ', 'P7', 'Ⅲ', '中', '2026-10-18 06:43:28', NULL, 60.1, 0, 285, '28', 'You cannot save people, you can just love them.', 0, '11');
INSERT INTO `work_items` VALUES (134, 'In the Objects tab, you can use                   ', 'How we spend our days is, of course,              ', 'P7', 'Ⅰ', '高', '2027-11-07 06:25:53', NULL, 45, 0, 236, '21', 'A man is not old until regrets                    ', 1, '26');
INSERT INTO `work_items` VALUES (135, 'Navicat 15 has added support for                  ', 'Difficult circumstances serve as                  ', 'P6', 'Ⅲ', '高', '2027-10-25 14:16:44', NULL, 53.8, 0, 222, '2', 'After comparing data, the window                  ', 1, '28');
INSERT INTO `work_items` VALUES (136, 'After comparing data, the window                  ', 'It wasn’t raining when Noah built the ark.', 'P7', 'Ⅰ', '中', '2027-09-18 22:14:23', NULL, 76.8, 0, 288, '0012', 'You must be the change you wish                   ', 1, '30');
INSERT INTO `work_items` VALUES (137, 'It provides strong authentication                 ', 'A man’s best friends are his ten fingers.       ', 'P2', 'Ⅱ', '中', '2027-01-05 20:22:53', NULL, 31.1, 0, 105, '25', 'Difficult circumstances serve as                  ', 0, '17');
INSERT INTO `work_items` VALUES (138, 'If you wait, all that happens is you get older.', 'Import Wizard allows you to import                ', 'P4', 'Ⅲ', '低', '2027-05-07 05:38:50', NULL, 90, 0, 226, '0012', 'The Navigation pane employs tree                  ', 1, '27');
INSERT INTO `work_items` VALUES (139, 'The past has no power over the present moment.    ', 'Navicat Monitor is a safe, simple                 ', 'P7', 'Ⅳ', '中', '2027-02-15 01:28:03', NULL, 44.4, 0, 30, '2', NULL, 1, '9');
INSERT INTO `work_items` VALUES (140, 'It is used while your ISPs do not                 ', 'The Navigation pane employs tree                  ', 'P7', 'Ⅲ', '高', '2026-11-10 02:36:35', NULL, 74.9, 0, 160, '17', 'Navicat Cloud provides a cloud                    ', 0, '4');
INSERT INTO `work_items` VALUES (141, 'In the Objects tab, you can use                   ', 'It is used while your ISPs do not                 ', 'P4', 'Ⅱ', '中', '2027-04-01 00:24:13', NULL, 77.6, 0, 186, '25', 'Genius is an infinite capacity for taking pains.', 1, '0000');
INSERT INTO `work_items` VALUES (142, 'If the plan doesn’t work, change                ', 'How we spend our days is, of course,              ', 'P4', 'Ⅳ', '高', '2026-09-27 01:31:02', NULL, 74.5, 0, 137, '10', NULL, 0, '15');
INSERT INTO `work_items` VALUES (143, 'Difficult circumstances serve as                  ', 'There is no way to happiness. Happiness           ', 'P4', 'Ⅰ', '中', '2027-09-16 00:59:37', NULL, 35, 0, 33, '16', 'The Navigation pane employs tree                  ', 1, '14');
INSERT INTO `work_items` VALUES (144, 'It wasn’t raining when Noah built the ark.', 'Navicat provides powerful tools                   ', 'P5', 'Ⅲ', '中', '2026-11-08 06:14:52', NULL, 11.1, 0, 73, '12', NULL, 1, '13');
INSERT INTO `work_items` VALUES (145, 'Navicat Data Modeler is a powerful                ', 'Export Wizard allows you to export                ', 'P3', 'Ⅳ', '高', '2027-03-17 14:47:08', NULL, 1.4, 0, 111, '3', 'In a Telnet session, all communications,          ', 1, '7');
INSERT INTO `work_items` VALUES (146, 'The past has no power over the present moment.', 'The Main Window consists of several               ', 'P4', 'Ⅲ', '中', '2027-06-13 19:37:05', NULL, 13.2, 0, 227, '18', NULL, 0, '16');
INSERT INTO `work_items` VALUES (147, 'You can select any connections,                   ', 'It is used while your ISPs do not                 ', 'P7', 'Ⅰ', '高', '2027-03-26 14:40:09', NULL, 34.9, 0, 218, '2', 'To get a secure connection, the                   ', 1, '30');
INSERT INTO `work_items` VALUES (148, 'You can select any connections,                   ', 'To connect to a database or schema,               ', 'P2', 'Ⅰ', '无', '2027-11-10 22:03:47', NULL, 97.4, 0, 109, '5', NULL, 1, '1');
INSERT INTO `work_items` VALUES (149, 'Navicat Monitor requires a repository             ', 'Navicat Monitor can be installed                  ', 'P4', 'Ⅱ', '低', '2027-06-22 12:39:02', NULL, 80.8, 0, 76, '30', NULL, 1, '28');
INSERT INTO `work_items` VALUES (150, 'In a Telnet session, all communications,          ', 'I may not have gone where I intended              ', 'P4', 'Ⅰ', '无', '2027-04-21 07:08:00', NULL, 60.4, 0, 54, '6', NULL, 0, '0012');
INSERT INTO `work_items` VALUES (151, 'Champions keep playing until they get it right.', 'Anyone who has never made a mistake               ', 'P6', 'Ⅳ', '无', '2027-02-09 10:44:21', NULL, 29.3, 0, 122, '8', NULL, 1, '23');
INSERT INTO `work_items` VALUES (152, 'All journeys have secret destinations             ', 'A comfort zone is a beautiful place,              ', 'P6', 'Ⅰ', '低', '2026-11-24 09:57:47', NULL, 25.5, 0, 53, '12', 'SSH serves to prevent such vulnerabilities        ', 0, '4');
INSERT INTO `work_items` VALUES (153, 'Optimism is the one quality more                  ', 'You cannot save people, you can just love them.', 'P3', 'Ⅲ', '无', '2027-01-20 19:25:04', NULL, 7.6, 0, 221, '5', 'Navicat Monitor is a safe, simple                 ', 1, '25');
INSERT INTO `work_items` VALUES (154, 'Navicat authorizes you to make                    ', 'A man’s best friends are his ten fingers.', 'P3', 'Ⅱ', '无', '2027-07-17 07:28:18', NULL, 6.2, 0, 133, '16', 'Instead of wondering when your                    ', 0, '22');
INSERT INTO `work_items` VALUES (155, 'Flexible settings enable you to                   ', 'To open a query using an external                 ', 'P4', 'Ⅱ', '高', '2026-11-14 21:48:44', NULL, 82.7, 0, 260, '0123', 'Monitored servers include MySQL,                  ', 0, '9');
INSERT INTO `work_items` VALUES (156, 'Optimism is the one quality more                  ', 'The On Startup feature allows you                 ', 'P5', 'Ⅱ', '高', '2027-11-24 06:52:48', NULL, 81.5, 0, 298, '29', 'To connect to a database or schema,               ', 1, '28');
INSERT INTO `work_items` VALUES (157, 'All journeys have secret destinations             ', 'You will succeed because most people are lazy.', 'P2', 'Ⅱ', '无', '2027-08-13 16:59:22', NULL, 94.7, 0, 285, '0012', 'To connect to a database or schema,               ', 0, '11');
INSERT INTO `work_items` VALUES (158, 'If you wait, all that happens is you get older.', 'Navicat Cloud could not connect                   ', 'P4', 'Ⅲ', '中', '2027-07-05 18:55:52', NULL, 71.1, 0, 323, '28', 'HTTP Tunneling is a method for                    ', 1, '0123');
INSERT INTO `work_items` VALUES (159, 'In other words, Navicat provides                  ', 'If your Internet Service Provider                 ', 'P7', 'Ⅲ', '低', '2026-09-14 06:49:50', NULL, 26.2, 0, 245, '29', NULL, 0, '6');
INSERT INTO `work_items` VALUES (160, 'Navicat Data Modeler is a powerful                ', 'It is used while your ISPs do not                 ', 'P3', 'Ⅳ', '中', '2027-03-22 18:55:34', NULL, 22.1, 0, 86, '0123', 'If it scares you, it might be a good thing to try.', 0, '0000');
INSERT INTO `work_items` VALUES (161, 'It can also manage cloud databases                ', 'All the Navicat Cloud objects are                 ', 'P3', 'Ⅳ', '中', '2026-11-03 15:51:35', NULL, 47.7, 0, 80, '10', 'It can also manage cloud databases                ', 1, '22');
INSERT INTO `work_items` VALUES (162, 'It wasn’t raining when Noah built the ark.', 'To open a query using an external                 ', 'P4', 'Ⅰ', '高', '2027-08-02 12:17:42', NULL, 69.2, 0, 74, '9', NULL, 0, '11');
INSERT INTO `work_items` VALUES (163, 'Remember that failure is an event, not a person.', 'Navicat allows you to transfer                    ', 'P4', 'Ⅱ', '无', '2027-09-30 09:28:32', NULL, 96.7, 0, 172, '5', 'It wasn’t raining when Noah built the ark.', 1, '28');
INSERT INTO `work_items` VALUES (164, 'Anyone who has ever made anything                 ', 'Secure Sockets Layer(SSL) is a                    ', 'P6', 'Ⅲ', '高', '2027-07-05 04:22:49', NULL, 14.3, 0, 258, '0123', NULL, 1, '7');
INSERT INTO `work_items` VALUES (165, 'You can select any connections,                   ', 'The first step is as good as half over.', 'P4', 'Ⅱ', '无', '2027-01-29 12:34:08', NULL, 20.8, 0, 324, '23', 'To connect to a database or schema,               ', 0, '18');
INSERT INTO `work_items` VALUES (166, 'Monitored servers include MySQL,                  ', 'It wasn’t raining when Noah built the ark.      ', 'P3', 'Ⅲ', '高', '2027-02-27 11:51:21', NULL, 70.1, 0, 45, '30', 'To open a query using an external                 ', 0, '0000');
INSERT INTO `work_items` VALUES (167, 'There is no way to happiness. Happiness           ', 'To get a secure connection, the                   ', 'P6', 'Ⅳ', '无', '2026-10-29 05:42:55', NULL, 41.1, 0, 177, '24', 'Secure Sockets Layer(SSL) is a                    ', 0, '15');
INSERT INTO `work_items` VALUES (168, 'Navicat 15 has added support for                  ', 'Secure SHell (SSH) is a program                   ', 'P8', 'Ⅰ', '低', '2026-12-05 00:52:07', NULL, 88.7, 0, 236, '5', 'With its well-designed Graphical                  ', 0, '26');
INSERT INTO `work_items` VALUES (169, 'Navicat 15 has added support for                  ', 'Secure Sockets Layer(SSL) is a                    ', 'P3', 'Ⅰ', '中', '2027-04-26 16:19:46', NULL, 74.2, 0, 249, '28', 'You cannot save people, you can just love them.', 0, '18');
INSERT INTO `work_items` VALUES (170, 'All journeys have secret destinations             ', 'The first step is as good as half over.           ', 'P6', 'Ⅳ', '高', '2027-06-04 10:40:24', NULL, 29.8, 0, 61, '9', 'In the middle of winter I at last                 ', 1, '8');
INSERT INTO `work_items` VALUES (171, 'Optimism is the one quality more                  ', 'Import Wizard allows you to import                ', 'P2', 'Ⅱ', '高', '2027-06-25 15:30:13', NULL, 68.7, 0, 91, '7', 'Always keep your eyes open. Keep                  ', 1, '11');
INSERT INTO `work_items` VALUES (172, 'Genius is an infinite capacity for taking pains.', 'If your Internet Service Provider                 ', 'P3', 'Ⅱ', '无', '2026-11-26 23:58:54', NULL, 18.7, 0, 37, '15', 'Monitored servers include MySQL,                  ', 0, '11');
INSERT INTO `work_items` VALUES (173, 'It can also manage cloud databases                ', 'In the Objects tab, you can use                   ', 'P5', 'Ⅱ', '低', '2026-12-11 20:43:57', NULL, 62.2, 0, 294, '10', 'Monitored servers include MySQL,                  ', 0, '15');
INSERT INTO `work_items` VALUES (174, 'SSH serves to prevent such vulnerabilities        ', 'Navicat is a multi-connections                    ', 'P4', 'Ⅱ', '中', '2027-11-07 15:36:34', NULL, 75.4, 0, 202, '26', NULL, 0, '5');
INSERT INTO `work_items` VALUES (175, 'If your Internet Service Provider                 ', 'With its well-designed Graphical                  ', 'P2', 'Ⅲ', '中', '2027-10-12 13:31:23', NULL, 44.3, 0, 101, '7', NULL, 0, '22');
INSERT INTO `work_items` VALUES (176, 'The Synchronize to Database function              ', 'In the middle of winter I at last                 ', 'P4', 'Ⅲ', '低', '2027-08-01 17:44:10', NULL, 25.1, 0, 53, '18', NULL, 0, '4');
INSERT INTO `work_items` VALUES (177, 'How we spend our days is, of course,              ', 'The first step is as good as half over.', 'P5', 'Ⅳ', '中', '2026-10-03 10:31:48', NULL, 43.4, 0, 184, '29', 'Import Wizard allows you to import                ', 1, '26');
INSERT INTO `work_items` VALUES (178, 'Import Wizard allows you to import                ', 'In the Objects tab, you can use                   ', 'P5', 'Ⅰ', '中', '2027-12-17 04:10:55', NULL, 10.5, 0, 315, '27', 'Flexible settings enable you to                   ', 0, '5');
INSERT INTO `work_items` VALUES (179, 'In the Objects tab, you can use                   ', 'Such sessions are also susceptible                ', 'P7', 'Ⅰ', '低', '2027-09-04 09:41:02', NULL, 43.9, 0, 50, '4', 'Instead of wondering when your                    ', 1, '18');
INSERT INTO `work_items` VALUES (180, 'What you get by achieving your                    ', 'Secure SHell (SSH) is a program                   ', 'P4', 'Ⅳ', '低', '2027-05-10 14:38:02', NULL, 1.6, 0, 126, '23', NULL, 0, '6');
INSERT INTO `work_items` VALUES (181, 'Navicat is a multi-connections                    ', 'Navicat Cloud provides a cloud                    ', 'P2', 'Ⅲ', '无', '2027-12-13 16:56:18', NULL, 29.5, 0, 202, '18', 'You must be the change you wish                   ', 0, '5');
INSERT INTO `work_items` VALUES (182, 'Difficult circumstances serve as                  ', 'In the middle of winter I at last                 ', 'P8', 'Ⅳ', '无', '2027-02-08 09:58:54', NULL, 8.2, 0, 178, '4', 'A comfort zone is a beautiful place,              ', 1, '29');
INSERT INTO `work_items` VALUES (183, 'Navicat Data Modeler enables you                  ', 'If opportunity doesn’t knock, build a door.', 'P7', 'Ⅱ', '低', '2027-01-10 00:39:04', NULL, 28.8, 0, 49, '24', NULL, 1, '0012');
INSERT INTO `work_items` VALUES (184, 'All the Navicat Cloud objects are                 ', 'Typically, it is employed as an                   ', 'P7', 'Ⅱ', '中', '2026-12-05 03:04:34', NULL, 15.5, 0, 127, '13', NULL, 1, '18');
INSERT INTO `work_items` VALUES (185, 'SSH serves to prevent such vulnerabilities        ', 'SSH serves to prevent such vulnerabilities        ', 'P8', 'Ⅳ', '高', '2027-10-30 12:29:04', NULL, 4.2, 0, 149, '30', 'Typically, it is employed as an                   ', 0, '0012');
INSERT INTO `work_items` VALUES (186, 'After comparing data, the window                  ', 'The On Startup feature allows you                 ', 'P5', 'Ⅰ', '低', '2027-02-08 07:28:59', NULL, 7.2, 0, 122, '1', NULL, 1, '23');
INSERT INTO `work_items` VALUES (187, 'Instead of wondering when your                    ', 'Navicat allows you to transfer                    ', 'P5', 'Ⅲ', '低', '2027-04-10 12:24:33', NULL, 65.3, 0, 109, '6', NULL, 0, '1');
INSERT INTO `work_items` VALUES (188, 'Creativity is intelligence having fun.', 'After logged in the Navicat Cloud                 ', 'P7', 'Ⅳ', '低', '2026-10-09 16:36:54', NULL, 97, 0, 29, '12', NULL, 0, '1');
INSERT INTO `work_items` VALUES (189, 'Flexible settings enable you to                   ', 'A comfort zone is a beautiful place,              ', 'P6', 'Ⅱ', '高', '2027-03-08 08:48:12', NULL, 0.9, 0, 253, '24', 'The Navigation pane employs tree                  ', 0, '14');
INSERT INTO `work_items` VALUES (190, 'Import Wizard allows you to import                ', 'Optimism is the one quality more                  ', 'P3', 'Ⅲ', '低', '2026-12-08 23:49:21', NULL, 49.7, 0, 228, '23', 'Anyone who has ever made anything                 ', 0, '16');
INSERT INTO `work_items` VALUES (191, 'I will greet this day with love in my heart.', 'To connect to a database or schema,               ', 'P8', 'Ⅱ', '无', '2027-10-31 00:31:27', NULL, 96.1, 0, 53, '5', 'The past has no power over the present moment.', 1, '4');
INSERT INTO `work_items` VALUES (192, 'To get a secure connection, the                   ', 'How we spend our days is, of course,              ', 'P5', 'Ⅱ', '中', '2027-04-02 03:20:06', NULL, 26.4, 0, 230, '22', 'The first step is as good as half over.', 0, '22');
INSERT INTO `work_items` VALUES (193, 'I destroy my enemies when I make them my friends.', 'Export Wizard allows you to export                ', 'P2', 'Ⅲ', '低', '2027-03-17 07:43:48', NULL, 42.9, 0, 67, '0000', 'Navicat is a multi-connections                    ', 1, '0000');
INSERT INTO `work_items` VALUES (194, 'Champions keep playing until they get it right.', 'It wasn’t raining when Noah built the ark.', 'P5', 'Ⅱ', '低', '2027-01-12 18:06:14', NULL, 26.8, 0, 304, '17', NULL, 1, '30');
INSERT INTO `work_items` VALUES (195, 'A comfort zone is a beautiful place,              ', 'Such sessions are also susceptible                ', 'P6', 'Ⅱ', '中', '2027-01-25 20:24:19', NULL, 47.9, 0, 224, '18', 'Flexible settings enable you to                   ', 0, '5');
INSERT INTO `work_items` VALUES (196, 'If opportunity doesn’t knock, build a door.', 'A comfort zone is a beautiful place,              ', 'P8', 'Ⅳ', '中', '2027-12-23 04:17:35', NULL, 10.3, 0, 109, '3', 'Navicat authorizes you to make                    ', 0, '1');
INSERT INTO `work_items` VALUES (197, 'To successfully establish a new                   ', 'In the middle of winter I at last                 ', 'P2', 'Ⅳ', '低', '2026-10-13 14:38:29', NULL, 24.1, 0, 74, '3', NULL, 0, '11');
INSERT INTO `work_items` VALUES (198, 'You cannot save people, you can just love them.', 'If the Show objects under schema                  ', 'P2', 'Ⅰ', '中', '2027-04-08 04:56:20', NULL, 85.5, 0, 274, '25', 'Navicat 15 has added support for                  ', 1, '29');
INSERT INTO `work_items` VALUES (199, 'If your Internet Service Provider                 ', 'The Navigation pane employs tree                  ', 'P8', 'Ⅱ', '低', '2026-12-09 06:37:40', NULL, 80.6, 0, 40, '5', NULL, 0, '29');
INSERT INTO `work_items` VALUES (200, 'The past has no power over the present moment.', 'It provides strong authentication                 ', 'P3', 'Ⅲ', '高', '2027-09-14 07:46:47', NULL, 52.1, 0, 116, '6', 'In the Objects tab, you can use                   ', 0, '10');
INSERT INTO `work_items` VALUES (201, 'Navicat Monitor is a safe, simple                 ', 'SQL Editor allows you to create                   ', 'P2', 'Ⅰ', '中', '2027-06-28 12:07:02', NULL, 21.8, 0, 160, '2', 'You must be the change you wish                   ', 0, '4');
INSERT INTO `work_items` VALUES (202, 'Import Wizard allows you to import                ', 'The On Startup feature allows you                 ', 'P5', 'Ⅲ', '低', '2026-11-28 20:18:36', NULL, 28.1, 0, 43, '9', 'Optimism is the one quality more                  ', 0, '3');
INSERT INTO `work_items` VALUES (203, 'To open a query using an external                 ', 'A man is not old until regrets                    ', 'P4', 'Ⅰ', '中', '2026-12-02 10:08:34', NULL, 52.4, 0, 241, '8', NULL, 1, '10');
INSERT INTO `work_items` VALUES (204, 'SSH serves to prevent such vulnerabilities        ', 'To start working with your server                 ', 'P6', 'Ⅳ', '无', '2027-10-30 07:31:38', NULL, 26.5, 0, 82, '26', 'Flexible settings enable you to                   ', 1, '16');
INSERT INTO `work_items` VALUES (205, 'In a Telnet session, all communications,          ', 'In a Telnet session, all communications,          ', 'P3', 'Ⅰ', '无', '2027-01-27 16:22:17', NULL, 7.8, 0, 179, '4', 'Difficult circumstances serve as                  ', 0, '18');
INSERT INTO `work_items` VALUES (206, 'In the Objects tab, you can use                   ', 'How we spend our days is, of course,              ', 'P8', 'Ⅱ', '高', '2027-05-07 16:58:00', NULL, 54.4, 0, 211, '14', 'If the Show objects under schema                  ', 1, '18');
INSERT INTO `work_items` VALUES (207, 'It collects process metrics such                  ', 'Monitored servers include MySQL,                  ', 'P4', 'Ⅲ', '低', '2027-08-03 10:58:38', NULL, 42.6, 0, 233, '0012', 'Navicat Monitor is a safe, simple                 ', 1, '10');
INSERT INTO `work_items` VALUES (208, 'The Synchronize to Database function              ', 'Instead of wondering when your                    ', 'P3', 'Ⅳ', '无', '2027-03-15 13:25:32', NULL, 32.6, 0, 175, '23', 'Navicat Data Modeler enables you                  ', 0, '23');
INSERT INTO `work_items` VALUES (209, 'Secure SHell (SSH) is a program                   ', 'After comparing data, the window                  ', 'P4', 'Ⅳ', '无', '2027-01-14 08:14:08', NULL, 15.4, 0, 132, '3', NULL, 1, '11');
INSERT INTO `work_items` VALUES (210, 'SSH serves to prevent such vulnerabilities        ', 'Always keep your eyes open. Keep                  ', 'P8', 'Ⅱ', '高', '2026-11-26 07:03:06', NULL, 53.3, 0, 84, '11', 'Always keep your eyes open. Keep                  ', 1, '22');
INSERT INTO `work_items` VALUES (211, 'To successfully establish a new                   ', 'Champions keep playing until they get it right.', 'P2', 'Ⅰ', '高', '2027-03-20 16:33:33', NULL, 45, 0, 279, '0123', 'Navicat provides powerful tools                   ', 1, '18');
INSERT INTO `work_items` VALUES (212, 'Navicat provides powerful tools                   ', 'If you wait, all that happens is you get older.', 'P5', 'Ⅱ', '低', '2027-07-20 20:10:29', NULL, 93, 0, 57, '25', NULL, 0, '2');
INSERT INTO `work_items` VALUES (213, 'Genius is an infinite capacity for taking pains.', 'What you get by achieving your                    ', 'P8', 'Ⅲ', '低', '2027-12-30 10:26:48', NULL, 73.2, 0, 133, '6', NULL, 1, '22');
INSERT INTO `work_items` VALUES (214, 'Actually it is just in an idea                    ', 'If your Internet Service Provider                 ', 'P5', 'Ⅲ', '低', '2027-12-17 13:58:46', NULL, 21, 0, 36, '26', NULL, 1, '19');
INSERT INTO `work_items` VALUES (215, 'With its well-designed Graphical                  ', 'A comfort zone is a beautiful place,              ', 'P6', 'Ⅱ', '中', '2027-08-11 11:52:39', NULL, 64.5, 0, 87, '25', NULL, 1, '12');
INSERT INTO `work_items` VALUES (216, 'If it scares you, it might be a good thing to try.', 'You can select any connections,                   ', 'P5', 'Ⅰ', '高', '2027-09-30 10:49:11', NULL, 95, 0, 224, '15', NULL, 1, '5');
INSERT INTO `work_items` VALUES (217, 'Actually it is just in an idea                    ', 'In a Telnet session, all communications,          ', 'P6', 'Ⅳ', '中', '2027-05-14 03:17:19', NULL, 45.8, 0, 84, '26', 'The Information Pane shows the                    ', 1, '22');
INSERT INTO `work_items` VALUES (218, 'Import Wizard allows you to import                ', 'Sometimes you win, sometimes you learn.', 'P2', 'Ⅱ', '无', '2027-12-30 12:06:39', NULL, 21.5, 0, 245, '30', 'HTTP Tunneling is a method for                    ', 0, '6');
INSERT INTO `work_items` VALUES (219, 'To connect to a database or schema,               ', 'Navicat Monitor requires a repository             ', 'P2', 'Ⅳ', '高', '2027-01-04 13:17:40', NULL, 10.8, 0, 224, '18', NULL, 0, '5');
INSERT INTO `work_items` VALUES (220, 'I may not have gone where I intended              ', 'Typically, it is employed as an                   ', 'P8', 'Ⅲ', '低', '2027-12-15 17:02:18', NULL, 9.1, 0, 184, '26', NULL, 1, '26');
INSERT INTO `work_items` VALUES (221, 'Genius is an infinite capacity for taking pains.', 'Navicat allows you to transfer                    ', 'P8', 'Ⅰ', '无', '2027-04-19 12:46:43', NULL, 73.6, 0, 224, '1', 'Anyone who has never made a mistake               ', 1, '5');
INSERT INTO `work_items` VALUES (222, 'Navicat Monitor requires a repository             ', 'In other words, Navicat provides                  ', 'P3', 'Ⅳ', '低', '2027-01-10 03:21:29', NULL, 54, 0, 176, '16', 'A comfort zone is a beautiful place,              ', 1, '20');
INSERT INTO `work_items` VALUES (223, 'The Information Pane shows the                    ', 'Navicat provides powerful tools                   ', 'P6', 'Ⅰ', '高', '2027-09-27 16:39:08', NULL, 10.2, 0, 91, '22', 'To successfully establish a new                   ', 0, '11');
INSERT INTO `work_items` VALUES (224, 'I may not have gone where I intended              ', 'You will succeed because most people are lazy.', 'P8', 'Ⅰ', '中', '2027-03-10 11:28:30', NULL, 54.2, 0, 314, '5', NULL, 0, '7');
INSERT INTO `work_items` VALUES (225, 'SSH serves to prevent such vulnerabilities        ', 'You must be the change you wish                   ', 'P3', 'Ⅰ', '低', '2027-11-03 04:07:27', NULL, 4.8, 0, 104, '0012', NULL, 0, '8');
INSERT INTO `work_items` VALUES (226, 'Genius is an infinite capacity for taking pains.', 'If you wait, all that happens is you get older.', 'P6', 'Ⅲ', '中', '2027-02-28 21:18:42', NULL, 67.4, 0, 155, '24', 'If your Internet Service Provider                 ', 0, '15');
INSERT INTO `work_items` VALUES (227, 'Navicat provides powerful tools                   ', 'Navicat provides a wide range advanced            ', 'P3', 'Ⅲ', '高', '2027-07-20 18:19:25', NULL, 37.9, 0, 310, '23', 'Such sessions are also susceptible                ', 1, '3');
INSERT INTO `work_items` VALUES (228, 'Instead of wondering when your                    ', 'If you wait, all that happens is you get older.', 'P3', 'Ⅲ', '低', '2027-04-28 19:54:05', NULL, 73.1, 0, 248, '9', NULL, 0, '27');
INSERT INTO `work_items` VALUES (229, 'The past has no power over the present moment.', 'Export Wizard allows you to export                ', 'P3', 'Ⅰ', '中', '2027-10-20 08:35:17', NULL, 25.4, 0, 79, '0123', NULL, 0, '12');
INSERT INTO `work_items` VALUES (230, 'You must be the change you wish                   ', 'The reason why a great man is great               ', 'P5', 'Ⅳ', '高', '2027-10-16 18:13:48', NULL, 44.8, 0, 122, '11', NULL, 0, '23');
INSERT INTO `work_items` VALUES (231, 'To successfully establish a new                   ', 'Creativity is intelligence having fun.', 'P8', 'Ⅲ', '低', '2027-09-20 03:06:45', NULL, 16.3, 0, 270, '21', 'Success consists of going from                    ', 1, '3');
INSERT INTO `work_items` VALUES (232, 'Secure SHell (SSH) is a program                   ', 'SQL Editor allows you to create                   ', 'P6', 'Ⅰ', '高', '2026-09-13 12:34:07', NULL, 50, 0, 60, '7', NULL, 0, '0012');
INSERT INTO `work_items` VALUES (233, 'The reason why a great man is great               ', 'Navicat 15 has added support for                  ', 'P7', 'Ⅱ', '中', '2027-03-28 17:05:56', NULL, 63.4, 0, 215, '18', 'How we spend our days is, of course,              ', 0, '22');
INSERT INTO `work_items` VALUES (234, 'It is used while your ISPs do not                 ', 'After logged in the Navicat Cloud                 ', 'P3', 'Ⅱ', '中', '2027-03-20 11:48:21', NULL, 97.5, 0, 271, '8', NULL, 1, '30');
INSERT INTO `work_items` VALUES (235, 'To clear or reload various internal               ', 'The Navigation pane employs tree                  ', 'P3', 'Ⅱ', '高', '2027-08-10 22:26:37', NULL, 19.8, 0, 316, '14', 'You will succeed because most people are lazy.', 1, '13');
INSERT INTO `work_items` VALUES (236, 'Navicat authorizes you to make                    ', 'Navicat allows you to transfer                    ', 'P2', 'Ⅳ', '无', '2027-07-11 09:42:55', NULL, 55.7, 0, 198, '27', NULL, 1, '20');
INSERT INTO `work_items` VALUES (237, 'Navicat Monitor can be installed                  ', 'The first step is as good as half over.', 'P7', 'Ⅱ', '高', '2027-02-16 19:34:19', NULL, 78.3, 0, 108, '13', 'Navicat Monitor requires a repository             ', 0, '23');
INSERT INTO `work_items` VALUES (238, 'Navicat provides powerful tools                   ', 'Actually it is just in an idea                    ', 'P3', 'Ⅰ', '中', '2027-11-08 03:16:48', NULL, 72.1, 0, 292, '15', 'A man’s best friends are his ten fingers.', 0, '5');
INSERT INTO `work_items` VALUES (239, 'To connect to a database or schema,               ', 'All the Navicat Cloud objects are                 ', 'P4', 'Ⅲ', '高', '2027-09-23 02:54:32', NULL, 77.3, 0, 101, '15', NULL, 0, '22');
INSERT INTO `work_items` VALUES (240, 'To successfully establish a new                   ', 'Monitored servers include MySQL,                  ', 'P3', 'Ⅳ', '无', '2027-11-07 00:17:22', NULL, 56.7, 0, 181, '21', NULL, 1, '17');
INSERT INTO `work_items` VALUES (241, 'Optimism is the one quality more                  ', 'It can also manage cloud databases                ', 'P8', 'Ⅱ', '高', '2026-11-24 17:36:39', NULL, 58.6, 0, 31, '0000', 'The past has no power over the present moment.', 1, '30');
INSERT INTO `work_items` VALUES (242, 'Import Wizard allows you to import                ', 'If it scares you, it might be a good thing to try.', 'P5', 'Ⅱ', '高', '2027-06-27 07:43:32', NULL, 82, 0, 80, '26', 'Difficult circumstances serve as                  ', 0, '22');
INSERT INTO `work_items` VALUES (243, 'You cannot save people, you can just love them.', 'If the plan doesn’t work, change                ', 'P2', 'Ⅲ', '高', '2027-09-27 23:25:44', NULL, 28.3, 0, 210, '28', 'I may not have gone where I intended              ', 0, '17');
INSERT INTO `work_items` VALUES (244, 'After logged in the Navicat Cloud                 ', 'Such sessions are also susceptible                ', 'P8', 'Ⅳ', '无', '2027-03-12 13:32:48', NULL, 17.3, 0, 44, '11', 'Secure Sockets Layer(SSL) is a                    ', 1, '23');
INSERT INTO `work_items` VALUES (245, 'There is no way to happiness. Happiness           ', 'Optimism is the one quality more                  ', 'P8', 'Ⅳ', '中', '2026-11-23 09:36:04', NULL, 4.5, 0, 136, '12', 'The Information Pane shows the                    ', 1, '25');
INSERT INTO `work_items` VALUES (246, 'If the plan doesn’t work, change                ', 'It can also manage cloud databases                ', 'P3', 'Ⅰ', '无', '2027-12-23 12:06:31', NULL, 39.1, 0, 82, '7', 'The first step is as good as half over.           ', 0, '16');
INSERT INTO `work_items` VALUES (247, 'Typically, it is employed as an                   ', 'The Synchronize to Database function              ', 'P4', 'Ⅲ', '低', '2027-03-09 06:05:57', NULL, 24.1, 0, 207, '9', 'Navicat is a multi-connections                    ', 1, '0001');
INSERT INTO `work_items` VALUES (248, 'I destroy my enemies when I make them my friends.', 'The On Startup feature allows you                 ', 'P6', 'Ⅰ', '低', '2027-04-30 17:07:42', NULL, 90.3, 0, 293, '18', 'Remember that failure is an event, not a person.', 1, '24');
INSERT INTO `work_items` VALUES (249, 'Secure SHell (SSH) is a program                   ', 'You will succeed because most people are lazy.', 'P5', 'Ⅳ', '高', '2027-08-05 23:04:50', NULL, 69.8, 0, 98, '12', NULL, 0, '9');
INSERT INTO `work_items` VALUES (250, 'A man’s best friends are his ten fingers.       ', 'Typically, it is employed as an                   ', 'P6', 'Ⅰ', '中', '2026-10-16 12:49:48', NULL, 34.3, 0, 318, '14', NULL, 0, '17');
INSERT INTO `work_items` VALUES (251, 'Instead of wondering when your                    ', 'Genius is an infinite capacity for taking pains.', 'P4', 'Ⅳ', '高', '2026-10-21 16:47:24', NULL, 87.9, 0, 57, '9', NULL, 1, '2');
INSERT INTO `work_items` VALUES (252, 'In other words, Navicat provides                  ', 'Navicat Data Modeler enables you                  ', 'P3', 'Ⅱ', '无', '2026-09-12 10:25:51', NULL, 32.2, 0, 318, '6', 'I may not have gone where I intended              ', 0, '17');
INSERT INTO `work_items` VALUES (253, 'In other words, Navicat provides                  ', 'The reason why a great man is great               ', 'P8', 'Ⅲ', '中', '2027-10-27 18:49:50', NULL, 90, 0, 242, '17', 'HTTP Tunneling is a method for                    ', 0, '0012');
INSERT INTO `work_items` VALUES (254, 'Navicat provides powerful tools                   ', 'To clear or reload various internal               ', 'P6', 'Ⅰ', '高', '2027-08-09 03:10:01', NULL, 41.6, 0, 311, '23', 'Navicat Data Modeler is a powerful                ', 0, '9');
INSERT INTO `work_items` VALUES (255, 'Navicat is a multi-connections                    ', 'SQL Editor allows you to create                   ', 'P7', 'Ⅲ', '高', '2027-12-29 01:39:02', NULL, 66, 0, 103, '12', 'The Information Pane shows the                    ', 0, '0001');
INSERT INTO `work_items` VALUES (256, 'Secure SHell (SSH) is a program                   ', 'Monitored servers include MySQL,                  ', 'P3', 'Ⅰ', '中', '2026-09-30 21:45:38', NULL, 60.4, 0, 231, '1', 'You cannot save people, you can just love them.   ', 1, '22');
INSERT INTO `work_items` VALUES (257, 'The Synchronize to Database function              ', 'I destroy my enemies when I make them my friends.', 'P8', 'Ⅱ', '低', '2027-08-21 06:45:52', NULL, 19.1, 0, 62, '27', 'Navicat authorizes you to make                    ', 0, '0123');
INSERT INTO `work_items` VALUES (258, 'Navicat Monitor is a safe, simple                 ', 'Remember that failure is an event, not a person.', 'P5', 'Ⅲ', '中', '2027-06-14 10:04:21', NULL, 93.4, 0, 126, '2', 'How we spend our days is, of course,              ', 0, '6');
INSERT INTO `work_items` VALUES (259, 'All journeys have secret destinations             ', 'You can select any connections,                   ', 'P2', 'Ⅳ', '高', '2027-06-30 22:41:49', NULL, 35.9, 0, 287, '18', NULL, 0, '30');
INSERT INTO `work_items` VALUES (260, 'The repository database can be                    ', 'Actually it is just in an idea                    ', 'P7', 'Ⅰ', '中', '2026-12-14 14:58:27', NULL, 7.1, 0, 208, '3', 'Navicat Cloud could not connect                   ', 0, '10');
INSERT INTO `work_items` VALUES (261, 'The reason why a great man is great               ', 'Difficult circumstances serve as                  ', 'P7', 'Ⅳ', '中', '2027-01-20 00:21:25', NULL, 69.8, 0, 294, '24', NULL, 0, '15');
INSERT INTO `work_items` VALUES (262, 'Remember that failure is an event, not a person.', 'HTTP Tunneling is a method for                    ', 'P5', 'Ⅳ', '中', '2027-02-17 09:07:41', NULL, 29.6, 0, 197, '28', NULL, 0, '4');
INSERT INTO `work_items` VALUES (263, 'The Main Window consists of several               ', 'Navicat 15 has added support for                  ', 'P7', 'Ⅳ', '中', '2027-09-09 01:03:07', NULL, 48.2, 0, 231, '16', 'The Navigation pane employs tree                  ', 0, '22');
INSERT INTO `work_items` VALUES (264, 'It is used while your ISPs do not                 ', 'Creativity is intelligence having fun.', 'P8', 'Ⅱ', '中', '2027-01-27 18:39:22', NULL, 92.9, 0, 281, '29', NULL, 0, '7');
INSERT INTO `work_items` VALUES (265, 'If you wait, all that happens is you get older.', 'Always keep your eyes open. Keep                  ', 'P5', 'Ⅰ', '无', '2027-06-18 11:38:47', NULL, 44.3, 0, 273, '15', NULL, 0, '26');
INSERT INTO `work_items` VALUES (266, 'To successfully establish a new                   ', 'Navicat 15 has added support for                  ', 'P7', 'Ⅳ', '中', '2026-11-01 16:28:23', NULL, 52.3, 0, 95, '29', 'Always keep your eyes open. Keep                  ', 0, '5');
INSERT INTO `work_items` VALUES (267, 'If it scares you, it might be a good thing to try.', 'The Main Window consists of several               ', 'P4', 'Ⅰ', '低', '2026-09-13 13:37:58', NULL, 83.3, 0, 168, '18', NULL, 0, '22');
INSERT INTO `work_items` VALUES (268, 'Navicat provides powerful tools                   ', 'Monitored servers include MySQL,                  ', 'P3', 'Ⅳ', '中', '2027-02-26 18:50:59', NULL, 70.4, 0, 107, '16', 'To connect to a database or schema,               ', 0, '4');
INSERT INTO `work_items` VALUES (269, 'Navicat Data Modeler is a powerful                ', 'The Main Window consists of several               ', 'P7', 'Ⅱ', '无', '2027-09-28 18:02:57', NULL, 76.7, 0, 211, '19', 'HTTP Tunneling is a method for                    ', 0, '18');
INSERT INTO `work_items` VALUES (270, 'Export Wizard allows you to export                ', 'Genius is an infinite capacity for taking pains.', 'P8', 'Ⅳ', '低', '2027-01-15 06:55:12', NULL, 53.4, 0, 134, '16', 'There is no way to happiness. Happiness           ', 1, '24');
INSERT INTO `work_items` VALUES (271, 'Navicat provides a wide range advanced            ', 'Typically, it is employed as an                   ', 'P4', 'Ⅰ', '中', '2027-10-12 08:53:38', NULL, 96.2, 0, 202, '0000', 'If the Show objects under schema                  ', 1, '5');
INSERT INTO `work_items` VALUES (272, 'The Synchronize to Database function              ', 'Navicat Data Modeler enables you                  ', 'P3', 'Ⅲ', '高', '2026-10-31 20:29:30', NULL, 2.8, 0, 199, '15', 'If you wait, all that happens is you get older.', 1, '17');
INSERT INTO `work_items` VALUES (273, 'The Information Pane shows the                    ', 'To start working with your server                 ', 'P2', 'Ⅰ', '中', '2027-08-07 23:47:13', NULL, 73.6, 0, 186, '24', NULL, 0, '0000');
INSERT INTO `work_items` VALUES (274, 'Actually it is just in an idea                    ', 'To successfully establish a new                   ', 'P3', 'Ⅰ', '低', '2026-10-02 17:50:14', NULL, 69.5, 0, 325, '22', 'In the Objects tab, you can use                   ', 1, '30');
INSERT INTO `work_items` VALUES (275, 'Creativity is intelligence having fun.', 'I may not have gone where I intended              ', 'P3', 'Ⅲ', '中', '2027-05-22 09:01:16', NULL, 80.6, 0, 140, '7', NULL, 0, '7');
INSERT INTO `work_items` VALUES (276, 'A query is used to extract data                   ', 'Such sessions are also susceptible                ', 'P3', 'Ⅱ', '低', '2026-10-07 11:45:56', NULL, 60.6, 0, 247, '0012', NULL, 0, '23');
INSERT INTO `work_items` VALUES (277, 'Navicat allows you to transfer                    ', 'Difficult circumstances serve as                  ', 'P6', 'Ⅰ', '中', '2027-12-10 20:02:43', NULL, 40, 0, 158, '14', NULL, 1, '30');
INSERT INTO `work_items` VALUES (278, 'The Synchronize to Database function              ', 'If the plan doesn’t work, change                ', 'P6', 'Ⅲ', '中', '2027-02-09 04:05:51', NULL, 69.5, 0, 59, '0123', 'Typically, it is employed as an                   ', 0, '5');
INSERT INTO `work_items` VALUES (279, 'Navicat is a multi-connections                    ', 'HTTP Tunneling is a method for                    ', 'P3', 'Ⅰ', '无', '2027-09-01 16:56:19', NULL, 53.7, 0, 304, '1', NULL, 0, '30');
INSERT INTO `work_items` VALUES (280, 'If you wait, all that happens is you get older.', 'To connect to a database or schema,               ', 'P2', 'Ⅱ', '中', '2027-08-22 04:06:46', NULL, 47.8, 0, 239, '15', 'It wasn’t raining when Noah built the ark.', 1, '18');
INSERT INTO `work_items` VALUES (281, 'After comparing data, the window                  ', 'Secure SHell (SSH) is a program                   ', 'P7', 'Ⅱ', '低', '2027-02-12 11:45:56', NULL, 52, 0, 219, '28', 'Difficult circumstances serve as                  ', 0, '5');
INSERT INTO `work_items` VALUES (282, 'Remember that failure is an event, not a person.', 'SQL Editor allows you to create                   ', 'P2', 'Ⅱ', '中', '2027-12-16 03:46:43', NULL, 91, 0, 243, '5', 'A query is used to extract data                   ', 0, '22');
INSERT INTO `work_items` VALUES (283, 'Monitored servers include MySQL,                  ', 'The Synchronize to Database function              ', 'P3', 'Ⅰ', '中', '2027-05-31 05:11:14', NULL, 98.8, 0, 261, '29', 'Champions keep playing until they get it right.', 0, '19');
INSERT INTO `work_items` VALUES (284, 'If your Internet Service Provider                 ', 'I will greet this day with love in my heart.      ', 'P8', 'Ⅲ', '高', '2027-01-26 01:52:40', NULL, 59, 0, 202, '0012', 'You cannot save people, you can just love them.   ', 0, '5');
INSERT INTO `work_items` VALUES (285, 'The Information Pane shows the                    ', 'To successfully establish a new                   ', 'P8', 'Ⅱ', '低', '2027-10-03 05:07:08', NULL, 98.8, 0, 113, '10', 'It provides strong authentication                 ', 0, '19');
INSERT INTO `work_items` VALUES (286, 'Anyone who has ever made anything                 ', 'Navicat Monitor can be installed                  ', 'P4', 'Ⅰ', '低', '2027-03-26 08:41:51', NULL, 59.2, 0, 327, '20', 'Typically, it is employed as an                   ', 0, '8');
INSERT INTO `work_items` VALUES (287, 'There is no way to happiness. Happiness           ', 'Secure SHell (SSH) is a program                   ', 'P2', 'Ⅲ', '高', '2027-06-22 15:13:17', NULL, 83.8, 0, 40, '11', NULL, 1, '29');
INSERT INTO `work_items` VALUES (288, 'Navicat provides a wide range advanced            ', 'The first step is as good as half over.', 'P5', 'Ⅲ', '低', '2027-09-03 19:18:26', NULL, 7.6, 0, 60, '5', NULL, 0, '0012');
INSERT INTO `work_items` VALUES (289, 'The Synchronize to Database function              ', 'There is no way to happiness. Happiness           ', 'P2', 'Ⅲ', '高', '2026-09-17 19:08:45', NULL, 67.4, 0, 266, '0123', 'SQL Editor allows you to create                   ', 1, '16');
INSERT INTO `work_items` VALUES (290, 'If opportunity doesn’t knock, build a door.     ', 'Navicat Data Modeler enables you                  ', 'P4', 'Ⅱ', '无', '2027-06-08 20:46:46', NULL, 52.3, 0, 189, '6', 'Navicat authorizes you to make                    ', 1, '22');
INSERT INTO `work_items` VALUES (291, 'The first step is as good as half over.           ', 'How we spend our days is, of course,              ', 'P8', 'Ⅱ', '低', '2026-10-27 21:40:11', NULL, 17, 0, 261, '4', 'Navicat provides powerful tools                   ', 0, '19');
INSERT INTO `work_items` VALUES (292, 'After logged in the Navicat Cloud                 ', 'Remember that failure is an event, not a person.', 'P7', 'Ⅰ', '无', '2026-10-26 13:14:25', NULL, 60.7, 0, 173, '17', NULL, 1, '18');
INSERT INTO `work_items` VALUES (293, 'Navicat provides a wide range advanced            ', 'The repository database can be                    ', 'P7', 'Ⅲ', '无', '2026-11-28 17:37:18', NULL, 77.4, 0, 176, '15', 'Navicat Data Modeler is a powerful                ', 1, '20');
INSERT INTO `work_items` VALUES (294, 'It collects process metrics such                  ', 'Export Wizard allows you to export                ', 'P6', 'Ⅰ', '中', '2026-12-22 17:52:42', NULL, 97.9, 0, 207, '8', 'Monitored servers include MySQL,                  ', 1, '0001');
INSERT INTO `work_items` VALUES (295, 'If opportunity doesn’t knock, build a door.', 'The reason why a great man is great               ', 'P4', 'Ⅱ', '高', '2027-05-12 18:14:45', NULL, 15.8, 0, 124, '24', NULL, 0, '29');
INSERT INTO `work_items` VALUES (296, 'Navicat Data Modeler is a powerful                ', 'The first step is as good as half over.', 'P4', 'Ⅲ', '低', '2027-01-30 19:52:42', NULL, 14.4, 0, 232, '20', 'I will greet this day with love in my heart.', 0, '18');
INSERT INTO `work_items` VALUES (297, 'If it scares you, it might be a good thing to try.', 'It collects process metrics such                  ', 'P7', 'Ⅰ', '中', '2027-11-17 18:30:37', NULL, 84.1, 0, 262, '29', 'Typically, it is employed as an                   ', 1, '24');
INSERT INTO `work_items` VALUES (298, 'It wasn’t raining when Noah built the ark.', 'In the Objects tab, you can use                   ', 'P6', 'Ⅰ', '低', '2027-04-29 21:45:39', NULL, 98.7, 0, 168, '3', 'Import Wizard allows you to import                ', 0, '22');
INSERT INTO `work_items` VALUES (299, 'In the Objects tab, you can use                   ', 'After logged in the Navicat Cloud                 ', 'P3', 'Ⅰ', '高', '2026-09-15 04:00:08', NULL, 25.5, 0, 51, '22', 'How we spend our days is, of course,              ', 1, '1');
INSERT INTO `work_items` VALUES (300, 'How we spend our days is, of course,              ', 'How we spend our days is, of course,              ', 'P2', 'Ⅳ', '低', '2027-12-05 09:25:57', NULL, 81.2, 0, 44, '11', 'In a Telnet session, all communications,          ', 1, '23');
INSERT INTO `work_items` VALUES (301, 'If the plan doesn’t work, change                ', 'To get a secure connection, the                   ', 'P3', 'Ⅰ', '中', '2026-10-13 19:32:13', NULL, 56.6, 0, 218, '8', NULL, 0, '30');
INSERT INTO `work_items` VALUES (302, 'After logged in the Navicat Cloud                 ', 'After comparing data, the window                  ', 'P8', 'Ⅳ', '中', '2027-06-06 06:57:05', NULL, 18.6, 0, 294, '14', NULL, 1, '15');
INSERT INTO `work_items` VALUES (303, 'You can select any connections,                   ', 'The Information Pane shows the                    ', 'P2', 'Ⅳ', '低', '2026-11-20 18:33:13', NULL, 13.1, 0, 190, '0000', 'Navicat Cloud provides a cloud                    ', 1, '0012');
INSERT INTO `work_items` VALUES (304, 'The reason why a great man is great               ', 'How we spend our days is, of course,              ', 'P5', 'Ⅳ', '中', '2027-05-18 14:58:06', NULL, 57.3, 0, 223, '4', 'If the plan doesn’t work, change                ', 0, '23');
INSERT INTO `work_items` VALUES (305, 'Sometimes you win, sometimes you learn.', 'It provides strong authentication                 ', 'P7', 'Ⅲ', '中', '2027-09-05 16:04:47', NULL, 22.3, 0, 122, '29', NULL, 0, '23');
INSERT INTO `work_items` VALUES (306, 'Navicat provides powerful tools                   ', 'I destroy my enemies when I make them my friends.', 'P5', 'Ⅱ', '高', '2027-02-20 16:53:24', NULL, 52.7, 0, 130, '0012', NULL, 1, '4');
INSERT INTO `work_items` VALUES (307, 'Navicat allows you to transfer                    ', 'If the plan doesn’t work, change                ', 'P7', 'Ⅳ', '低', '2027-05-26 06:02:48', NULL, 81.2, 0, 264, '15', 'Navicat Monitor requires a repository             ', 0, '12');
INSERT INTO `work_items` VALUES (308, 'If the Show objects under schema                  ', 'With its well-designed Graphical                  ', 'P4', 'Ⅳ', '无', '2027-03-05 05:32:30', NULL, 8.3, 0, 291, '25', 'Actually it is just in an idea                    ', 1, '19');
INSERT INTO `work_items` VALUES (309, 'If opportunity doesn’t knock, build a door.', 'Success consists of going from                    ', 'P5', 'Ⅱ', '中', '2027-08-26 02:12:28', NULL, 92.3, 0, 90, '0012', 'A man’s best friends are his ten fingers.', 0, '27');
INSERT INTO `work_items` VALUES (310, 'To successfully establish a new                   ', 'There is no way to happiness. Happiness           ', 'P6', 'Ⅳ', '无', '2027-10-17 04:19:56', NULL, 46.1, 0, 315, '22', 'The Main Window consists of several               ', 1, '5');
INSERT INTO `work_items` VALUES (311, 'Actually it is just in an idea                    ', 'You must be the change you wish                   ', 'P4', 'Ⅰ', '无', '2026-11-23 04:10:17', NULL, 11.5, 0, 41, '1', 'What you get by achieving your                    ', 1, '21');
INSERT INTO `work_items` VALUES (312, 'Navicat allows you to transfer                    ', 'Navicat allows you to transfer                    ', 'P2', 'Ⅱ', '中', '2027-04-17 07:36:56', NULL, 64.7, 0, 142, '30', 'Remember that failure is an event, not a person.', 1, '12');
INSERT INTO `work_items` VALUES (313, 'Navicat is a multi-connections                    ', 'Genius is an infinite capacity for taking pains.', 'P2', 'Ⅱ', '高', '2027-03-18 04:34:26', NULL, 30, 0, 54, '22', 'Navicat Data Modeler is a powerful                ', 0, '0012');
INSERT INTO `work_items` VALUES (314, 'The Main Window consists of several               ', 'To get a secure connection, the                   ', 'P4', 'Ⅱ', '无', '2027-01-14 03:04:44', NULL, 7.1, 0, 229, '8', 'In other words, Navicat provides                  ', 1, '16');
INSERT INTO `work_items` VALUES (315, 'All journeys have secret destinations             ', 'What you get by achieving your                    ', 'P6', 'Ⅲ', '无', '2027-12-05 08:25:40', NULL, 76.5, 0, 110, '16', 'All journeys have secret destinations             ', 1, '14');
INSERT INTO `work_items` VALUES (316, 'After logged in the Navicat Cloud                 ', 'There is no way to happiness. Happiness           ', 'P7', 'Ⅰ', '无', '2027-01-31 20:44:43', NULL, 95.8, 0, 63, '15', 'With its well-designed Graphical                  ', 0, '24');
INSERT INTO `work_items` VALUES (317, 'Navicat Cloud provides a cloud                    ', 'Always keep your eyes open. Keep                  ', 'P3', 'Ⅲ', '无', '2026-09-23 19:14:34', NULL, 41.8, 0, 251, '12', NULL, 1, '6');
INSERT INTO `work_items` VALUES (318, 'If opportunity doesn’t knock, build a door.', 'It collects process metrics such                  ', 'P2', 'Ⅰ', '低', '2027-09-20 12:26:16', NULL, 34.7, 0, 279, '24', 'Navicat Cloud provides a cloud                    ', 0, '18');
INSERT INTO `work_items` VALUES (319, 'Flexible settings enable you to                   ', 'If you wait, all that happens is you get older.', 'P5', 'Ⅲ', '高', '2027-10-30 19:30:24', NULL, 87.8, 0, 222, '0000', 'The Navigation pane employs tree                  ', 0, '28');
INSERT INTO `work_items` VALUES (320, 'To get a secure connection, the                   ', 'Secure Sockets Layer(SSL) is a                    ', 'P4', 'Ⅰ', '高', '2026-10-20 17:01:42', NULL, 62.1, 0, 270, '5', 'Always keep your eyes open. Keep                  ', 0, '3');
INSERT INTO `work_items` VALUES (321, 'The repository database can be                    ', 'Creativity is intelligence having fun.', 'P2', 'Ⅰ', '高', '2026-12-19 18:20:33', NULL, 73.1, 0, 38, '0012', NULL, 1, '8');
INSERT INTO `work_items` VALUES (322, 'Navicat is a multi-connections                    ', 'Remember that failure is an event, not a person.', 'P6', 'Ⅲ', '高', '2026-10-14 12:48:14', NULL, 60.6, 0, 259, '20', 'I destroy my enemies when I make them my friends.', 0, '0123');
INSERT INTO `work_items` VALUES (323, 'After logged in the Navicat Cloud                 ', 'All the Navicat Cloud objects are                 ', 'P2', 'Ⅲ', '高', '2026-12-16 16:18:20', NULL, 87.1, 0, 185, '8', NULL, 0, '13');
INSERT INTO `work_items` VALUES (324, 'It wasn’t raining when Noah built the ark.', 'Navicat is a multi-connections                    ', 'P7', 'Ⅲ', '中', '2026-11-02 20:30:30', NULL, 31.1, 0, 276, '29', 'Flexible settings enable you to                   ', 0, '26');
INSERT INTO `work_items` VALUES (325, 'Navicat Cloud provides a cloud                    ', 'You can select any connections,                   ', 'P8', 'Ⅲ', '低', '2027-04-25 08:18:04', NULL, 41.3, 0, 157, '21', 'It wasn’t raining when Noah built the ark.', 1, '16');
INSERT INTO `work_items` VALUES (326, 'It provides strong authentication                 ', 'Secure SHell (SSH) is a program                   ', 'P3', 'Ⅳ', '低', '2026-10-08 07:43:25', NULL, 76.1, 0, 210, '11', NULL, 1, '17');
INSERT INTO `work_items` VALUES (327, 'All the Navicat Cloud objects are                 ', 'In a Telnet session, all communications,          ', 'P3', 'Ⅲ', '中', '2027-05-08 03:09:29', NULL, 86.6, 0, 268, '18', 'Remember that failure is an event, not a person.', 1, '14');
INSERT INTO `work_items` VALUES (328, 'Export Wizard allows you to export                ', 'Navicat provides powerful tools                   ', 'P8', 'Ⅱ', '高', '2027-08-27 15:31:33', NULL, 44.5, 0, 279, '0123', 'Such sessions are also susceptible                ', 0, '18');
INSERT INTO `work_items` VALUES (329, 'Optimism is the one quality more                  ', 'The Main Window consists of several               ', 'P2', 'Ⅱ', '低', '2027-09-06 17:55:42', NULL, 61.2, 0, 48, '30', NULL, 0, '2');
INSERT INTO `work_items` VALUES (330, 'The reason why a great man is great               ', 'Monitored servers include MySQL,                  ', 'P8', 'Ⅳ', '低', '2027-12-26 20:38:23', NULL, 66.8, 0, 305, '0001', NULL, 0, '15');
INSERT INTO `work_items` VALUES (331, 'In the Objects tab, you can use                   ', 'Optimism is the one quality more                  ', 'P2', 'Ⅱ', '中', '2026-11-23 22:27:25', NULL, 3.8, 0, 310, '23', NULL, 0, '3');
INSERT INTO `work_items` VALUES (332, 'The Main Window consists of several               ', 'The first step is as good as half over.           ', 'P4', 'Ⅳ', '高', '2027-01-23 19:05:41', NULL, 12.8, 0, 254, '11', 'If it scares you, it might be a good thing to try.', 1, '29');
INSERT INTO `work_items` VALUES (333, 'A comfort zone is a beautiful place,              ', 'Navicat Monitor is a safe, simple                 ', 'P8', 'Ⅲ', '中', '2026-12-29 07:36:49', NULL, 92.9, 0, 152, '0000', NULL, 1, '26');
INSERT INTO `work_items` VALUES (334, 'Navicat Cloud provides a cloud                    ', 'What you get by achieving your                    ', 'P7', 'Ⅲ', '高', '2027-05-23 18:41:16', NULL, 59.1, 0, 244, '0001', 'Anyone who has ever made anything                 ', 1, '15');
INSERT INTO `work_items` VALUES (335, 'There is no way to happiness. Happiness           ', 'To clear or reload various internal               ', 'P6', 'Ⅱ', '中', '2027-01-13 13:51:45', NULL, 28.7, 0, 187, '11', 'Creativity is intelligence having fun.            ', 1, '0000');
INSERT INTO `work_items` VALUES (336, 'You must be the change you wish                   ', 'After logged in the Navicat Cloud                 ', 'P5', 'Ⅲ', '中', '2026-12-20 06:53:07', NULL, 85.7, 0, 124, '12', 'Secure Sockets Layer(SSL) is a                    ', 1, '29');
INSERT INTO `work_items` VALUES (337, 'In a Telnet session, all communications,          ', 'Such sessions are also susceptible                ', 'P8', 'Ⅳ', '中', '2027-04-20 22:43:42', NULL, 63.1, 0, 169, '12', 'Navicat authorizes you to make                    ', 1, '11');
INSERT INTO `work_items` VALUES (338, 'Navicat allows you to transfer                    ', 'A query is used to extract data                   ', 'P4', 'Ⅱ', '高', '2027-06-14 17:03:39', NULL, 76, 0, 51, '1', NULL, 0, '1');
INSERT INTO `work_items` VALUES (339, 'It wasn’t raining when Noah built the ark.', 'Monitored servers include MySQL,                  ', 'P4', 'Ⅱ', '低', '2026-12-14 03:28:44', NULL, 57.8, 0, 177, '19', NULL, 1, '15');
INSERT INTO `work_items` VALUES (340, 'Navicat is a multi-connections                    ', 'Anyone who has ever made anything                 ', 'P4', 'Ⅱ', '无', '2027-03-19 13:23:38', NULL, 28.3, 0, 204, '23', 'Navicat authorizes you to make                    ', 0, '24');
INSERT INTO `work_items` VALUES (341, 'Remember that failure is an event, not a person.', 'There is no way to happiness. Happiness           ', 'P6', 'Ⅳ', '无', '2027-04-11 13:28:43', NULL, 88.9, 0, 155, '26', 'It collects process metrics such                  ', 1, '15');
INSERT INTO `work_items` VALUES (342, 'Actually it is just in an idea                    ', 'A man’s best friends are his ten fingers.', 'P3', 'Ⅱ', '高', '2026-10-24 03:03:24', NULL, 7.8, 0, 137, '13', 'Typically, it is employed as an                   ', 1, '15');
INSERT INTO `work_items` VALUES (343, 'I may not have gone where I intended              ', 'It collects process metrics such                  ', 'P6', 'Ⅲ', '无', '2027-10-08 11:20:40', NULL, 72.8, 0, 191, '0001', NULL, 1, '8');
INSERT INTO `work_items` VALUES (344, 'Navicat allows you to transfer                    ', 'The Main Window consists of several               ', 'P3', 'Ⅱ', '无', '2027-10-08 08:31:48', NULL, 83.6, 0, 176, '0000', NULL, 0, '20');
INSERT INTO `work_items` VALUES (345, 'If the Show objects under schema                  ', 'All journeys have secret destinations             ', 'P8', 'Ⅲ', '低', '2027-02-27 20:58:32', NULL, 23.7, 0, 193, '5', NULL, 1, '15');
INSERT INTO `work_items` VALUES (346, 'Sometimes you win, sometimes you learn.           ', 'To successfully establish a new                   ', 'P3', 'Ⅲ', '无', '2027-04-24 09:43:21', NULL, 4.6, 0, 266, '30', 'You can select any connections,                   ', 1, '16');
INSERT INTO `work_items` VALUES (347, 'A comfort zone is a beautiful place,              ', 'Secure SHell (SSH) is a program                   ', 'P6', 'Ⅱ', '低', '2027-12-28 09:03:09', NULL, 13.6, 0, 136, '20', NULL, 1, '25');
INSERT INTO `work_items` VALUES (348, 'Success consists of going from                    ', 'Difficult circumstances serve as                  ', 'P8', 'Ⅰ', '低', '2027-02-12 19:25:59', NULL, 38.2, 0, 174, '27', NULL, 1, '0001');
INSERT INTO `work_items` VALUES (349, 'Navicat Data Modeler is a powerful                ', 'If your Internet Service Provider                 ', 'P6', 'Ⅳ', '低', '2027-06-29 19:48:41', NULL, 45.9, 0, 227, '21', 'Navicat Monitor requires a repository             ', 1, '16');
INSERT INTO `work_items` VALUES (350, 'It provides strong authentication                 ', 'Navicat Cloud could not connect                   ', 'P7', 'Ⅲ', '中', '2026-12-18 00:25:54', NULL, 14.9, 0, 77, '29', 'It wasn’t raining when Noah built the ark.', 1, '3');
INSERT INTO `work_items` VALUES (351, 'Import Wizard allows you to import                ', 'A man is not old until regrets                    ', 'P2', 'Ⅱ', '无', '2027-02-17 14:13:21', NULL, 30.3, 0, 307, '23', 'In the Objects tab, you can use                   ', 1, '26');
INSERT INTO `work_items` VALUES (352, 'Anyone who has ever made anything                 ', 'The On Startup feature allows you                 ', 'P3', 'Ⅰ', '中', '2027-03-08 11:59:09', NULL, 83, 0, 296, '28', 'With its well-designed Graphical                  ', 1, '29');
INSERT INTO `work_items` VALUES (353, 'There is no way to happiness. Happiness           ', 'HTTP Tunneling is a method for                    ', 'P6', 'Ⅰ', '高', '2027-07-08 22:00:53', NULL, 84.2, 0, 236, '13', NULL, 1, '26');
INSERT INTO `work_items` VALUES (354, 'Navicat provides a wide range advanced            ', 'The repository database can be                    ', 'P2', 'Ⅳ', '高', '2027-08-17 21:18:40', NULL, 78.5, 0, 55, '14', 'The Information Pane shows the                    ', 0, '26');
INSERT INTO `work_items` VALUES (355, 'How we spend our days is, of course,              ', 'Typically, it is employed as an                   ', 'P4', 'Ⅳ', '高', '2026-09-28 10:54:46', NULL, 22.1, 0, 272, '0001', 'The Navigation pane employs tree                  ', 1, '0000');
INSERT INTO `work_items` VALUES (356, 'A comfort zone is a beautiful place,              ', 'A comfort zone is a beautiful place,              ', 'P2', 'Ⅳ', '低', '2027-10-05 23:25:54', NULL, 9.2, 0, 288, '3', NULL, 1, '30');
INSERT INTO `work_items` VALUES (357, 'A man is not old until regrets                    ', 'Navicat authorizes you to make                    ', 'P7', 'Ⅲ', '中', '2027-02-12 21:19:19', NULL, 88.2, 0, 141, '1', 'A query is used to extract data                   ', 0, '20');
INSERT INTO `work_items` VALUES (358, 'Import Wizard allows you to import                ', 'A query is used to extract data                   ', 'P2', 'Ⅰ', '无', '2027-12-07 20:01:11', NULL, 13.8, 0, 124, '22', NULL, 0, '29');
INSERT INTO `work_items` VALUES (359, 'You will succeed because most people are lazy.', 'Navicat Monitor can be installed                  ', 'P7', 'Ⅰ', '中', '2027-11-21 02:49:38', NULL, 25.8, 0, 41, '26', NULL, 0, '21');
INSERT INTO `work_items` VALUES (360, 'After logged in the Navicat Cloud                 ', 'It provides strong authentication                 ', 'P2', 'Ⅱ', '无', '2027-08-27 17:20:16', NULL, 45.8, 0, 45, '28', NULL, 1, '0000');
INSERT INTO `work_items` VALUES (361, 'All the Navicat Cloud objects are                 ', 'Champions keep playing until they get it right.', 'P6', 'Ⅲ', '低', '2027-04-22 00:34:47', NULL, 64, 0, 307, '11', 'A comfort zone is a beautiful place,              ', 0, '26');
INSERT INTO `work_items` VALUES (362, 'Always keep your eyes open. Keep                  ', 'Navicat 15 has added support for                  ', 'P6', 'Ⅳ', '无', '2027-05-29 22:10:32', NULL, 77.1, 0, 252, '0000', 'If the plan doesn’t work, change                ', 0, '2');
INSERT INTO `work_items` VALUES (363, 'Creativity is intelligence having fun.', 'The past has no power over the present moment.', 'P8', 'Ⅰ', '高', '2027-03-17 07:24:43', NULL, 12.6, 0, 176, '0123', 'To connect to a database or schema,               ', 1, '20');
INSERT INTO `work_items` VALUES (364, 'A comfort zone is a beautiful place,              ', 'You can select any connections,                   ', 'P6', 'Ⅳ', '中', '2027-01-14 21:20:25', NULL, 3.3, 0, 30, '18', NULL, 1, '9');
INSERT INTO `work_items` VALUES (365, 'I destroy my enemies when I make them my friends.', 'The reason why a great man is great               ', 'P5', 'Ⅳ', '中', '2027-05-13 14:41:13', NULL, 11.1, 0, 68, '20', NULL, 1, '6');
INSERT INTO `work_items` VALUES (366, 'Remember that failure is an event, not a person.', 'There is no way to happiness. Happiness           ', 'P4', 'Ⅲ', '低', '2027-07-05 06:07:12', NULL, 78, 0, 57, '28', 'You will succeed because most people are lazy.', 1, '2');
INSERT INTO `work_items` VALUES (367, 'Actually it is just in an idea                    ', 'It wasn’t raining when Noah built the ark.', 'P6', 'Ⅱ', '无', '2027-05-01 16:21:31', NULL, 75.5, 0, 198, '2', 'After logged in the Navicat Cloud                 ', 1, '20');
INSERT INTO `work_items` VALUES (368, 'I destroy my enemies when I make them my friends.', 'Import Wizard allows you to import                ', 'P6', 'Ⅱ', '高', '2026-12-07 21:02:59', NULL, 12, 0, 64, '27', NULL, 0, '29');
INSERT INTO `work_items` VALUES (369, 'Success consists of going from                    ', 'Navicat provides powerful tools                   ', 'P7', 'Ⅱ', '高', '2026-10-07 18:50:19', NULL, 67.8, 0, 86, '25', NULL, 0, '0000');
INSERT INTO `work_items` VALUES (370, 'To connect to a database or schema,               ', 'To get a secure connection, the                   ', 'P5', 'Ⅱ', '无', '2027-01-22 05:43:44', NULL, 69.6, 0, 104, '23', 'Import Wizard allows you to import                ', 1, '8');
INSERT INTO `work_items` VALUES (371, 'Navicat Cloud could not connect                   ', 'You cannot save people, you can just love them.', 'P7', 'Ⅳ', '高', '2027-09-28 04:37:51', NULL, 13.5, 0, 268, '0001', 'If the Show objects under schema                  ', 0, '14');
INSERT INTO `work_items` VALUES (372, 'A query is used to extract data                   ', 'Navicat Cloud could not connect                   ', 'P6', 'Ⅳ', '低', '2027-10-01 06:58:35', NULL, 73.2, 0, 196, '16', 'Navicat Cloud provides a cloud                    ', 0, '28');
INSERT INTO `work_items` VALUES (373, 'If you wait, all that happens is you get older.   ', 'Navicat 15 has added support for                  ', 'P5', 'Ⅰ', '无', '2027-06-27 20:34:14', NULL, 10.8, 0, 194, '18', NULL, 0, '30');
INSERT INTO `work_items` VALUES (374, 'If it scares you, it might be a good thing to try.', 'The repository database can be                    ', 'P8', 'Ⅱ', '高', '2026-10-08 00:10:59', NULL, 47, 0, 39, '13', NULL, 0, '23');
INSERT INTO `work_items` VALUES (375, 'There is no way to happiness. Happiness           ', 'It collects process metrics such                  ', 'P4', 'Ⅲ', '高', '2027-06-18 18:22:09', NULL, 60.2, 0, 140, '13', NULL, 1, '7');
INSERT INTO `work_items` VALUES (376, 'Genius is an infinite capacity for taking pains.', 'In a Telnet session, all communications,          ', 'P5', 'Ⅲ', '高', '2026-09-14 13:47:06', NULL, 98, 0, 286, '12', 'It provides strong authentication                 ', 1, '10');
INSERT INTO `work_items` VALUES (377, 'In a Telnet session, all communications,          ', 'After logged in the Navicat Cloud                 ', 'P8', 'Ⅳ', '中', '2027-09-25 07:43:23', NULL, 35, 0, 216, '11', 'If you wait, all that happens is you get older.', 1, '30');
INSERT INTO `work_items` VALUES (378, 'Navicat provides powerful tools                   ', 'How we spend our days is, of course,              ', 'P7', 'Ⅲ', '中', '2026-09-19 11:05:40', NULL, 12.5, 0, 93, '22', NULL, 1, '16');
INSERT INTO `work_items` VALUES (379, 'Typically, it is employed as an                   ', 'Actually it is just in an idea                    ', 'P4', 'Ⅱ', '高', '2027-09-09 12:57:22', NULL, 26.3, 0, 202, '6', 'I may not have gone where I intended              ', 1, '5');
INSERT INTO `work_items` VALUES (380, 'Champions keep playing until they get it right.', 'Navicat is a multi-connections                    ', 'P3', 'Ⅳ', '中', '2027-11-13 21:24:50', NULL, 90.1, 0, 184, '0012', 'It is used while your ISPs do not                 ', 1, '26');
INSERT INTO `work_items` VALUES (381, 'It wasn’t raining when Noah built the ark.', 'After comparing data, the window                  ', 'P5', 'Ⅲ', '低', '2027-01-24 10:05:35', NULL, 11.8, 0, 109, '1', 'The Navigation pane employs tree                  ', 0, '1');
INSERT INTO `work_items` VALUES (382, 'It can also manage cloud databases                ', 'Optimism is the one quality more                  ', 'P2', 'Ⅲ', '中', '2027-01-20 02:29:28', NULL, 59.4, 0, 267, '27', 'To connect to a database or schema,               ', 0, '29');
INSERT INTO `work_items` VALUES (383, 'All journeys have secret destinations             ', 'If the plan doesn’t work, change                ', 'P6', 'Ⅰ', '低', '2027-06-12 16:08:27', NULL, 75.3, 0, 254, '23', 'Navicat Data Modeler enables you                  ', 0, '29');
INSERT INTO `work_items` VALUES (384, 'Flexible settings enable you to                   ', 'You can select any connections,                   ', 'P4', 'Ⅳ', '中', '2027-02-19 08:09:55', NULL, 79.7, 0, 252, '16', 'To connect to a database or schema,               ', 0, '2');
INSERT INTO `work_items` VALUES (385, 'Monitored servers include MySQL,                  ', 'Navicat provides a wide range advanced            ', 'P4', 'Ⅲ', '中', '2027-01-25 08:06:50', NULL, 63.5, 0, 165, '5', 'Navicat allows you to transfer                    ', 1, '0012');
INSERT INTO `work_items` VALUES (386, 'The Navigation pane employs tree                  ', 'With its well-designed Graphical                  ', 'P5', 'Ⅳ', '低', '2027-01-11 07:23:21', NULL, 2.6, 0, 202, '28', NULL, 1, '5');
INSERT INTO `work_items` VALUES (387, 'Navicat provides powerful tools                   ', 'I may not have gone where I intended              ', 'P4', 'Ⅲ', '低', '2027-03-22 23:38:25', NULL, 31.7, 0, 41, '22', 'Navicat is a multi-connections                    ', 1, '21');
INSERT INTO `work_items` VALUES (388, 'The repository database can be                    ', 'All journeys have secret destinations             ', 'P6', 'Ⅲ', '无', '2027-12-19 21:47:00', NULL, 59.5, 0, 242, '21', NULL, 0, '0012');
INSERT INTO `work_items` VALUES (389, 'In the middle of winter I at last                 ', 'A man’s best friends are his ten fingers.', 'P6', 'Ⅱ', '中', '2027-04-13 21:39:40', NULL, 54.4, 0, 207, '0012', 'You can select any connections,                   ', 0, '0001');
INSERT INTO `work_items` VALUES (390, 'All journeys have secret destinations             ', 'Monitored servers include MySQL,                  ', 'P6', 'Ⅰ', '无', '2026-09-18 23:29:18', NULL, 66.2, 0, 200, '7', NULL, 0, '14');
INSERT INTO `work_items` VALUES (391, 'A query is used to extract data                   ', 'Navicat allows you to transfer                    ', 'P8', 'Ⅲ', '中', '2027-01-03 21:07:14', NULL, 65.1, 0, 192, '26', 'Navicat Cloud provides a cloud                    ', 1, '1');
INSERT INTO `work_items` VALUES (392, 'Navicat Data Modeler enables you                  ', 'Navicat Monitor can be installed                  ', 'P3', 'Ⅲ', '中', '2027-01-23 09:28:18', NULL, 27.5, 0, 96, '26', 'With its well-designed Graphical                  ', 1, '0123');
INSERT INTO `work_items` VALUES (393, 'The On Startup feature allows you                 ', 'You can select any connections,                   ', 'P2', 'Ⅱ', '高', '2027-04-29 14:37:13', NULL, 4.9, 0, 98, '24', 'How we spend our days is, of course,              ', 1, '9');
INSERT INTO `work_items` VALUES (394, 'Optimism is the one quality more                  ', 'In a Telnet session, all communications,          ', 'P3', 'Ⅱ', '无', '2026-09-20 07:16:42', NULL, 37, 0, 273, '11', 'Success consists of going from                    ', 1, '26');
INSERT INTO `work_items` VALUES (395, 'In the Objects tab, you can use                   ', 'I destroy my enemies when I make them my friends.', 'P2', 'Ⅳ', '中', '2026-12-12 03:37:35', NULL, 1.2, 0, 277, '1', 'A man’s best friends are his ten fingers.       ', 1, '20');
INSERT INTO `work_items` VALUES (396, 'To successfully establish a new                   ', 'Navicat is a multi-connections                    ', 'P5', 'Ⅱ', '中', '2027-01-15 07:42:54', NULL, 1.2, 0, 171, '16', 'Navicat Cloud provides a cloud                    ', 0, '25');
INSERT INTO `work_items` VALUES (397, 'It provides strong authentication                 ', 'Such sessions are also susceptible                ', 'P8', 'Ⅲ', '中', '2026-10-10 15:30:11', NULL, 49.7, 0, 277, '1', 'Navicat Monitor is a safe, simple                 ', 0, '20');
INSERT INTO `work_items` VALUES (398, 'If your Internet Service Provider                 ', 'Secure SHell (SSH) is a program                   ', 'P5', 'Ⅰ', '无', '2026-09-26 07:30:13', NULL, 64, 0, 174, '23', 'The first step is as good as half over.           ', 0, '0001');
INSERT INTO `work_items` VALUES (399, 'To successfully establish a new                   ', 'If it scares you, it might be a good thing to try.', 'P8', 'Ⅳ', '低', '2027-03-06 03:22:57', NULL, 44.1, 0, 88, '22', NULL, 0, '18');
INSERT INTO `work_items` VALUES (400, 'There is no way to happiness. Happiness           ', 'I destroy my enemies when I make them my friends.', 'P4', 'Ⅱ', '高', '2027-11-14 09:22:19', NULL, 57, 0, 298, '8', 'Navicat is a multi-connections                    ', 0, '28');
INSERT INTO `work_items` VALUES (401, 'Navicat Cloud provides a cloud                    ', 'HTTP Tunneling is a method for                    ', 'P8', 'Ⅱ', '无', '2027-01-09 14:58:49', NULL, 61.5, 0, 298, '30', 'SQL Editor allows you to create                   ', 0, '28');
INSERT INTO `work_items` VALUES (402, 'You can select any connections,                   ', 'Anyone who has ever made anything                 ', 'P7', 'Ⅱ', '无', '2027-01-06 11:50:43', NULL, 49.7, 0, 106, '4', NULL, 1, '9');
INSERT INTO `work_items` VALUES (403, 'Anyone who has ever made anything                 ', 'In the middle of winter I at last                 ', 'P7', 'Ⅱ', '无', '2027-02-20 17:31:50', NULL, 41.3, 0, 284, '22', NULL, 1, '6');
INSERT INTO `work_items` VALUES (404, 'Anyone who has ever made anything                 ', 'Optimism is the one quality more                  ', 'P8', 'Ⅳ', '无', '2026-10-15 01:06:35', NULL, 54.9, 0, 252, '12', 'The On Startup feature allows you                 ', 1, '2');
INSERT INTO `work_items` VALUES (405, 'In a Telnet session, all communications,          ', 'It provides strong authentication                 ', 'P3', 'Ⅱ', '无', '2027-02-15 19:18:45', NULL, 16.4, 0, 199, '26', 'You cannot save people, you can just love them.', 1, '17');
INSERT INTO `work_items` VALUES (406, 'Sometimes you win, sometimes you learn.', 'Success consists of going from                    ', 'P7', 'Ⅲ', '无', '2027-09-26 12:18:57', NULL, 71.9, 0, 280, '30', NULL, 1, '11');
INSERT INTO `work_items` VALUES (407, 'The Information Pane shows the                    ', 'The reason why a great man is great               ', 'P5', 'Ⅱ', '无', '2027-11-18 11:34:19', NULL, 30.4, 0, 239, '29', 'What you get by achieving your                    ', 1, '18');
INSERT INTO `work_items` VALUES (408, 'Navicat Monitor can be installed                  ', 'With its well-designed Graphical                  ', 'P2', 'Ⅳ', '高', '2027-12-02 22:26:39', NULL, 14.1, 0, 278, '4', 'Success consists of going from                    ', 0, '22');
INSERT INTO `work_items` VALUES (409, 'The Navigation pane employs tree                  ', 'The Main Window consists of several               ', 'P4', 'Ⅱ', '高', '2026-10-24 11:55:33', NULL, 58, 0, 264, '26', 'Secure Sockets Layer(SSL) is a                    ', 0, '12');
INSERT INTO `work_items` VALUES (410, 'To get a secure connection, the                   ', 'Navicat 15 has added support for                  ', 'P4', 'Ⅰ', '中', '2026-10-18 01:40:14', NULL, 13.7, 0, 222, '0012', 'Navicat Monitor requires a repository             ', 0, '28');
INSERT INTO `work_items` VALUES (411, 'Navicat provides a wide range advanced            ', 'Flexible settings enable you to                   ', 'P8', 'Ⅰ', '高', '2026-10-18 14:31:59', NULL, 95.7, 0, 230, '4', NULL, 0, '22');
INSERT INTO `work_items` VALUES (412, 'Success consists of going from                    ', 'It collects process metrics such                  ', 'P3', 'Ⅰ', '低', '2027-08-09 09:18:33', NULL, 41.3, 0, 248, '12', 'Navicat provides a wide range advanced            ', 0, '27');
INSERT INTO `work_items` VALUES (413, 'Champions keep playing until they get it right.', 'You will succeed because most people are lazy.    ', 'P3', 'Ⅱ', '中', '2026-10-10 04:19:18', NULL, 82.4, 0, 189, '21', 'The Main Window consists of several               ', 0, '22');
INSERT INTO `work_items` VALUES (414, 'If you wait, all that happens is you get older.', 'If you wait, all that happens is you get older.', 'P7', 'Ⅲ', '中', '2027-04-30 20:07:52', NULL, 67.5, 0, 259, '29', 'To connect to a database or schema,               ', 0, '0123');
INSERT INTO `work_items` VALUES (415, 'Navicat is a multi-connections                    ', 'It collects process metrics such                  ', 'P7', 'Ⅲ', '中', '2027-07-22 16:43:21', NULL, 54.9, 0, 121, '15', 'Optimism is the one quality more                  ', 0, '13');
INSERT INTO `work_items` VALUES (416, 'I will greet this day with love in my heart.', 'If it scares you, it might be a good thing to try.', 'P4', 'Ⅳ', '中', '2027-04-30 11:23:48', NULL, 65.6, 0, 165, '17', 'To successfully establish a new                   ', 0, '0012');
INSERT INTO `work_items` VALUES (417, 'You can select any connections,                   ', 'SSH serves to prevent such vulnerabilities        ', 'P2', 'Ⅱ', '中', '2027-10-25 09:06:47', NULL, 9.3, 0, 84, '30', NULL, 0, '22');
INSERT INTO `work_items` VALUES (418, 'A man’s best friends are his ten fingers.       ', 'After logged in the Navicat Cloud                 ', 'P4', 'Ⅱ', '中', '2026-10-08 03:54:02', NULL, 57.4, 0, 195, '17', NULL, 1, '24');
INSERT INTO `work_items` VALUES (419, 'Navicat Monitor is a safe, simple                 ', 'I will greet this day with love in my heart.', 'P8', 'Ⅰ', '中', '2027-04-18 07:31:37', NULL, 33.8, 0, 288, '30', 'Navicat Monitor requires a repository             ', 0, '30');
INSERT INTO `work_items` VALUES (420, 'In a Telnet session, all communications,          ', 'Navicat Cloud could not connect                   ', 'P2', 'Ⅱ', '中', '2027-05-27 22:02:02', NULL, 77.4, 0, 151, '12', NULL, 0, '4');
INSERT INTO `work_items` VALUES (421, 'It wasn’t raining when Noah built the ark.', 'In other words, Navicat provides                  ', 'P6', 'Ⅲ', '中', '2026-11-03 23:01:25', NULL, 35.1, 0, 259, '11', 'You will succeed because most people are lazy.', 0, '0123');
INSERT INTO `work_items` VALUES (422, 'You cannot save people, you can just love them.', 'The Synchronize to Database function              ', 'P6', 'Ⅳ', '中', '2027-09-11 03:41:26', NULL, 95.3, 0, 222, '25', 'Optimism is the one quality more                  ', 1, '28');
INSERT INTO `work_items` VALUES (423, 'Difficult circumstances serve as                  ', 'You can select any connections,                   ', 'P6', 'Ⅱ', '高', '2027-02-18 09:40:45', NULL, 5.2, 0, 128, '17', 'Monitored servers include MySQL,                  ', 1, '22');
INSERT INTO `work_items` VALUES (424, 'Navicat 15 has added support for                  ', 'What you get by achieving your                    ', 'P4', 'Ⅰ', '低', '2027-05-31 10:05:29', NULL, 38, 0, 42, '21', 'All the Navicat Cloud objects are                 ', 1, '3');
INSERT INTO `work_items` VALUES (425, 'Secure SHell (SSH) is a program                   ', 'All the Navicat Cloud objects are                 ', 'P5', 'Ⅰ', '高', '2027-02-07 23:58:12', NULL, 97.2, 0, 28, '8', NULL, 1, '24');
INSERT INTO `work_items` VALUES (426, 'Champions keep playing until they get it right.', 'The repository database can be                    ', 'P5', 'Ⅳ', '无', '2027-07-09 09:48:15', NULL, 86.2, 0, 205, '0000', 'You will succeed because most people are lazy.    ', 0, '8');
INSERT INTO `work_items` VALUES (427, 'The Synchronize to Database function              ', 'A man’s best friends are his ten fingers.', 'P5', 'Ⅲ', '无', '2027-10-24 10:30:59', NULL, 19.3, 0, 97, '28', NULL, 1, '16');
INSERT INTO `work_items` VALUES (428, 'Such sessions are also susceptible                ', 'Navicat Monitor can be installed                  ', 'P5', 'Ⅰ', '低', '2027-04-29 03:33:36', NULL, 89.7, 0, 142, '8', 'Navicat authorizes you to make                    ', 0, '12');
INSERT INTO `work_items` VALUES (429, 'Monitored servers include MySQL,                  ', 'Always keep your eyes open. Keep                  ', 'P3', 'Ⅲ', '低', '2027-05-01 23:49:08', NULL, 99.6, 0, 296, '9', 'Secure Sockets Layer(SSL) is a                    ', 1, '29');
INSERT INTO `work_items` VALUES (430, 'I will greet this day with love in my heart.', 'If opportunity doesn’t knock, build a door.     ', 'P6', 'Ⅰ', '高', '2026-10-22 10:50:43', NULL, 88.8, 0, 114, '17', 'Navicat provides a wide range advanced            ', 1, '5');
INSERT INTO `work_items` VALUES (431, 'Navicat Monitor can be installed                  ', 'SSH serves to prevent such vulnerabilities        ', 'P4', 'Ⅳ', '中', '2027-08-28 17:39:58', NULL, 8.2, 0, 56, '29', 'With its well-designed Graphical                  ', 0, '13');
INSERT INTO `work_items` VALUES (432, 'In a Telnet session, all communications,          ', 'The Navigation pane employs tree                  ', 'P8', 'Ⅲ', '低', '2026-12-18 09:22:50', NULL, 43.9, 0, 34, '8', NULL, 0, '28');
INSERT INTO `work_items` VALUES (433, 'I will greet this day with love in my heart.', 'I will greet this day with love in my heart.      ', 'P4', 'Ⅰ', '无', '2027-12-09 14:08:26', NULL, 50.1, 0, 317, '7', 'Navicat Cloud provides a cloud                    ', 1, '11');
INSERT INTO `work_items` VALUES (434, 'To successfully establish a new                   ', 'Navicat authorizes you to make                    ', 'P7', 'Ⅱ', '高', '2026-12-27 11:39:41', NULL, 62.4, 0, 173, '19', 'Difficult circumstances serve as                  ', 0, '18');
INSERT INTO `work_items` VALUES (435, 'Navicat Data Modeler enables you                  ', 'To start working with your server                 ', 'P7', 'Ⅱ', '中', '2027-04-17 13:28:31', NULL, 61.7, 0, 152, '0123', 'A comfort zone is a beautiful place,              ', 1, '26');
INSERT INTO `work_items` VALUES (436, 'Anyone who has never made a mistake               ', 'Success consists of going from                    ', 'P2', 'Ⅱ', '无', '2027-11-22 17:47:21', NULL, 17.6, 0, 81, '27', NULL, 1, '8');
INSERT INTO `work_items` VALUES (437, 'Typically, it is employed as an                   ', 'Navicat Monitor can be installed                  ', 'P7', 'Ⅲ', '低', '2027-05-04 12:20:15', NULL, 94.6, 0, 305, '10', 'You must be the change you wish                   ', 0, '15');
INSERT INTO `work_items` VALUES (438, 'Champions keep playing until they get it right.   ', 'Monitored servers include MySQL,                  ', 'P2', 'Ⅳ', '高', '2027-01-07 14:49:59', NULL, 11, 0, 63, '6', 'It can also manage cloud databases                ', 0, '24');
INSERT INTO `work_items` VALUES (439, 'It collects process metrics such                  ', 'The Navigation pane employs tree                  ', 'P5', 'Ⅳ', '低', '2027-10-02 03:02:09', NULL, 79.8, 0, 278, '1', 'You must be the change you wish                   ', 0, '22');
INSERT INTO `work_items` VALUES (440, 'You must be the change you wish                   ', 'You cannot save people, you can just love them.', 'P7', 'Ⅳ', '中', '2027-10-07 00:10:27', NULL, 60.8, 0, 261, '29', NULL, 0, '19');
INSERT INTO `work_items` VALUES (441, 'Navicat allows you to transfer                    ', 'Remember that failure is an event, not a person.', 'P8', 'Ⅱ', '高', '2027-03-21 06:36:44', NULL, 3.6, 0, 170, '22', NULL, 1, '29');
INSERT INTO `work_items` VALUES (442, 'Typically, it is employed as an                   ', 'You must be the change you wish                   ', 'P5', 'Ⅳ', '中', '2027-09-05 03:34:19', NULL, 78.8, 0, 40, '20', NULL, 1, '29');
INSERT INTO `work_items` VALUES (443, 'Navicat allows you to transfer                    ', 'Secure SHell (SSH) is a program                   ', 'P3', 'Ⅰ', '低', '2027-09-26 18:00:02', NULL, 22.7, 0, 248, '4', 'You can select any connections,                   ', 1, '27');
INSERT INTO `work_items` VALUES (444, 'It provides strong authentication                 ', 'Optimism is the one quality more                  ', 'P8', 'Ⅳ', '高', '2027-11-11 01:55:20', NULL, 87.6, 0, 229, '0001', 'The first step is as good as half over.', 1, '16');
INSERT INTO `work_items` VALUES (445, 'I destroy my enemies when I make them my friends.', 'Anyone who has never made a mistake               ', 'P3', 'Ⅰ', '高', '2026-12-11 03:13:53', NULL, 64.2, 0, 145, '1', 'Import Wizard allows you to import                ', 1, '1');
INSERT INTO `work_items` VALUES (446, 'To successfully establish a new                   ', 'To get a secure connection, the                   ', 'P2', 'Ⅳ', '高', '2027-02-19 21:46:38', NULL, 34.2, 0, 40, '0123', 'Remember that failure is an event, not a person.', 1, '29');
INSERT INTO `work_items` VALUES (447, 'Difficult circumstances serve as                  ', 'Navicat provides a wide range advanced            ', 'P8', 'Ⅱ', '无', '2027-08-10 21:56:09', NULL, 90.9, 0, 327, '13', 'The first step is as good as half over.           ', 1, '8');
INSERT INTO `work_items` VALUES (448, 'Flexible settings enable you to                   ', 'Navicat Monitor requires a repository             ', 'P6', 'Ⅳ', '无', '2027-08-11 15:25:18', NULL, 79.2, 0, 125, '2', NULL, 0, '21');
INSERT INTO `work_items` VALUES (449, 'Navicat Monitor is a safe, simple                 ', 'It provides strong authentication                 ', 'P7', 'Ⅱ', '中', '2027-02-19 05:24:41', NULL, 8.1, 0, 80, '9', 'It is used while your ISPs do not                 ', 0, '22');
INSERT INTO `work_items` VALUES (450, 'The Information Pane shows the                    ', 'A query is used to extract data                   ', 'P4', 'Ⅰ', '高', '2026-11-07 00:08:11', NULL, 92.1, 0, 112, '7', 'Navicat Monitor requires a repository             ', 0, '10');
INSERT INTO `work_items` VALUES (451, 'Optimism is the one quality more                  ', 'After logged in the Navicat Cloud                 ', 'P4', 'Ⅱ', '高', '2027-08-10 08:24:21', NULL, 16.1, 0, 225, '5', 'Anyone who has ever made anything                 ', 0, '26');
INSERT INTO `work_items` VALUES (452, 'It collects process metrics such                  ', 'Navicat Monitor is a safe, simple                 ', 'P3', 'Ⅰ', '中', '2027-08-19 23:12:56', NULL, 10.4, 0, 292, '0012', 'HTTP Tunneling is a method for                    ', 0, '5');
INSERT INTO `work_items` VALUES (453, 'Import Wizard allows you to import                ', 'If you wait, all that happens is you get older.', 'P3', 'Ⅰ', '低', '2027-07-31 23:43:15', NULL, 49.9, 0, 136, '2', 'Sometimes you win, sometimes you learn.', 1, '25');
INSERT INTO `work_items` VALUES (454, 'Navicat 15 has added support for                  ', 'If your Internet Service Provider                 ', 'P7', 'Ⅱ', '无', '2027-01-31 14:00:32', NULL, 48.3, 0, 129, '25', 'The repository database can be                    ', 0, '19');
INSERT INTO `work_items` VALUES (455, 'A man’s best friends are his ten fingers.       ', 'With its well-designed Graphical                  ', 'P2', 'Ⅰ', '无', '2026-12-03 18:58:45', NULL, 82.7, 0, 223, '22', 'Typically, it is employed as an                   ', 1, '23');
INSERT INTO `work_items` VALUES (456, 'After comparing data, the window                  ', 'You will succeed because most people are lazy.', 'P8', 'Ⅰ', '高', '2027-12-07 08:20:09', NULL, 1.2, 0, 303, '20', 'You can select any connections,                   ', 0, '18');
INSERT INTO `work_items` VALUES (457, 'To start working with your server                 ', 'Navicat allows you to transfer                    ', 'P7', 'Ⅳ', '无', '2027-08-13 08:00:09', NULL, 76.8, 0, 188, '1', 'If it scares you, it might be a good thing to try.', 1, '29');
INSERT INTO `work_items` VALUES (458, 'HTTP Tunneling is a method for                    ', 'Creativity is intelligence having fun.', 'P3', 'Ⅰ', '高', '2027-06-07 14:32:43', NULL, 10.8, 0, 163, '0000', 'To open a query using an external                 ', 1, '17');
INSERT INTO `work_items` VALUES (459, 'If your Internet Service Provider                 ', 'With its well-designed Graphical                  ', 'P7', 'Ⅰ', '中', '2027-07-10 03:42:18', NULL, 41.5, 0, 177, '21', 'If it scares you, it might be a good thing to try.', 1, '15');
INSERT INTO `work_items` VALUES (460, 'The Information Pane shows the                    ', 'Navicat 15 has added support for                  ', 'P6', 'Ⅳ', '无', '2027-08-23 16:47:22', NULL, 42.3, 0, 107, '18', 'It can also manage cloud databases                ', 1, '4');
INSERT INTO `work_items` VALUES (461, 'If it scares you, it might be a good thing to try.', 'It is used while your ISPs do not                 ', 'P8', 'Ⅰ', '低', '2026-12-21 08:37:35', NULL, 17.2, 0, 152, '18', 'Anyone who has ever made anything                 ', 1, '26');
INSERT INTO `work_items` VALUES (462, 'It can also manage cloud databases                ', 'There is no way to happiness. Happiness           ', 'P8', 'Ⅰ', '中', '2027-08-23 20:19:17', NULL, 81, 0, 66, '0012', 'Navicat provides powerful tools                   ', 1, '28');
INSERT INTO `work_items` VALUES (463, 'To clear or reload various internal               ', 'Sometimes you win, sometimes you learn.', 'P2', 'Ⅲ', '无', '2026-11-10 19:41:40', NULL, 81.1, 0, 299, '15', 'It provides strong authentication                 ', 1, '0000');
INSERT INTO `work_items` VALUES (464, 'You must be the change you wish                   ', 'If opportunity doesn’t knock, build a door.', 'P7', 'Ⅲ', '低', '2027-11-06 16:03:10', NULL, 93.6, 0, 160, '12', 'I destroy my enemies when I make them my friends.', 1, '4');
INSERT INTO `work_items` VALUES (465, 'Flexible settings enable you to                   ', 'With its well-designed Graphical                  ', 'P5', 'Ⅲ', '高', '2026-12-15 02:34:37', NULL, 61.6, 0, 220, '0000', 'Champions keep playing until they get it right.', 0, '1');
INSERT INTO `work_items` VALUES (466, 'There is no way to happiness. Happiness           ', 'If it scares you, it might be a good thing to try.', 'P7', 'Ⅲ', '无', '2027-08-25 17:00:48', NULL, 87.5, 0, 149, '25', 'Navicat Cloud provides a cloud                    ', 0, '0012');
INSERT INTO `work_items` VALUES (467, 'A man is not old until regrets                    ', 'To successfully establish a new                   ', 'P5', 'Ⅲ', '高', '2027-01-09 10:50:32', NULL, 4.5, 0, 291, '2', 'To open a query using an external                 ', 1, '19');
INSERT INTO `work_items` VALUES (468, 'Export Wizard allows you to export                ', 'Difficult circumstances serve as                  ', 'P8', 'Ⅱ', '高', '2026-09-14 01:33:53', NULL, 53.6, 0, 182, '13', 'In a Telnet session, all communications,          ', 0, '26');
INSERT INTO `work_items` VALUES (469, 'You can select any connections,                   ', 'If your Internet Service Provider                 ', 'P2', 'Ⅱ', '无', '2027-06-09 10:47:03', NULL, 11.6, 0, 65, '22', 'Creativity is intelligence having fun.', 0, '26');
INSERT INTO `work_items` VALUES (470, 'All the Navicat Cloud objects are                 ', 'If the plan doesn’t work, change                ', 'P6', 'Ⅳ', '高', '2027-02-21 18:54:33', NULL, 25.6, 0, 241, '24', 'It wasn’t raining when Noah built the ark.', 0, '10');
INSERT INTO `work_items` VALUES (471, 'Champions keep playing until they get it right.   ', 'Always keep your eyes open. Keep                  ', 'P6', 'Ⅱ', '中', '2027-06-28 16:50:09', NULL, 99.3, 0, 74, '2', NULL, 0, '11');
INSERT INTO `work_items` VALUES (472, 'With its well-designed Graphical                  ', 'To clear or reload various internal               ', 'P5', 'Ⅲ', '无', '2027-06-10 02:08:28', NULL, 42.2, 0, 85, '9', 'In other words, Navicat provides                  ', 0, '7');
INSERT INTO `work_items` VALUES (473, 'To successfully establish a new                   ', 'Genius is an infinite capacity for taking pains.', 'P7', 'Ⅲ', '无', '2027-12-18 22:56:25', NULL, 48.8, 0, 164, '27', 'With its well-designed Graphical                  ', 1, '16');
INSERT INTO `work_items` VALUES (474, 'To connect to a database or schema,               ', 'To get a secure connection, the                   ', 'P6', 'Ⅱ', '高', '2027-03-30 05:42:57', NULL, 12.3, 0, 59, '22', 'In the Objects tab, you can use                   ', 1, '5');
INSERT INTO `work_items` VALUES (475, 'Navicat provides a wide range advanced            ', 'If you wait, all that happens is you get older.', 'P2', 'Ⅱ', '高', '2027-04-14 05:42:38', NULL, 13.5, 0, 103, '20', NULL, 1, '0001');
INSERT INTO `work_items` VALUES (476, 'Instead of wondering when your                    ', 'You can select any connections,                   ', 'P8', 'Ⅰ', '无', '2027-12-28 01:04:46', NULL, 32.4, 0, 235, '2', 'Navicat Data Modeler is a powerful                ', 0, '26');
INSERT INTO `work_items` VALUES (477, 'To start working with your server                 ', 'Champions keep playing until they get it right.', 'P2', 'Ⅳ', '无', '2027-01-23 03:13:16', NULL, 35.5, 0, 280, '7', NULL, 1, '11');
INSERT INTO `work_items` VALUES (478, 'Genius is an infinite capacity for taking pains.', 'SQL Editor allows you to create                   ', 'P5', 'Ⅱ', '无', '2026-11-09 17:06:01', NULL, 54.1, 0, 78, '1', 'The Information Pane shows the                    ', 1, '30');
INSERT INTO `work_items` VALUES (479, 'SQL Editor allows you to create                   ', 'The Synchronize to Database function              ', 'P7', 'Ⅲ', '低', '2027-01-27 22:28:55', NULL, 7.7, 0, 50, '27', 'To clear or reload various internal               ', 0, '18');
INSERT INTO `work_items` VALUES (480, 'In a Telnet session, all communications,          ', 'There is no way to happiness. Happiness           ', 'P2', 'Ⅰ', '无', '2026-10-08 13:06:11', NULL, 78, 0, 232, '21', 'The Main Window consists of several               ', 0, '18');
INSERT INTO `work_items` VALUES (481, 'To start working with your server                 ', 'The past has no power over the present moment.', 'P4', 'Ⅳ', '高', '2027-03-28 13:10:43', NULL, 93.1, 0, 136, '22', NULL, 0, '25');
INSERT INTO `work_items` VALUES (482, 'The Main Window consists of several               ', 'Navicat Cloud provides a cloud                    ', 'P7', 'Ⅲ', '无', '2027-01-27 05:50:08', NULL, 86.6, 0, 70, '26', 'Such sessions are also susceptible                ', 0, '1');
INSERT INTO `work_items` VALUES (483, 'Navicat provides powerful tools                   ', 'The first step is as good as half over.           ', 'P5', 'Ⅲ', '无', '2027-12-27 04:20:28', NULL, 18, 0, 102, '0000', 'To clear or reload various internal               ', 0, '11');
INSERT INTO `work_items` VALUES (484, 'To connect to a database or schema,               ', 'SQL Editor allows you to create                   ', 'P8', 'Ⅲ', '低', '2026-12-08 20:34:24', NULL, 33.9, 0, 59, '15', NULL, 1, '5');
INSERT INTO `work_items` VALUES (485, 'Navicat is a multi-connections                    ', 'SQL Editor allows you to create                   ', 'P7', 'Ⅳ', '高', '2027-07-25 05:26:57', NULL, 91.5, 0, 290, '23', 'If opportunity doesn’t knock, build a door.', 0, '23');
INSERT INTO `work_items` VALUES (486, 'A query is used to extract data                   ', 'SQL Editor allows you to create                   ', 'P5', 'Ⅰ', '中', '2026-12-01 21:58:21', NULL, 14.5, 0, 33, '16', 'It collects process metrics such                  ', 0, '14');
INSERT INTO `work_items` VALUES (487, 'If you wait, all that happens is you get older.', 'After comparing data, the window                  ', 'P2', 'Ⅳ', '中', '2027-01-21 14:31:48', NULL, 18.8, 0, 211, '23', 'Instead of wondering when your                    ', 0, '18');
INSERT INTO `work_items` VALUES (488, 'There is no way to happiness. Happiness           ', 'Anyone who has ever made anything                 ', 'P2', 'Ⅲ', '无', '2027-04-19 05:01:30', NULL, 40, 0, 89, '7', 'Navicat Cloud could not connect                   ', 1, '2');
INSERT INTO `work_items` VALUES (489, 'Secure Sockets Layer(SSL) is a                    ', 'SQL Editor allows you to create                   ', 'P4', 'Ⅱ', '无', '2027-11-20 15:41:31', NULL, 33.6, 0, 242, '21', 'It collects process metrics such                  ', 1, '0012');
INSERT INTO `work_items` VALUES (490, 'To connect to a database or schema,               ', 'The On Startup feature allows you                 ', 'P3', 'Ⅲ', '中', '2026-12-03 20:10:09', NULL, 95.4, 0, 58, '0123', 'It is used while your ISPs do not                 ', 0, '0012');
INSERT INTO `work_items` VALUES (491, 'If it scares you, it might be a good thing to try.', 'A query is used to extract data                   ', 'P2', 'Ⅱ', '无', '2027-12-25 17:26:28', NULL, 64, 0, 263, '23', 'A query is used to extract data                   ', 0, '0012');
INSERT INTO `work_items` VALUES (492, 'What you get by achieving your                    ', 'In the middle of winter I at last                 ', 'P6', 'Ⅱ', '中', '2026-09-14 22:43:33', NULL, 98.1, 0, 308, '0000', NULL, 1, '8');
INSERT INTO `work_items` VALUES (493, 'If the Show objects under schema                  ', 'Navicat Monitor can be installed                  ', 'P3', 'Ⅳ', '中', '2027-09-24 23:32:00', NULL, 14.9, 0, 137, '0001', NULL, 1, '15');
INSERT INTO `work_items` VALUES (494, 'A query is used to extract data                   ', 'There is no way to happiness. Happiness           ', 'P7', 'Ⅳ', '高', '2026-12-19 19:08:27', NULL, 68, 0, 64, '30', 'How we spend our days is, of course,              ', 1, '29');
INSERT INTO `work_items` VALUES (495, 'If the Show objects under schema                  ', 'You must be the change you wish                   ', 'P6', 'Ⅲ', '高', '2027-07-27 17:11:02', NULL, 13.1, 0, 79, '3', NULL, 0, '12');
INSERT INTO `work_items` VALUES (496, 'Genius is an infinite capacity for taking pains.', 'Creativity is intelligence having fun.', 'P6', 'Ⅳ', '无', '2027-11-22 18:54:36', NULL, 64, 0, 202, '15', 'If it scares you, it might be a good thing to try.', 0, '5');
INSERT INTO `work_items` VALUES (497, 'It provides strong authentication                 ', 'If your Internet Service Provider                 ', 'P4', 'Ⅰ', '高', '2027-08-13 12:37:31', NULL, 63.7, 0, 155, '25', NULL, 0, '15');
INSERT INTO `work_items` VALUES (498, 'To connect to a database or schema,               ', 'Navicat allows you to transfer                    ', 'P2', 'Ⅰ', '低', '2027-12-08 19:03:53', NULL, 67.9, 0, 245, '21', NULL, 1, '6');
INSERT INTO `work_items` VALUES (499, 'Navicat Data Modeler enables you                  ', 'The reason why a great man is great               ', 'P7', 'Ⅳ', '中', '2027-06-14 14:04:10', NULL, 34.1, 0, 216, '15', 'To open a query using an external                 ', 1, '30');
INSERT INTO `work_items` VALUES (500, 'If opportunity doesn’t knock, build a door.', 'Such sessions are also susceptible                ', 'P8', 'Ⅰ', '无', '2027-06-14 22:22:00', NULL, 50.1, 0, 156, '0012', 'It provides strong authentication                 ', 0, '15');
INSERT INTO `work_items` VALUES (501, 'Success consists of going from                    ', 'To successfully establish a new                   ', 'P8', 'Ⅲ', '无', '2027-04-09 16:51:29', NULL, 69.5, 0, 30, '10', NULL, 1, '9');
INSERT INTO `work_items` VALUES (502, 'If your Internet Service Provider                 ', 'The Main Window consists of several               ', 'P4', 'Ⅱ', '低', '2027-04-23 20:08:40', NULL, 5.2, 0, 109, '13', 'Sometimes you win, sometimes you learn.', 1, '1');
INSERT INTO `work_items` VALUES (503, 'Secure Sockets Layer(SSL) is a                    ', 'To connect to a database or schema,               ', 'P6', 'Ⅰ', '高', '2027-04-10 07:10:15', NULL, 15.1, 0, 143, '20', NULL, 1, '14');
INSERT INTO `work_items` VALUES (504, 'Flexible settings enable you to                   ', 'Remember that failure is an event, not a person.', 'P2', 'Ⅰ', '低', '2026-11-24 13:06:42', NULL, 30.7, 0, 127, '0012', 'Genius is an infinite capacity for taking pains.', 1, '18');
INSERT INTO `work_items` VALUES (505, 'If you wait, all that happens is you get older.', 'You can select any connections,                   ', 'P4', 'Ⅲ', '高', '2027-05-24 08:36:18', NULL, 34.2, 0, 281, '21', 'The Navigation pane employs tree                  ', 0, '7');
INSERT INTO `work_items` VALUES (506, 'Success consists of going from                    ', 'Export Wizard allows you to export                ', 'P3', 'Ⅲ', '无', '2027-10-04 15:24:40', NULL, 10.6, 0, 148, '20', NULL, 0, '12');
INSERT INTO `work_items` VALUES (507, 'SQL Editor allows you to create                   ', 'The Information Pane shows the                    ', 'P8', 'Ⅱ', '高', '2027-07-11 12:14:11', NULL, 65.7, 0, 215, '0001', 'You must be the change you wish                   ', 1, '22');
INSERT INTO `work_items` VALUES (508, 'Secure Sockets Layer(SSL) is a                    ', 'The Main Window consists of several               ', 'P3', 'Ⅰ', '无', '2027-08-04 01:18:30', NULL, 65.6, 0, 108, '8', 'Champions keep playing until they get it right.', 0, '23');
INSERT INTO `work_items` VALUES (509, 'If it scares you, it might be a good thing to try.', 'Anyone who has ever made anything                 ', 'P4', 'Ⅲ', '高', '2027-12-10 20:51:56', NULL, 80.9, 0, 302, '12', 'Secure SHell (SSH) is a program                   ', 1, '18');
INSERT INTO `work_items` VALUES (510, 'If the Show objects under schema                  ', 'The Main Window consists of several               ', 'P5', 'Ⅱ', '低', '2026-09-18 06:39:41', NULL, 35.7, 0, 93, '15', NULL, 1, '16');
INSERT INTO `work_items` VALUES (511, 'Creativity is intelligence having fun.            ', 'You cannot save people, you can just love them.', 'P6', 'Ⅱ', '低', '2027-10-07 11:59:50', NULL, 7.4, 0, 43, '8', 'To get a secure connection, the                   ', 0, '3');
INSERT INTO `work_items` VALUES (512, 'With its well-designed Graphical                  ', 'You will succeed because most people are lazy.', 'P8', 'Ⅲ', '中', '2027-02-16 04:53:16', NULL, 48.5, 0, 169, '27', 'Navicat 15 has added support for                  ', 1, '11');
INSERT INTO `work_items` VALUES (513, 'The reason why a great man is great               ', 'To start working with your server                 ', 'P5', 'Ⅳ', '低', '2027-02-01 07:24:36', NULL, 27.4, 0, 211, '14', 'Navicat Monitor can be installed                  ', 0, '18');
INSERT INTO `work_items` VALUES (514, 'The first step is as good as half over.', 'You cannot save people, you can just love them.', 'P4', 'Ⅰ', '无', '2027-03-02 08:42:54', NULL, 30.2, 0, 39, '27', NULL, 1, '23');
INSERT INTO `work_items` VALUES (515, 'Anyone who has ever made anything                 ', 'All journeys have secret destinations             ', 'P2', 'Ⅳ', '无', '2027-09-17 15:00:11', NULL, 7.9, 0, 172, '2', 'Always keep your eyes open. Keep                  ', 1, '28');
INSERT INTO `work_items` VALUES (516, 'It collects process metrics such                  ', 'The past has no power over the present moment.', 'P5', 'Ⅲ', '低', '2026-12-23 16:02:54', NULL, 66, 0, 318, '3', 'The repository database can be                    ', 1, '17');
INSERT INTO `work_items` VALUES (517, 'In a Telnet session, all communications,          ', 'Navicat Data Modeler is a powerful                ', 'P3', 'Ⅱ', '低', '2027-08-07 23:10:25', NULL, 65.8, 0, 80, '15', 'In a Telnet session, all communications,          ', 0, '22');
INSERT INTO `work_items` VALUES (518, 'The reason why a great man is great               ', 'After logged in the Navicat Cloud                 ', 'P7', 'Ⅳ', '无', '2027-11-19 22:30:54', NULL, 41.5, 0, 144, '14', 'Navicat Data Modeler is a powerful                ', 0, '27');
INSERT INTO `work_items` VALUES (519, 'The Information Pane shows the                    ', 'It provides strong authentication                 ', 'P3', 'Ⅲ', '无', '2027-04-17 04:29:39', NULL, 27.7, 0, 315, '11', 'Navicat Cloud could not connect                   ', 1, '5');
INSERT INTO `work_items` VALUES (520, 'To clear or reload various internal               ', 'Instead of wondering when your                    ', 'P7', 'Ⅰ', '高', '2027-06-26 03:37:51', NULL, 41.3, 0, 234, '16', 'It provides strong authentication                 ', 1, '19');
INSERT INTO `work_items` VALUES (521, 'Success consists of going from                    ', 'Navicat Data Modeler is a powerful                ', 'P4', 'Ⅳ', '无', '2027-09-17 10:42:26', NULL, 7, 0, 97, '0000', 'Creativity is intelligence having fun.', 1, '16');
INSERT INTO `work_items` VALUES (522, 'The first step is as good as half over.', 'I may not have gone where I intended              ', 'P7', 'Ⅰ', '低', '2026-10-04 07:33:29', NULL, 62.8, 0, 79, '24', 'SQL Editor allows you to create                   ', 0, '12');
INSERT INTO `work_items` VALUES (523, 'A comfort zone is a beautiful place,              ', 'All journeys have secret destinations             ', 'P7', 'Ⅳ', '中', '2027-12-02 23:11:34', NULL, 52, 0, 247, '4', NULL, 1, '23');
INSERT INTO `work_items` VALUES (524, 'Sometimes you win, sometimes you learn.', 'Champions keep playing until they get it right.', 'P7', 'Ⅲ', '低', '2026-10-19 06:47:51', NULL, 97.6, 0, 188, '19', 'What you get by achieving your                    ', 0, '29');
INSERT INTO `work_items` VALUES (525, 'Genius is an infinite capacity for taking pains.', 'The first step is as good as half over.', 'P2', 'Ⅲ', '低', '2027-01-29 21:24:59', NULL, 40.2, 0, 58, '8', 'Success consists of going from                    ', 1, '0012');
INSERT INTO `work_items` VALUES (526, 'Navicat Monitor is a safe, simple                 ', 'In a Telnet session, all communications,          ', 'P6', 'Ⅱ', '高', '2027-02-22 00:48:15', NULL, 62.5, 0, 251, '17', 'It collects process metrics such                  ', 0, '6');
INSERT INTO `work_items` VALUES (527, 'Optimism is the one quality more                  ', 'To open a query using an external                 ', 'P2', 'Ⅰ', '无', '2027-05-13 04:24:42', NULL, 21.5, 0, 127, '22', 'In other words, Navicat provides                  ', 1, '18');
INSERT INTO `work_items` VALUES (528, 'To successfully establish a new                   ', 'The past has no power over the present moment.', 'P4', 'Ⅲ', '中', '2027-12-21 15:17:17', NULL, 90.8, 0, 252, '28', 'A query is used to extract data                   ', 1, '2');
INSERT INTO `work_items` VALUES (529, 'In the Objects tab, you can use                   ', 'The Main Window consists of several               ', 'P3', 'Ⅲ', '无', '2027-11-03 11:10:08', NULL, 74.8, 0, 228, '3', 'Secure SHell (SSH) is a program                   ', 0, '16');
INSERT INTO `work_items` VALUES (530, 'It collects process metrics such                  ', 'Navicat provides a wide range advanced            ', 'P2', 'Ⅰ', '高', '2027-03-26 15:34:10', NULL, 53.2, 0, 199, '5', 'The reason why a great man is great               ', 0, '17');
INSERT INTO `work_items` VALUES (531, 'Difficult circumstances serve as                  ', 'To start working with your server                 ', 'P7', 'Ⅲ', '中', '2027-01-22 03:31:28', NULL, 22.2, 0, 243, '0012', 'HTTP Tunneling is a method for                    ', 1, '22');
INSERT INTO `work_items` VALUES (532, 'Navicat provides a wide range advanced            ', 'To successfully establish a new                   ', 'P8', 'Ⅱ', '高', '2027-11-08 21:50:58', NULL, 3.9, 0, 186, '6', NULL, 1, '0000');
INSERT INTO `work_items` VALUES (533, 'The first step is as good as half over.', 'Monitored servers include MySQL,                  ', 'P6', 'Ⅰ', '无', '2026-11-10 07:56:22', NULL, 45.1, 0, 56, '24', 'Import Wizard allows you to import                ', 1, '13');
INSERT INTO `work_items` VALUES (534, 'Difficult circumstances serve as                  ', 'If it scares you, it might be a good thing to try.', 'P7', 'Ⅲ', '中', '2026-12-01 18:16:32', NULL, 60.6, 0, 38, '16', NULL, 0, '8');
INSERT INTO `work_items` VALUES (535, 'A query is used to extract data                   ', 'Sometimes you win, sometimes you learn.', 'P6', 'Ⅰ', '无', '2027-02-21 15:57:13', NULL, 41, 0, 232, '7', 'Navicat allows you to transfer                    ', 0, '18');
INSERT INTO `work_items` VALUES (536, 'The On Startup feature allows you                 ', 'There is no way to happiness. Happiness           ', 'P4', 'Ⅳ', '中', '2026-12-07 05:13:55', '2026-09-15 15:11:40', 92.9, 1, 45, '0123', 'Navicat authorizes you to make                    ', 0, '0000');
INSERT INTO `work_items` VALUES (537, 'In a Telnet session, all communications,          ', 'Flexible settings enable you to                   ', 'P2', 'Ⅱ', '无', '2027-05-07 22:39:06', NULL, 31.2, 0, 181, '21', 'The Main Window consists of several               ', 1, '17');
INSERT INTO `work_items` VALUES (538, 'If your Internet Service Provider                 ', 'Difficult circumstances serve as                  ', 'P4', 'Ⅲ', '高', '2027-05-05 03:51:25', NULL, 10.1, 0, 254, '12', 'Navicat Monitor can be installed                  ', 1, '29');
INSERT INTO `work_items` VALUES (539, 'It is used while your ISPs do not                 ', 'A man is not old until regrets                    ', 'P3', 'Ⅲ', '无', '2026-12-17 14:46:52', NULL, 27.7, 0, 193, '7', 'There is no way to happiness. Happiness           ', 1, '15');
INSERT INTO `work_items` VALUES (540, 'Navicat provides a wide range advanced            ', 'The repository database can be                    ', 'P8', 'Ⅱ', '高', '2026-10-07 10:00:07', NULL, 12.7, 0, 287, '22', NULL, 0, '30');
INSERT INTO `work_items` VALUES (541, 'You can select any connections,                   ', 'Navicat Data Modeler enables you                  ', 'P8', 'Ⅳ', '高', '2026-09-19 14:37:56', NULL, 47.8, 0, 123, '7', 'Navicat Cloud could not connect                   ', 1, '9');
INSERT INTO `work_items` VALUES (542, 'Navicat 15 has added support for                  ', 'You will succeed because most people are lazy.', 'P3', 'Ⅱ', '无', '2026-12-06 01:04:03', NULL, 11.1, 0, 270, '28', 'All the Navicat Cloud objects are                 ', 0, '3');
INSERT INTO `work_items` VALUES (543, 'Navicat Monitor is a safe, simple                 ', 'You will succeed because most people are lazy.', 'P5', 'Ⅱ', '无', '2026-12-18 19:10:17', NULL, 48.5, 0, 149, '17', 'Genius is an infinite capacity for taking pains.', 0, '0012');
INSERT INTO `work_items` VALUES (544, 'Navicat Cloud provides a cloud                    ', 'What you get by achieving your                    ', 'P6', 'Ⅰ', '无', '2026-11-12 18:56:48', NULL, 7.6, 0, 273, '6', 'To open a query using an external                 ', 0, '26');
INSERT INTO `work_items` VALUES (545, 'If you wait, all that happens is you get older.', 'Typically, it is employed as an                   ', 'P8', 'Ⅱ', '高', '2027-07-26 01:52:01', NULL, 12.6, 0, 148, '2', NULL, 1, '12');
INSERT INTO `work_items` VALUES (546, 'Navicat Data Modeler is a powerful                ', 'Monitored servers include MySQL,                  ', 'P7', 'Ⅱ', '无', '2027-08-08 21:42:27', NULL, 28.7, 0, 283, '21', 'SSH serves to prevent such vulnerabilities        ', 1, '29');
INSERT INTO `work_items` VALUES (547, 'If the plan doesn’t work, change                ', 'Remember that failure is an event, not a person.', 'P6', 'Ⅱ', '中', '2026-12-14 21:43:33', NULL, 69.5, 0, 182, '21', 'The Information Pane shows the                    ', 0, '26');
INSERT INTO `work_items` VALUES (548, 'HTTP Tunneling is a method for                    ', 'A query is used to extract data                   ', 'P3', 'Ⅲ', '高', '2027-07-26 19:58:24', NULL, 1.9, 0, 237, '28', 'It wasn’t raining when Noah built the ark.', 0, '19');
INSERT INTO `work_items` VALUES (549, 'In the Objects tab, you can use                   ', 'Anyone who has ever made anything                 ', 'P8', 'Ⅳ', '无', '2026-10-28 01:18:57', NULL, 90.3, 0, 267, '21', NULL, 1, '29');
INSERT INTO `work_items` VALUES (550, 'If you wait, all that happens is you get older.', 'Actually it is just in an idea                    ', 'P6', 'Ⅱ', '无', '2026-11-03 14:40:56', NULL, 24.6, 0, 156, '19', 'Navicat Cloud could not connect                   ', 0, '15');
INSERT INTO `work_items` VALUES (551, 'To start working with your server                 ', 'In a Telnet session, all communications,          ', 'P3', 'Ⅳ', '低', '2027-01-28 07:28:18', NULL, 29.5, 0, 138, '9', 'Navicat Monitor requires a repository             ', 1, '28');
INSERT INTO `work_items` VALUES (552, 'Flexible settings enable you to                   ', 'The On Startup feature allows you                 ', 'P7', 'Ⅰ', '高', '2027-10-06 17:32:04', NULL, 77.2, 0, 214, '2', 'If it scares you, it might be a good thing to try.', 1, '29');
INSERT INTO `work_items` VALUES (553, 'If you wait, all that happens is you get older.', 'Navicat provides powerful tools                   ', 'P7', 'Ⅲ', '高', '2026-11-21 12:47:34', NULL, 93.2, 0, 271, '0000', 'You must be the change you wish                   ', 1, '30');
INSERT INTO `work_items` VALUES (554, 'It collects process metrics such                  ', 'Navicat provides powerful tools                   ', 'P3', 'Ⅳ', '中', '2027-07-17 08:04:43', NULL, 50.1, 0, 90, '0123', 'It can also manage cloud databases                ', 0, '27');
INSERT INTO `work_items` VALUES (555, 'Monitored servers include MySQL,                  ', 'What you get by achieving your                    ', 'P6', 'Ⅰ', '高', '2026-12-04 21:12:30', NULL, 79.9, 0, 128, '28', 'Navicat Cloud could not connect                   ', 0, '22');
INSERT INTO `work_items` VALUES (556, 'In the Objects tab, you can use                   ', 'A query is used to extract data                   ', 'P7', 'Ⅳ', '无', '2027-01-24 15:30:51', NULL, 4.2, 0, 127, '0000', NULL, 1, '18');
INSERT INTO `work_items` VALUES (557, 'You will succeed because most people are lazy.', 'Export Wizard allows you to export                ', 'P4', 'Ⅳ', '中', '2027-09-18 20:44:19', NULL, 73.4, 0, 121, '8', 'Anyone who has ever made anything                 ', 0, '13');

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
-- Records of work_package_categories
-- ----------------------------
INSERT INTO `work_package_categories` VALUES (1, '1');
INSERT INTO `work_package_categories` VALUES (2, '2');
INSERT INTO `work_package_categories` VALUES (3, '3');
INSERT INTO `work_package_categories` VALUES (4, '4');
INSERT INTO `work_package_categories` VALUES (5, '5');

-- ----------------------------
-- Table structure for work_package_split_requests
-- ----------------------------
DROP TABLE IF EXISTS `work_package_split_requests`;
CREATE TABLE `work_package_split_requests`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `work_package_id` int NOT NULL,
  `applicant_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `split_items` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `reviewer_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `review_comment` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
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
) ENGINE = InnoDB AUTO_INCREMENT = 43 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of work_package_split_requests
-- ----------------------------

-- ----------------------------
-- Table structure for work_packages
-- ----------------------------
DROP TABLE IF EXISTS `work_packages`;
CREATE TABLE `work_packages`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `complete_status` tinyint(1) NULL DEFAULT NULL,
  `tech_owner_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `project_id` int NOT NULL,
  `category_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `objective` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `isclosed` tinyint(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `owner_id`(`owner_id` ASC) USING BTREE,
  INDEX `category_name`(`category_name` ASC) USING BTREE,
  INDEX `ix_work_packages_id`(`id` ASC) USING BTREE,
  INDEX `idx_work_packages_project_id`(`project_id` ASC) USING BTREE,
  CONSTRAINT `work_packages_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `work_packages_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 328 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of work_packages
-- ----------------------------
INSERT INTO `work_packages` VALUES (28, 'HH-691', '24', 'To start working with your server                 ', 1, '24', 136, '5', 'Navicat Cloud could not connect and access your databases.            ', 1);
INSERT INTO `work_packages` VALUES (29, 'FA-384', '1', 'It collects process metrics such                  ', 1, '1', 157, '1', 'Success consists of going from failure to failure without             ', 1);
INSERT INTO `work_packages` VALUES (30, 'IG-604', '9', 'In a Telnet session, all communications,          ', 1, '9', 151, '4', 'The repository database can be an existing MySQL, MariaDB,            ', 0);
INSERT INTO `work_packages` VALUES (31, 'BA-037', '30', 'Creativity is intelligence having fun.            ', 1, '30', 189, '5', 'Navicat Monitor can be installed on any local computer                ', 1);
INSERT INTO `work_packages` VALUES (32, 'YB-955', '0000', 'Optimism is the one quality more                  ', 1, '0000', 154, '5', 'All journeys have secret destinations of which the                    ', 1);
INSERT INTO `work_packages` VALUES (33, 'PI-894', '14', 'If the plan doesn’t work, change                ', 1, '14', 182, '1', 'What you get by achieving your goals is not as important              ', 1);
INSERT INTO `work_packages` VALUES (34, 'GW-737', '28', 'Optimism is the one quality more                  ', 0, '28', 138, '5', 'If you wait, all that happens is you get older.                       ', 0);
INSERT INTO `work_packages` VALUES (35, 'UC-901', '0123', 'Difficult circumstances serve as                  ', 1, '0123', 164, '3', 'Navicat Cloud could not connect and access your databases.            ', 1);
INSERT INTO `work_packages` VALUES (36, 'TG-687', '19', 'Navicat authorizes you to make                    ', 0, '19', 172, '5', 'Navicat provides a wide range advanced features, such                 ', 1);
INSERT INTO `work_packages` VALUES (37, 'SP-238', '11', 'All journeys have secret destinations             ', 1, '11', 198, '2', 'Navicat is a multi-connections Database Administration                ', 1);
INSERT INTO `work_packages` VALUES (38, 'RY-705', '8', 'If you wait, all that happens is you get older.', 0, '8', 126, '2', 'It provides strong authentication and secure encrypted                ', 1);
INSERT INTO `work_packages` VALUES (39, 'OX-593', '23', 'Typically, it is employed as an                   ', 1, '23', 208, '4', 'The past has no power over the present moment.', 1);
INSERT INTO `work_packages` VALUES (40, 'XD-788', '29', 'In the Objects tab, you can use                   ', 1, '29', 172, '3', 'It is used while your ISPs do not allow direct connections,           ', 0);
INSERT INTO `work_packages` VALUES (41, 'IX-284', '21', 'The Main Window consists of several               ', 0, '21', 145, '2', 'Optimism is the one quality more associated with success              ', 0);
INSERT INTO `work_packages` VALUES (42, 'EU-873', '3', 'In the middle of winter I at last                 ', 1, '3', 152, '2', 'A man is not old until regrets take the place of dreams.', 0);
INSERT INTO `work_packages` VALUES (43, 'NG-481', '3', 'To connect to a database or schema,               ', 0, '3', 194, '5', 'Anyone who has ever made anything of importance was disciplined.', 1);
INSERT INTO `work_packages` VALUES (44, 'LT-796', '23', 'To open a query using an external                 ', 1, '23', 169, '1', 'SQL Editor allows you to create and edit SQL text,                    ', 0);
INSERT INTO `work_packages` VALUES (45, 'JQ-172', '0000', 'Always keep your eyes open. Keep                  ', 0, '0000', 121, '2', 'In a Telnet session, all communications, including                    ', 0);
INSERT INTO `work_packages` VALUES (46, 'ES-924', '18', 'Anyone who has ever made anything                 ', 1, '18', 169, '1', 'Sometimes you win, sometimes you learn.', 1);
INSERT INTO `work_packages` VALUES (47, 'QT-552', '0001', 'To start working with your server                 ', 0, '0001', 195, '5', 'Actually it is just in an idea when feel oneself can                  ', 0);
INSERT INTO `work_packages` VALUES (48, 'NN-500', '2', 'To clear or reload various internal               ', 0, '2', 130, '3', 'I may not have gone where I intended to go, but I think               ', 1);
INSERT INTO `work_packages` VALUES (49, 'UT-410', '0012', 'Navicat Monitor requires a repository             ', 1, '0012', 136, '3', 'Navicat is a multi-connections Database Administration                ', 1);
INSERT INTO `work_packages` VALUES (50, 'DF-770', '18', 'It can also manage cloud databases                ', 0, '18', 155, '4', 'Remember that failure is an event, not a person.', 1);
INSERT INTO `work_packages` VALUES (51, 'DK-602', '1', 'Genius is an infinite capacity for taking pains.', 1, '1', 167, '3', 'The Navigation pane employs tree structure which allows               ', 1);
INSERT INTO `work_packages` VALUES (52, 'MO-953', '8', 'Navicat Data Modeler is a powerful                ', 0, '8', 134, '3', 'Creativity is intelligence having fun. To clear or                    ', 0);
INSERT INTO `work_packages` VALUES (53, 'VR-665', '4', 'With its well-designed Graphical                  ', 1, '4', 157, '1', 'You can select any connections, objects or projects,                  ', 0);
INSERT INTO `work_packages` VALUES (54, 'PA-525', '0012', 'Export Wizard allows you to export                ', 1, '0012', 140, '4', 'Navicat Data Modeler enables you to build high-quality                ', 1);
INSERT INTO `work_packages` VALUES (55, 'ZE-638', '26', 'If it scares you, it might be a good thing to try.', 1, '26', 180, '2', 'You can select any connections, objects or projects,                  ', 1);
INSERT INTO `work_packages` VALUES (56, 'PJ-215', '13', 'Navicat Cloud provides a cloud                    ', 0, '13', 127, '2', 'The Navigation pane employs tree structure which allows               ', 1);
INSERT INTO `work_packages` VALUES (57, 'CW-366', '2', 'You must be the change you wish                   ', 1, '2', 144, '2', 'In the middle of winter I at last discovered that there               ', 1);
INSERT INTO `work_packages` VALUES (58, 'KM-785', '0012', 'A comfort zone is a beautiful place,              ', 0, '0012', 188, '2', 'I will greet this day with love in my heart.                          ', 1);
INSERT INTO `work_packages` VALUES (59, 'TM-151', '5', 'It can also manage cloud databases                ', 1, '5', 174, '3', 'The first step is as good as half over.', 1);
INSERT INTO `work_packages` VALUES (60, 'RI-070', '0012', 'You will succeed because most people are lazy.', 0, '0012', 157, '3', 'You cannot save people, you can just love them.                       ', 0);
INSERT INTO `work_packages` VALUES (61, 'GX-284', '8', 'Anyone who has ever made anything                 ', 1, '8', 194, '3', 'In other words, Navicat provides the ability for data                 ', 1);
INSERT INTO `work_packages` VALUES (62, 'VJ-220', '0123', 'You cannot save people, you can just love them.', 1, '0123', 140, '4', 'Genius is an infinite capacity for taking pains.', 0);
INSERT INTO `work_packages` VALUES (63, 'QS-073', '24', 'The repository database can be                    ', 0, '24', 203, '5', 'I destroy my enemies when I make them my friends.                     ', 0);
INSERT INTO `work_packages` VALUES (64, 'OX-822', '29', 'The past has no power over the present moment.', 1, '29', 151, '4', 'It provides strong authentication and secure encrypted                ', 0);
INSERT INTO `work_packages` VALUES (65, 'HK-233', '26', 'The Synchronize to Database function              ', 0, '26', 132, '2', 'The past has no power over the present moment.', 0);
INSERT INTO `work_packages` VALUES (66, 'PG-402', '28', 'Navicat Cloud could not connect                   ', 1, '28', 210, '4', 'Flexible settings enable you to set up a custom key                   ', 1);
INSERT INTO `work_packages` VALUES (67, 'NM-897', '0000', 'How we spend our days is, of course,              ', 0, '0000', 137, '2', 'Navicat Monitor requires a repository to store alerts                 ', 1);
INSERT INTO `work_packages` VALUES (68, 'HA-033', '6', 'How we spend our days is, of course,              ', 0, '6', 190, '2', 'SSH serves to prevent such vulnerabilities and allows                 ', 0);
INSERT INTO `work_packages` VALUES (69, 'QK-810', '10', 'The reason why a great man is great               ', 0, '10', 197, '3', 'You will succeed because most people are lazy.                        ', 0);
INSERT INTO `work_packages` VALUES (70, 'LD-296', '1', 'Navicat 15 has added support for                  ', 0, '1', 196, '5', 'How we spend our days is, of course, how we spend our lives.', 0);
INSERT INTO `work_packages` VALUES (71, 'XX-113', '15', 'Such sessions are also susceptible                ', 0, '15', 217, '2', 'In other words, Navicat provides the ability for data                 ', 0);
INSERT INTO `work_packages` VALUES (72, 'TE-763', '16', 'Secure SHell (SSH) is a program                   ', 1, '16', 138, '1', 'A man is not old until regrets take the place of dreams.', 0);
INSERT INTO `work_packages` VALUES (73, 'PC-820', '13', 'To successfully establish a new                   ', 1, '13', 206, '4', 'You must be the change you wish to see in the world.', 0);
INSERT INTO `work_packages` VALUES (74, 'MZ-740', '11', 'Actually it is just in an idea                    ', 0, '11', 155, '4', 'Navicat 15 has added support for the system-wide dark mode.', 0);
INSERT INTO `work_packages` VALUES (75, 'OS-739', '2', 'Creativity is intelligence having fun.            ', 1, '2', 184, '3', 'Sometimes you win, sometimes you learn.                               ', 1);
INSERT INTO `work_packages` VALUES (76, 'TQ-034', '28', 'After logged in the Navicat Cloud                 ', 0, '28', 133, '3', 'Navicat Monitor is a safe, simple and agentless remote                ', 0);
INSERT INTO `work_packages` VALUES (77, 'HH-485', '3', 'It wasn’t raining when Noah built the ark.', 0, '3', 197, '1', 'You cannot save people, you can just love them.', 1);
INSERT INTO `work_packages` VALUES (78, 'UI-946', '30', 'To get a secure connection, the                   ', 1, '30', 203, '5', 'Secure Sockets Layer(SSL) is a protocol for transmitting              ', 1);
INSERT INTO `work_packages` VALUES (79, 'MJ-351', '12', 'After logged in the Navicat Cloud                 ', 1, '12', 121, '1', 'The Main Window consists of several toolbars and panes                ', 1);
INSERT INTO `work_packages` VALUES (80, 'AY-698', '22', 'It collects process metrics such                  ', 0, '22', 141, '4', 'Actually it is just in an idea when feel oneself can                  ', 0);
INSERT INTO `work_packages` VALUES (81, 'OZ-955', '8', 'What you get by achieving your                    ', 1, '8', 119, '5', 'Navicat provides a wide range advanced features, such                 ', 1);
INSERT INTO `work_packages` VALUES (82, 'JE-068', '16', 'It is used while your ISPs do not                 ', 0, '16', 205, '1', 'There is no way to happiness. Happiness is the way.', 0);
INSERT INTO `work_packages` VALUES (83, 'TP-799', '29', 'Navicat provides a wide range advanced            ', 1, '29', 140, '4', 'After comparing data, the window shows the number of                  ', 1);
INSERT INTO `work_packages` VALUES (84, 'EX-891', '22', 'Navicat Cloud provides a cloud                    ', 1, '22', 212, '5', 'It provides strong authentication and secure encrypted                ', 1);
INSERT INTO `work_packages` VALUES (85, 'BD-079', '7', 'To get a secure connection, the                   ', 0, '7', 119, '3', 'It wasn’t raining when Noah built the ark.                          ', 1);
INSERT INTO `work_packages` VALUES (86, 'QF-815', '0000', 'In a Telnet session, all communications,          ', 1, '0000', 135, '1', 'After comparing data, the window shows the number of                  ', 0);
INSERT INTO `work_packages` VALUES (87, 'PF-211', '12', 'To connect to a database or schema,               ', 1, '12', 166, '3', 'Import Wizard allows you to import data to tables/collections         ', 1);
INSERT INTO `work_packages` VALUES (88, 'PO-926', '18', 'Navicat 15 has added support for                  ', 1, '18', 134, '2', 'HTTP Tunneling is a method for connecting to a server                 ', 0);
INSERT INTO `work_packages` VALUES (89, 'NX-871', '2', 'It is used while your ISPs do not                 ', 1, '2', 174, '5', 'To open a query using an external editor, control-click               ', 1);
INSERT INTO `work_packages` VALUES (90, 'WS-286', '27', 'In the Objects tab, you can use                   ', 0, '27', 173, '3', 'All the Navicat Cloud objects are located under different             ', 0);
INSERT INTO `work_packages` VALUES (91, 'EW-026', '11', 'Navicat Data Modeler enables you                  ', 1, '11', 186, '1', 'Navicat provides a wide range advanced features, such                 ', 1);
INSERT INTO `work_packages` VALUES (92, 'DS-885', '5', 'Instead of wondering when your                    ', 1, '5', 141, '5', 'If the Show objects under schema in navigation pane                   ', 0);
INSERT INTO `work_packages` VALUES (93, 'CF-574', '16', 'All the Navicat Cloud objects are                 ', 1, '16', 165, '2', 'If the plan doesn’t work, change the plan, but never the goal.', 0);
INSERT INTO `work_packages` VALUES (94, 'WX-363', '25', 'It is used while your ISPs do not                 ', 1, '25', 170, '3', 'SSH serves to prevent such vulnerabilities and allows                 ', 0);
INSERT INTO `work_packages` VALUES (95, 'WG-805', '5', 'If the Show objects under schema                  ', 0, '5', 190, '1', 'It wasn’t raining when Noah built the ark.                          ', 0);
INSERT INTO `work_packages` VALUES (96, 'IZ-638', '0123', 'I may not have gone where I intended              ', 0, '0123', 200, '3', 'Always keep your eyes open. Keep watching. Because                    ', 1);
INSERT INTO `work_packages` VALUES (97, 'AS-232', '16', 'Navicat Data Modeler enables you                  ', 0, '16', 149, '1', 'Navicat allows you to transfer data from one database                 ', 1);
INSERT INTO `work_packages` VALUES (98, 'RQ-696', '9', 'Always keep your eyes open. Keep                  ', 0, '9', 182, '5', 'The On Startup feature allows you to control what tabs                ', 0);
INSERT INTO `work_packages` VALUES (99, 'LH-499', '11', 'In a Telnet session, all communications,          ', 1, '11', 146, '3', 'Navicat Cloud could not connect and access your databases.            ', 0);
INSERT INTO `work_packages` VALUES (100, 'AQ-895', '12', 'To get a secure connection, the                   ', 1, '12', 124, '5', 'In the middle of winter I at last discovered that there               ', 0);
INSERT INTO `work_packages` VALUES (101, 'IB-619', '22', 'Navicat allows you to transfer                    ', 1, '22', 212, '3', 'Navicat 15 has added support for the system-wide dark mode.', 1);
INSERT INTO `work_packages` VALUES (102, 'KF-028', '11', 'Optimism is the one quality more                  ', 1, '11', 121, '5', 'Anyone who has ever made anything of importance was disciplined.', 1);
INSERT INTO `work_packages` VALUES (103, 'CF-169', '0001', 'Always keep your eyes open. Keep                  ', 1, '0001', 202, '4', 'Sometimes you win, sometimes you learn.', 0);
INSERT INTO `work_packages` VALUES (104, 'PH-763', '8', 'The first step is as good as half over.', 0, '8', 150, '5', 'Anyone who has ever made anything of importance was disciplined.      ', 1);
INSERT INTO `work_packages` VALUES (105, 'SU-982', '17', 'Difficult circumstances serve as                  ', 1, '17', 123, '5', 'Secure Sockets Layer(SSL) is a protocol for transmitting              ', 1);
INSERT INTO `work_packages` VALUES (106, 'SQ-444', '9', 'Always keep your eyes open. Keep                  ', 0, '9', 132, '5', 'Navicat allows you to transfer data from one database                 ', 0);
INSERT INTO `work_packages` VALUES (107, 'AN-753', '4', 'Navicat Cloud could not connect                   ', 1, '4', 123, '2', 'Navicat Monitor requires a repository to store alerts                 ', 1);
INSERT INTO `work_packages` VALUES (108, 'RY-731', '23', 'Instead of wondering when your                    ', 0, '23', 170, '3', 'In a Telnet session, all communications, including                    ', 1);
INSERT INTO `work_packages` VALUES (109, 'RF-116', '1', 'To successfully establish a new                   ', 1, '1', 176, '2', 'Genius is an infinite capacity for taking pains.                      ', 1);
INSERT INTO `work_packages` VALUES (110, 'XF-448', '14', 'After comparing data, the window                  ', 0, '14', 139, '3', 'How we spend our days is, of course, how we spend our lives.', 1);
INSERT INTO `work_packages` VALUES (111, 'XG-709', '7', 'In a Telnet session, all communications,          ', 1, '7', 209, '4', 'If you wait, all that happens is you get older.                       ', 0);
INSERT INTO `work_packages` VALUES (112, 'BL-033', '10', 'Secure SHell (SSH) is a program                   ', 0, '10', 145, '4', 'I destroy my enemies when I make them my friends.                     ', 0);
INSERT INTO `work_packages` VALUES (113, 'SS-233', '19', 'If opportunity doesn’t knock, build a door.     ', 1, '19', 118, '3', 'I will greet this day with love in my heart.                          ', 1);
INSERT INTO `work_packages` VALUES (114, 'XT-404', '5', 'If the plan doesn’t work, change                ', 0, '5', 189, '5', 'Navicat authorizes you to make connection to remote                   ', 0);
INSERT INTO `work_packages` VALUES (115, 'RF-645', '20', 'To start working with your server                 ', 0, '20', 152, '5', 'Such sessions are also susceptible to session hijacking,              ', 0);
INSERT INTO `work_packages` VALUES (116, 'TD-693', '10', 'The past has no power over the present moment.', 1, '10', 206, '5', 'It provides strong authentication and secure encrypted                ', 1);
INSERT INTO `work_packages` VALUES (117, 'DS-920', '26', 'You will succeed because most people are lazy.', 0, '26', 124, '5', 'Sometimes you win, sometimes you learn.                               ', 0);
INSERT INTO `work_packages` VALUES (118, 'XU-795', '0012', 'Anyone who has never made a mistake               ', 1, '0012', 193, '1', 'SSH serves to prevent such vulnerabilities and allows                 ', 1);
INSERT INTO `work_packages` VALUES (119, 'KL-101', '19', 'If it scares you, it might be a good thing to try.', 0, '19', 136, '4', 'Export Wizard allows you to export data from tables,                  ', 1);
INSERT INTO `work_packages` VALUES (120, 'RB-146', '22', 'It can also manage cloud databases                ', 1, '22', 150, '3', 'Navicat Monitor is a safe, simple and agentless remote                ', 1);
INSERT INTO `work_packages` VALUES (121, 'YM-594', '13', 'I may not have gone where I intended              ', 0, '13', 148, '1', 'A man is not old until regrets take the place of dreams.', 0);
INSERT INTO `work_packages` VALUES (122, 'XS-587', '23', 'Navicat 15 has added support for                  ', 0, '23', 154, '1', 'If it scares you, it might be a good thing to try.                    ', 1);
INSERT INTO `work_packages` VALUES (123, 'CY-421', '9', 'A query is used to extract data                   ', 0, '9', 124, '1', 'SQL Editor allows you to create and edit SQL text,                    ', 0);
INSERT INTO `work_packages` VALUES (124, 'TE-343', '29', 'All journeys have secret destinations             ', 1, '29', 170, '4', 'I will greet this day with love in my heart.', 0);
INSERT INTO `work_packages` VALUES (125, 'UH-940', '21', 'Difficult circumstances serve as                  ', 1, '21', 151, '3', 'HTTP Tunneling is a method for connecting to a server                 ', 1);
INSERT INTO `work_packages` VALUES (126, 'UC-855', '6', 'Navicat Data Modeler is a powerful                ', 0, '6', 126, '5', 'To successfully establish a new connection to local/remote            ', 1);
INSERT INTO `work_packages` VALUES (127, 'EG-708', '18', 'Anyone who has ever made anything                 ', 0, '18', 196, '1', 'HTTP Tunneling is a method for connecting to a server                 ', 0);
INSERT INTO `work_packages` VALUES (128, 'UX-116', '22', 'The first step is as good as half over.           ', 1, '22', 191, '1', 'Anyone who has never made a mistake has never tried anything new.', 1);
INSERT INTO `work_packages` VALUES (129, 'XK-331', '19', 'A man is not old until regrets                    ', 1, '19', 183, '2', 'If the plan doesn’t work, change the plan, but never the goal.', 1);
INSERT INTO `work_packages` VALUES (130, 'VJ-425', '4', 'To connect to a database or schema,               ', 0, '4', 172, '1', 'Navicat Monitor is a safe, simple and agentless remote                ', 1);
INSERT INTO `work_packages` VALUES (131, 'VP-859', '30', 'A query is used to extract data                   ', 1, '30', 122, '3', 'The Information Pane shows the detailed object information,           ', 1);
INSERT INTO `work_packages` VALUES (132, 'DW-142', '11', 'Secure Sockets Layer(SSL) is a                    ', 0, '11', 121, '5', 'With its well-designed Graphical User Interface(GUI),                 ', 1);
INSERT INTO `work_packages` VALUES (133, 'XF-437', '22', 'Navicat Monitor requires a repository             ', 0, '22', 210, '3', 'To clear or reload various internal caches, flush tables,             ', 0);
INSERT INTO `work_packages` VALUES (134, 'VR-246', '24', 'Navicat Data Modeler is a powerful                ', 1, '24', 190, '1', 'SQL Editor allows you to create and edit SQL text,                    ', 0);
INSERT INTO `work_packages` VALUES (135, 'FH-121', '16', 'Navicat Data Modeler enables you                  ', 0, '16', 174, '2', 'Navicat Cloud could not connect and access your databases.            ', 1);
INSERT INTO `work_packages` VALUES (136, 'JN-101', '25', 'You must be the change you wish                   ', 0, '25', 147, '4', 'It wasn’t raining when Noah built the ark.                          ', 0);
INSERT INTO `work_packages` VALUES (137, 'VA-581', '15', 'Optimism is the one quality more                  ', 0, '15', 201, '2', 'Sometimes you win, sometimes you learn.                               ', 0);
INSERT INTO `work_packages` VALUES (138, 'RG-693', '28', 'HTTP Tunneling is a method for                    ', 0, '28', 140, '4', 'There is no way to happiness. Happiness is the way.', 1);
INSERT INTO `work_packages` VALUES (139, 'AC-291', '15', 'After comparing data, the window                  ', 1, '15', 127, '5', 'To successfully establish a new connection to local/remote            ', 0);
INSERT INTO `work_packages` VALUES (140, 'YE-128', '7', 'All journeys have secret destinations             ', 1, '7', 129, '4', 'Export Wizard allows you to export data from tables,                  ', 1);
INSERT INTO `work_packages` VALUES (141, 'NH-370', '20', 'Sometimes you win, sometimes you learn.', 1, '20', 158, '2', 'There is no way to happiness. Happiness is the way.                   ', 1);
INSERT INTO `work_packages` VALUES (142, 'IL-265', '12', 'If your Internet Service Provider                 ', 1, '12', 214, '1', 'Navicat allows you to transfer data from one database                 ', 0);
INSERT INTO `work_packages` VALUES (143, 'US-095', '14', 'Genius is an infinite capacity for taking pains.', 1, '14', 151, '2', 'Anyone who has never made a mistake has never tried anything new.', 0);
INSERT INTO `work_packages` VALUES (144, 'FU-748', '27', 'The past has no power over the present moment.', 0, '27', 206, '1', 'After logged in the Navicat Cloud feature, the Navigation             ', 1);
INSERT INTO `work_packages` VALUES (145, 'OZ-494', '1', 'If your Internet Service Provider                 ', 1, '1', 142, '1', 'The Main Window consists of several toolbars and panes                ', 0);
INSERT INTO `work_packages` VALUES (146, 'UD-122', '6', 'Anyone who has ever made anything                 ', 1, '6', 176, '5', 'Anyone who has never made a mistake has never tried anything new.', 0);
INSERT INTO `work_packages` VALUES (147, 'GA-144', '24', 'If you wait, all that happens is you get older.   ', 1, '24', 129, '2', 'Champions keep playing until they get it right.', 1);
INSERT INTO `work_packages` VALUES (148, 'QI-210', '12', 'Flexible settings enable you to                   ', 1, '12', 172, '1', 'What you get by achieving your goals is not as important              ', 0);
INSERT INTO `work_packages` VALUES (149, 'XW-152', '0012', 'Anyone who has never made a mistake               ', 0, '0012', 154, '1', 'A query is used to extract data from the database in                  ', 1);
INSERT INTO `work_packages` VALUES (150, 'MK-132', '20', 'Navicat Cloud provides a cloud                    ', 1, '20', 212, '2', 'Navicat Cloud provides a cloud service for synchronizing              ', 0);
INSERT INTO `work_packages` VALUES (151, 'YE-018', '4', 'Genius is an infinite capacity for taking pains.', 0, '4', 204, '3', 'Navicat allows you to transfer data from one database                 ', 0);
INSERT INTO `work_packages` VALUES (152, 'UA-168', '26', 'Navicat Cloud provides a cloud                    ', 1, '26', 176, '4', 'A man is not old until regrets take the place of dreams.', 0);
INSERT INTO `work_packages` VALUES (153, 'GC-388', '29', 'The repository database can be                    ', 0, '29', 141, '5', 'After logged in the Navicat Cloud feature, the Navigation             ', 0);
INSERT INTO `work_packages` VALUES (154, 'KW-253', '0001', 'Navicat Cloud provides a cloud                    ', 1, '0001', 139, '2', 'The past has no power over the present moment.', 1);
INSERT INTO `work_packages` VALUES (155, 'XA-173', '15', 'Navicat Data Modeler is a powerful                ', 0, '15', 137, '4', 'To successfully establish a new connection to local/remote            ', 1);
INSERT INTO `work_packages` VALUES (156, 'XP-002', '15', 'The Main Window consists of several               ', 0, '15', 175, '1', 'All journeys have secret destinations of which the                    ', 0);
INSERT INTO `work_packages` VALUES (157, 'GY-436', '16', 'The Information Pane shows the                    ', 0, '16', 190, '4', 'What you get by achieving your goals is not as important              ', 0);
INSERT INTO `work_packages` VALUES (158, 'VT-553', '30', 'To successfully establish a new                   ', 1, '30', 138, '1', 'The past has no power over the present moment.', 0);
INSERT INTO `work_packages` VALUES (159, 'YW-559', '3', 'Instead of wondering when your                    ', 0, '3', 128, '3', 'The On Startup feature allows you to control what tabs                ', 0);
INSERT INTO `work_packages` VALUES (160, 'ZL-277', '4', 'The first step is as good as half over.', 1, '4', 128, '1', 'In other words, Navicat provides the ability for data                 ', 0);
INSERT INTO `work_packages` VALUES (161, 'RJ-412', '0000', 'The repository database can be                    ', 1, '0000', 181, '3', 'In the Objects tab, you can use the List List, Detail                 ', 0);
INSERT INTO `work_packages` VALUES (162, 'RE-183', '27', 'If opportunity doesn’t knock, build a door.', 1, '27', 185, '2', 'The On Startup feature allows you to control what tabs                ', 1);
INSERT INTO `work_packages` VALUES (163, 'UP-040', '17', 'It can also manage cloud databases                ', 0, '17', 159, '5', 'If the plan doesn’t work, change the plan, but never the goal.', 1);
INSERT INTO `work_packages` VALUES (164, 'SA-857', '16', 'Such sessions are also susceptible                ', 0, '16', 215, '3', 'Genius is an infinite capacity for taking pains.                      ', 1);
INSERT INTO `work_packages` VALUES (165, 'UO-101', '0012', 'If the Show objects under schema                  ', 0, '0012', 146, '5', 'All the Navicat Cloud objects are located under different             ', 1);
INSERT INTO `work_packages` VALUES (166, 'FI-668', '17', 'Navicat allows you to transfer                    ', 0, '17', 124, '4', 'It is used while your ISPs do not allow direct connections,           ', 0);
INSERT INTO `work_packages` VALUES (167, 'EM-341', '19', 'Secure SHell (SSH) is a program                   ', 1, '19', 133, '5', 'Flexible settings enable you to set up a custom key                   ', 0);
INSERT INTO `work_packages` VALUES (168, 'AY-267', '22', 'It provides strong authentication                 ', 1, '22', 209, '5', 'Navicat provides a wide range advanced features, such                 ', 0);
INSERT INTO `work_packages` VALUES (169, 'DU-907', '11', 'You cannot save people, you can just love them.   ', 1, '11', 188, '5', 'If the Show objects under schema in navigation pane                   ', 0);
INSERT INTO `work_packages` VALUES (170, 'VD-222', '29', 'The first step is as good as half over.', 0, '29', 165, '2', 'What you get by achieving your goals is not as important              ', 1);
INSERT INTO `work_packages` VALUES (171, 'EP-549', '25', 'It provides strong authentication                 ', 0, '25', 151, '2', 'It can also manage cloud databases such as Amazon Redshift,           ', 1);
INSERT INTO `work_packages` VALUES (172, 'RH-172', '28', 'The past has no power over the present moment.', 1, '28', 211, '4', 'Navicat Data Modeler enables you to build high-quality                ', 1);
INSERT INTO `work_packages` VALUES (173, 'KF-223', '18', 'A man’s best friends are his ten fingers.', 1, '18', 181, '5', 'The Navigation pane employs tree structure which allows               ', 0);
INSERT INTO `work_packages` VALUES (174, 'DU-618', '0001', 'If it scares you, it might be a good thing to try.', 1, '0001', 168, '1', 'I destroy my enemies when I make them my friends.', 1);
INSERT INTO `work_packages` VALUES (175, 'FM-366', '23', 'Typically, it is employed as an                   ', 1, '23', 160, '5', 'To start working with your server in Navicat, you should              ', 1);
INSERT INTO `work_packages` VALUES (176, 'MY-816', '20', 'To start working with your server                 ', 1, '20', 210, '4', 'The repository database can be an existing MySQL, MariaDB,            ', 0);
INSERT INTO `work_packages` VALUES (177, 'NV-301', '15', 'It is used while your ISPs do not                 ', 1, '15', 126, '4', 'Sometimes you win, sometimes you learn.', 1);
INSERT INTO `work_packages` VALUES (178, 'XI-410', '29', 'Secure Sockets Layer(SSL) is a                    ', 1, '29', 193, '4', 'A query is used to extract data from the database in                  ', 0);
INSERT INTO `work_packages` VALUES (179, 'YF-399', '18', 'After logged in the Navicat Cloud                 ', 1, '18', 136, '1', 'You must be the change you wish to see in the world.                  ', 1);
INSERT INTO `work_packages` VALUES (180, 'KP-630', '17', 'Anyone who has never made a mistake               ', 1, '17', 163, '5', 'Export Wizard allows you to export data from tables,                  ', 1);
INSERT INTO `work_packages` VALUES (181, 'LH-457', '17', 'SSH serves to prevent such vulnerabilities        ', 0, '17', 158, '5', 'Optimism is the one quality more associated with success              ', 1);
INSERT INTO `work_packages` VALUES (182, 'JV-796', '26', 'A man’s best friends are his ten fingers.', 0, '26', 199, '2', 'All the Navicat Cloud objects are located under different             ', 0);
INSERT INTO `work_packages` VALUES (183, 'PN-027', '21', 'It provides strong authentication                 ', 1, '21', 166, '3', 'It wasn’t raining when Noah built the ark.', 1);
INSERT INTO `work_packages` VALUES (184, 'HT-438', '26', 'To successfully establish a new                   ', 1, '26', 128, '2', 'All the Navicat Cloud objects are located under different             ', 1);
INSERT INTO `work_packages` VALUES (185, 'FK-805', '13', 'You cannot save people, you can just love them.', 0, '13', 183, '1', 'If you wait, all that happens is you get older.                       ', 1);
INSERT INTO `work_packages` VALUES (186, 'NO-162', '0000', 'In the middle of winter I at last                 ', 1, '0000', 152, '1', 'In a Telnet session, all communications, including                    ', 1);
INSERT INTO `work_packages` VALUES (187, 'EY-749', '0000', 'A query is used to extract data                   ', 1, '0000', 150, '2', 'To start working with your server in Navicat, you should              ', 1);
INSERT INTO `work_packages` VALUES (188, 'UD-999', '29', 'If the plan doesn’t work, change                ', 0, '29', 135, '2', 'To successfully establish a new connection to local/remote            ', 1);
INSERT INTO `work_packages` VALUES (189, 'WJ-940', '22', 'If it scares you, it might be a good thing to try.', 1, '22', 133, '5', 'Anyone who has never made a mistake has never tried anything new.', 1);
INSERT INTO `work_packages` VALUES (190, 'ZC-556', '0012', 'In other words, Navicat provides                  ', 1, '0012', 134, '4', 'I may not have gone where I intended to go, but I think               ', 1);
INSERT INTO `work_packages` VALUES (191, 'CO-856', '8', 'All journeys have secret destinations             ', 0, '8', 141, '4', 'Navicat provides powerful tools for working with queries:             ', 1);
INSERT INTO `work_packages` VALUES (192, 'IZ-612', '1', 'It can also manage cloud databases                ', 0, '1', 178, '1', 'In the middle of winter I at last discovered that there               ', 0);
INSERT INTO `work_packages` VALUES (193, 'WR-347', '15', 'Navicat Data Modeler is a powerful                ', 0, '15', 121, '4', 'Import Wizard allows you to import data to tables/collections         ', 0);
INSERT INTO `work_packages` VALUES (194, 'WX-373', '30', 'Navicat allows you to transfer                    ', 1, '30', 171, '3', 'You must be the change you wish to see in the world.                  ', 1);
INSERT INTO `work_packages` VALUES (195, 'SR-239', '24', 'After comparing data, the window                  ', 0, '24', 153, '4', 'All the Navicat Cloud objects are located under different             ', 1);
INSERT INTO `work_packages` VALUES (196, 'YM-053', '28', 'Remember that failure is an event, not a person.', 0, '28', 123, '5', 'A man’s best friends are his ten fingers.                           ', 0);
INSERT INTO `work_packages` VALUES (197, 'EJ-497', '4', 'Navicat Cloud provides a cloud                    ', 0, '4', 134, '1', 'Navicat provides a wide range advanced features, such                 ', 0);
INSERT INTO `work_packages` VALUES (198, 'BC-865', '20', 'SSH serves to prevent such vulnerabilities        ', 0, '20', 148, '5', 'To connect to a database or schema, simply double-click               ', 0);
INSERT INTO `work_packages` VALUES (199, 'DY-387', '17', 'To successfully establish a new                   ', 0, '17', 167, '1', 'In the middle of winter I at last discovered that there               ', 0);
INSERT INTO `work_packages` VALUES (200, 'XE-758', '14', 'In the Objects tab, you can use                   ', 1, '14', 195, '3', 'Secure Sockets Layer(SSL) is a protocol for transmitting              ', 1);
INSERT INTO `work_packages` VALUES (201, 'IW-816', '12', 'To successfully establish a new                   ', 1, '12', 145, '5', 'If you wait, all that happens is you get older.                       ', 1);
INSERT INTO `work_packages` VALUES (202, 'MK-273', '5', 'If you wait, all that happens is you get older.', 0, '5', 162, '1', 'I will greet this day with love in my heart.                          ', 0);
INSERT INTO `work_packages` VALUES (203, 'SP-274', '2', 'SSH serves to prevent such vulnerabilities        ', 0, '2', 202, '3', 'Such sessions are also susceptible to session hijacking,              ', 0);
INSERT INTO `work_packages` VALUES (204, 'WW-217', '24', 'To get a secure connection, the                   ', 1, '24', 196, '4', 'In the middle of winter I at last discovered that there               ', 0);
INSERT INTO `work_packages` VALUES (205, 'OQ-671', '8', 'Monitored servers include MySQL,                  ', 1, '8', 188, '2', 'A query is used to extract data from the database in                  ', 0);
INSERT INTO `work_packages` VALUES (206, 'YT-122', '0012', 'Secure SHell (SSH) is a program                   ', 1, '0012', 148, '1', 'The Synchronize to Database function will give you                    ', 0);
INSERT INTO `work_packages` VALUES (207, 'HW-149', '0001', 'Navicat provides a wide range advanced            ', 0, '0001', 205, '3', 'What you get by achieving your goals is not as important              ', 0);
INSERT INTO `work_packages` VALUES (208, 'CX-831', '10', 'Navicat Monitor is a safe, simple                 ', 0, '10', 186, '1', 'I will greet this day with love in my heart.                          ', 0);
INSERT INTO `work_packages` VALUES (209, 'NT-175', '20', 'Creativity is intelligence having fun.', 0, '20', 149, '1', 'To successfully establish a new connection to local/remote            ', 1);
INSERT INTO `work_packages` VALUES (210, 'QV-566', '17', 'The reason why a great man is great               ', 0, '17', 142, '4', 'It is used while your ISPs do not allow direct connections,           ', 0);
INSERT INTO `work_packages` VALUES (211, 'PL-614', '18', 'Instead of wondering when your                    ', 0, '18', 199, '1', 'Success consists of going from failure to failure without             ', 1);
INSERT INTO `work_packages` VALUES (212, 'UM-166', '30', 'SQL Editor allows you to create                   ', 1, '30', 165, '2', 'The reason why a great man is great is that he resolves               ', 1);
INSERT INTO `work_packages` VALUES (213, 'KB-491', '11', 'You can select any connections,                   ', 0, '11', 200, '2', 'Flexible settings enable you to set up a custom key                   ', 0);
INSERT INTO `work_packages` VALUES (214, 'RN-690', '29', 'To open a query using an external                 ', 1, '29', 149, '1', 'Always keep your eyes open. Keep watching. Because                    ', 0);
INSERT INTO `work_packages` VALUES (215, 'GJ-487', '22', 'With its well-designed Graphical                  ', 1, '22', 118, '4', 'You can select any connections, objects or projects,                  ', 0);
INSERT INTO `work_packages` VALUES (216, 'XY-032', '30', 'Navicat Cloud could not connect                   ', 0, '30', 159, '4', 'Anyone who has never made a mistake has never tried anything new.', 0);
INSERT INTO `work_packages` VALUES (217, 'WU-840', '0000', 'There is no way to happiness. Happiness           ', 0, '0000', 122, '5', 'Navicat Cloud could not connect and access your databases.            ', 1);
INSERT INTO `work_packages` VALUES (218, 'TO-926', '30', 'Navicat Monitor requires a repository             ', 0, '30', 205, '2', 'Genius is an infinite capacity for taking pains.', 1);
INSERT INTO `work_packages` VALUES (219, 'HZ-932', '5', 'A man is not old until regrets                    ', 1, '5', 122, '2', 'SSH serves to prevent such vulnerabilities and allows                 ', 1);
INSERT INTO `work_packages` VALUES (220, 'VQ-565', '1', 'Navicat Monitor is a safe, simple                 ', 0, '1', 171, '3', 'The Information Pane shows the detailed object information,           ', 0);
INSERT INTO `work_packages` VALUES (221, 'WN-465', '25', 'SSH serves to prevent such vulnerabilities        ', 0, '25', 143, '1', 'The repository database can be an existing MySQL, MariaDB,            ', 1);
INSERT INTO `work_packages` VALUES (222, 'AF-474', '28', 'Navicat Data Modeler enables you                  ', 0, '28', 138, '4', 'You cannot save people, you can just love them.', 1);
INSERT INTO `work_packages` VALUES (223, 'RK-641', '23', 'To clear or reload various internal               ', 1, '23', 189, '2', 'The On Startup feature allows you to control what tabs                ', 1);
INSERT INTO `work_packages` VALUES (224, 'ZE-951', '5', 'There is no way to happiness. Happiness           ', 0, '5', 160, '1', 'SQL Editor allows you to create and edit SQL text,                    ', 0);
INSERT INTO `work_packages` VALUES (225, 'FU-033', '26', 'If it scares you, it might be a good thing to try.', 1, '26', 154, '5', 'In other words, Navicat provides the ability for data                 ', 1);
INSERT INTO `work_packages` VALUES (226, 'XK-349', '27', 'In other words, Navicat provides                  ', 0, '27', 217, '3', 'To successfully establish a new connection to local/remote            ', 1);
INSERT INTO `work_packages` VALUES (227, 'OT-901', '16', 'In other words, Navicat provides                  ', 0, '16', 152, '1', 'If the plan doesn’t work, change the plan, but never the goal.', 1);
INSERT INTO `work_packages` VALUES (228, 'NQ-555', '16', 'The On Startup feature allows you                 ', 1, '16', 128, '1', 'It is used while your ISPs do not allow direct connections,           ', 0);
INSERT INTO `work_packages` VALUES (229, 'SA-739', '16', 'If you wait, all that happens is you get older.', 0, '16', 192, '4', 'There is no way to happiness. Happiness is the way.                   ', 0);
INSERT INTO `work_packages` VALUES (230, 'WP-249', '22', 'With its well-designed Graphical                  ', 1, '22', 201, '2', 'In a Telnet session, all communications, including                    ', 0);
INSERT INTO `work_packages` VALUES (231, 'OW-761', '22', 'A comfort zone is a beautiful place,              ', 1, '22', 158, '5', 'Always keep your eyes open. Keep watching. Because                    ', 1);
INSERT INTO `work_packages` VALUES (232, 'HU-192', '18', 'Navicat Data Modeler enables you                  ', 1, '18', 157, '3', 'In a Telnet session, all communications, including                    ', 0);
INSERT INTO `work_packages` VALUES (233, 'SO-534', '10', 'Import Wizard allows you to import                ', 1, '10', 148, '3', 'Genius is an infinite capacity for taking pains.                      ', 1);
INSERT INTO `work_packages` VALUES (234, 'KB-560', '19', 'Navicat 15 has added support for                  ', 0, '19', 133, '1', 'To start working with your server in Navicat, you should              ', 1);
INSERT INTO `work_packages` VALUES (235, 'WG-697', '26', 'Optimism is the one quality more                  ', 1, '26', 139, '5', 'A query is used to extract data from the database in                  ', 1);
INSERT INTO `work_packages` VALUES (236, 'NH-275', '26', 'Secure SHell (SSH) is a program                   ', 1, '26', 165, '1', 'If the Show objects under schema in navigation pane                   ', 0);
INSERT INTO `work_packages` VALUES (237, 'LZ-985', '19', 'Success consists of going from                    ', 0, '19', 150, '1', 'Anyone who has never made a mistake has never tried anything new.', 0);
INSERT INTO `work_packages` VALUES (238, 'RZ-063', '28', 'To successfully establish a new                   ', 0, '28', 144, '2', 'A man is not old until regrets take the place of dreams.              ', 1);
INSERT INTO `work_packages` VALUES (239, 'MU-433', '18', 'It provides strong authentication                 ', 1, '18', 159, '5', 'The Synchronize to Database function will give you                    ', 1);
INSERT INTO `work_packages` VALUES (240, 'ZD-988', '1', 'Such sessions are also susceptible                ', 0, '1', 129, '1', 'SSH serves to prevent such vulnerabilities and allows                 ', 0);
INSERT INTO `work_packages` VALUES (241, 'LD-217', '10', 'Flexible settings enable you to                   ', 0, '10', 186, '3', 'Creativity is intelligence having fun.', 1);
INSERT INTO `work_packages` VALUES (242, 'WB-237', '0012', 'Navicat 15 has added support for                  ', 1, '0012', 198, '2', 'Flexible settings enable you to set up a custom key                   ', 0);
INSERT INTO `work_packages` VALUES (243, 'SV-540', '22', 'Navicat provides a wide range advanced            ', 0, '22', 134, '5', 'Genius is an infinite capacity for taking pains.', 0);
INSERT INTO `work_packages` VALUES (244, 'NP-342', '15', 'To open a query using an external                 ', 0, '15', 165, '3', 'If you wait, all that happens is you get older.                       ', 1);
INSERT INTO `work_packages` VALUES (245, 'XL-792', '6', 'HTTP Tunneling is a method for                    ', 0, '6', 128, '2', 'If the Show objects under schema in navigation pane                   ', 0);
INSERT INTO `work_packages` VALUES (246, 'BT-162', '19', 'In a Telnet session, all communications,          ', 0, '19', 193, '4', 'Navicat allows you to transfer data from one database                 ', 1);
INSERT INTO `work_packages` VALUES (247, 'QW-637', '23', 'Import Wizard allows you to import                ', 0, '23', 166, '5', 'The reason why a great man is great is that he resolves               ', 1);
INSERT INTO `work_packages` VALUES (248, 'CM-353', '27', 'Instead of wondering when your                    ', 0, '27', 177, '2', 'Champions keep playing until they get it right.', 1);
INSERT INTO `work_packages` VALUES (249, 'IG-356', '18', 'Optimism is the one quality more                  ', 1, '18', 160, '4', 'Navicat Data Modeler is a powerful and cost-effective                 ', 0);
INSERT INTO `work_packages` VALUES (250, 'DQ-959', '11', 'Difficult circumstances serve as                  ', 0, '11', 203, '2', 'Genius is an infinite capacity for taking pains.', 1);
INSERT INTO `work_packages` VALUES (251, 'CU-720', '6', 'The repository database can be                    ', 0, '6', 149, '2', 'To clear or reload various internal caches, flush tables,             ', 0);
INSERT INTO `work_packages` VALUES (252, 'AI-027', '2', 'I will greet this day with love in my heart.', 1, '2', 176, '2', 'To successfully establish a new connection to local/remote            ', 0);
INSERT INTO `work_packages` VALUES (253, 'OK-447', '14', 'The Information Pane shows the                    ', 0, '14', 129, '3', 'Genius is an infinite capacity for taking pains.', 1);
INSERT INTO `work_packages` VALUES (254, 'JW-751', '29', 'Always keep your eyes open. Keep                  ', 1, '29', 216, '5', 'Always keep your eyes open. Keep watching. Because                    ', 1);
INSERT INTO `work_packages` VALUES (255, 'ZE-682', '30', 'In other words, Navicat provides                  ', 1, '30', 207, '1', 'Optimism is the one quality more associated with success              ', 1);
INSERT INTO `work_packages` VALUES (256, 'PH-880', '15', 'Navicat Data Modeler is a powerful                ', 1, '15', 132, '4', 'It is used while your ISPs do not allow direct connections,           ', 1);
INSERT INTO `work_packages` VALUES (257, 'RA-152', '13', 'If it scares you, it might be a good thing to try.', 1, '13', 123, '2', 'Sometimes you win, sometimes you learn.                               ', 1);
INSERT INTO `work_packages` VALUES (258, 'OC-375', '7', 'Export Wizard allows you to export                ', 0, '7', 121, '3', 'A man is not old until regrets take the place of dreams.', 1);
INSERT INTO `work_packages` VALUES (259, 'RO-053', '0123', 'HTTP Tunneling is a method for                    ', 1, '0123', 189, '2', 'Navicat Monitor can be installed on any local computer                ', 1);
INSERT INTO `work_packages` VALUES (260, 'TA-499', '9', 'To successfully establish a new                   ', 0, '9', 186, '3', 'After comparing data, the window shows the number of                  ', 0);
INSERT INTO `work_packages` VALUES (261, 'EO-536', '19', 'All the Navicat Cloud objects are                 ', 0, '19', 206, '5', 'Flexible settings enable you to set up a custom key                   ', 0);
INSERT INTO `work_packages` VALUES (262, 'YL-895', '24', 'Always keep your eyes open. Keep                  ', 1, '24', 124, '2', 'All the Navicat Cloud objects are located under different             ', 1);
INSERT INTO `work_packages` VALUES (263, 'EH-392', '0012', 'The Synchronize to Database function              ', 1, '0012', 184, '3', 'To successfully establish a new connection to local/remote            ', 1);
INSERT INTO `work_packages` VALUES (264, 'QY-751', '12', 'It wasn’t raining when Noah built the ark.', 0, '12', 188, '2', 'To clear or reload various internal caches, flush tables,             ', 1);
INSERT INTO `work_packages` VALUES (265, 'LH-965', '16', 'Navicat Monitor can be installed                  ', 1, '16', 156, '1', 'In the middle of winter I at last discovered that there               ', 0);
INSERT INTO `work_packages` VALUES (266, 'QG-333', '16', 'You must be the change you wish                   ', 0, '16', 122, '2', 'Success consists of going from failure to failure without             ', 1);
INSERT INTO `work_packages` VALUES (267, 'EG-371', '29', 'Secure SHell (SSH) is a program                   ', 0, '29', 129, '4', 'It provides strong authentication and secure encrypted                ', 0);
INSERT INTO `work_packages` VALUES (268, 'SI-139', '14', 'The Information Pane shows the                    ', 0, '14', 123, '2', 'Success consists of going from failure to failure without             ', 1);
INSERT INTO `work_packages` VALUES (269, 'DF-237', '8', 'What you get by achieving your                    ', 0, '8', 180, '4', 'Navicat provides a wide range advanced features, such                 ', 1);
INSERT INTO `work_packages` VALUES (270, 'NX-887', '3', 'Navicat authorizes you to make                    ', 0, '3', 141, '5', 'The Synchronize to Database function will give you                    ', 1);
INSERT INTO `work_packages` VALUES (271, 'RL-133', '30', 'Actually it is just in an idea                    ', 0, '30', 190, '5', 'Navicat 15 has added support for the system-wide dark mode.           ', 0);
INSERT INTO `work_packages` VALUES (272, 'LE-620', '0000', 'Sometimes you win, sometimes you learn.', 1, '0000', 194, '4', 'In the middle of winter I at last discovered that there               ', 0);
INSERT INTO `work_packages` VALUES (273, 'EM-438', '26', 'In the Objects tab, you can use                   ', 1, '26', 200, '1', 'Anyone who has ever made anything of importance was disciplined.', 0);
INSERT INTO `work_packages` VALUES (274, 'RW-465', '29', 'All the Navicat Cloud objects are                 ', 0, '29', 155, '1', 'To successfully establish a new connection to local/remote            ', 0);
INSERT INTO `work_packages` VALUES (275, 'EW-731', '12', 'In other words, Navicat provides                  ', 0, '12', 175, '1', 'Actually it is just in an idea when feel oneself can                  ', 1);
INSERT INTO `work_packages` VALUES (276, 'CM-975', '26', 'Navicat provides a wide range advanced            ', 1, '26', 195, '1', 'It is used while your ISPs do not allow direct connections,           ', 0);
INSERT INTO `work_packages` VALUES (277, 'UL-291', '20', 'The first step is as good as half over.', 1, '20', 197, '2', 'The Navigation pane employs tree structure which allows               ', 0);
INSERT INTO `work_packages` VALUES (278, 'SV-185', '22', 'Secure Sockets Layer(SSL) is a                    ', 0, '22', 140, '3', 'The reason why a great man is great is that he resolves               ', 1);
INSERT INTO `work_packages` VALUES (279, 'GC-534', '18', 'The Synchronize to Database function              ', 1, '18', 130, '1', 'You will succeed because most people are lazy.', 1);
INSERT INTO `work_packages` VALUES (280, 'WQ-170', '11', 'It can also manage cloud databases                ', 1, '11', 145, '3', 'Optimism is the one quality more associated with success              ', 1);
INSERT INTO `work_packages` VALUES (281, 'YO-716', '7', 'I may not have gone where I intended              ', 0, '7', 183, '1', 'Such sessions are also susceptible to session hijacking,              ', 0);
INSERT INTO `work_packages` VALUES (282, 'XG-501', '3', 'Such sessions are also susceptible                ', 0, '3', 123, '2', 'Champions keep playing until they get it right.                       ', 1);
INSERT INTO `work_packages` VALUES (283, 'AT-467', '29', 'Navicat Monitor is a safe, simple                 ', 0, '29', 133, '2', 'Sometimes you win, sometimes you learn.', 0);
INSERT INTO `work_packages` VALUES (284, 'WP-774', '6', 'I may not have gone where I intended              ', 1, '6', 184, '3', 'Success consists of going from failure to failure without             ', 1);
INSERT INTO `work_packages` VALUES (285, 'HQ-168', '11', 'The Synchronize to Database function              ', 0, '11', 181, '4', 'If the Show objects under schema in navigation pane                   ', 1);
INSERT INTO `work_packages` VALUES (286, 'VE-249', '10', 'Success consists of going from                    ', 1, '10', 157, '2', 'With its well-designed Graphical User Interface(GUI),                 ', 0);
INSERT INTO `work_packages` VALUES (287, 'GX-786', '30', 'Such sessions are also susceptible                ', 1, '30', 157, '1', 'Navicat Monitor can be installed on any local computer                ', 0);
INSERT INTO `work_packages` VALUES (288, 'DI-277', '30', 'Difficult circumstances serve as                  ', 0, '30', 203, '3', 'The Synchronize to Database function will give you                    ', 0);
INSERT INTO `work_packages` VALUES (289, 'GZ-316', '10', 'You will succeed because most people are lazy.', 0, '10', 161, '2', 'All journeys have secret destinations of which the                    ', 1);
INSERT INTO `work_packages` VALUES (290, 'CB-333', '23', 'What you get by achieving your                    ', 1, '23', 123, '3', 'Navicat Cloud could not connect and access your databases.            ', 1);
INSERT INTO `work_packages` VALUES (291, 'PQ-144', '19', 'In a Telnet session, all communications,          ', 1, '19', 202, '3', 'Actually it is just in an idea when feel oneself can                  ', 0);
INSERT INTO `work_packages` VALUES (292, 'AS-402', '5', 'Export Wizard allows you to export                ', 1, '5', 128, '3', 'Navicat provides a wide range advanced features, such                 ', 0);
INSERT INTO `work_packages` VALUES (293, 'XC-153', '24', 'Instead of wondering when your                    ', 0, '24', 211, '3', 'A man’s best friends are his ten fingers.', 1);
INSERT INTO `work_packages` VALUES (294, 'XJ-637', '15', 'The repository database can be                    ', 0, '15', 168, '1', 'Navicat allows you to transfer data from one database                 ', 0);
INSERT INTO `work_packages` VALUES (295, 'OS-332', '8', 'A man is not old until regrets                    ', 0, '8', 161, '1', 'Sometimes you win, sometimes you learn.', 0);
INSERT INTO `work_packages` VALUES (296, 'MM-876', '29', 'The repository database can be                    ', 1, '29', 184, '3', 'The Synchronize to Database function will give you                    ', 0);
INSERT INTO `work_packages` VALUES (297, 'FT-561', '30', 'To connect to a database or schema,               ', 1, '30', 171, '4', 'Secure SHell (SSH) is a program to log in into another                ', 0);
INSERT INTO `work_packages` VALUES (298, 'NT-460', '28', 'In a Telnet session, all communications,          ', 1, '28', 147, '4', 'All journeys have secret destinations of which the                    ', 0);
INSERT INTO `work_packages` VALUES (299, 'AL-610', '0000', 'How we spend our days is, of course,              ', 1, '0000', 155, '1', 'Creativity is intelligence having fun.', 0);
INSERT INTO `work_packages` VALUES (300, 'NS-139', '7', 'Success consists of going from                    ', 1, '7', 173, '4', 'Monitored servers include MySQL, MariaDB and SQL Server,              ', 1);
INSERT INTO `work_packages` VALUES (301, 'KJ-352', '21', 'HTTP Tunneling is a method for                    ', 1, '21', 170, '5', 'Navicat is a multi-connections Database Administration                ', 0);
INSERT INTO `work_packages` VALUES (302, 'UH-965', '18', 'To successfully establish a new                   ', 1, '18', 205, '1', 'Navicat provides powerful tools for working with queries:             ', 0);
INSERT INTO `work_packages` VALUES (303, 'MR-863', '18', 'It wasn’t raining when Noah built the ark.', 1, '18', 127, '4', 'Navicat Monitor requires a repository to store alerts                 ', 1);
INSERT INTO `work_packages` VALUES (304, 'KI-736', '30', 'The Information Pane shows the                    ', 1, '30', 170, '5', 'To get a secure connection, the first thing you need                  ', 1);
INSERT INTO `work_packages` VALUES (305, 'LS-065', '15', 'Always keep your eyes open. Keep                  ', 1, '15', 129, '4', 'If the plan doesn’t work, change the plan, but never the goal.      ', 1);
INSERT INTO `work_packages` VALUES (306, 'WY-658', '9', 'Navicat Data Modeler is a powerful                ', 1, '9', 211, '4', 'Export Wizard allows you to export data from tables,                  ', 1);
INSERT INTO `work_packages` VALUES (307, 'UV-160', '26', 'Creativity is intelligence having fun.', 1, '26', 159, '5', 'All the Navicat Cloud objects are located under different             ', 1);
INSERT INTO `work_packages` VALUES (308, 'EU-999', '8', 'To start working with your server                 ', 1, '8', 195, '4', 'Optimism is the one quality more associated with success              ', 1);
INSERT INTO `work_packages` VALUES (309, 'QO-637', '21', 'Creativity is intelligence having fun.            ', 1, '21', 177, '2', 'In the middle of winter I at last discovered that there               ', 1);
INSERT INTO `work_packages` VALUES (310, 'IR-541', '3', 'All the Navicat Cloud objects are                 ', 1, '3', 192, '2', 'After logged in the Navicat Cloud feature, the Navigation             ', 0);
INSERT INTO `work_packages` VALUES (311, 'VC-754', '9', 'To get a secure connection, the                   ', 1, '9', 203, '5', 'Navicat Monitor requires a repository to store alerts                 ', 0);
INSERT INTO `work_packages` VALUES (312, 'FJ-951', '8', 'To open a query using an external                 ', 0, '8', 119, '4', 'The Main Window consists of several toolbars and panes                ', 1);
INSERT INTO `work_packages` VALUES (313, 'IA-973', '4', 'Export Wizard allows you to export                ', 0, '4', 205, '4', 'Anyone who has ever made anything of importance was disciplined.', 1);
INSERT INTO `work_packages` VALUES (314, 'DU-378', '7', 'Secure SHell (SSH) is a program                   ', 1, '7', 193, '3', 'If the Show objects under schema in navigation pane                   ', 0);
INSERT INTO `work_packages` VALUES (315, 'IY-546', '5', 'A man is not old until regrets                    ', 0, '5', 165, '4', 'Secure Sockets Layer(SSL) is a protocol for transmitting              ', 0);
INSERT INTO `work_packages` VALUES (316, 'KU-233', '13', 'Difficult circumstances serve as                  ', 0, '13', 160, '4', 'To successfully establish a new connection to local/remote            ', 0);
INSERT INTO `work_packages` VALUES (317, 'ZC-830', '11', 'Navicat provides a wide range advanced            ', 0, '11', 126, '1', 'I will greet this day with love in my heart.                          ', 0);
INSERT INTO `work_packages` VALUES (318, 'AC-756', '17', 'Secure SHell (SSH) is a program                   ', 1, '17', 157, '2', 'It collects process metrics such as CPU load, RAM usage,              ', 0);
INSERT INTO `work_packages` VALUES (319, 'UU-137', '4', 'It can also manage cloud databases                ', 0, '4', 190, '3', 'Navicat allows you to transfer data from one database                 ', 0);
INSERT INTO `work_packages` VALUES (320, 'MA-981', '4', 'In a Telnet session, all communications,          ', 1, '4', 165, '4', 'Navicat Monitor requires a repository to store alerts                 ', 0);
INSERT INTO `work_packages` VALUES (321, 'MS-052', '0012', 'A query is used to extract data                   ', 0, '0012', 157, '4', 'If your Internet Service Provider (ISP) does not provide              ', 1);
INSERT INTO `work_packages` VALUES (322, 'GK-031', '27', 'In other words, Navicat provides                  ', 0, '27', 164, '3', 'It is used while your ISPs do not allow direct connections,           ', 1);
INSERT INTO `work_packages` VALUES (323, 'CT-083', '0123', 'The On Startup feature allows you                 ', 0, '0123', 131, '5', 'Navicat Cloud could not connect and access your databases.            ', 1);
INSERT INTO `work_packages` VALUES (324, 'GJ-404', '18', 'The Information Pane shows the                    ', 1, '18', 150, '1', 'Navicat authorizes you to make connection to remote                   ', 1);
INSERT INTO `work_packages` VALUES (325, 'FH-636', '30', 'Success consists of going from                    ', 0, '30', 133, '2', 'Actually it is just in an idea when feel oneself can                  ', 0);
INSERT INTO `work_packages` VALUES (326, 'EV-605', '18', 'Navicat Monitor requires a repository             ', 1, '18', 129, '4', 'What you get by achieving your goals is not as important              ', 1);
INSERT INTO `work_packages` VALUES (327, 'TU-481', '8', 'To connect to a database or schema,               ', 1, '8', 141, '3', 'Creativity is intelligence having fun.', 0);

SET FOREIGN_KEY_CHECKS = 1;
