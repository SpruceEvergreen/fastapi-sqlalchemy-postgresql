from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Path, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.services.database import get_db
from src.models import Table as TableModel, Reservation as ReservationModel

router = APIRouter()

# alembic upgrade head

# Schemas
class TableBase(BaseModel):
    name: str = Field(min_length=3, description='Name of the table')
    seats: int = Field(description='Amount of seats of the table')
    location: str = Field(description='Table location')

class TableSchemaCreate(TableBase):
    pass

class TableSchema(TableBase):
    id: int = Field(..., description='Unique identifier of the table')

class ReservationBase(BaseModel):
    customer_name: str = Field(min_length=3, description='Customer name')
    reservation_time: datetime = Field(description='Time of reservation')
    duration_minutes: float = Field(description='Reservation duration in minutes')
    table_id: int = Field(description="Id of the table")

class ReservationSchemaCreate(ReservationBase):
    pass

class ReservationSchema(ReservationBase):
    id: int = Field(..., description='Unique identifier of the reservation')

# Методы API:
# GET /tables/ — список всех столиков
@router.get("/tables", response_model=list[TableSchema])
async def get_tables(db: AsyncSession = Depends(get_db)):
    tables = await TableModel.get_all(db)
    return tables

# GET /reservations/ — список всех броней
@router.get("/reservations", response_model=list[ReservationSchema])
async def get_reservations(db: AsyncSession = Depends(get_db)):
    reservations = await ReservationModel.get_all(db)
    return reservations

# POST /tables/ — создать новый столик
@router.post("/tables", response_model=TableSchema, status_code=status.HTTP_201_CREATED)
async def create_table(table: TableSchemaCreate, db: AsyncSession = Depends(get_db)):
    existing_table = await db.execute(select(TableModel).where(TableModel.name == table.name))
    if existing_table.scalar():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT , detail="Table name already exists")

    new_table = await TableModel.create(db, **table.model_dump())
    return new_table

# функция для выявления конфликта броней
def check_reservation(new_res, reservations):
    all_res = []
    for reservation in reservations:
        res_dict = {
            "customer_name": reservation.customer_name,
            "reservation_time": reservation.reservation_time,
            "duration_minutes": reservation.duration_minutes,
            "table_id": reservation.table_id,
        }
        all_res.append(res_dict)

    new_res_end = new_res["reservation_time"] + timedelta(minutes=new_res["duration_minutes"])
    for item in all_res:
        print(f"Item duration minutes type: {type(item['duration_minutes'])}, value: {item['duration_minutes']}")
        exist_res_end = item["reservation_time"] + timedelta(minutes=item["duration_minutes"])
        if item["reservation_time"] <= new_res_end <= exist_res_end:
            return True
        if item["reservation_time"] <= new_res["reservation_time"] <= exist_res_end:
            return True

# POST /reservations/ — создать новую бронь
@router.post("/reservations", response_model=ReservationSchema, status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationSchemaCreate, db: AsyncSession = Depends(get_db)):
    existing_table = await db.execute(select(TableModel).where(TableModel.id == reservation.table_id))
    if not existing_table.scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table with this id doesn't exist")

    temp_reservation = reservation.model_dump()
    result = await db.execute(select(ReservationModel).where(ReservationModel.table_id == temp_reservation["table_id"]))
    reservations = result.scalars()

    if reservations:
        conflict = check_reservation(temp_reservation, reservations)
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Table is booked for this time period')

    new_reservation = await ReservationModel.create(db, **reservation.model_dump())
    return new_reservation

# DELETE /tables/{id} — удалить столик
# Нельзя удалить столик, если у столика есть брони. Сначала нужно удалить связанные со столиком
# брони, после чего можно удалить сам столик.
@router.delete('/table/{table_id}')
async def delete_table(table_id:int = Path(gt=0),db: AsyncSession = Depends(get_db)):
    deleted_table = await TableModel.get(db, table_id)
    if deleted_table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Table not found')
    result = await db.execute(select(ReservationModel).where(ReservationModel.table_id == deleted_table.id))
    found_reservations = result.scalars()
    all_res = []
    for reservation in found_reservations:
        res_dict = {
            "customer_name": reservation.customer_name,
            "reservation_time": reservation.reservation_time,
            "duration_minutes": reservation.duration_minutes,
            "table_id": reservation.table_id,
        }
        all_res.append(res_dict)
    if len(all_res) != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Can't delete table because there are reservations associated with the table. Please delete reservations first")
    deleted_table_dict = {
        'name': deleted_table.name,
        'seats': deleted_table.seats,
        'location': deleted_table.location
    }
    await db.delete(deleted_table)
    await db.commit()
    return deleted_table_dict

# DELETE /reservations/{id} — удалить бронь
@router.delete('/reservation/{reservation_id}')
async def delete_reservation(reservation_id:int = Path(gt=0),db: AsyncSession = Depends(get_db)):
    deleted_reservation = await ReservationModel.get(db, reservation_id)
    if deleted_reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reservation not found')

    deleted_reservation_dict = {
        'customer name': deleted_reservation.customer_name,
        'reservation time':  deleted_reservation.reservation_time,
        'reservation duration': deleted_reservation.duration_minutes
    }
    await db.delete(deleted_reservation)
    await db.commit()
    return deleted_reservation_dict
