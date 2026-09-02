-- AI Study Copilot: initial database foundation
-- Target: Supabase PostgreSQL with pgvector enabled.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE universities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT courses_university_name_key UNIQUE (university_id, name),
    CONSTRAINT courses_id_university_key UNIQUE (id, university_id)
);

CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT semesters_course_name_key UNIQUE (course_id, name),
    CONSTRAINT semesters_id_course_key UNIQUE (id, course_id)
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    course_id UUID NOT NULL,
    semester_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_course_university_fkey
        FOREIGN KEY (course_id, university_id)
        REFERENCES courses (id, university_id) ON DELETE RESTRICT,
    CONSTRAINT users_semester_course_fkey
        FOREIGN KEY (semester_id, course_id)
        REFERENCES semesters (id, course_id) ON DELETE RESTRICT
);

CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT subjects_user_name_key UNIQUE (user_id, name),
    CONSTRAINT subjects_user_code_key UNIQUE (user_id, code)
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_path TEXT NOT NULL UNIQUE,
    mime_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT topics_subject_name_key UNIQUE (subject_id, name),
    CONSTRAINT topics_id_subject_key UNIQUE (id, subject_id)
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL,
    embedding VECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT document_chunks_document_index_key UNIQUE (document_id, chunk_index)
);

CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL,
    topic_id UUID NOT NULL,
    source_document_chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL DEFAULT 'multi_select'
        CHECK (question_type = 'multi_select'),
    options JSONB NOT NULL CHECK (
        jsonb_typeof(options) = 'array' AND jsonb_array_length(options) > 0
    ),
    correct_options JSONB NOT NULL CHECK (
        jsonb_typeof(correct_options) = 'array' AND jsonb_array_length(correct_options) > 0
    ),
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT questions_topic_subject_fkey
        FOREIGN KEY (topic_id, subject_id)
        REFERENCES topics (id, subject_id) ON DELETE CASCADE
);

CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT quiz_questions_quiz_question_key UNIQUE (quiz_id, question_id),
    CONSTRAINT quiz_questions_quiz_position_key UNIQUE (quiz_id, position)
);

CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score_percent NUMERIC(5, 2) CHECK (score_percent BETWEEN 0 AND 100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT quiz_attempts_completed_after_started_check
        CHECK (completed_at IS NULL OR completed_at >= started_at)
);

CREATE TABLE quiz_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_attempt_id UUID NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    selected_options JSONB NOT NULL CHECK (jsonb_typeof(selected_options) = 'array'),
    is_correct BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT quiz_answers_attempt_question_key UNIQUE (quiz_attempt_id, question_id)
);

CREATE TABLE topic_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    questions_attempted INTEGER NOT NULL DEFAULT 0 CHECK (questions_attempted >= 0),
    questions_correct INTEGER NOT NULL DEFAULT 0 CHECK (questions_correct >= 0),
    score_percent NUMERIC(5, 2) NOT NULL DEFAULT 0 CHECK (score_percent BETWEEN 0 AND 100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT topic_performance_correct_within_attempted_check
        CHECK (questions_correct <= questions_attempted),
    CONSTRAINT topic_performance_user_topic_key UNIQUE (user_id, topic_id)
);

CREATE TABLE exam_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL,
    topic_id UUID NOT NULL,
    priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT exam_topics_topic_subject_fkey
        FOREIGN KEY (topic_id, subject_id)
        REFERENCES topics (id, subject_id) ON DELETE CASCADE,
    CONSTRAINT exam_topics_subject_topic_key UNIQUE (subject_id, topic_id)
);

CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    topic_id UUID,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT study_sessions_topic_subject_fkey
        FOREIGN KEY (topic_id, subject_id)
        REFERENCES topics (id, subject_id) ON DELETE CASCADE,
    CONSTRAINT study_sessions_ended_after_started_check
        CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE TABLE revision_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT revision_sessions_completed_after_scheduled_check
        CHECK (completed_at IS NULL OR completed_at >= scheduled_for)
);

CREATE INDEX courses_university_id_idx ON courses (university_id);
CREATE INDEX semesters_course_id_idx ON semesters (course_id);
CREATE INDEX users_university_id_idx ON users (university_id);
CREATE INDEX users_course_id_idx ON users (course_id);
CREATE INDEX users_semester_id_idx ON users (semester_id);
CREATE INDEX subjects_user_id_idx ON subjects (user_id);
CREATE INDEX documents_subject_id_idx ON documents (subject_id);
CREATE INDEX topics_subject_id_idx ON topics (subject_id);
CREATE INDEX document_chunks_topic_id_idx ON document_chunks (topic_id);
CREATE INDEX questions_subject_id_idx ON questions (subject_id);
CREATE INDEX questions_topic_id_idx ON questions (topic_id);
CREATE INDEX questions_source_document_chunk_id_idx ON questions (source_document_chunk_id);
CREATE INDEX quizzes_user_id_idx ON quizzes (user_id);
CREATE INDEX quizzes_subject_id_idx ON quizzes (subject_id);
CREATE INDEX quiz_questions_question_id_idx ON quiz_questions (question_id);
CREATE INDEX quiz_attempts_user_quiz_started_at_idx ON quiz_attempts (user_id, quiz_id, started_at DESC);
CREATE INDEX quiz_answers_question_id_idx ON quiz_answers (question_id);
CREATE INDEX topic_performance_topic_id_idx ON topic_performance (topic_id);
CREATE INDEX exam_topics_topic_id_idx ON exam_topics (topic_id);
CREATE INDEX study_sessions_user_started_at_idx ON study_sessions (user_id, started_at DESC);
CREATE INDEX study_sessions_subject_id_idx ON study_sessions (subject_id);
CREATE INDEX study_sessions_topic_id_idx ON study_sessions (topic_id);
CREATE INDEX revision_sessions_user_scheduled_for_idx ON revision_sessions (user_id, scheduled_for);
CREATE INDEX revision_sessions_topic_id_idx ON revision_sessions (topic_id);
