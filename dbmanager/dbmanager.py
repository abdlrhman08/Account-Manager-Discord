from datetime import datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select, func, update, exists

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

        self.session = async_sessionmaker(self.engine, expire_on_commit=False)

    def __delete__(self):
        self.engine.dispose()

    def __exit__(self):
        self.engine.dispose()

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    '''  Deprecated   '''
    '''async def get_supply_size(self):
        async with self.session() as session:
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
    '''

    '''Check main account type availability'''
    async def check_availability(self, type: int, sub: bool = False):
        async with self.session() as session:
            
            if (sub):
                availability_query = select(exists().where(
                    OWAccount.type == type,
                    OWAccount.taken == False
                ))
            else:
                availability_query = select(exists().where(
                    OWAccount.type / 10 < type + 1, 
                    OWAccount.type / 10 >= type,
                    OWAccount.taken == False
            ))

            return (await session.execute(availability_query)).scalar()
    
    async def get_supply_size(self, supply_count_list: dict):
        types = None

        for k in supply_count_list.keys():
            supply_count_list[k] = 0

        async with self.session() as session:
            types = (await session.execute(select(OWAccount.type, func.count(OWAccount.type)).select_from(OWAccount).where(
                OWAccount.taken == False
            ).group_by(OWAccount.type))).all()
        
        for row in types:
            supply_count_list["total"] += row[1]
            if (row[0] != 30):
                supply_count_list[f"{int(row[0] / 10)}Total"] += row[1]
            supply_count_list[str(row[0])] = row[1]

    async def get_secret_keys(self):
        async with self.session() as session:
            query = select(
                OWAccount.id,
                OWAccount.hex_secret_key
            ).filter(
                OWAccount.taken == False
            )
            
            return (await session.execute(query)).all()

    async def get_account(self, id: int) -> OWAccount:
        async with self.session() as session:
            query = select(OWAccount).where(OWAccount.id==id)
            result = await session.execute(query)

            return result.scalar()
        
    async def get_accounts(self) -> OWAccount:
        async with self.session() as session:
            query = select(OWAccount)
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_account_by_channel(self, channelID: str):
        async with self.session() as session:
            query = select(OWAccount).where(OWAccount.channelid==channelID)
            result = await session.execute(query)

            return result.scalars().one()
        
    async def get_account_id_by_channel(self, channelID: str):
        async with self.session() as session:
            query = select(
                OWAccount.id
            ).filter(
                OWAccount.channelid == channelID
            )

            result = await session.execute(query)

            return result.one()[0]
        
    async def get_account_type_by_channel(self, channelID: str):
        async with self.session() as session:
            query = select(
                OWAccount.type
            ).filter(
                OWAccount.channelid == channelID
            )

            result = await session.execute(query)

            return result.one()[0]

    async def get_new_account(self, username: str, type: int):
        async with self.session() as session:
            query = select(
                OWAccount.id,
                OWAccount.type,
                OWAccount.email,
                OWAccount.password,
                OWAccount.battle_tag
            ).filter(
                OWAccount.taken==False,
                OWAccount.type == type
            )

            result = await session.execute(query)

            account_data = result.first()

            if account_data is None:                
                return None, None, None, None, None
            
            id : int = account_data[0]
            type: int = account_data[1]
            email: str = account_data[2]
            password: str = account_data[3]
            battle_tag: str = account_data[4]

            set_user_query = update(OWAccount).filter(OWAccount.id == id).values(
                taken = True,
                user = username
            )
            
            await session.execute(set_user_query)
            await session.commit()
            
            return id, type, email, password, battle_tag
            
        
    async def get_finished_accounts(self):
        async with self.session() as session:
            query = select(OWAccount).where(OWAccount.finished==True)
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_payments(self):
        async with self.session() as session:
            query = select(Payment)
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_payments_unconfirmed(self):
        async with self.session() as session:
            query = select(Payment).where(
                Payment.confirmed == False
            )
            result = await session.execute(query)

            return result.scalars().all()
        
    async def get_payment_by_channelid(self, channelid: str):
        async with self.session() as session:
            query = select(Payment).where(Payment.channelid == channelid)
            result = await session.execute(query)

            return result.scalars().one()
            
    async def get_payment_by_id(self, id: str):
        async with self.session() as session:
            query = select(Payment).where(Payment.id == id)
            result = await session.execute(query)

            return result.scalars().one()
        
    #TODO: Fix of user has multiple accounts
    #DONE
    async def set_as_finished(self, user: str, description: str):
        async with self.session() as session:

            query = update(OWAccount).filter(
                OWAccount.user == user,
                OWAccount.finished == False
            ).values(
                finished = True,
                finished_date = datetime.now().strftime("%d/%m/%Y"),
                description = description
            )
            
            await session.execute(query)
            await session.commit()

    async def set_channel(self, accountID: int, channelID: str):
        async with self.session() as session:
            
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
        async with self.session() as session:
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
        async with self.session() as session:
            query = update(Payment).filter(
                Payment.id == id
            ).values(
                confirmed = True
            )

            await session.execute(query)
            await session.commit()

    async def set_payment_info(self, id: int, date: str, amount: int):
        async with self.session() as session:
            query = update(Payment).filter(
                Payment.id == id
            ).values(
                paymentDate = date,
                amount = amount
            )

            await session.execute(query)
            await session.commit()


    async def add(self, object):
        async with self.session() as session:
            session.add(object)
            await session.commit()
            await session.refresh(object)

    async def check_user(self, username: str):
        async with self.session() as session:

            user_check = await session.execute(select(exists().where(
                OWAccount.user == username,
                OWAccount.finished == False
            )))

            return user_check.scalar()

            #A better and lighter approach is to get the count
            
            '''query = select(OWAccount).filter(
                OWAccount.user == username,
                OWAccount.finished == False
            )

            result = await session.execute(query)
            

            if  (account_count.scalar() > 0):
                return False
        return True

            '''



