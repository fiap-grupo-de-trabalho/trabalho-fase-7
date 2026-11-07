CREATE TABLE sifsm_leituras (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ciclo INT,
    modulo VARCHAR2(40),
    tipo VARCHAR2(20),
    codigo_sensor VARCHAR2(10),
    ocupantes INT,
    temperatura_c NUMBER(5,2),
    consumo_kwh NUMBER(7,2),
    geracao_solar_kwh NUMBER(7,2),
    carga_bateria_pct NUMBER(5,2),
    critico INT,
    status VARCHAR2(15)
);
