CREATE TABLE raw_transactions (
    chck_date DATETIME(6), /* down to miliseconds*/
    payment_type VARCHAR(255),
    category VARCHAR(255), /* cat str */
    amount DOUBLE, /* like float used in the rest of pipeline */
    fraud BOOLEAN
) ENGINE=InnoDB;

CREATE TABLE preprocessed_transactions LIKE raw_transactions;

CREATE TABLE transaction_features (
    amount DOUBLE,
    fraud BOOLEAN,
    z_score DOUBLE,
    z_score_by_category DOUBLE,
    enc_category JSON,
    enc_payment_type JSON,
    is_large_transaction BOOLEAN
) ENGINE=InnoDB;