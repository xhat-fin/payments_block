from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import db
import uvicorn


app = FastAPI(
    debug=True,
    title="Payment Blocking API",
    description="API для управления блокировкой платежей клиентов",
    version="1.0.0"
)


# условная пользовательская сессия. Сейчас всегда тестовый пользователь с id=1
class UserSession:
    def __init__(self):
        self.user_id = 1

    def get_user(self):
        return self.user_id


session = UserSession()


class BlockRequest(BaseModel):
    reason_id: int


class ReasonRequest(BaseModel):
    reason_title: str
    is_fraud: bool = False


@app.post("/api/clients/{unp}/block", tags=['Блокировка'],
          summary="Заблокировать платежи",
          description="Блокировка платежей клиента")
def block_client(unp: str, request: BlockRequest):

    client = db.select_client(unp)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    reason_id = request.reason_id
    reason = db.select_reason(reason_id=reason_id)

    if not reason:
        raise HTTPException(status_code=404, detail="Причина блокировки не найдена")

    if client.get('status_block') and client.get('current_reason_id') == reason_id:
        raise HTTPException(status_code=400, detail="Клиент уже заблокирован с такой причиной")

    user_id = session.get_user()

    db.block(client_id=client.get('id'), reason_id=reason_id, user_id=user_id)

    return {
        "unp": unp,
        "status_block": True,
        "current_reason_id": reason_id,
        "message": "Клиент заблокирован"
    }


@app.post("/api/clients/{unp}/unblock", tags=['Блокировка'],
          summary="Разблокировать платежи",
          description="Разблокировка платежей клиента")
def unblock_client(unp: str):

    client = db.select_client(unp)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    if not client.get('status_block'):
        raise HTTPException(status_code=400, detail="Клиент не заблокирован")

    user_id = session.get_user()

    db.unblock(client_id=client.get('id'), user_id=user_id)

    return {
        "unp": unp,
        "status_block": False,
        "message": "Клиент разблокирован"
    }


@app.get("/api/clients/{unp}", tags=['Клиенты'], summary="Информация по клиенту")
def get_client(unp: str):
    client = db.select_client(unp)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@app.get("/api/clients/", tags=['Клиенты'], summary="Информация по всем клиентам")
def get_clients():
    clients = db.select_clients()
    if not clients:
        raise HTTPException(status_code=400, detail="Клиентов не найдено")
    return clients


@app.post("/api/clients/{unp}", tags=['Клиенты'],
          summary="Создать клиента")
def create_client(unp: str):
    try:
        client = db.select_client(unp)
        if client:
            raise HTTPException(status_code=400, detail="Клиент уже существует")

        success = db.create_client(unp)
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось создать клиента")

        return {"message": f"Клиент УНП: {unp} создан"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


@app.get("/api/clients/block-log/{unp}", tags=['Логи'], summary="История действия по клиенту")
def get_client_logs(unp):
    try:
        client = db.select_client(unp)
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")

        logs = db.select_log(client.get('id'))
        if logs:
            return logs
        else:
            raise HTTPException(status_code=400, detail="Действий по клиенту не найдено")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


@app.get("/api/reasons/", tags=['Причины блокировок'], summary="Все причины блокировок")
def get_reasons():
    reasons = db.select_reasons()
    if not reasons:
        raise HTTPException(status_code=404, detail="Причины блокировок не найдены")
    return reasons


@app.post("/api/reasons/", tags=['Причины блокировок'],
          summary="Создать новую причину блокировки")
def create_reason(request: ReasonRequest):
    reason_title = request.reason_title
    is_fraud = request.is_fraud

    reason = db.select_reason(reason_title=reason_title)
    if reason is not None:
        raise HTTPException(status_code=400, detail="Причина уже существует")

    success = db.create_reason(
        reason_title=reason_title,
        is_fraud=is_fraud
    )

    if not success:
        raise HTTPException(status_code=500, detail="Не удалось создать причину блокировки")

    return {
        "message": "Причина блокировки создана",
        "reason_title": request.reason_title,
        "is_fraud": request.is_fraud
    }


if __name__ == '__main__':
    db.init_db()
    uvicorn.run(app, port=8000)
