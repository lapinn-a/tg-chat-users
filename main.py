import asyncio
import io
import os
import sys
import qrcode
import typing
import getpass
import xlsxwriter
from telethon.sync import TelegramClient
from telethon import functions, types, errors, utils
import configparser

# Считываем учетные данные
config = configparser.ConfigParser()
config.read("config.ini")

# Присваиваем значения внутренним переменным
api_id   = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']

def display_url_as_qr(url):
    qr = qrcode.QRCode()
    qr.add_data(url)
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())
    print(url)

async def main():
    password: typing.Callable[[], str] = lambda: getpass.getpass('Please enter your password: ')
    chat: typing.Callable[[], str] = lambda: input('Please enter chat name: ')
    client = TelegramClient(username, api_id, api_hash)
    two_step_detected = False

    try:
        await client.connect()
        if not await client.is_user_authorized():
            qr_login = await client.qr_login()
            display_url_as_qr(qr_login.url)
            await qr_login.wait()
            #client.send_code_request(phone_number)
            #me = client.sign_in(phone_number, input('Enter code: '))
    
        # REST OF YOUR CODE
    except errors.SessionPasswordNeededError:
            two_step_detected = True

    if two_step_detected:
        for _ in range(3):
            try:
                value = password()
                me = await client.sign_in(password=value)
                break
            except errors.PasswordHashInvalidError:
                print('Invalid password. Please try again', file=sys.stderr)
        else:
            raise errors.PasswordHashInvalidError(request=None)
    else:
        me = await client.sign_in(password=password)

    # We won't reach here if any step failed (exit by exception)
    signed, name = 'Signed in successfully as', utils.get_display_name(me)
    try:
        print(signed, name)
    except UnicodeEncodeError:
        # Some terminals don't support certain characters
        print(signed, name.encode('utf-8', errors='ignore')
                            .decode('ascii', errors='ignore'))

    client.iter_dialogs()
    #async for dialog in client.iter_dialogs():
        #print(dialog.name, 'has ID', dialog.id)

    result = client.iter_participants(chat())

    print(result)

    workbook = xlsxwriter.Workbook('users.xlsx')
    worksheet = workbook.add_worksheet()

    i = 0
    async for user in result:
        print(f'{user.id}\t{user.first_name}\t{user.last_name}\t{user.username}\t{user.phone}')
        worksheet.write('A' + str(i), user.id)
        worksheet.write('B' + str(i), user.first_name)
        worksheet.write('C' + str(i), user.last_name)
        worksheet.write('D' + str(i), user.username)
        worksheet.write('E' + str(i), user.phone)
        i = i+1
    #print(str(len(result)) + '/' + str(result.count))

    workbook.close()
    os.system("pause")

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())