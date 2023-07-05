from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

from dbmanager.models import Base, OWAccount, Payment 


class DBManager():    
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password


        #TODO: Change to host
        self.db_url = f"postgresql+asyncpg://{self.username}:{self.password}@localhost/accounts"

        self.engine = create_async_engine(
            self.db_url,

            #For debugging only
            echo=True,
        )

    def __delete__(self):
        self.engine.dispose()

    def __exit__(self):
        self.engine.dispose()


    async def create_tables(self) -> None:
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_account(self, id: int) -> OWAccount:
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.id==id)
            result = await session.execute(query)

            return result.scalars().one()
        
    async def get_account_by_channel(self, channelID: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.channelid==channelID)
            result = await session.execute(query)

            return result.scalars().one()


    async def get_new_account(self, user: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.taken==False)
            result = await session.execute(query)

            account = result.scalars().first()

            if account is None:
                return None

            account.user = user
            account.taken = True

            await session.commit()

            return account
        
    async def get_finished_accounts(self):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.finished==True)
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_payments(self):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(Payment)
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_payment_by_channelid(self, channelid: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(Payment).where(Payment.channelid == channelid)
            result = await session.execute(query)

            return result.scalars().one()
            
    async def get_payment_by_id(self, id: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(Payment).where(Payment.id == id)
            result = await session.execute(query)

            return result.scalars().one()
        
    #TODO: Fix of user has multiple accounts
    #DONE
    async def set_as_finished(self, user: str, description: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).filter(
                OWAccount.user == user,
                OWAccount.finished == False    
            )
            result = await session.execute(query)

            account = result.scalars().one()
            account.finished = True
            account.description = description
            
            await session.commit()

    async def set_channel(self, accountID: int, channelID: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.id==accountID)
            result = await session.execute(query)

            account = result.scalars().one()
            account.channelid = channelID

            await session.commit()

    async def set_payment_done(self, id: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(Payment).where(Payment.id==id)
            result = await session.execute(query)

            payment = result.scalars().one()
            payment.payed = True

            await session.commit()
            
            return payment
        
    async def set_payment_confirmed(self, id: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(Payment).where(Payment.id==id)
            result = await session.execute(query)

            payment = result.scalars().one()
            payment.confirmed = True

            await session.commit()

    async def set_payment_info(self, id: int, date: str, amount: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(Payment).where(Payment.id==id)
            result = await session.execute(query)

            payment = result.scalars().one()
            payment.paymentDate = date
            payment.amount = amount

            await session.commit()

    async def add(self, object):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            session.add(object)
            await session.commit()
            await session.refresh(object)

    async def check_user(self, username: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).filter(
                OWAccount.user == username,
                OWAccount.finished == False
            )

            result = await session.execute(query)

            if len(result.scalars().all()) > 0:
                print("Returned")
                return False
            
        return True



