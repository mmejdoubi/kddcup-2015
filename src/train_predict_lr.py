#!/usr/bin/env python

from __future__ import division
from sklearn.cross_validation import StratifiedKFold
from sklearn.metrics import roc_auc_score as AUC
from sklearn.linear_model import LogisticRegression as LR
from sklearn.preprocessing import StandardScaler

import argparse
import logging
import numpy as np
import os
import time

from kaggler.data_io import load_data


def train_predict(train_file, test_file, predict_valid_file, predict_test_file,
                  C, n_fold=5):

    feature_name = os.path.basename(train_file)[:-4]
    logging.basicConfig(format='%(asctime)s   %(levelname)s   %(message)s',
                        level=logging.DEBUG, filename='lr_{}_{}.log'.format(
                                                        C, feature_name
                                                       ))

    logging.info('Loading training and test data...')
    X, y = load_data(train_file)
    X_tst, _ = load_data(test_file)

    logging.info('Normalizing data...')
    scaler = StandardScaler(with_mean=False)
    X = scaler.fit_transform(X)
    X_tst = scaler.transform(X_tst)

    clf = LR(C=C, class_weight='auto', random_state=2015)

    cv = StratifiedKFold(y, n_folds=n_fold, shuffle=True, random_state=2015)

    p_val = np.zeros_like(y)
    for i, (i_trn, i_val) in enumerate(cv, 1):
        logging.info('Training CV #{}...'.format(i))
        clf.fit(X[i_trn], y[i_trn])
        p_val[i_val] = clf.predict_proba(X[i_val])[:, 1]
        logging.info('AUC TRN = {:.6f}'.format(AUC(y[i_trn], clf.predict_proba(X[i_trn])[:, 1])))
        logging.info('AUC VAL = {:.6f}'.format(AUC(y[i_val], p_val[i_val])))

    logging.info('AUC = {:.6f}'.format(AUC(y, p_val)))

    logging.info('Retraining with 100% data...')
    clf.fit(X, y)
    p_tst = clf.predict_proba(X_tst)[:, 1]

    logging.info('Saving predictions...')
    np.savetxt(predict_valid_file, p_val, fmt='%.6f')
    np.savetxt(predict_test_file, p_tst, fmt='%.6f')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-file', required=True, dest='train_file')
    parser.add_argument('--test-file', required=True, dest='test_file')
    parser.add_argument('--predict-valid-file', required=True,
                        dest='predict_valid_file')
    parser.add_argument('--predict-test-file', required=True,
                        dest='predict_test_file')
    parser.add_argument('--C', default=1, type=float, dest='C')

    args = parser.parse_args()

    start = time.time()
    train_predict(train_file=args.train_file,
                  test_file=args.test_file,
                  predict_valid_file=args.predict_valid_file,
                  predict_test_file=args.predict_test_file,
                  C=args.C)
    logging.info('finished ({:.2f} min elasped)'.format((time.time() - start) /
                                                        60))
