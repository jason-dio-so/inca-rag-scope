-- inca-rag-scope: Coverage Code to Multiplier Name Mapping (Seed Data)
-- STEP NEXT-GENERAL-MAP-1: Manual 1:1 mapping (ZERO TOLERANCE - no estimation)
-- Created: 2026-01-12
-- Method: Manual matching based on canonical coverage code definitions

-- Delete existing mappings (idempotent)
TRUNCATE TABLE coverage_code_name_map;

-- SECTION 1: DEATH COVERAGES (상해사망, 질병사망)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('S100', '상해사망', 'Accidental death'),
    ('S200', '질병사망', 'Disease death');

-- SECTION 2: SURGERY COVERAGES (수술비)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('S101', '상해수술비', 'Accident surgery'),
    ('S201', '질병수술비', 'Disease surgery');

-- SECTION 3: HOSPITALIZATION (입원비)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('S300', '상해입원비', 'Accident hospitalization');
    -- Note: 질병입원비 not mapped yet (need to find code)

-- SECTION 4: CANCER COVERAGES (암 관련)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('A4200_1', '암진단비(유사암제외)', 'Cancer diagnosis (excluding carcinoma in situ)'),
    ('A4209', '유사암진단비', 'Carcinoma in situ diagnosis'),
    ('A4299_1', '암수술비(유사암제외)', 'Cancer surgery (excluding carcinoma in situ)'),
    ('A4301_1', '유사암수술비', 'Carcinoma in situ surgery'),
    ('A4101', '고액암진단비', 'High-cost cancer diagnosis'),
    ('A4302', '재진단암진단비', 'Cancer re-diagnosis'),
    ('A4104_1', '암직접치료입원일당(1-180,요양병원제외)', 'Cancer hospitalization daily benefit'),
    ('A4105', '항암방사선약물치료비(최초1회한)', 'Anti-cancer radiation/drug therapy (first time)'),
    ('A4102', '표적항암약물허가치료비(최초1회한)', 'Targeted anti-cancer drug therapy (first time)'),
    ('A4103', '카티(CAR-T)항암약물허가치료비', 'CAR-T immunotherapy'),
    ('A9630_1', '다빈치로봇암수술비', 'Da Vinci robot cancer surgery');

-- SECTION 5: CEREBROVASCULAR (뇌혈관)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('A5100', '뇌혈관질환진단비', 'Cerebrovascular disease diagnosis'),
    ('A5104_1', '뇌졸중진단비', 'Stroke diagnosis'),
    ('A5107_1', '뇌출혈진단비', 'Cerebral hemorrhage diagnosis'),
    ('A5200', '뇌혈관질환수술비', 'Cerebrovascular surgery'),
    ('A5300', '혈전용해치료비', 'Thrombolytic therapy');

-- SECTION 6: CARDIOVASCULAR (심장질환)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('A6100_1', '허혈성심장질환진단비', 'Ischemic heart disease diagnosis'),
    ('A6200', '허혈성심장질환수술비', 'Ischemic heart disease surgery'),
    ('A6300_1', '심장질환진단비', 'Heart disease diagnosis');

-- SECTION 7: OTHER DIAGNOSES (기타 진단)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('A9617_1', '골절진단비(치아파절제외)', 'Fracture diagnosis (excluding dental)'),
    ('A9619_1', '화상진단비', 'Burn diagnosis');

-- SECTION 8: DISABILITY (장해)
INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
    ('A1100', '상해후유장해(3~100%)', 'Accidental disability (3-100%)');

-- UNMAPPED CODES (need clarification):
-- A1300 - Unknown
-- A3300_1 - Unknown
-- A4210 - Unknown (possibly another cancer coverage)
-- A5298_001 - Unknown (possibly cerebrovascular related)
-- A9620_1 - Unknown
-- A9640_1 - Unknown

-- Verification query (run after loading):
-- SELECT COUNT(*) as mapped_count FROM coverage_code_name_map;
-- Expected: 23 rows (out of 33 total codes)
