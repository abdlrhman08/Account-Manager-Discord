from dbmanager.models import OWAccount

class utils():

    @classmethod
    def export(self, account: OWAccount) -> str:
        return f"""Info for {account.user} given account
Recovery mail: {account.email}
Password: {account.password}
Phone: {account.phonenum}
SafeUM User: {account.safe_um_user}
SafeUM Pass: {account.safe_um_pass}
Serial Number: {account.serial_number}
Restore Code: {account.restore_code}
Security Question: {account.security_q}
Answer: {account.q_ans}
Description {account.description}"""