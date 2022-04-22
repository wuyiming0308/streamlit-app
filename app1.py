from asyncore import write
from distutils.log import error
import zipfile
import streamlit as st
from zipfile import ZipFile
from urllib.request import urlretrieve
import os
import pandas as pd
import os
import validators
import shutil

# Initialize
if 'validUrl' not in st.session_state:
    st.session_state['validUrl'] = False
if 'loadingText' not in st.session_state:
    st.session_state['loadingText'] = ''

# functions


def removeError():
    if 'zipError' in st.session_state:
        del st.session_state['zipError']


def retrieve_and_process():
    st.session_state['loadingText'] = 'processing data......'

    if os.path.exists('./DownloadedFile.zip'):
        os.remove('./DownloadedFile.zip')
    if os.path.exists('./DownloadedFile'):
        shutil.rmtree('./DownloadedFile', ignore_errors=True)

    # specifiying url of zip file
    #url = "https://www.dropbox.com/s/0n0u003pk5avp95/321529.zip?dl=1"
    inputFile = "./DownloadedFile.zip"
    outputDir = "DownloadedFile"
    # put zip file in local directory -- this takes a while.. file is big
    try:
        urlretrieve(st.session_state.urlInput, inputFile)
    except:
        st.session_state['zipError'] = 'Even though you entered an URL, but it is not valid.'
        return
    # unzip contents into output folder -- this takes a while.. file is big
    if not zipfile.is_zipfile(inputFile):
        st.session_state['zipError'] = 'The url you enter does not contains a zipFile'
        return

    removeError()
    with ZipFile(inputFile) as zipObj:
        zipObj.extractall(outputDir)

    # Extract pic names in the folder
    file_list = os.listdir("./DownloadedFile")
    file_list.sort()
    # remove .jpg
    new_list = [s.replace(".jpg", "") for s in file_list]

    # input csv
    # read the csv file (put 'r' before the path string to address any special characters in the path, such as '\'). Don't forget to put the file name at the end of the path + ".csv"
    try:
        CustomerList = pd.read_csv("./liveCustomerList.csv")
        CustomerList['firstName'] = CustomerList['firstName'].str.upper()
        CustomerList['lastName'] = CustomerList['lastName'].str.upper()
        FraudList = pd.read_csv("./liveFraudList.csv")
        FraudList["fraudster"] = '1'

        # change custID list to Dataframe
        custID = pd.DataFrame(new_list, columns=['custID'])
        # change datatype
        custID['custID'] = custID['custID'].astype(int)

        # left join table custID and customerlist
        custIDname = pd.merge(custID, CustomerList, on='custID', how='left')
        custIDnameFraud = pd.merge(custIDname, FraudList, on=[
            'firstName', 'lastName'], how='left')
        custIDnameFraud['fraudster'] = custIDnameFraud['fraudster'].fillna(0)

        # FraudTestOnput.csv
        output = custIDnameFraud[['custID', 'fraudster']]
        st.session_state['output'] = output
    except:
        st.session_state['zipError'] = 'Error processing data, please retry'


# UI
st.write('Step 1: Procide Milestone 2 Input File')


def validateUrl():
    removeError()
    st.session_state['validUrl'] = validators.url(st.session_state.urlInput)


def appendExampleUrl():
    st.session_state.urlInput = 'https://www.dropbox.com/s/0n0u003pk5avp95/321529.zip?dl=1'
    validateUrl()


st.button(label='try example url', on_click=appendExampleUrl)


formc1, formc2 = st.columns([3, 1])
with formc1:
    st.text_input(label='Url Input', value='', key='urlInput',
                  on_change=validateUrl, placeholder='Enter URL of Test Data')
with formc2:
    st.write('')
    st.write('')
    st.button(label='Submit', disabled=not st.session_state.validUrl,
              on_click=retrieve_and_process)

if st.session_state.validUrl:
    st.write('The url you enter is', st.session_state.urlInput, '.')
elif st.session_state.urlInput != '':
    st.error('Please enter a valid url!!')
if 'zipError' in st.session_state:
    st.error(st.session_state.zipError)

st.write('Step 2: Download Fraudster Detection Result')


@st.cache
def convert_df_to_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')


if 'output' in st.session_state:
    st.download_button(
        label='Download',
        data=convert_df_to_csv(st.session_state.output),
        file_name=st.session_state.urlInput[-15:-9]+'.csv',
        mime='text/csv',
    )
else:
    st.button(
        label='No data',
        disabled=True
    )
