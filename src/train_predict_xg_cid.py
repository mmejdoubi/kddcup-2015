#!/usr/bin/env python

from __future__ import division
from sklearn.cross_validation import StratifiedKFold
from sklearn.metrics import roc_auc_score as AUC

import argparse
import logging
import numpy as np
import os
import time

from kaggler.data_io import load_data

import xgboost as xgb


PARAM = [[400, 0.005, 4],
          [800, 0.02, 6],
          [400, 0.005, 4],
          [200, 0.005, 4],
          [400, 0.005, 4],
          [400, 0.01, 4],
          [800, 0.005, 4],
          [400, 0.005, 4],
          [400, 0.01, 4],
          [800, 0.005, 4],
          [400, 0.01, 4],
          [800, 0.005, 4],
          [200, 0.01, 4],
          [200, 0.01, 4],
          [200, 0.02, 4],
          [200, 0.02, 5],
          [200, 0.005, 4],
          [400, 0.01, 5],
          [400, 0.005, 4],
          [200, 0.01, 6],
          [200, 0.02, 4],
          [800, 0.005, 4],
          [200, 0.02, 4],
          [200, 0.01, 4],
          [200, 0.005, 4],
          [400, 0.02, 6],
          [800, 0.005, 4],
          [200, 0.005, 4],
          [800, 0.005, 4],
          [200, 0.02, 4],
          [400, 0.01, 5],
          [200, 0.005, 4],
          [200, 0.02, 4],
          [400, 0.005, 4],
          [200, 0.005, 4],
          [400, 0.01, 4],
          [200, 0.02, 5],
          [200, 0.01, 5],
          [200, 0.01, 4]]

def train_predict(train_file, test_file,
                  predict_valid_file, predict_test_file,
                  cid_train_file, cid_test_file):

    feature_name = os.path.basename(train_file)[:-4]
    logging.basicConfig(format='%(asctime)s   %(levelname)s   %(message)s',
                        level=logging.DEBUG,
                        filename='xg_cid_{}.log'.format(feature_name))

    logging.info('Loading course IDs for training and test data')
    cid_trn = np.loadtxt(cid_train_file, dtype=int)
    cid_tst = np.loadtxt(cid_test_file, dtype=int)
    
    logging.info('Loading training and test data...')
    X, y = load_data(train_file)
    X_tst, y_tst = load_data(test_file)

    cv = StratifiedKFold(y, n_folds=5, shuffle=True, random_state=2015)

    p = np.zeros_like(y)
    for i, (i_trn, i_val) in enumerate(cv, 1):
        logging.info('Training model #{}...'.format(i))
        X_trn = X[i_trn]
        y_trn = y[i_trn]
        X_val = X[i_val]
        y_val = y[i_val]
        cid_valtrn = cid_trn[i_trn]
        cid_valtst = cid_trn[i_val]

        p_trn = np.zeros_like(y_trn)
        p_val = np.zeros_like(y_val)
        for j in range(39):
            idx_trn = np.where(cid_valtrn == j)[0]
            idx_val = np.where(cid_valtst == j)[0]

            clf = xgb.XGBClassifier(max_depth=PARAM[j][2],
                                    learning_rate=PARAM[j][1],
                                    n_estimators=PARAM[j][0],
                                    colsample_bytree=1,
                                    subsample=.4,
                                    nthread=6)

            clf.fit(X_trn[idx_trn], y_trn[idx_trn])
            p_trn[idx_trn] = clf.predict_proba(X_trn[idx_trn])[:, 1]
            p_val[idx_val] = clf.predict_proba(X_val[idx_val])[:, 1]
            logging.info('CID #{}: {:.4f}, {:.4f}'.format(
                j,
                AUC(y_trn[idx_trn], p_trn[idx_trn]),
                AUC(y_val[idx_val], p_val[idx_val])
            ))

        logging.info('AUC TRN = {:.6f}'.format(AUC(y_trn, p_trn)))
        logging.info('AUC VAL = {:.6f}'.format(AUC(y_val, p_val)))
        p[i_val] = p_val

    logging.info('AUC = {:.6f}'.format(AUC(y, p)))
    logging.info('Saving CV predictions...')
    np.savetxt(predict_valid_file, p, fmt='%.6f')

    logging.info('Retraining with 100% data...')
    p_tst = np.zeros_like(y_tst)
    n_tst = len(p_tst)
    for j in range(39):
        idx_trn = np.where(cid_trn == j)[0]
        idx_tst = np.where(cid_tst == j)[0]
        logging.info('CID #{}: {:.2f}%'.format(j, len(idx_tst) / n_tst * 100))
        clf.fit(X[idx_trn], y[idx_trn])
        p_tst[idx_tst] = clf.predict_proba(X_tst[idx_tst])[:, 1]

    logging.info('Saving test predictions...')
    np.savetxt(predict_test_file, p_tst, fmt='%.6f')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-file', required=True, dest='train_file')
    parser.add_argument('--test-file', required=True, dest='test_file')
    parser.add_argument('--predict-valid-file', required=True,
                        dest='predict_valid_file')
    parser.add_argument('--predict-test-file', required=True,
                        dest='predict_test_file')
    parser.add_argument('--cid-train-file', required=True,
                        dest='cid_train_file')
    parser.add_argument('--cid-test-file', required=True,
                        dest='cid_test_file')

    args = parser.parse_args()

    start = time.time()
    train_predict(train_file=args.train_file,
                  test_file=args.test_file,
                  predict_valid_file=args.predict_valid_file,
                  predict_test_file=args.predict_test_file,
                  cid_train_file=args.cid_train_file,
                  cid_test_file=args.cid_test_file)
    logging.info('finished ({:.2f} min elasped)'.format((time.time() - start) /
                                                        60))
