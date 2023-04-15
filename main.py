import os
import dotenv
from random import choice
from typing import Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend

from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import SessionLocal, engine, Base
from session import SessionData, BasicVerifier
from models import Item, UserSession

Base.metadata.create_all(bind=engine)

CURRENCIES = ["korunek", "peněz", "penízků", "kaček"]

dotenv.load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory="templates")


def pluralize(amount: int, singuar: str, plural: str):
    if amount == 1:
        return f"{amount} {singuar}"
    else:
        return f"{amount} {plural}"


def random_currency():
    return choice(CURRENCIES)


templates.env.globals["pluralize"] = pluralize
templates.env.globals["random_currency"] = random_currency


cookie_params = CookieParameters()
cookie = SessionCookie(
    cookie_name="sesh",
    identifier="general_verifier",
    auto_error=True,
    secret_key=os.getenv("SECRET_KEY"),
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


@app.post("/add/{id}")
async def add(request: Request, id: str, db: Session = Depends(get_db)):
    if session := request.session.get("id"):
        item = db.query(Item).filter_by(id=id).first()
        session = db.query(UserSession).filter_by(id=session).first()

        if item != None and session != None:
            session.items.append(item)
            db.commit()

    return Response(status_code=status.HTTP_200_OK)


@app.post("/remove/{id}")
async def add(request: Request, id: str, db: Session = Depends(get_db)):
    if session := request.session.get("id"):
        item = db.query(Item).filter_by(id=id).first()
        session = db.query(UserSession).filter_by(id=session).first()

        if item != None and session != None:
            session.items.remove(item)
            db.commit()

    return Response(status_code=status.HTTP_200_OK)


class CheckoutDetails(BaseModel):
    paymentMethod: Literal["qr"]
    email: str


@app.post("/checkout")
async def checkout(
    request: Request, details: CheckoutDetails, db: Session = Depends(get_db)
):
    if session_id := request.session.get("id"):
        session = db.query(UserSession).filter_by(id=session_id).first()
        if not session:
            return Response(status_code=status.HTTP_403_FORBIDDEN)

        session_items = session.items
        for item in session_items:
            db.query(Item).filter_by(id=item.id).update({"is_sold": True})

        db.delete(session)

        # TODO: Implement buying logic
        print("there's a buyer!!")
        print(details)

        request.session.clear()
        session = UserSession()

        db.add(session)
        db.commit()
        db.refresh(session)

        request.session.update({"id": str(session.id)})

    return Response(status_code=status.HTTP_200_OK)


async def get_items_in_cart(request: Request, db: Session):
    if session_id := request.session.get("id"):
        session = db.query(UserSession).filter_by(id=session_id).first()
        if not session:
            return 0

        return len(session.items)

    return 0


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    items = db.query(Item).filter_by(is_sold=False).all()

    response = templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "items": items,
            "items_in_cart": await get_items_in_cart(request, db),
        },
    )

    if not request.session.get("id"):
        session = UserSession()

        db.add(session)
        db.commit()
        db.refresh(session)

        request.session.update({"id": str(session.id)})

    return response


@app.get("/product/{id}", response_class=HTMLResponse)
async def product(request: Request, id: str, db: Session = Depends(get_db)):
    item = db.query(Item).filter_by(id=id).first()

    if not item:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "item": item,
            "items_in_cart": await get_items_in_cart(request, db),
        },
    )


@app.get("/cart", response_class=HTMLResponse)
async def product(request: Request, db: Session = Depends(get_db)):
    items = []

    if session_id := request.session.get("id"):
        session = db.query(UserSession).filter_by(id=session_id).first()
        if session:
            items = session.items

    return templates.TemplateResponse("cart.html", {"request": request, "items": items})
