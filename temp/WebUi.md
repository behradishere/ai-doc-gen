# ContractTypeController

**Namespace:** `WebUi.Areas.Hr.Controllers`  
**Inherits:** `HrBaseController`  
**Purpose:** Manage CRUD operations for HR Contract Types using MediatR.

---

## Create Contract Type

**Method:** `POST`  
**Route:** `/Definitions/ContractType/ContractType_Create`

Creates a new contract type.

**Request Body:**
```json
{
  "name": "Full-Time",
  "description": "Standard full-time employment contract"
}
```
---

## Edit Contract Type

**Method:** `PUT`  
**Route:** `/ContractType/ContractType_Edit/{id}`

Updates an existing contract type.

**Request Body:**
```json
{
  "contractTypeId": 5,
  "name": "Part-Time",
  "description": "Updated part-time contract details"
}
```
**Response:**
```json
{
  "succeeded": true,
  "message": "Contract type updated successfully"
}
```
---

## List Contract Type

**Method:** `GET`  
**Route:** `/ContractType/ContractType_List`

Retrieves a paginated list of contract types.

**Request Body:**
```json
GET /ContractType/ContractType_List?page=1&pageSize=10
```
**Response:**
```json
{
    "succeeded": true,
    "code": 0,
    "message": "عملیات درخواستی با موفقیت انجام شد",
    "errors": {
        "item1": [],
        "item2": 0
    },
    "data": {
        "lists": [
            {
                "contractTypeId": 0,
                "contractTypeCode": 0,
                "contractTypeName": "string",
                "contractSortId": 0,
                "rowNo": 0,
                "createdBy": 0,
                "lastModifiedBy": null,
                "createdShamsiDate": 0,
                "createdTime": null,
                "lastModifiedShamsiDate": null,
                "lastModifiedTime": null,
                "userTitleCreated": null,
                "userTitleLastModified": null
            }
        ],
        "count": 0,
        "currentPageNumber": 0,
        "currentPageSize": 0
    }
}
```
---

## Delete Contract Type

**Method:** `Delete `  
**Route:** `/ContractType/ContractType_Delete/{id}`

Deletes an existing contract type.

**Request Body:**
```json
{
  "contractTypeId": 0
}
```
**Response:**
```json
{
  "succeeded": true,
  "message": "رکورد مورد نظر حذف شد"
}
```