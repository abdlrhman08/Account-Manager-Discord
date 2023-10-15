from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy.types import BigInteger

from sqlalchemy import String, ForeignKey

class Base(DeclarativeBase):
    pass

class OWAccount(Base):

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[int] = mapped_column(nullable=False)
    
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_password: Mapped[str] = mapped_column(String(40), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    user: Mapped[str] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(40), nullable=True)

    battle_tag: Mapped[str] = mapped_column(String(20), nullable=True)
    
    phonenum: Mapped[str] = mapped_column(String(15), nullable=True) 

    safe_um_user: Mapped[str] = mapped_column(String(30), nullable=True)
    safe_um_pass: Mapped[str] = mapped_column(String(30), nullable=True)

    creation_date: Mapped[str] = mapped_column(String(12), nullable=True)
    birthdate: Mapped[str] = mapped_column(String(12), nullable=True)

    finished_date: Mapped[str] = mapped_column(String(12), nullable=True)

    description: Mapped[str] = mapped_column(String(255), nullable=True)

    channelid: Mapped[str] = mapped_column(String(255), nullable=True)

    finished: Mapped[bool] = mapped_column(default=False)
    taken: Mapped[bool] = mapped_column(default=False)


    '''
    hex_secret_key: Mapped[str] = mapped_column(String(41), nullable=True)

    serial: Mapped[str] = mapped_column(String(14), nullable=True)
    restore_code: Mapped[str] = mapped_column(String(10), nullable=True)
    '''

    #TODO: Edit the way of query and and probably refactor the whole database driver

    authenticator: Mapped["Authenticator"] = relationship(back_populates="account", lazy="joined")

class Authenticator(Base):
    __tablename__ = "authenticators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    account: Mapped["OWAccount"] = relationship(back_populates="authenticator", lazy="joined")

    hex_secret_key: Mapped[str] = mapped_column(String(41), nullable=True)

    serial: Mapped[str] = mapped_column(String(14), nullable=True)
    restore_code: Mapped[str] = mapped_column(String(10), nullable=True)

'''
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)

'''

class Payment(Base):
    __tablename__ = "payments"


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    #user: Mapped[str] = mapped_column(String(255), nullable=False)
    paymentDate: Mapped[str] = mapped_column(String(20), nullable=True)
    paymentNum: Mapped[str] = mapped_column(String(15), nullable=False)

    amount: Mapped[int] = mapped_column(nullable=True)

    #channelid: Mapped[str] = mapped_column(String(255), nullable=True)

    payed: Mapped[bool] = mapped_column(default=False)
    confirmed: Mapped[bool] = mapped_column(default=False)