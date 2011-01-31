ALTER TABLE quiz_category ADD COLUMN  parent_id type integer;
ALTER TABLE quiz_quizdata ADD COLUMN  question_type integer;
UPDATE quiz_quizdata WHERE question_type is Null set question_type=0;

