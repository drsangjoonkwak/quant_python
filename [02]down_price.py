import pandas as pd
import numpy as np
from datetime import date
from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
import requests as rq
from io import BytesIO
import re
import time
from tqdm import tqdm
import pandas_datareader.data as web

if not os.path.exists('data/KOR_price'):
    os.makedirs('data/KOR_price')

print('주가를 다운로드 합니다.')
KOR_ticker = pd.read_csv('data/KOR_ticker.csv', index_col=0)
KOR_ticker['종목코드'] = KOR_ticker['종목코드'].astype(np.str).str.zfill(6)
error_list = []

for i in tqdm(range(0, len(KOR_ticker))): 

    # 빈 데이터프레임 생성
    price = pd.DataFrame({'Price' : [np.nan]})
    price.index = [date.today().strftime("%Y-%m-%d")]
    
    # 티커 선택
    name = KOR_ticker['종목코드'][i]
    
    # 시작일과 종료일 
    fr = (date.today() + relativedelta(years=-5)).strftime("%Y%m%d")
    to = (date.today()).strftime("%Y%m%d")
    
    # 오류 발생 시 이를 무시하고 다음 루프로 진행
    try:
        # 데이터 다운로드
        price = web.DataReader(name, 'naver', start = fr, end = to)
    
    except:
        # 오류 발생시 해당 종목명을 저장하고 다음 루프로 이동
        error_list.append(name)
    
    # 다운로드 받은 파일을 생성한 폴더 내 csv 파일로 저장
    price.to_csv('data/KOR_price/'+name+'_price.csv')
    
    # 타임슬립 적용
    time.sleep(1)    

print('주가를 정리합니다')

KOR_ticker = pd.read_csv('data/KOR_ticker.csv', index_col=0)
KOR_ticker['종목코드'] = KOR_ticker['종목코드'].astype(np.str).str.zfill(6)

price_list = {}

for i in tqdm(range(0, len(KOR_ticker))):
    name = KOR_ticker['종목코드'][i]
    price_list[name] = pd.read_csv('data/KOR_price/'+name+'_price.csv', index_col=0)
    
price_list = pd.DataFrame({tic: data['Close'] for tic, data in price_list.items()})
price_list = price_list.fillna(method='ffill')

price_list.to_csv('data/KOR_price.csv')

input("작업을 완료하였습니다. 엔터를 누르면 프로그램이 종료됩니다.")