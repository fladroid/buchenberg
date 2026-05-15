-- Buchenberg · step2_truncate.sql
-- Tabula raza — briše sve podatke prije novog punjenja.
-- CASCADE se brine o foreign key zavisnostima.

TRUNCATE books CASCADE;
