from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)

def test_alldata():
    response = client.get("/GET_DATA")
    if response.status_code == 200:
        print('My Dearest Tester, Congrats your endpoint GET_DATA has been successfully tested and the response is {}'.format(response.status_code))


def test_lendata():
    response = client.get("/LENGTH_DATA")
    if response.status_code == 200:
        print('My Dearest Tester, Congrats your endpoint LENGTH_DATA has been successfully tested and the response is {}'.format(response.status_code))


def test_insertdata():
    response = client.get("/INSERT_DATA")
    if response.status_code == 200:
        print('My Dearest Tester, Congrats your endpoint INSERT_DATA has been successfully tested and the response is {}'.format(response.status_code))



    
test_alldata()
test_lendata()
test_insertdata()