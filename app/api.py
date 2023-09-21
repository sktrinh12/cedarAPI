from fastapi import FastAPI, Response, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
import requests
from os import getenv
import json
import xml.etree.ElementTree as ET
from pydantic import BaseModel
from typing import Optional

client_name = getenv("CLIENT_NAME", "5bd9dda7fed2a4e521e29809d5b1e6fb")
headers = {"Content-Type": "text/xml; charset=utf-8"}


class GetDataSchema(BaseModel):
    compound_id: str
    barcode: Optional[str] = None
    pha_id: Optional[str] = None


app = FastAPI()

origins = ["http://localhost:3000", "localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"CEDAR": "API"}


@app.get("/cedar")
def get_cedar(data: GetDataSchema = Depends()) -> Response:
    # barcode = "PH00316568"
    # compound_id = "FT002787"
    url = "https://wx.pharmaron.cn/stock5/public/index.php/web/cms"
    soap_message = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" 
            xmlns:urn="urn:cm1">
          <soap12:Body>
          <urn:getlist
            soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <client_name xsi:type="xsd:string">{client_name}</client_name>
            """
    if data.barcode:
        soap_message += f"""
        <barcode xsi:type="xsd:string">{data.barcode}</barcode>"""

    soap_message += f"""
        <Compound_ID xsi:type="xsd:string">{data.compound_id}</Compound_ID>
          </urn:getlist>
          </soap12:Body>
        </soap12:Envelope>
        """
    # print(soap_message)
    response = requests.post(url, data=soap_message, headers=headers)
    if response:
        getlist_json = {"ERROR": "empty xml"}
        xml_string = response.content.decode("utf-8")
        xml_data = ET.fromstring(xml_string)
        getlist = xml_data.find(".//getlist").text
        # print(getlist)
        if getlist:
            getlist_json = json.loads(
                getlist.replace("\n", " ").replace("\t", " ").replace("\r", " ")
            )
            getlist_json = getlist_json["msg"][0]
            # remaining_amt = getlist_json["msg"][0]["remaining_amount"]
        return getlist_json
    else:
        data = {"ERROR": f"status code {response.status_code}: {response.text}"}
    return data
