from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select, func, update

from dbmanager.models import Base, OWAccount, Payment 


class DBManager():    
    def __init__(self, username: str, password: str, host: str, database: str) -> None:
        self.username = username
        self.password = password
        self.database = database
        self.host = host


        #TODO: Change to host
        self.db_url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}/{self.database}"

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

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_supply_size(self):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            #All accounts

            fresh =  await session.execute(select(func.count(OWAccount.id)).select_from(OWAccount).filter(
                OWAccount.type == 0,
                OWAccount.taken == False
            ))
            
            one_role = await session.execute(select(func.count(OWAccount.id)).select_from(OWAccount).filter(
                OWAccount.type == 1,
                OWAccount.taken == False
            ))

            two_role =  await session.execute(select(func.count(OWAccount.id)).select_from(OWAccount).filter(
                OWAccount.type == 2,
                OWAccount.taken == False
            ))

            three_role =  await session.execute(select(func.count(OWAccount.id)).select_from(OWAccount).filter(
                OWAccount.type == 3,
                OWAccount.taken == False
            ))


            fresh_count = fresh.scalar()
            one_role_count = one_role.scalar()
            two_role_count = two_role.scalar()                
            three_role_count = three_role.scalar()
            total = fresh_count + one_role_count + two_role_count + three_role_count 

            return total, fresh_count, one_role_count, two_role_count, three_role_count

    async def get_account(self, id: int) -> OWAccount:
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.id==id)
            result = await session.execute(query)

            return result.scalar()
        
    async def get_accounts(self) -> OWAccount:
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount)
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_account_by_channel(self, channelID: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(OWAccount.channelid==channelID)
            result = await session.execute(query)

            return result.scalars().one()


    async def get_new_account(self, user: str, type: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = select(OWAccount).where(
                OWAccount.taken==False,
                OWAccount.type == type
            )

            result = await session.execute(query)

            account = result.scalars().first()

            if account is not None:                
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

            query = update(OWAccount).filter(
                OWAccount.user == user,
                OWAccount.finished == False
            ).values(
                finished = True,
                description = description
            )
            
            await session.execute(query)
            await session.commit()

    async def set_channel(self, accountID: int, channelID: str):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            
            query = update(OWAccount).filter(
                OWAccount.id == accountID
            ).values(
                channelid = channelID
            )

            await session.execute(query)
            await session.commit()


            '''
            query = select(OWAccount).where(OWAccount.id==accountID)
            result = await session.execute(query)

            account = result.scalars().one()
            account.channelid = channelID '''

    async def set_payment_done(self, id: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            if (id < 1000):
                query = select(Payment).where(Payment.id==id)
            else:
                query = select(Payment).where(Payment.channelid==str(id))
            
            result = await session.execute(query)

            payment = result.scalars().one()
            payment.payed = True

            await session.commit()
            
            return payment
        
    async def set_payment_confirmed(self, id: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = update(Payment).filter(
                Payment.id == id
            ).values(
                confirmed = True
            )

            await session.execute(query)
            await session.commit()

    async def set_payment_info(self, id: int, date: str, amount: int):
        session = async_sessionmaker(self.engine, expire_on_commit=False)

        async with session() as session:
            query = update(Payment).filter(
                Payment.id == id
            ).values(
                paymentDate = date,
                amount = amount
            )

            await session.execute(query)
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

            account_count =  await session.execute(select(func.count(OWAccount.id)).select_from(OWAccount).filter(
                OWAccount.user == username,
                OWAccount.finished == False
            ))

            #A better and lighter approach is to get the count
            
            '''query = select(OWAccount).filter(
                OWAccount.user == username,
                OWAccount.finished == False
            )

            result = await session.execute(query)
            '''

            if  (account_count.scalar() > 0):
                return False
        return True



