import pandas as pd
import numpy as np
import os
import time
import re
from tqdm import tqdm
import pickle
from tqdm import tqdm

if not os.path.exists('data/KOR_fs'):
    os.makedirs('data/KOR_fs')
    
if not os.path.exists('data/KOR_value'):
    os.makedirs('data/KOR_value')

print('재무제표 및 가치지표를 다운로드 합니다')

KOR_ticker = pd.read_csv('data/KOR_ticker.csv', index_col=0)
KOR_ticker['종목코드'] = KOR_ticker['종목코드'].astype(np.str).str.zfill(6)
error_list = []

for i in tqdm(range(0, len(KOR_ticker))):
    
    # 빈 데이터프레임 생성
    data_fs = pd.DataFrame({'' : [np.nan]})
    data_value = pd.DataFrame({'' : [np.nan]})
    
    # 티커 선택
    name = KOR_ticker['종목코드'][i]
    
    # 오류 발생 시 이를 무시하고 다음 루프로 진행
    try:
        # url 생성
        url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A'+name        
        
        # 데이터 다운로드 후 테이블 추출    
        data = pd.read_html(url, displayed_only = False)        
        data_IS = data[0]
        data_BS = data[2]
        data_CF = data[4]
        data_IS = data_IS.iloc[:, 0:(len(data_IS.columns)-2)]
        
        # 클렌징
        data_fs = pd.concat([data_IS, data_BS, data_CF]).reset_index(drop=True)
        data_fs.iloc[:, 0] = data_fs.iloc[:, 0].replace({'계산에 참여한 계정 펼치기':''}, regex = True)
        data_fs = data_fs.set_index(data_fs.columns[0])
        data_fs = data_fs[~data_fs.index.duplicated(keep='first')]
        data_fs = data_fs.filter(like = '12', axis = 1)
        
        # 가치 지표 선택
        value_type = ['지배주주순이익', '자본', '영업활동으로인한현금흐름', '매출액']            
        value_index = data_fs.loc[value_type].iloc[:, -1:]  
        
        # 현재 주가
        url_snap = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A'+name
        data_snap = pd.read_html(url_snap)[0]
        
        price = data_snap.iloc[0, 1].split()[0]
        price = price.replace(",", "")
        price = int(re.findall("[0-9]+", price)[0])
        
        # 상장 주식수
        share = data_snap.iloc[6, 1].split()[0]
        share = share.replace(",", "")
        share = int(re.findall("[0-9]+", share)[0])
        
        data_value = data_value = price / (value_index.iloc[:, [0]] * 100000000 / share)
        data_value.index = ['PER', 'PBR', 'PCR', 'PSR']
        data_value[data_value.iloc[:, 0] < 0] = np.nan     
        data_value = data_value.replace(np.inf, np.nan)
        
    except:
        # 오류 발생시 해당 종목명을 저장하고 다음 루프로 이동        
        error_list.append(name)     
    
    # 다운로드 받은 파일을 생성한 폴더 내 csv 파일로 저장    
    data_fs.to_csv('data/KOR_fs/'+name+'_fs.csv')
    data_value.to_csv('data/KOR_value/'+name+'_value.csv')
    
    # 타임슬립 적용
    time.sleep(1)

print('재무제표를 정리합니다')
data_fs = {}

for i in tqdm(range(0, len(KOR_ticker))):
    name = KOR_ticker['종목코드'][i]
    data_fs[name] = pd.read_csv('data/KOR_fs/'+name+'_fs.csv', index_col=0)

fs_list = {}
fs_item = data_fs['005930'].index

for i in tqdm(fs_item):        
    select_fs = {}
    for j in data_fs:                
        # 해당 항목이 있으면 데이터 선택
        if i in data_fs[j].index:
            select_fs[j] = data_fs[j].loc[[i], :]
        # 해당 항목 없으면 NA 데이터프레임 생성
        else:
            select_fs[j] = pd.DataFrame({'Blank' : [np.nan]})
    
    # 데이터 프레임으로 합쳐주기
    select_fs = pd.concat(select_fs, axis=0)
    
    # 빈 컬럼 삭제 후 클렌징
    select_fs = select_fs.loc[:, ~select_fs.columns.isin(['Blank'])]
    select_fs = select_fs.sort_index(axis = 1)
    select_fs.index = KOR_ticker['종목코드']
    
    fs_list[i] = select_fs

with open('data/KOR_fs.pickle', 'wb') as f:
    pickle.dump(fs_list, f, pickle.HIGHEST_PROTOCOL)

print('가치지표를 정리합니다')

data_value = {}

for i in tqdm(range(0, len(KOR_ticker))):
    name = KOR_ticker['종목코드'][i]
    read_value = pd.read_csv('data/KOR_value/'+name+'_value.csv', index_col=0).transpose()
    data_value[name] = read_value

value_list = pd.concat(data_value, axis=0)
value_list = value_list.loc[:, ['PER', 'PBR', 'PCR', 'PSR']]
value_list.index = KOR_ticker['종목코드']

value_list.to_csv('data/KOR_value.csv')

input("작업을 완료하였습니다. 엔터를 누르면 프로그램이 종료됩니다.")