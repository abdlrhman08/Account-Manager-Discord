from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column
from sqlalchemy import String

class Base(DeclarativeBase):
    pass

class OWAccount(Base):

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    user: Mapped[str] = mapped_column(String(255), nullable=True)

    serial_number: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    restore_code: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)

    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    phonenum: Mapped[str] = mapped_column(String(15), nullable=True) 

    safe_um_user: Mapped[str] = mapped_column(String(30), nullable=True)
    safe_um_pass: Mapped[str] = mapped_column(String(30), nullable=True)

    security_q: Mapped[str] = mapped_column(String(255), nullable=True)
    q_ans: Mapped[str] = mapped_column(String(255), nullable=True)

    channelid: Mapped[str] = mapped_column(String(255), nullable=True)

    finished: Mapped[bool] = mapped_column(default=False)
    taken: Mapped[bool] = mapped_column(default=False)

class Payment(Base):
    __tablename__ = "payments"


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user: Mapped[str] = mapped_column(String(255), nullable=False)
    paymentDate: Mapped[str] = mapped_column(String(20), nullable=True)
    paymentNum: Mapped[str] = mapped_column(String(15), nullable=False)

    amount: Mapped[int] = mapped_column(nullable=True)

    channelid: Mapped[str] = mapped_column(String(255), nullable=True)

    payed: Mapped[bool] = mapped_column(default=False)
    confirmed: Mapped[bool] = mapped_column(default=False)