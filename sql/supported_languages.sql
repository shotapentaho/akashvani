CREATE TABLE akashvani_languages (
    sequence_id SERIAL PRIMARY KEY,
    language VARCHAR(50) NOT NULL,
    tts_language VARCHAR(50) NOT NULL
);

INSERT INTO akashvani_languages (sequence_id, language, tts_language) VALUES
    (1, 'English', 'English'),
    (2, 'Hindi', 'हिन्दी'),
    (3, 'Bengali', 'বাংলা'),
    (4, 'Telugu', 'తెలుగు'),
    (5, 'Marathi', 'मराठी'),
    (6, 'Tamil', 'தமிழ்'),
    (7, 'Gujarati', 'ગુજરાતી'),
    (8, 'Urdu', 'اردو'),
    (9, 'Kannada', 'ಕನ್ನಡ'),
    (10, 'Odia', 'ଓଡ଼ିଆ'),
    (11, 'Malayalam', 'മലയാളം'),
    (12, 'Punjabi', 'ਪੰਜਾਬੀ');
