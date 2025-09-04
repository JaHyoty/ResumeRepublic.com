# CareerPathPro Schema Design

This schema defines the relational database structure for CareerPathPro’s Experience and Skills Catalog (ESC). It supports user profiles, work experiences, achievements, tools, skills, publications, and certifications.

---

## 1. Users

```sql
CREATE TABLE users (
  id                   SERIAL PRIMARY KEY,
  email                VARCHAR(255) UNIQUE NOT NULL,
  first_name           VARCHAR(100) NOT NULL,
  last_name            VARCHAR(100) NOT NULL,
  preferred_first_name VARCHAR(100),
  created_at           TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 2. Experiences and Job Titles

```sql
CREATE TABLE experiences (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company     VARCHAR(100) NOT NULL,
  location    VARCHAR(100),
  start_date  DATE NOT NULL,
  end_date    DATE,
  description TEXT
);

CREATE TABLE experience_titles (
  id             SERIAL PRIMARY KEY,
  experience_id  INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
  title          VARCHAR(100) NOT NULL,
  is_primary     BOOLEAN NOT NULL DEFAULT FALSE
);
```

---

## 3. Achievements

```sql
CREATE TABLE achievements (
  id             SERIAL PRIMARY KEY,
  experience_id  INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
  description    TEXT NOT NULL
);
```

---

## 4. Tools and Experience Tools Mapping

```sql
CREATE TABLE tools (
  id   SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE experience_tools (
  experience_id INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
  tool_id       INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
  PRIMARY KEY (experience_id, tool_id)
);
```

---

## 5. Skills

```sql
CREATE TABLE skills (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name             VARCHAR(100) NOT NULL,
  proficiency      VARCHAR(50),
  years_experience DECIMAL(3,1),
  source           VARCHAR(50)
);
```

---

## 6. Publications

```sql
CREATE TABLE publications (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title            VARCHAR(255) NOT NULL,
  co_authors       TEXT,
  publication_date DATE,
  url              VARCHAR(500),
  description      TEXT
);
```

---

## 7. Certifications

```sql
CREATE TABLE certifications (
  id                   SERIAL PRIMARY KEY,
  user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name                 VARCHAR(255) NOT NULL,
  issuing_organization VARCHAR(150),
  date_obtained        DATE,
  expiration_date      DATE,
  credential_url       VARCHAR(500)
);
```

---

